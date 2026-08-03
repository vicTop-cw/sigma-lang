//! §SK — SocketKit Protocol: Auditable App Behavior
//! (spec/spec_p0_socketkit.md)
//!
//! Rust-side reference implementation of the SocketKit operations, mirroring
//! `impl/python/sigma_core.py` §SK so the three implementations (Python /
//! Rust / Elixir) behave identically (Law XIII — one symbol, one meaning,
//! one result). Run the self-check with:
//!
//!     cargo run -- --sk-self-check
//!
//! Exit code 0 = all §SK canonical tests pass.

/// Task 状态机 (需求文档 §五): 0=open 1=in_progress 2=pending_review 3=completed
const STATUS_OPEN: i64 = 0;
const STATUS_IN_PROGRESS: i64 = 1;
const STATUS_PENDING: i64 = 2;
const STATUS_COMPLETED: i64 = 3;

/// Task posting: (author, bounty) → [author, bounty, 0, 0] (open, unclaimed).
/// §SK.3.1 — Bounty : Type ≝ ℕ, so a negative bounty is rejected.
pub fn task_create(author: i64, bounty: i64) -> Result<Vec<i64>, &'static str> {
    if bounty < 0 {
        return Err("BountyErr");
    }
    Ok(vec![author, bounty, STATUS_OPEN, 0])
}

/// Task claiming: status 0 → 1 (in_progress), hunter recorded.
/// §SK.3.2 — claiming a non-open task is a StateError.
pub fn accept_task(task: &[i64], hunter: i64) -> Result<Vec<i64>, &'static str> {
    if task[2] != STATUS_OPEN {
        return Err("StateError");
    }
    Ok(vec![task[0], task[1], STATUS_IN_PROGRESS, hunter])
}

/// Work submission: status 1 → 2 (pending_review), hunter preserved.
/// §SK.3.3 — submitting a non-in-progress task is a StateError.
pub fn task_submit(task: &[i64]) -> Result<Vec<i64>, &'static str> {
    if task[2] != STATUS_IN_PROGRESS {
        return Err("StateError");
    }
    Ok(vec![task[0], task[1], STATUS_PENDING, task[3]])
}

/// Acceptance confirmation: status 2 → 3 (completed), hunter preserved.
/// §SK.3.4 — 受茬人单人验收确认 (MVP); accepting a non-pending task is a
/// StateError. INV-4 (授权): only the author (caller ≡ task[0]) may accept
/// their own task, otherwise AuthError.
pub fn task_accept(task: &[i64], caller: i64) -> Result<Vec<i64>, &'static str> {
    if task[2] != STATUS_PENDING {
        return Err("StateError");
    }
    if caller != task[0] {
        return Err("AuthError");
    }
    Ok(vec![task[0], task[1], STATUS_COMPLETED, task[3]])
}

/// Review resolution: opinions[] → decision (1 = accept, 0 = reject).
/// §SK.3.6 — growth-phase 核验师多人评审; decision ≡ 1 if weighted_accept(os)
/// ≥ weighted_reject(os) else 0. Each opinion is [reviewer_id, vote, weight];
/// order-independent by construction.
pub fn review_merge(opinions: &[Vec<i64>]) -> i64 {
    let w_accept: i64 = opinions
        .iter()
        .filter(|o| o[1] == 1)
        .map(|o| o[2])
        .sum();
    let w_reject: i64 = opinions
        .iter()
        .filter(|o| o[1] == 0)
        .map(|o| o[2])
        .sum();
    if w_accept >= w_reject { 1 } else { 0 }
}

/// Contribution scoring: actions[] → points, fold ⊕ over deltas floored at 0.
/// §SK.3.5 — 贡献值终身累计，负数不参与分红. Each action is [actor_id, kind, delta].
pub fn contribution_score(actions: &[Vec<i64>]) -> i64 {
    let total: i64 = actions.iter().map(|a| a[2]).sum();
    total.max(0)
}

