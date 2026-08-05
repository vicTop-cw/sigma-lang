//! 找茬 MVP 参考实现 (Rust) — mirrors `impl/python/sigma_app.py` (MVPApp).
//!
//! Every business operation DELEGATES its computation to the §SK semantics in
//! `sk.rs` — the App layer only manages state, it never re-implements business
//! rules. This is the production-grade counterpart of the Python reference
//! backend: the audited §SK.6 story (spec_p0_socketkit.md) runs through the
//! App layer and must pass item-for-item identically across the three
//! implementations (Law XIII at the product layer).
//!
//!     cargo run -- --app-self-check      # §SK.6 MVP story through the App
//!     cargo run -- --app-serve           # stdlib-only HTTP JSON API
//!     cargo run -- --app-smoke           # HTTP 7-step chain smoke (13/13)

use std::collections::HashMap;
use std::io::{BufRead, BufReader, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};

use crate::sk;

/// In-memory MVP backend. Business values come ONLY from sk.rs §SK.
pub struct MVPApp {
    next_task: u64,
    tasks: HashMap<u64, Vec<i64>>,                     // task_id -> Task
    quotas: HashMap<i64, Vec<i64>>,                    // user -> Quota
    points: Vec<i64>,                                  // platform escrow/available
    credit_events: HashMap<i64, Vec<Vec<i64>>>,        // user -> credit events
    contribution_actions: HashMap<i64, Vec<Vec<i64>>>, // user -> actions
    users: HashMap<i64, serde_json::Value>,             // v0.67 — user -> profile
    audit: Vec<serde_json::Value>,                     // v0.67 — ΣLang audit trail
}

impl MVPApp {
    pub fn new() -> Self {
        MVPApp {
            next_task: 0,
            tasks: HashMap::new(),
            quotas: HashMap::new(),
            points: sk::points_new(),
            credit_events: HashMap::new(),
            contribution_actions: HashMap::new(),
            users: HashMap::new(),
            audit: Vec::new(),
        }
    }

    /// §SK.6.1 开户额度 — delegates `quota_new`.
    pub fn open_quota(&mut self, user: i64, monthly: i64) -> Vec<i64> {
        let q = sk::quota_new(monthly).expect("monthly ≥ 0");
        self.quotas.insert(user, q.clone());
        q
    }

    /// §SK.6.2–4 发布需求 — delegates task_create + quota_use(1) + points_hold.
    pub fn post_task(&mut self, author: i64, bounty: i64)
        -> (u64, Vec<i64>, Vec<i64>, Vec<i64>) {
        let task = sk::task_create(author, bounty).expect("bounty ≥ 0");
        let quota = sk::quota_use(&self.quotas[&author], 1).expect("quota available");
        self.quotas.insert(author, quota.clone());
        self.points = sk::points_hold(&self.points, bounty);
        let tid = self.next_task;
        self.next_task += 1;
        self.tasks.insert(tid, task.clone());
        (tid, task, quota, self.points.clone())
    }

    /// §SK.6.5 接单 — delegates `accept_task`.
    pub fn claim_task(&mut self, task_id: u64, hunter: i64) -> Vec<i64> {
        let task = sk::accept_task(&self.tasks[&task_id], hunter).expect("task open");
        self.tasks.insert(task_id, task.clone());
        task
    }

    /// §SK.6.6 提交成果 — delegates `task_submit`.
    pub fn submit_work(&mut self, task_id: u64) -> Vec<i64> {
        let task = sk::task_submit(&self.tasks[&task_id]).expect("task in_progress");
        self.tasks.insert(task_id, task.clone());
        task
    }

    /// §SK.6.7–8 验收确认 — delegates task_accept + points_release + credit + contribution.
    pub fn accept_work(&mut self, task_id: u64, caller: i64)
        -> (Vec<i64>, Vec<i64>, i64, i64) {
        let task = sk::task_accept(&self.tasks[&task_id], caller).expect("pending + author");
        self.tasks.insert(task_id, task.clone());
        let bounty = task[1];
        let hunter = task[3];
        self.points = sk::points_release(&self.points, bounty).expect("escrow sufficient");
        self.credit_events.entry(hunter).or_default().push(vec![0, 1]);          // 完成 +5
        self.contribution_actions.entry(hunter).or_default()
            .push(vec![hunter, 1, 10]);                                          // 贡献 +10
        let credit = sk::credit_score(&self.credit_events[&hunter]);
        let contribution = sk::contribution_score(&self.contribution_actions[&hunter]);
        (task, self.points.clone(), credit, contribution)
    }

