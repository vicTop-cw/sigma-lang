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

/// Task submission: (author, bounty) → [author, bounty, 0] (status 0 = open).
/// §SK.3.1 — Bounty : Type ≝ ℕ, so a negative bounty is rejected.
pub fn task_create(author: i64, bounty: i64) -> Result<Vec<i64>, &'static str> {
    if bounty < 0 {
        return Err("BountyErr");
    }
    Ok(vec![author, bounty, 0])
}

/// Review resolution: opinions[] → decision (1 = accept, 0 = reject).
/// §SK.3.2 — decision ≡ 1 if weighted_accept(os) ≥ weighted_reject(os) else 0.
/// Each opinion is [reviewer_id, vote, weight]; order-independent by construction.
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
/// §SK.3.3 — points : Type ≝ ℕ, so the running total never goes below 0.
/// Each action is [actor_id, kind, delta].
pub fn contribution_score(actions: &[Vec<i64>]) -> i64 {
    let total: i64 = actions.iter().map(|a| a[2]).sum();
    total.max(0)
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
    check!("task_create_shape", task_create(1, 100) == Ok(vec![1, 100, 0]));
    check!("task_create_open", task_create(5, 50).map(|t| t[2]) == Ok(0));
    check!("task_create_bounty_ge0", task_create(2, 0) == Ok(vec![2, 0, 0]));
    check!("task_create_neg_bounty_rejected", task_create(1, -5).is_err());

    // §SK.3.2 review_merge
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

    // §SK.3.3 contribution_score
    let acts = vec![vec![1, 1, 3], vec![2, 2, 4]];
    check!("contribution_fold", contribution_score(&acts) == 7);
    let acts_floor = vec![vec![1, 1, -5], vec![2, 2, 3]];
    check!("contribution_floor_at_0", contribution_score(&acts_floor) == 0); // -2 floored
    let acts_z = vec![vec![1, 1, 3]];
    let acts_z0 = vec![vec![1, 1, 3], vec![9, 0, 0]];
    check!("contribution_zero_neutral", contribution_score(&acts_z) == contribution_score(&acts_z0));

    // §SK.4 encodings (Law II)
    check!("encode_task_nat", encode_task(&[1, 2, 0]) >= 0);
    check!("encode_distinct", encode_task(&[1, 2, 0]) != encode_task(&[1, 3, 0]));
    check!("encode_opinion_nat", encode_opinion(&[1, 1, 3]) >= 0);
    check!("encode_action_nat", encode_action(&[1, 1, 3]) >= 0);

    (passed, total)
}