/// Credit scoring: events[] → credit (契分制).
/// §SK.3.7 — base 100; kind 0 (complete) +5 per count; kind 1 (breach) ×0.7
/// per count (integer ×7 ÷10, floor); floored at 0. Each event is [kind, count].
pub fn credit_score(events: &[Vec<i64>]) -> i64 {
    let mut credit: i64 = 100;
    for e in events {
        match e[0] {
            0 => credit += 5 * e[1], // complete
            1 => {
                for _ in 0..e[1] {
                    credit = (credit * 7) / 10; // breach ×0.7, floor
                }
            }
            _ => return 0, // unknown kind — treat as no-op
        }
    }
    credit.max(0)
}

/// Law II — encode a List⟨ℕ⟩ to a single ℕ (deterministic, injective-ish).
fn encode_list(xs: &[i64], base: i64) -> i64 {
    xs.iter()
        .enumerate()
        .map(|(i, x)| x * base.pow(i as u32))
        .sum()
}

/// Law II — Task → ℕ.
pub fn encode_task(task: &[i64]) -> i64 {
    encode_list(task, 1000)
}

/// Law II — Opinion → ℕ.
pub fn encode_opinion(opinion: &[i64]) -> i64 {
    encode_list(opinion, 1000)
}

/// Law II — Action → ℕ.
pub fn encode_action(action: &[i64]) -> i64 {
    encode_list(action, 1000)
}

/// Law II — Event → ℕ.
pub fn encode_event(event: &[i64]) -> i64 {
    encode_list(event, 1000)
}

// ============================================================
// §SK.3.9–3.11 — 找茬五大制度补齐 (v0.20, 需求文档 §四)
// 额度制 quota / 积分制 points / 勋章制 badge_level
// ============================================================

/// 额度制: 本月额度 = 剩余额度. §SK.3.9 — monthly ≥ 0.
pub fn quota_new(monthly: i64) -> Result<Vec<i64>, &'static str> {
    if monthly < 0 {
        return Err("TypeError");
    }
    Ok(vec![monthly, monthly])
}

/// 额度制: 扣减额度，不足则 ⊥ QuotaExhausted. §SK.3.9.
pub fn quota_use(quota: &[i64], amount: i64) -> Result<Vec<i64>, &'static str> {
    let (monthly, remaining) = (quota[0], quota[1]);
    if amount > remaining {
        return Err("QuotaExhausted");
    }
    Ok(vec![monthly, remaining - amount])
}

/// 额度制: 月底清零，恢复满额. §SK.3.9.
pub fn quota_reset(quota: &[i64]) -> Vec<i64> {
    let monthly = quota[0];
    vec![monthly, monthly]
}

/// 积分制: 无托管、无可用. §SK.3.10.
pub fn points_new() -> Vec<i64> {
    vec![0, 0]
}

/// 积分制: 冻结（托管中）. §SK.3.10.
pub fn points_hold(points: &[i64], amount: i64) -> Vec<i64> {
    let (escrow, available) = (points[0], points[1]);
    vec![escrow + amount, available]
}

/// 积分制: 释放入可用，不足托管则 ⊥ InsufficientEscrow. §SK.3.10.
pub fn points_release(points: &[i64], amount: i64) -> Result<Vec<i64>, &'static str> {
    let (escrow, available) = (points[0], points[1]);
    if amount > escrow {
        return Err("InsufficientEscrow");
    }
    Ok(vec![escrow - amount, available + amount])
}

/// 积分制: 提现，不足可用则 ⊥ InsufficientPoints. §SK.3.10.
pub fn points_withdraw(points: &[i64], amount: i64) -> Result<Vec<i64>, &'static str> {
    let (escrow, available) = (points[0], points[1]);
    if amount > available {
        return Err("InsufficientPoints");
    }
    Ok(vec![escrow, available - amount])
}

/// 勋章制: 0=铜 1=银 2=金 3=钻石. §SK.3.11.
pub fn badge_level(score: i64) -> i64 {
    if score < 100 {
        0
    } else if score < 300 {
        1
    } else if score < 600 {
        2
    } else {
        3
    }
}

