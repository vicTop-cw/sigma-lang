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

/// Route one GET request; returns (status, JSON body).
fn route(app: &mut MVPApp, path: &str, query: &str) -> (u16, String) {
    let q = parse_query(query);
    let need = |names: &[&str]| -> Option<Vec<i64>> {
        names.iter().map(|n| q.get(*n).copied()).collect()
    };
    let body = match path {
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
                    Err(e) => return (400, serde_json::json!({"error": e}).to_string()),
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
                    Err(e) => return (400, serde_json::json!({"error": e}).to_string()),
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
                        Err(e) => return (400, serde_json::json!({"error": e}).to_string()),
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
                        Err(e) => return (400, serde_json::json!({"error": e}).to_string()),
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
                        Err(e) => return (400, serde_json::json!({"error": e}).to_string()),
                    },
                    Err(_) => return (400, serde_json::json!({"error": "bad entries"}).to_string()),
                },
                None => return (400, serde_json::json!({"error": "need entries"}).to_string()),
            }
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
        // delegation — catch them and reply 400 like the Python backend.
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            route(&mut app.lock().unwrap(), path, query)
        }));
        match result {
            Ok(r) => r,
            Err(_) => (400, serde_json::json!({"error": "rejected"}).to_string()),
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

    // 1. 开户额度   /quota?user=7&monthly=50          → {"quota": [50, 50]}
    let r = http_get(port, "/quota?user=7&monthly=50");
    check!("HTTP /quota", r == serde_json::json!({"quota": [50, 50]}));

    // 2. 发布需求   /post?author=7&bounty=100        → task / quota / points
    let r = http_get(port, "/post?author=7&bounty=100");
    check!("HTTP /post task", r["task"] == serde_json::json!([7, 100, 0, 0]));
    check!("HTTP /post quota", r["quota"] == serde_json::json!([50, 49]));
    check!("HTTP /post points", r["points"] == serde_json::json!([100, 0]));
    let tid = r["task_id"].as_u64().unwrap_or(0);

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

    (passed, total)
}