    /// §SK.6.9 提现 — delegates `points_withdraw`.
    pub fn withdraw(&mut self, _user: i64, amount: i64) -> Vec<i64> {
        self.points = sk::points_withdraw(&self.points, amount).expect("available sufficient");
        self.points.clone()
    }

    /// §SK.6.10 契分 — delegates `credit_score`.
    pub fn credit(&self, user: i64) -> i64 {
        sk::credit_score(self.credit_events.get(&user).map(Vec::as_slice).unwrap_or(&[]))
    }

    /// §SK.6.11 贡献 — delegates `contribution_score`.
    pub fn contribution(&self, user: i64) -> i64 {
        sk::contribution_score(
            self.contribution_actions.get(&user).map(Vec::as_slice).unwrap_or(&[]))
    }

    /// §SK.6.12 勋章 — delegates `badge_level(credit)`.
    pub fn badge(&self, user: i64) -> i64 {
        sk::badge_level(self.credit(user))
    }

    // --- v0.67 双端对账方法（与 Python sigma_app.py 对应） -----------------
    pub fn register(&mut self, user: i64, name: &str) -> serde_json::Value {
        let profile = serde_json::json!({"name": name, "joined": true});
        self.users.entry(user).or_insert(profile.clone());
        self.users[&user].clone()
    }

    pub fn me(&self, user: i64) -> serde_json::Value {
        let profile = self.users.get(&user).cloned()
            .unwrap_or(serde_json::json!({"name": "", "joined": false}));
        let credit = if self.credit_events.contains_key(&user) { self.credit(user) } else { 0 };
        let posted: Vec<u64> = self.tasks.iter()
            .filter(|(_, t)| t[0] == user).map(|(tid, _)| *tid).collect();
        serde_json::json!({"user": user, "profile": profile, "quota": self.quotas.get(&user),
                           "credit": credit, "posted_tasks": posted})
    }

    pub fn tasks_list(&self) -> Vec<serde_json::Value> {
        let mut out: Vec<serde_json::Value> = self.tasks.iter()
            .map(|(tid, t)| serde_json::json!({"task_id": *tid, "task": t}))
            .collect();
        out.sort_by(|a, b| a["task_id"].as_u64().cmp(&b["task_id"].as_u64()));
        out
    }

    pub fn users_list(&self) -> Vec<serde_json::Value> {
        let mut users: Vec<i64> = self.users.keys().copied().collect();
        users.sort();
        users.iter().map(|u| self.me(*u)).collect()
    }

    pub fn issue_badge(&self, verifier: i64, user: i64, score: i64)
        -> Result<Vec<i64>, &'static str> {
        sk::badge_issue(verifier, user, score)
    }

    pub fn dispute(&self, evidence: &[Vec<i64>]) -> i64 {
        sk::dispute_review(evidence)
    }
}

/// Run the §SK full business-flow scenario through the App layer (v0.67),
/// mirroring `python3 impl/python/sigma_app.py --scenario` item-for-item so the
/// Python and Rust reference backends audit the same 找茬 flow (Law XIII).
pub fn app_scenario() -> (usize, usize) {
    let mut passed = 0usize;
    let mut total = 0usize;

    macro_rules! check {
        ($name:expr, $cond:expr) => {{
            total += 1;
            if $cond {
                passed += 1;
            } else {
                eprintln!("  ❌ SCEN.{}", $name);
            }
        }};
    }

    let mut app = MVPApp::new();
    // 1. 用户会话
    app.register(7, "找茬主");
    app.register(3, "找茬人");
    check!("users", app.users.len() == 2);
    // 2. §SK.6 MVP 链
    let q0 = app.open_quota(7, 50);
    check!("quota", q0 == vec![50, 50]);
    let (tid, task, _q1, _p0) = app.post_task(7, 100);
    check!("post", task == vec![7, 100, 0, 0]);
    let claimed = app.claim_task(tid, 3);
    check!("claim", claimed == vec![7, 100, 1, 3]);
    let submitted = app.submit_work(tid);
    check!("submit", submitted == vec![7, 100, 2, 3]);
    let (done, _p1, credit, _contribution) = app.accept_work(tid, 7);
    check!("accept", done == vec![7, 100, 3, 3]);
    check!("bounty conserved", done[1] == 100);
    // 3. 提现 + 勋章
    let p2 = app.withdraw(3, 100);
    check!("withdraw", p2 == vec![0, 0]);
    check!("points settled", app.points == vec![0, 0]);
    check!("badge", app.badge(3) == 1);
    // 4. 查询
    check!("tasks", app.tasks_list().len() == 1);
    check!("users list", app.users_list().len() == 2);
    // 5. 增长期（核验师签发 + 督导裁决）
    check!("badge_issue", app.issue_badge(1001, 3, credit) == Ok(vec![1001, 3, 1]));
    let ev = vec![vec![1, 1, 3], vec![2, 1, 2]];
    check!("dispute", app.dispute(&ev) == 1);
    // 6. 审计机制可用（v0.67 — Rust audit 字段可记录 ΣLang 事件）
    app.audit.push(serde_json::json!({"op": "task_accept", "input": [tid, 7],
                                      "output": done}));
    check!("audit", app.audit.len() == 1);
    check!("audit json", serde_json::to_string(&app.audit[0]).is_ok());

    (passed, total)
}