/// 核验师签发勋章: (v, u, s) → [v, u, badge_level(s)]. §SK.3.12 — only
/// authorized verifiers (v ≥ 1000) may issue, otherwise ⊥ AuthError.
pub fn badge_issue(verifier: i64, user: i64, score: i64)
    -> Result<Vec<i64>, &'static str> {
    if verifier < 1000 {
        return Err("AuthError");
    }
    Ok(vec![verifier, user, badge_level(score)])
}

/// 督导处理纠纷: evidence[] → decision (1 = 支持, 0 = 驳回). §SK.3.13 —
/// decision ≡ 1 if weighted_support ≥ weighted_reject else 0. Each evidence
/// is [reviewer_id, side, weight]; order-independent by construction.
pub fn dispute_review(evidence: &[Vec<i64>]) -> i64 {
    let w_support: i64 = evidence.iter()
        .filter(|e| e[1] == 1).map(|e| e[2]).sum();
    let w_reject: i64 = evidence.iter()
        .filter(|e| e[1] == 0).map(|e| e[2]).sum();
    if w_support >= w_reject { 1 } else { 0 }
}

/// 团机制: 受茬团/找茬团创建. §SK.3.14 — capacity ≥ 1 否则 ⊥ TypeError.
/// Team = [owner, kind, size, capacity] (kind 0=受茬团 1=找茬团).
pub fn team_create(owner: i64, kind: i64, capacity: i64)
    -> Result<Vec<i64>, &'static str> {
    if capacity < 1 {
        return Err("TypeError");
    }
    Ok(vec![owner, kind, 1, capacity])
}

/// 团机制: 加入团队. §SK.3.14 — 未满员则加入，满员 → ⊥ TeamFull.
pub fn team_join(team: &[i64], _member: i64) -> Result<Vec<i64>, &'static str> {
    let (owner, kind, size, capacity) = (team[0], team[1], team[2], team[3]);
    if size >= capacity {
        return Err("TeamFull");
    }
    Ok(vec![owner, kind, size + 1, capacity])
}

/// 团内收益按贡献分配: shareᵢ = floor(r·cᵢ/Σc). §SK.3.15 — total = 0 → ⊥ DivByZero.
pub fn team_share(contribs: &[Vec<i64>], reward: i64)
    -> Result<Vec<Vec<i64>>, &'static str> {
    let total: i64 = contribs.iter().map(|e| e[1]).sum();
    if total == 0 {
        return Err("DivByZero");
    }
    Ok(contribs.iter().map(|e| vec![e[0], reward * e[1] / total]).collect())
}

/// 额度预支: [m, r] → [m, r + m]. §SK.3.16.
pub fn quota_advance(quota: &[i64]) -> Vec<i64> {
    let (monthly, remaining) = (quota[0], quota[1]);
    vec![monthly, remaining + monthly]
}

/// 积分来源可追溯: entries[] → [[entry_id, source_id, amount], …]. §SK.3.17 —
/// source_id ≥ 1 方可追溯否则 ⊥ NotTraceable；amount ≥ 0（ℕ）.
pub fn points_ledger(entries: &[Vec<i64>]) -> Result<Vec<Vec<i64>>, &'static str> {
    let mut ledger = Vec::new();
    for (i, e) in entries.iter().enumerate() {
        let (_kind, amount, source) = (e[0], e[1], e[2]);
        if source < 1 {
            return Err("NotTraceable");
        }
        if amount < 0 {
            return Err("TypeError");
        }
        ledger.push(vec![(i + 1) as i64, source, amount]);
    }
    Ok(ledger)
}

// ============================================================
// §IN — Inventory Protocol (spec_p0_inventory.md, v0.41)
// ============================================================

/// 开仓: (qtyA, qtyB) → [qtyA, qtyB]. §IN.3.1 — 库存 ≥ 0.
pub fn inventory_new(qty_a: i64, qty_b: i64) -> Result<Vec<i64>, &'static str> {
    if qty_a < 0 || qty_b < 0 {
        return Err("TypeError");
    }
    Ok(vec![qty_a, qty_b])
}

