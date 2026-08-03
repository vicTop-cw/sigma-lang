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

use std::collections::HashMap;

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