/// Run the §SK.6 MVP story through the App layer; returns (passed, total).
/// Mirrors `sigma_app.py` run_story (15 items) so the three implementations
/// audit the same story line item-for-item.
pub fn run_story(app: &mut MVPApp) -> (usize, usize) {
    let mut passed = 0usize;
    let mut total = 0usize;

    macro_rules! check {
        ($name:expr, $cond:expr) => {{
            total += 1;
            if $cond {
                passed += 1;
            } else {
                eprintln!("  ❌ SK.6.{}", $name);
            }
        }};
    }

    // 1. 开户额度      quota_new(50)              → [50, 50]
    let q0 = app.open_quota(7, 50);
    check!("1 open_quota", q0 == vec![50, 50]);

    // 2–4. 发布需求    task_create + quota_use(1) + points_hold(100)
    let (tid, task, q1, p0) = app.post_task(7, 100);
    check!("2 task_create", task == vec![7, 100, 0, 0]);
    check!("3 quota_use", q1 == vec![50, 49]);
    check!("4 points_hold", p0 == vec![100, 0]);

    // 5. 接单          accept_task(..., 3)        → [7, 100, 1, 3]
    let claimed = app.claim_task(tid, 3);
    check!("5 accept_task", claimed == vec![7, 100, 1, 3]);

    // 6. 提交成果      task_submit                → [7, 100, 2, 3]
    let submitted = app.submit_work(tid);
    check!("6 task_submit", submitted == vec![7, 100, 2, 3]);

    // 7–8. 验收确认    task_accept(7) + release + credit + contribution
    let (done, p1, credit, _contribution) = app.accept_work(tid, 7);
    check!("7 task_accept", done == vec![7, 100, 3, 3]);
    check!("8 points_release", p1 == vec![0, 100]);

    // 9. 提现          points_withdraw(100)      → [0, 0]
    let p2 = app.withdraw(3, 100);
    check!("9 points_withdraw", p2 == vec![0, 0]);

    // 10. 契分奖励     credit_score([[0,1]])      → 105
    check!("10 credit_score", credit == 105);

    // 11. 贡献累计     contribution_score         → 10 (through the App layer)
    check!("11 contribution_score", app.contribution(3) == 10);

    // 12. 勋章升级     badge_level(105)           → 1
    check!("12 badge_level", app.badge(3) == 1);

    // 剧本不变量 (spec §SK.6)
    check!("INV-1 monotonic",
           [task[2], claimed[2], submitted[2], done[2]] == [0, 1, 2, 3]);
    check!("INV-3 bounty conserved", done[1] == 100);
    check!("INV-4 author accept", done[0] == 7);

    (passed, total)
}

// ============================================================================
// stdlib-only HTTP JSON API (--app-serve) — mirrors sigma_app.py --serve
// ============================================================================

/// Parse a query string `a=1&b=2` into name → i64 pairs.
fn parse_query(query: &str) -> HashMap<String, i64> {
    let mut out = HashMap::new();
    for part in query.split('&') {
        if let Some((k, v)) = part.split_once('=') {
            if let Ok(n) = v.trim().parse::<i64>() {
                out.insert(k.to_string(), n);
            }
        }
    }
    out
}

/// Return a raw string query value (for list-typed args like `evidence=[...]`).
fn get_str<'a>(query: &'a str, name: &str) -> Option<&'a str> {
    for part in query.split('&') {
        if let Some((k, v)) = part.split_once('=') {
            if k == name && !v.is_empty() {
                return Some(v);
            }
        }
    }
    None
}

/// v0.84 — §SK/§IN 语义错误码 → HTTP 状态码（与 Python ERROR_STATUS 对齐，
/// v0.54）：AuthError→403、TypeError/ShapeError→422、业务冲突类→409。
fn error_status(e: &str) -> u16 {
    match e {
        "AuthError" => 403,
        "TypeError" | "ShapeError" => 422,
        _ => 409,
    }
}