/// 入库: 加库存（可加性）. §IN.3.2 — item 0/1 否则 UnknownItem.
pub fn receive_stock(inventory: &[i64], item: i64, qty: i64)
    -> Result<Vec<i64>, &'static str> {
    if item != 0 && item != 1 {
        return Err("UnknownItem");
    }
    if qty < 0 {
        return Err("TypeError");
    }
    let mut inv = inventory.to_vec();
    inv[item as usize] += qty;
    Ok(inv)
}

/// 出库: 扣库存，不超卖. §IN.3.3 — qty ≤ held 否则 InsufficientStock.
pub fn ship_stock(inventory: &[i64], item: i64, qty: i64)
    -> Result<Vec<i64>, &'static str> {
    if item != 0 && item != 1 {
        return Err("UnknownItem");
    }
    if qty < 0 {
        return Err("TypeError");
    }
    if qty > inventory[item as usize] {
        return Err("InsufficientStock");
    }
    let mut inv = inventory.to_vec();
    inv[item as usize] -= qty;
    Ok(inv)
}

/// 库存水位: inventory[item]. §IN.3.4 — item 0/1 否则 TypeError.
pub fn stock_level(inventory: &[i64], item: i64) -> Result<i64, &'static str> {
    if item != 0 && item != 1 {
        return Err("TypeError");
    }
    Ok(inventory[item as usize])
}

/// 履约率: shipped / demanded. §IN.3.5 — demanded = 0 → DivByZero.
pub fn fill_rate(shipped: i64, demanded: i64) -> Result<f64, &'static str> {
    if demanded == 0 {
        return Err("DivByZero");
    }
    Ok(shipped as f64 / demanded as f64)
}

/// Law II — Quota → ℕ.
pub fn encode_quota(quota: &[i64]) -> i64 {
    encode_list(quota, 1000)
}

/// Law II — Points → ℕ.
pub fn encode_points(points: &[i64]) -> i64 {
    encode_list(points, 1000)
}

/// Run the §SK self-check (mirrors `sigma_core.py` §SK block); returns
/// (passed, total).
pub fn self_check() -> (usize, usize) {
    let mut passed = 0usize;
    let mut total = 0usize;

    macro_rules! check {
        ($name:expr, $cond:expr) => {{
            total += 1;
            if $cond {
                passed += 1;
            } else {
                eprintln!("  ❌ SK.{}", $name);
            }
        }};
    }

    // §SK.3.1 task_create
    check!("task_create_shape", task_create(1, 100) == Ok(vec![1, 100, 0, 0]));
    check!("task_create_open", task_create(5, 50).map(|t| t[2]) == Ok(0));
    check!("task_create_unclaimed", task_create(5, 50).map(|t| t[3]) == Ok(0));
    check!("task_create_bounty_ge0", task_create(2, 0) == Ok(vec![2, 0, 0, 0]));
    check!("task_create_neg_bounty_rejected", task_create(1, -5).is_err());

    // §SK.3.2 accept_task
    let t_open = task_create(7, 100).unwrap();
    check!("accept_task_claim", accept_task(&t_open, 3) == Ok(vec![7, 100, 1, 3]));
    let t_open2 = task_create(2, 0).unwrap();
    check!("accept_task_in_progress", accept_task(&t_open2, 9).map(|t| t[2]) == Ok(1));
    let t_claimed = accept_task(&t_open, 3).unwrap();
    check!("accept_task_non_open_rejected", accept_task(&t_claimed, 5).is_err());

    // §SK.3.3 task_submit
    let t_sub = task_submit(&t_claimed).unwrap();
    check!("task_submit_pending", t_sub == vec![7, 100, 2, 3]);
    check!("task_submit_hunter_preserved", task_submit(&t_claimed).map(|t| t[3]) == Ok(3));
    check!("task_submit_non_in_progress_rejected", task_submit(&t_open).is_err());

    // §SK.3.4 task_accept
    check!("task_accept_completed", task_accept(&t_sub, 7) == Ok(vec![7, 100, 3, 3]));
    check!("task_accept_hunter_preserved", task_accept(&t_sub, 7).map(|t| t[3]) == Ok(3));
    check!("task_accept_non_author_rejected", task_accept(&t_sub, 9).is_err());
    check!("task_accept_non_pending_rejected", task_accept(&t_open, 7).is_err());

    // §SK.3.6 review_merge
    let os_accept = vec![vec![1, 1, 3], vec![2, 1, 2]];
    check!("review_merge_accept", review_merge(&os_accept) == 1); // 5 ≥ 0
    let os_reject = vec![vec![1, 0, 3], vec![2, 1, 2]];
    check!("review_merge_reject", review_merge(&os_reject) == 0); // 2 < 3
    let os_tie = vec![vec![1, 0, 3], vec![2, 1, 3]];
    check!("review_merge_tie_accept", review_merge(&os_tie) == 1); // 3 ≥ 3
    let os_bin = vec![vec![1, 1, 1], vec![2, 0, 1]];
    check!("review_merge_binary", (0..=1).contains(&review_merge(&os_bin)));
    let os_a = vec![vec![1, 1, 3], vec![2, 0, 2], vec![3, 1, 1]];
    let os_rev = vec![vec![3, 1, 1], vec![1, 1, 3], vec![2, 0, 2]];
    check!("review_merge_order_indep", review_merge(&os_a) == review_merge(&os_rev));

    // §SK.3.5 contribution_score
    let acts = vec![vec![1, 1, 3], vec![2, 2, 4]];
    check!("contribution_fold", contribution_score(&acts) == 7);
    let acts_floor = vec![vec![1, 1, -5], vec![2, 2, 3]];
    check!("contribution_floor_at_0", contribution_score(&acts_floor) == 0); // -2 floored
    let acts_z = vec![vec![1, 1, 3]];
    let acts_z0 = vec![vec![1, 1, 3], vec![9, 0, 0]];
    check!("contribution_zero_neutral", contribution_score(&acts_z) == contribution_score(&acts_z0));

    // §SK.3.7 credit_score
    check!("credit_base", credit_score(&[]) == 100);
    check!("credit_complete", credit_score(&[vec![0, 1]]) == 105);
    check!("credit_breach", credit_score(&[vec![1, 1]]) == 70); // 100×0.7
    check!("credit_breach_then_complete",
           credit_score(&[vec![1, 1], vec![0, 1]]) == 75); // 70+5
    check!("credit_double_breach", credit_score(&[vec![1, 2]]) == 49); // 70×0.7

    // §SK.3.9 额度制 quota
    check!("quota_new_shape", quota_new(50) == Ok(vec![50, 50]));
    check!("quota_use", quota_use(&quota_new(50).unwrap(), 20) == Ok(vec![50, 30]));
    check!("quota_reset",
           quota_reset(&quota_use(&quota_new(50).unwrap(), 20).unwrap()) == vec![50, 50]);
    check!("quota_use_exhausted_rejected", quota_use(&quota_new(50).unwrap(), 60).is_err());

    // §SK.3.10 积分制 points
    check!("points_new_shape", points_new() == vec![0, 0]);
    check!("points_hold", points_hold(&points_new(), 100) == vec![100, 0]);
    check!("points_release",
           points_release(&points_hold(&points_new(), 100), 100) == Ok(vec![0, 100]));
    check!("points_withdraw",
           points_withdraw(&points_release(&points_hold(&points_new(), 100), 100).unwrap(), 40)
               == Ok(vec![0, 60]));
    check!("points_release_insufficient_escrow_rejected",
           points_release(&points_new(), 10).is_err());
    check!("points_withdraw_insufficient_available_rejected",
           points_withdraw(&points_new(), 10).is_err());

    // §SK.3.11 勋章制 badge_level
    check!("badge_zero", badge_level(0) == 0);
    check!("badge_bronze", badge_level(50) == 0);
    check!("badge_silver", badge_level(150) == 1);
    check!("badge_gold", badge_level(450) == 2);
    check!("badge_diamond", badge_level(900) == 3);
    check!("badge_bounded", (0..=3).contains(&badge_level(12345)));
    check!("badge_monotonic", badge_level(100) <= badge_level(200));
    check!("encode_quota_nat", encode_quota(&[50, 30]) >= 0);
    check!("encode_points_nat", encode_points(&[0, 60]) >= 0);

    // §SK.3.12 核验师签发勋章 badge_issue
    check!("badge_issue_silver", badge_issue(1001, 3, 105) == Ok(vec![1001, 3, 1]));
    check!("badge_issue_gold", badge_issue(1002, 3, 450) == Ok(vec![1002, 3, 2]));
    check!("badge_issue_diamond", badge_issue(1001, 3, 900) == Ok(vec![1001, 3, 3]));
    check!("badge_issue_unauthorized_rejected", badge_issue(999, 3, 105).is_err());

    // §SK.3.13 督导处理纠纷 dispute_review
    let ev_sup = vec![vec![1, 1, 3], vec![2, 1, 2]];
    check!("dispute_support", dispute_review(&ev_sup) == 1); // 5 ≥ 0
    let ev_rej = vec![vec![1, 0, 5], vec![2, 1, 2]];
    check!("dispute_reject", dispute_review(&ev_rej) == 0); // 2 < 5
    let ev_bin = vec![vec![1, 1, 1], vec![2, 0, 1]];
    check!("dispute_binary", (0..=1).contains(&dispute_review(&ev_bin)));
    let ev_a = vec![vec![1, 1, 3], vec![2, 0, 2], vec![3, 1, 1]];
    let ev_rev = vec![vec![3, 1, 1], vec![1, 1, 3], vec![2, 0, 2]];
    check!("dispute_order_indep", dispute_review(&ev_a) == dispute_review(&ev_rev));

    // §SK.3.14 团机制 team_create / team_join
    check!("team_create_shape", team_create(7, 0, 3) == Ok(vec![7, 0, 1, 3]));
    check!("team_create_finder", team_create(3, 1, 2) == Ok(vec![3, 1, 1, 2]));
    check!("team_create_zero_capacity_rejected", team_create(7, 0, 0).is_err());
    check!("team_join", team_join(&team_create(7, 0, 3).unwrap(), 5) == Ok(vec![7, 0, 2, 3]));
    check!("team_join_full_rejected", team_join(&vec![7, 0, 2, 2], 5).is_err());

    // §SK.3.15 团内收益按贡献分配 team_share
    check!("team_share_even",
           team_share(&[vec![3, 2], vec![4, 4]], 6) == Ok(vec![vec![3, 2], vec![4, 4]]));
    check!("team_share_weighted",
           team_share(&[vec![3, 1], vec![4, 3]], 10) == Ok(vec![vec![3, 2], vec![4, 7]]));
    check!("team_share_zero_total_rejected",
           team_share(&[vec![3, 0], vec![4, 0]], 5).is_err());

    // §SK.3.16 额度预支 quota_advance
    check!("quota_advance_full", quota_advance(&quota_new(50).unwrap()) == vec![50, 100]);
    check!("quota_advance_used", quota_advance(&vec![50, 30]) == vec![50, 80]);
    check!("quota_reset_after_advance",
           quota_reset(&quota_advance(&quota_new(50).unwrap())) ==
           quota_reset(&quota_new(50).unwrap()));

    // §SK.3.17 积分来源可追溯 points_ledger
    check!("points_ledger_single",
           points_ledger(&[vec![0, 100, 1]]) == Ok(vec![vec![1, 1, 100]]));
    check!("points_ledger_multi",
           points_ledger(&[vec![0, 50, 2], vec![1, 30, 3]])
               == Ok(vec![vec![1, 2, 50], vec![2, 3, 30]]));
    check!("points_ledger_untraceable_rejected",
           points_ledger(&[vec![0, 100, 0]]).is_err());

    // §SK.4 encodings (Law II)
    check!("encode_task_nat", encode_task(&[1, 2, 0, 0]) >= 0);
    check!("encode_distinct", encode_task(&[1, 2, 0, 0]) != encode_task(&[1, 3, 0, 0]));
    check!("encode_opinion_nat", encode_opinion(&[1, 1, 3]) >= 0);
    check!("encode_action_nat", encode_action(&[1, 1, 3]) >= 0);
    check!("encode_event_nat", encode_event(&[0, 1]) >= 0);

    (passed, total)
}