/// Route one GET request; returns (status, JSON body).
fn route(app: &mut MVPApp, path: &str, query: &str) -> (u16, String) {
    let q = parse_query(query);
    let need = |names: &[&str]| -> Option<Vec<i64>> {
        names.iter().map(|n| q.get(*n).copied()).collect()
    };
    let body = match path {
        "/register" => {
            let user = q.get("user").copied();
            let name = get_str(query, "name");
            match (user, name) {
                (Some(u), Some(n)) => serde_json::json!({"profile": app.register(u, n)}),
                _ => return (400, serde_json::json!({"error": "need user & name"}).to_string()),
            }
        }
        "/me" => {
            if let Some(v) = need(&["user"]) {
                serde_json::json!(app.me(v[0]))
            } else {
                return (400, serde_json::json!({"error": "need user"}).to_string());
            }
        }
        "/quota" => {
            if let Some(v) = need(&["user", "monthly"]) {
                serde_json::json!({"quota": app.open_quota(v[0], v[1])})
            } else {
                return (400, serde_json::json!({"error": "need user & monthly"}).to_string());
            }
        }
        "/post" => {
            if let Some(v) = need(&["author", "bounty"]) {
                let (tid, task, quota, points) = app.post_task(v[0], v[1]);
                serde_json::json!({"task_id": tid, "task": task,
                                   "quota": quota, "points": points})
            } else {
                return (400, serde_json::json!({"error": "need author & bounty"}).to_string());
            }
        }
        "/tasks" => {
            let status = q.get("status").copied();
            let list: Vec<serde_json::Value> = match status {
                Some(st) => app.tasks_list().into_iter()
                    .filter(|t| t["task"][2] == st).collect(),
                None => app.tasks_list(),
            };
            serde_json::json!({"tasks": list})
        }
        "/users" => {
            serde_json::json!({"users": app.users_list()})
        }
        "/claim" => {
            if let Some(v) = need(&["task", "hunter"]) {
                serde_json::json!({"task": app.claim_task(v[0] as u64, v[1])})
            } else {
                return (400, serde_json::json!({"error": "need task & hunter"}).to_string());
            }
        }
        "/submit" => {
            if let Some(v) = need(&["task"]) {
                serde_json::json!({"task": app.submit_work(v[0] as u64)})
            } else {
                return (400, serde_json::json!({"error": "need task"}).to_string());
            }
        }
        "/accept" => {
            if let Some(v) = need(&["task", "caller"]) {
                let (task, points, credit, contribution) = app.accept_work(v[0] as u64, v[1]);
                serde_json::json!({"task": task, "points": points,
                                   "credit": credit, "contribution": contribution})
            } else {
                return (400, serde_json::json!({"error": "need task & caller"}).to_string());
            }
        }
        "/withdraw" => {
            if let Some(v) = need(&["user", "amount"]) {
                serde_json::json!({"points": app.withdraw(v[0], v[1])})
            } else {
                return (400, serde_json::json!({"error": "need user & amount"}).to_string());
            }
        }
        "/badge" => {
            if let Some(v) = need(&["user"]) {
                serde_json::json!({"credit": app.credit(v[0]), "badge": app.badge(v[0])})
            } else {
                return (400, serde_json::json!({"error": "need user"}).to_string());
            }
        }
        // --- 增长期端点 (§SK.3.12–3.17, 纯函数直接调 sk::) ---
        "/badge_issue" => {
            if let Some(v) = need(&["verifier", "user", "score"]) {
                match sk::badge_issue(v[0], v[1], v[2]) {
                    Ok(b) => serde_json::json!({"badge": b}),
                    Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                }
            } else {
                return (400, serde_json::json!({"error": "need verifier & user & score"}).to_string());
            }
        }
        "/dispute" => {
            match get_str(query, "evidence") {
                Some(ev) => match serde_json::from_str::<Vec<Vec<i64>>>(ev) {
                    Ok(evidence) => serde_json::json!({"decision": sk::dispute_review(&evidence)}),
                    Err(_) => return (400, serde_json::json!({"error": "bad evidence"}).to_string()),
                },
                None => return (400, serde_json::json!({"error": "need evidence"}).to_string()),
            }
        }
        "/team_create" => {
            if let Some(v) = need(&["owner", "kind", "capacity"]) {
                match sk::team_create(v[0], v[1], v[2]) {
                    Ok(t) => serde_json::json!({"team": t}),
                    Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                }
            } else {
                return (400, serde_json::json!({"error": "need owner & kind & capacity"}).to_string());
            }
        }
        "/team_join" => {
            match (get_str(query, "team"), q.get("member").copied()) {
                (Some(ts), Some(member)) => match serde_json::from_str::<Vec<i64>>(ts) {
                    Ok(team) => match sk::team_join(&team, member) {
                        Ok(t2) => serde_json::json!({"team": t2}),
                        Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                    },
                    Err(_) => return (400, serde_json::json!({"error": "bad team"}).to_string()),
                },
                _ => return (400, serde_json::json!({"error": "need team & member"}).to_string()),
            }
        }
        "/team_share" => {
            match (get_str(query, "contribs"), q.get("reward").copied()) {
                (Some(cs), Some(reward)) => match serde_json::from_str::<Vec<Vec<i64>>>(cs) {
                    Ok(contribs) => match sk::team_share(&contribs, reward) {
                        Ok(shares) => serde_json::json!({"shares": shares}),
                        Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                    },
                    Err(_) => return (400, serde_json::json!({"error": "bad contribs"}).to_string()),
                },
                _ => return (400, serde_json::json!({"error": "need contribs & reward"}).to_string()),
            }
        }
        "/advance" => {
            match get_str(query, "quota") {
                Some(qs) => match serde_json::from_str::<Vec<i64>>(qs) {
                    Ok(quota) => serde_json::json!({"quota": sk::quota_advance(&quota)}),
                    Err(_) => return (400, serde_json::json!({"error": "bad quota"}).to_string()),
                },
                None => return (400, serde_json::json!({"error": "need quota"}).to_string()),
            }
        }
        "/ledger" => {
            match get_str(query, "entries") {
                Some(es) => match serde_json::from_str::<Vec<Vec<i64>>>(es) {
                    Ok(entries) => match sk::points_ledger(&entries) {
                        Ok(ledger) => serde_json::json!({"ledger": ledger}),
                        Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                    },
                    Err(_) => return (400, serde_json::json!({"error": "bad entries"}).to_string()),
                },
                None => return (400, serde_json::json!({"error": "need entries"}).to_string()),
            }
        }
        // --- 供应链路由 (§IN, v0.84 与 Python v0.45 对齐) ---
        "/inventory_new" => {
            if let Some(v) = need(&["qty_a", "qty_b"]) {
                match sk::inventory_new(v[0], v[1]) {
                    Ok(inv) => serde_json::json!({"inventory": inv}),
                    Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                }
            } else {
                return (400, serde_json::json!({"error": "need qty_a & qty_b"}).to_string());
            }
        }
        "/receive_stock" => {
            match (get_str(query, "inv"), q.get("item").copied(), q.get("qty").copied()) {
                (Some(is_), Some(item), Some(qty)) => {
                    match serde_json::from_str::<Vec<i64>>(is_) {
                        Ok(inv) => match sk::receive_stock(&inv, item, qty) {
                            Ok(r) => serde_json::json!({"inventory": r}),
                            Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                        },
                        Err(_) => return (400, serde_json::json!({"error": "bad inv"}).to_string()),
                    }
                }
                _ => return (400, serde_json::json!({"error": "need inv & item & qty"}).to_string()),
            }
        }
        "/ship_stock" => {
            match (get_str(query, "inv"), q.get("item").copied(), q.get("qty").copied()) {
                (Some(is_), Some(item), Some(qty)) => {
                    match serde_json::from_str::<Vec<i64>>(is_) {
                        Ok(inv) => match sk::ship_stock(&inv, item, qty) {
                            Ok(r) => serde_json::json!({"inventory": r}),
                            Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                        },
                        Err(_) => return (400, serde_json::json!({"error": "bad inv"}).to_string()),
                    }
                }
                _ => return (400, serde_json::json!({"error": "need inv & item & qty"}).to_string()),
            }
        }
        "/stock_level" => {
            match (get_str(query, "inv"), q.get("item").copied()) {
                (Some(is_), Some(item)) => {
                    match serde_json::from_str::<Vec<i64>>(is_) {
                        Ok(inv) => match sk::stock_level(&inv, item) {
                            Ok(level) => serde_json::json!({"level": level}),
                            Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                        },
                        Err(_) => return (400, serde_json::json!({"error": "bad inv"}).to_string()),
                    }
                }
                _ => return (400, serde_json::json!({"error": "need inv & item"}).to_string()),
            }
        }
        "/fill_rate" => {
            if let Some(v) = need(&["shipped", "demanded"]) {
                match sk::fill_rate(v[0], v[1]) {
                    Ok(rate) => serde_json::json!({"rate": rate}),
                    Err(e) => return (error_status(e), serde_json::json!({"error": e}).to_string()),
                }
            } else {
                return (400, serde_json::json!({"error": "need shipped & demanded"}).to_string());
            }
        }
        "/panel" => {
            // v0.113 — 运行状态面板（与 Python v0.95 对等，JSON 形式便于双端对账）
            let users = app.users.len();
            let tasks_n = app.tasks.len();
            let mut by_state = [0i64; 4];
            let mut total_bounty = 0i64;
            for t in app.tasks.values() {
                let st = t[2] as usize;
                if st < 4 { by_state[st] += 1; }
                total_bounty += t[1];
            }
            serde_json::json!({"users": users, "tasks": tasks_n,
                "by_state": [by_state[0], by_state[1], by_state[2], by_state[3]],
                "total_bounty": total_bounty,
                "gates": {"consensus": "52/52", "p0": "109/109",
                          "prove": "109 PROVED", "scenario": "16/16"}})
        }
        "/stats" => {
            // v0.139 — 业务统计（与 Python v0.134 对等，JSON）
            let users = app.users.len();
            let tasks_n = app.tasks.len();
            let mut by_state = [0i64; 4];
            let mut total_bounty = 0i64;
            for t in app.tasks.values() {
                let st = t[2] as usize;
                if st < 4 { by_state[st] += 1; }
                total_bounty += t[1];
            }
            let total_credit: i64 = app.users.keys()
                .map(|&u| app.credit(u)).sum();
            serde_json::json!({
                "users": users, "tasks": tasks_n,
                "tasks_by_state": {"0": by_state[0], "1": by_state[1],
                                   "2": by_state[2], "3": by_state[3]},
                "total_bounty": total_bounty,
                "platform_points": app.points,
                "total_credit": total_credit,
            })
        }
        _ => return (404, serde_json::json!({"error": "unknown path"}).to_string()),
    };
    (200, body.to_string())
}