/// Run the §SK.6 MVP story (spec_p0_socketkit.md) — 12 steps + INV-1/3/4
/// invariants, mirroring `sigma_app.py` run_story and `sigma-runtime --story`
/// so the three implementations audit the same story line (Law XIII).
/// Returns (passed, total).
pub fn story() -> (usize, usize) {
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

    // 1. 开户额度      quota_new(50)                    → [50, 50]
    let q0 = quota_new(50).unwrap();
    check!("1 open_quota", q0 == vec![50, 50]);

    // 2. 发布需求      task_create(7, 100)              → [7, 100, 0, 0]
    let task = task_create(7, 100).unwrap();
    check!("2 task_create", task == vec![7, 100, 0, 0]);

    // 3. 扣减额度      quota_use([50, 50], 1)           → [50, 49]
    let q1 = quota_use(&q0, 1).unwrap();
    check!("3 quota_use", q1 == vec![50, 49]);

    // 4. 赏金托管      points_hold(points_new(), 100)   → [100, 0]
    let p0 = points_hold(&points_new(), 100);
    check!("4 points_hold", p0 == vec![100, 0]);

    // 5. 接单          accept_task(..., 3)              → [7, 100, 1, 3]
    let claimed = accept_task(&task, 3).unwrap();
    check!("5 accept_task", claimed == vec![7, 100, 1, 3]);

    // 6. 提交成果      task_submit                      → [7, 100, 2, 3]
    let submitted = task_submit(&claimed).unwrap();
    check!("6 task_submit", submitted == vec![7, 100, 2, 3]);

    // 7. 验收确认      task_accept(..., 7)              → [7, 100, 3, 3]
    let done = task_accept(&submitted, 7).unwrap();
    check!("7 task_accept", done == vec![7, 100, 3, 3]);

    // 8. 释放赏金      points_release([100, 0], 100)    → [0, 100]
    let p1 = points_release(&p0, 100).unwrap();
    check!("8 points_release", p1 == vec![0, 100]);

    // 9. 找茬人提现    points_withdraw([0, 100], 100)   → [0, 0]
    let p2 = points_withdraw(&p1, 100).unwrap();
    check!("9 points_withdraw", p2 == vec![0, 0]);

    // 10. 契分奖励     credit_score([[0, 1]])           → 105
    let credit = credit_score(&[vec![0, 1]]);
    check!("10 credit_score", credit == 105);

    // 11. 贡献累计     contribution_score               → 10
    let contribution = contribution_score(&[vec![3, 1, 10]]);
    check!("11 contribution_score", contribution == 10);

    // 12. 勋章升级     badge_level(105)                 → 1
    check!("12 badge_level", badge_level(105) == 1);

    // 剧本不变量 (spec §SK.6)
    check!("INV-1 monotonic",
           [task[2], claimed[2], submitted[2], done[2]] == [0, 1, 2, 3]);
    check!("INV-3 bounty conserved", done[1] == 100);
    check!("INV-4 author accept", done[0] == 7);

    (passed, total)
}