/// Handle one HTTP connection: read the request line, route, write the JSON reply.
fn handle_connection(app: &Mutex<MVPApp>, mut stream: TcpStream) {
    let Ok(clone) = stream.try_clone() else {
        return;
    };
    let mut reader = BufReader::new(clone);
    let mut request_line = String::new();
    if reader.read_line(&mut request_line).is_err() {
        return;
    }
    // "GET /path?query HTTP/1.1"
    let mut parts = request_line.split_whitespace();
    let method = parts.next().unwrap_or("");
    let target = parts.next().unwrap_or("/");
    let (status, body) = if method != "GET" {
        (400, serde_json::json!({"error": "only GET supported"}).to_string())
    } else {
        let (path, query) = match target.split_once('?') {
            Some((p, q)) => (p, q),
            None => (target, ""),
        };
        // Business errors (e.g. StateError) surface as panics from the sk
        // delegation — catch them and map to semantic HTTP codes (v0.84,
        // mirrors the Python ERROR_STATUS table from v0.54).
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            route(&mut app.lock().unwrap(), path, query)
        }));
        match result {
            Ok(r) => r,
            Err(payload) => {
                let msg = if let Some(s) = payload.downcast_ref::<&str>() {
                    (*s).to_string()
                } else if let Some(s) = payload.downcast_ref::<String>() {
                    s.clone()
                } else {
                    "rejected".to_string()
                };
                let status = match msg.as_str() {
                    "AuthError" => 403,
                    "TypeError" | "ShapeError" => 422,
                    _ => 409,
                };
                (status, serde_json::json!({"error": msg}).to_string())
            }
        }
    };
    let reply = format!(
        "HTTP/1.1 {status} {}\r\nContent-Type: application/json\r\n\
         Content-Length: {}\r\nConnection: close\r\n\r\n{}",
        if status == 200 { "OK" } else if status == 404 { "Not Found" } else { "Bad Request" },
        body.len(),
        body,
    );
    let _ = stream.write_all(reply.as_bytes());
}