/// Run the §SK.3.12–3.17 growth-phase audit story (spec_p0_socketkit.md),
/// mirroring `sigma-runtime --growth` so the three implementations audit the
/// same growth storyline (Law XIII). Returns (passed, total).
pub fn growth_story() -> (usize, usize) {
    let mut passed = 0usize;
    let mut total = 0usize;

    macro_rules! check {
        ($name:expr, $cond:expr) => {{
            total += 1;
            if $cond {
                passed += 1;
            } else {
                eprintln!("  ❌ SK.{}", $name);
            }
        }};
    }

    // §SK.3.12 核验师签发勋章
    check!("badge_issue", badge_issue(1001, 3, 105) == Ok(vec![1001, 3, 1]));
    check!("badge_issue_unauthorized", badge_issue(999, 3, 105).is_err());
    // §SK.3.13 督导处理纠纷
    let ev = vec![vec![1, 1, 3], vec![2, 1, 2]];
    check!("dispute_review", dispute_review(&ev) == 1);
    check!("dispute_binary", (0..=1).contains(&dispute_review(&ev)));
    // §SK.3.14 团机制
    let team = team_create(7, 0, 3).unwrap();
    check!("team_create", team == vec![7, 0, 1, 3]);
    check!("team_join", team_join(&team, 5) == Ok(vec![7, 0, 2, 3]));
    // §SK.3.15 团收益
    check!("team_share",
           team_share(&[vec![3, 2], vec![4, 4]], 6) == Ok(vec![vec![3, 2], vec![4, 4]]));
    // §SK.3.16 额度预支
    let qa = quota_advance(&quota_new(50).unwrap());
    check!("quota_advance", qa == vec![50, 100]);
    check!("quota_reset_after_advance",
           quota_reset(&qa) == quota_reset(&quota_new(50).unwrap()));
    // §SK.3.17 积分可追溯
    check!("points_ledger",
           points_ledger(&[vec![0, 100, 1]]) == Ok(vec![vec![1, 1, 100]]));
    check!("points_ledger_untraceable",
           points_ledger(&[vec![0, 100, 0]]).is_err());

    // §IN — Inventory Protocol (spec_p0_inventory.md)
    check!("inventory_new_shape", inventory_new(10, 20) == Ok(vec![10, 20]));
    check!("inventory_new_zero", inventory_new(0, 0) == Ok(vec![0, 0]));
    check!("inventory_new_neg_rejected", inventory_new(-5, 10).is_err());
    check!("receive_a",
           receive_stock(&inventory_new(10, 20).unwrap(), 0, 5) == Ok(vec![15, 20]));
    check!("receive_b",
           receive_stock(&inventory_new(10, 20).unwrap(), 1, 3) == Ok(vec![10, 23]));
    check!("receive_unknown_item_rejected",
           receive_stock(&inventory_new(10, 20).unwrap(), 2, 5).is_err());
    check!("ship_a",
           ship_stock(&inventory_new(10, 20).unwrap(), 0, 4) == Ok(vec![6, 20]));
    check!("ship_all",
           ship_stock(&inventory_new(10, 20).unwrap(), 1, 20) == Ok(vec![10, 0]));
    check!("ship_insufficient_rejected",
           ship_stock(&inventory_new(10, 20).unwrap(), 0, 11).is_err());
    check!("stock_level_a", stock_level(&inventory_new(10, 20).unwrap(), 0) == Ok(10));
    check!("stock_level_b", stock_level(&inventory_new(10, 20).unwrap(), 1) == Ok(20));
    check!("stock_level_type_rejected", stock_level(&vec![5, 5], 2).is_err());
    check!("fill_rate", fill_rate(6, 10) == Ok(0.6));
    check!("fill_rate_full", fill_rate(10, 10) == Ok(1.0));
    check!("fill_rate_zero_demand_rejected", fill_rate(6, 0).is_err());

    (passed, total)
}