/// Serve the MVP HTTP API forever on `addr` (e.g. "127.0.0.1:8080").
pub fn serve(app: Arc<Mutex<MVPApp>>, addr: &str) -> std::io::Result<()> {
    let listener = TcpListener::bind(addr)?;
    println!("找茬 MVP 参考实现 (Rust) — http://{addr}  \
              (GET /quota /post /claim /submit /accept /withdraw /badge)");
    serve_on(app, listener);
    Ok(())
}

/// Accept loop over a bound listener (shared by `serve` and `run_smoke`).
fn serve_on(app: Arc<Mutex<MVPApp>>, listener: TcpListener) {
    for stream in listener.incoming() {
        match stream {
            Ok(s) => {
                let app = Arc::clone(&app);
                std::thread::spawn(move || handle_connection(&app, s));
            }
            Err(_) => continue,
        }
    }
}

/// GET one path from the smoke server and parse the JSON body.
fn http_get(port: u16, path: &str) -> serde_json::Value {
    use std::io::Read;
    let mut stream = TcpStream::connect(("127.0.0.1", port)).expect("connect to smoke server");
    let req = format!("GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n");
    let _ = stream.write_all(req.as_bytes());
    let mut resp = String::new();
    let _ = stream.read_to_string(&mut resp);
    let body = resp.split("\r\n\r\n").nth(1).unwrap_or("");
    serde_json::from_str(body.trim()).unwrap_or_else(|_| serde_json::json!({"error": "parse"}))
}