/// Run the §IN supply-chain audit story (spec_p0_inventory.md), mirroring
/// `sigma-runtime --inventory` so the three implementations audit the same
/// inventory storyline (Law XIII). Returns (passed, total).
pub fn inventory_story() -> (usize, usize) {
    let mut passed = 0usize;
    let mut total = 0usize;

    macro_rules! check {
        ($name:expr, $cond:expr) => {{
            total += 1;
            if $cond {
                passed += 1;
            } else {
                eprintln!("  ❌ IN.{}", $name);
            }
        }};
    }

    // §IN.3.1 开仓
    let inv = inventory_new(10, 20).unwrap();
    check!("inventory_new", inv == vec![10, 20]);
    // §IN.3.2 入库（可加性）
    let inv_r = receive_stock(&inv, 0, 5).unwrap();
    check!("receive_stock", inv_r == vec![15, 20]);
    // §IN.3.3 出库（不超卖）
    let inv_s = ship_stock(&inv_r, 0, 4).unwrap();
    check!("ship_stock", inv_s == vec![11, 20]);
    check!("ship_insufficient_rejected", ship_stock(&inv_r, 0, 20).is_err());
    // §IN.3.4 库存水位
    check!("stock_level", stock_level(&inv_s, 0) == Ok(11));
    // §IN.3.5 履约率
    check!("fill_rate", fill_rate(6, 10) == Ok(0.6));

    (passed, total)
}