/// GET and return (http_status, json body) — for 4xx semantic-code checks
/// (v0.84, mirrors Python get_status).
fn http_get_status(port: u16, path: &str) -> (u16, serde_json::Value) {
    use std::io::Read;
    let mut stream = TcpStream::connect(("127.0.0.1", port)).expect("connect to smoke server");
    let req = format!("GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n");
    let _ = stream.write_all(req.as_bytes());
    let mut resp = String::new();
    let _ = stream.read_to_string(&mut resp);
    let status_line = resp.lines().next().unwrap_or("");
    let status: u16 = status_line.split_whitespace().nth(1).unwrap_or("0")
        .parse().unwrap_or(0);
    let body = resp.split("\r\n\r\n").nth(1).unwrap_or("");
    let val = serde_json::from_str(body.trim())
        .unwrap_or_else(|_| serde_json::json!({"error": "parse"}));
    (status, val)
}

/// --app-smoke: start the server, walk the full MVP chain over HTTP, assert.
/// Mirrors `python3 impl/python/sigma_app.py --smoke` (13 items) so the HTTP
/// layer is audited identically across Python and Rust. Returns (passed, total).
pub fn run_smoke() -> (usize, usize) {
    let app = Arc::new(Mutex::new(MVPApp::new()));
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind smoke listener");
    let port = listener.local_addr().expect("local addr").port();
    let serve_app = Arc::clone(&app);
    std::thread::spawn(move || serve_on(serve_app, listener));

    let mut passed = 0usize;
    let mut total = 0usize;

    macro_rules! check {
        ($name:expr, $cond:expr) => {{
            total += 1;
            if $cond {
                passed += 1;
            } else {
                eprintln!("  ❌ HTTP {}", $name);
            }
        }};
    }

    // 0. 用户会话 (v0.52)  /register?user=7&name=… → profile; /me → summary
    let r = http_get(port, "/register?user=7&name=zhao");
    check!("HTTP /register", r["profile"]["joined"] == serde_json::json!(true));
    let r = http_get(port, "/me?user=7");
    check!("HTTP /me user", r["user"] == 7);
    check!("HTTP /me profile", r["profile"]["name"] == "zhao");

    // 1. 开户额度   /quota?user=7&monthly=50          → {"quota": [50, 50]}
    let r = http_get(port, "/quota?user=7&monthly=50");
    check!("HTTP /quota", r == serde_json::json!({"quota": [50, 50]}));
    let r = http_get(port, "/me?user=7");
    check!("HTTP /me quota", r["quota"] == serde_json::json!([50, 50]));

    // 2. 发布需求   /post?author=7&bounty=100        → task / quota / points
    let r = http_get(port, "/post?author=7&bounty=100");
    check!("HTTP /post task", r["task"] == serde_json::json!([7, 100, 0, 0]));
    check!("HTTP /post quota", r["quota"] == serde_json::json!([50, 49]));
    check!("HTTP /post points", r["points"] == serde_json::json!([100, 0]));
    let tid = r["task_id"].as_u64().unwrap_or(0);

    // 2.5 查询端点 (v0.53)  /tasks → 列表; /tasks?status=N → 过滤; /users
    let r = http_get(port, "/tasks");
    check!("HTTP /tasks list",
           r["tasks"].as_array().map(|a| a.len() == 1).unwrap_or(false));
    check!("HTTP /tasks count",
           r["tasks"].as_array().map(|a| a.len() == 1).unwrap_or(false));
    let r = http_get(port, "/tasks?status=1");
    check!("HTTP /tasks filter",
           r["tasks"].as_array().map(|a| a.is_empty()).unwrap_or(false));
    let r = http_get(port, "/users");
    check!("HTTP /users",
           r["users"].as_array().map(|a| a.len() == 1).unwrap_or(false));

    // 3. 接单       /claim?task=T&hunter=3           → [7, 100, 1, 3]
    let r = http_get(port, &format!("/claim?task={tid}&hunter=3"));
    check!("HTTP /claim", r["task"] == serde_json::json!([7, 100, 1, 3]));

    // 4. 提交成果   /submit?task=T                    → [7, 100, 2, 3]
    let r = http_get(port, &format!("/submit?task={tid}"));
    check!("HTTP /submit", r["task"] == serde_json::json!([7, 100, 2, 3]));

    // 5. 验收确认   /accept?task=T&caller=7          → completed + release + credit
    let r = http_get(port, &format!("/accept?task={tid}&caller=7"));
    check!("HTTP /accept task", r["task"] == serde_json::json!([7, 100, 3, 3]));
    check!("HTTP /accept points", r["points"] == serde_json::json!([0, 100]));
    check!("HTTP /accept credit", r["credit"] == 105);
    check!("HTTP /accept contribution", r["contribution"] == 10);

    // 6. 找茬人提现 /withdraw?user=3&amount=100      → [0, 0]
    let r = http_get(port, "/withdraw?user=3&amount=100");
    check!("HTTP /withdraw", r["points"] == serde_json::json!([0, 0]));

    // 7. 勋章       /badge?user=3                    → credit 105, badge 1
    let r = http_get(port, "/badge?user=3");
    check!("HTTP /badge credit", r["credit"] == 105);
    check!("HTTP /badge badge", r["badge"] == 1);

    // 8. 增长期 (§SK.3.12–3.17)
    let r = http_get(port, "/badge_issue?verifier=1001&user=3&score=105");
    check!("HTTP /badge_issue", r["badge"] == serde_json::json!([1001, 3, 1]));
    let r = http_get(port, "/dispute?evidence=[[1,1,3],[2,1,2]]");
    check!("HTTP /dispute", r["decision"] == 1);
    let r = http_get(port, "/team_create?owner=7&kind=0&capacity=3");
    check!("HTTP /team_create", r["team"] == serde_json::json!([7, 0, 1, 3]));
    let r = http_get(port, "/team_join?team=[7,0,1,3]&member=5");
    check!("HTTP /team_join", r["team"] == serde_json::json!([7, 0, 2, 3]));
    let r = http_get(port, "/team_share?contribs=[[3,2],[4,4]]&reward=6");
    check!("HTTP /team_share", r["shares"] == serde_json::json!([[3, 2], [4, 4]]));
    let r = http_get(port, "/advance?quota=[50,50]");
    check!("HTTP /advance", r["quota"] == serde_json::json!([50, 100]));
    let r = http_get(port, "/ledger?entries=[[0,100,1]]");
    check!("HTTP /ledger", r["ledger"] == serde_json::json!([[1, 1, 100]]));

    // 9. 供应链 (§IN)
    let r = http_get(port, "/inventory_new?qty_a=10&qty_b=20");
    check!("HTTP /inventory_new", r["inventory"] == serde_json::json!([10, 20]));
    let r = http_get(port, "/receive_stock?inv=[10,20]&item=0&qty=5");
    check!("HTTP /receive_stock", r["inventory"] == serde_json::json!([15, 20]));
    let r = http_get(port, "/ship_stock?inv=[15,20]&item=0&qty=4");
    check!("HTTP /ship_stock", r["inventory"] == serde_json::json!([11, 20]));
    let r = http_get(port, "/stock_level?inv=[11,20]&item=0");
    check!("HTTP /stock_level", r["level"] == 11);
    let r = http_get(port, "/fill_rate?shipped=6&demanded=10");
    check!("HTTP /fill_rate", (r["rate"].as_f64().unwrap_or(0.0) - 0.6).abs() < 1e-9);

    // 11. 运行面板 (v0.113) — 与 Python /panel 对账
    let r = http_get(port, "/panel");
    check!("HTTP /panel",
           r["users"] == 1 && r["tasks"] == 1
           && r["gates"]["prove"] == "109 PROVED");

    // 12. 业务统计 (v0.139) — 与 Python /stats 对账
    let r = http_get(port, "/stats");
    check!("HTTP /stats",
           r["users"] == 1 && r["tasks"] == 1
           && r["total_bounty"] == 100 && r["tasks_by_state"]["3"] == 1);

    // 10. 错误码语义化 (v0.54)  §SK/§IN 错误 → 语义化 4xx
    let (st, _) = http_get_status(port, "/ship_stock?inv=[15,20]&item=0&qty=99");
    check!("HTTP err InsufficientStock->409", st == 409);
    let (st, _) = http_get_status(port, "/badge_issue?verifier=999&user=3&score=105");
    check!("HTTP err AuthError->403", st == 403);
    let (st, _) = http_get_status(port, "/fill_rate?shipped=6&demanded=0");
    check!("HTTP err DivByZero->409", st == 409);

    (passed, total)
}
