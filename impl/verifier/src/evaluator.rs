//! ΣLang minimal canonical-test evaluator (tensor ops subset).
//!
//! Values: `{:num, i64}`, `{:fnum, f64}`, or nested lists. Mirrors the
//! Python (`verify_consensus.py`) and Elixir (`sigma_verify.exs`) evaluators
//! so E-05 / Law XIII verdicts agree across implementations.

/// A tiny ΣLang value: number, float, or nested list.
#[derive(Debug, Clone, PartialEq)]
pub enum TVal {
    Num(i64),
    FNum(f64),
    List(Vec<TVal>),
}

/// Evaluate a canonical-test input string and compare with the expected output.
/// Returns Ok(()) on pass, Err(detail) on failure.
pub fn eval_test(input: &str, expected: &str) -> Result<(), String> {
    let expect_err = expected.trim_start().starts_with('⊥');
    match eval_expr(input) {
        Ok(v) => {
            if expect_err {
                Err(format!("expected error, got {}", fmt_val(&v)))
            } else {
                match parse_val(expected) {
                    Some(exp) if exp == v => Ok(()),
                    Some(exp) => Err(format!("expected {}, got {}", fmt_val(&exp), fmt_val(&v))),
                    None => Err(format!("unparseable expectation: {}", expected)),
                }
            }
        }
        Err(e) => {
            if expect_err {
                Ok(())
            } else {
                Err(format!("evaluation failed: {}", e))
            }
        }
    }
}

/// Evaluate an expression: literal, ⊕, ⊗, index(...).
fn eval_expr(s: &str) -> Result<TVal, String> {
    let s = s.trim();
    if s.contains("where shape mismatch") {
        return Err("ShapeError".to_string());
    }
    if s.contains('⊕') {
        let (a, b) = s.split_once('⊕').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return elemwise_add(&va, &vb);
    }
    if s.contains('⊗') {
        let (a, b) = s.split_once('⊗').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return mat_mul(&va, &vb);
    }
    if s.contains('⊖') {
        let (a, b) = s.split_once('⊖').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return elemwise_sub(&va, &vb);
    }
    if s.contains('⊘') {
        let (a, b) = s.split_once('⊘').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return elemwise_div(&va, &vb);
    }
    if s.contains('⊙') {
        let (a, b) = s.split_once('⊙').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return elemwise_mul(&va, &vb);
    }
    if s.contains('≡') {
        let (a, b) = s.split_once('≡').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return value_eq(&va, &vb);
    }
    if s.contains('≥') {
        let (a, b) = s.split_once('≥').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return value_cmp(&va, &vb, true);
    }
    if s.contains('≤') {
        let (a, b) = s.split_once('≤').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return value_cmp(&va, &vb, false);
    }
    if s.contains('∈') {
        let (a, b) = s.split_once('∈').unwrap();
        let (va, vb) = (eval_expr(a)?, eval_expr(b)?);
        return value_in(&va, &vb);
    }
    if let Some(rest) = s.strip_prefix("index(") {
        let inner = rest.strip_suffix(')').ok_or("bad index call")?;
        let (target, idx) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad index args: {}", inner))?;
        let tv = eval_expr(target)?;
        let iv = parse_val(&idx).ok_or_else(|| format!("bad index: {}", idx))?;
        return index_into(&tv, &iv);
    }
    // §SK — SocketKit Protocol operations (spec_p0_socketkit.md §SK.3).
    // Real function calls, not spec-expression aliases: mirrors
    // verify_consensus.py so the corpus consensus gate verifies app behavior.
    if let Some(rest) = s.strip_prefix("task_create(") {
        let inner = rest.strip_suffix(')').ok_or("bad task_create call")?;
        let (a, b) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad task_create args: {}", inner))?;
        let va = eval_expr(a)?;
        let vb = eval_expr(b)?;
        return match (va, vb) {
            (TVal::Num(author), TVal::Num(bounty)) => {
                if bounty < 0 {
                    // Bounty : Type ≝ ℕ
                    Err("BountyErr".to_string())
                } else {
                    // [author, bounty, 0=open, 0=unclaimed]
                    Ok(TVal::List(vec![
                        TVal::Num(author),
                        TVal::Num(bounty),
                        TVal::Num(0),
                        TVal::Num(0),
                    ]))
                }
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("accept_task(") {
        let inner = rest.strip_suffix(')').ok_or("bad accept_task call")?;
        let (t, h) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad accept_task args: {}", inner))?;
        let vt = eval_expr(t)?;
        let vh = eval_expr(h)?;
        return match (vt, vh) {
            (TVal::List(task), TVal::Num(hunter)) if task.len() == 4 => {
                if task[2] != TVal::Num(0) {
                    // status 0 = open
                    return Err("StateError".to_string());
                }
                Ok(TVal::List(vec![
                    task[0].clone(),
                    task[1].clone(),
                    TVal::Num(1),
                    TVal::Num(hunter),
                ]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("task_submit(") {
        let inner = rest.strip_suffix(')').ok_or("bad task_submit call")?;
        let vt = eval_expr(inner)?;
        return match vt {
            TVal::List(task) if task.len() == 4 => {
                if task[2] != TVal::Num(1) {
                    // status 1 = in_progress
                    return Err("StateError".to_string());
                }
                Ok(TVal::List(vec![
                    task[0].clone(),
                    task[1].clone(),
                    TVal::Num(2),
                    task[3].clone(),
                ]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("task_accept(") {
        let inner = rest.strip_suffix(')').ok_or("bad task_accept call")?;
        let (t, c) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad task_accept args: {}", inner))?;
        let vt = eval_expr(t)?;
        let vc = eval_expr(c)?;
        return match (vt, vc) {
            (TVal::List(task), TVal::Num(caller)) if task.len() == 4 => {
                if task[2] != TVal::Num(2) {
                    // status 2 = pending_review
                    return Err("StateError".to_string());
                }
                if caller != match &task[0] {
                    TVal::Num(a) => *a,
                    _ => return Err("TypeError".to_string()),
                } {
                    // INV-4: only the author may accept their own task
                    return Err("AuthError".to_string());
                }
                Ok(TVal::List(vec![
                    task[0].clone(),
                    task[1].clone(),
                    TVal::Num(3),
                    task[3].clone(),
                ]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("review_merge(") {
        let inner = rest.strip_suffix(')').ok_or("bad review_merge call")?;
        let v = eval_expr(inner)?;
        return match v {
            TVal::List(opinions) => {
                let mut w_accept = 0i64;
                let mut w_reject = 0i64;
                for o in &opinions {
                    match o {
                        TVal::List(fields) if fields.len() == 3 => {
                            match (&fields[1], &fields[2]) {
                                (TVal::Num(vote), TVal::Num(weight)) => {
                                    if *vote == 1 {
                                        w_accept += weight;
                                    } else if *vote == 0 {
                                        w_reject += weight;
                                    } else {
                                        return Err("TypeError".to_string());
                                    }
                                }
                                _ => return Err("TypeError".to_string()),
                            }
                        }
                        _ => return Err("ShapeError".to_string()),
                    }
                }
                Ok(TVal::Num(if w_accept >= w_reject { 1 } else { 0 }))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("contribution_score(") {
        let inner = rest.strip_suffix(')').ok_or("bad contribution_score call")?;
        let v = eval_expr(inner)?;
        return match v {
            TVal::List(actions) => {
                let mut total = 0i64;
                for a in &actions {
                    match a {
                        TVal::List(fields) if fields.len() == 3 => {
                            match &fields[2] {
                                TVal::Num(delta) => total += delta,
                                _ => return Err("TypeError".to_string()),
                            }
                        }
                        _ => return Err("ShapeError".to_string()),
                    }
                }
                Ok(TVal::Num(total.max(0)))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("credit_score(") {
        let inner = rest.strip_suffix(')').ok_or("bad credit_score call")?;
        let v = eval_expr(inner)?;
        return match v {
            TVal::List(events) => {
                let mut credit = 100i64;
                for e in &events {
                    match e {
                        TVal::List(fields) if fields.len() == 2 => {
                            match (&fields[0], &fields[1]) {
                                (TVal::Num(kind), TVal::Num(count)) => {
                                    if *kind == 0 {
                                        // complete: +5 per count
                                        credit += 5 * count;
                                    } else if *kind == 1 {
                                        // breach: ×0.7 per count (×7 ÷10, floor)
                                        for _ in 0..*count {
                                            credit = (credit * 7) / 10;
                                        }
                                    } else {
                                        return Err("TypeError".to_string());
                                    }
                                }
                                _ => return Err("TypeError".to_string()),
                            }
                        }
                        _ => return Err("ShapeError".to_string()),
                    }
                }
                Ok(TVal::Num(credit.max(0)))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §PF — Portfolio Protocol operations (spec_p0_portfolio.md §PF.3).
    // Second novel domain: finance. Real function calls, mirrors
    // verify_consensus.py so the consensus gate verifies investment semantics.
    if let Some(rest) = s.strip_prefix("portfolio_new(") {
        let inner = rest.strip_suffix(')').ok_or("bad portfolio_new call")?;
        let vc = eval_expr(inner)?;
        return match vc {
            TVal::Num(cash) => {
                if cash < 0 {
                    // Cash : Type ≝ ℕ
                    Err("TypeError".to_string())
                } else {
                    Ok(TVal::List(vec![TVal::Num(cash), TVal::Num(0), TVal::Num(0)]))
                }
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("buy(") {
        let inner = rest.strip_suffix(')').ok_or("bad buy call")?;
        let (a, rest2) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad buy args: {}", inner))?;
        let (b, c) = split_top_level(rest2, ',')
            .ok_or_else(|| format!("bad buy args: {}", inner))?;
        let vp = eval_expr(a)?;
        let va = eval_expr(b)?;
        let vq = eval_expr(c)?;
        return match (vp, va, vq) {
            (TVal::List(pf), TVal::Num(asset), TVal::Num(qty))
                if pf.len() == 3 =>
            {
                if asset != 0 && asset != 1 {
                    return Err("UnknownAsset".to_string());
                }
                let (cash, q_a, q_b) = match (&pf[0], &pf[1], &pf[2]) {
                    (TVal::Num(c), TVal::Num(a), TVal::Num(b)) => (*c, *a, *b),
                    _ => return Err("TypeError".to_string()),
                };
                if cash < qty {
                    return Err("InsufficientFunds".to_string());
                }
                if asset == 0 {
                    Ok(TVal::List(vec![
                        TVal::Num(cash - qty),
                        TVal::Num(q_a + qty),
                        TVal::Num(q_b),
                    ]))
                } else {
                    Ok(TVal::List(vec![
                        TVal::Num(cash - qty),
                        TVal::Num(q_a),
                        TVal::Num(q_b + qty),
                    ]))
                }
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("sell(") {
        let inner = rest.strip_suffix(')').ok_or("bad sell call")?;
        let (a, rest2) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad sell args: {}", inner))?;
        let (b, c) = split_top_level(rest2, ',')
            .ok_or_else(|| format!("bad sell args: {}", inner))?;
        let vp = eval_expr(a)?;
        let va = eval_expr(b)?;
        let vq = eval_expr(c)?;
        return match (vp, va, vq) {
            (TVal::List(pf), TVal::Num(asset), TVal::Num(qty))
                if pf.len() == 3 =>
            {
                if asset != 0 && asset != 1 {
                    return Err("UnknownAsset".to_string());
                }
                let (cash, q_a, q_b) = match (&pf[0], &pf[1], &pf[2]) {
                    (TVal::Num(c), TVal::Num(a), TVal::Num(b)) => (*c, *a, *b),
                    _ => return Err("TypeError".to_string()),
                };
                let held = if asset == 0 { q_a } else { q_b };
                if qty > held {
                    return Err("InsufficientShares".to_string());
                }
                if asset == 0 {
                    Ok(TVal::List(vec![
                        TVal::Num(cash + qty),
                        TVal::Num(q_a - qty),
                        TVal::Num(q_b),
                    ]))
                } else {
                    Ok(TVal::List(vec![
                        TVal::Num(cash + qty),
                        TVal::Num(q_a),
                        TVal::Num(q_b - qty),
                    ]))
                }
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("portfolio_value(") {
        let inner = rest.strip_suffix(')').ok_or("bad portfolio_value call")?;
        let vp = eval_expr(inner)?;
        return match vp {
            TVal::List(pf) if pf.len() == 3 => {
                let (cash, q_a, q_b) = match (&pf[0], &pf[1], &pf[2]) {
                    (TVal::Num(c), TVal::Num(a), TVal::Num(b)) => (*c, *a, *b),
                    _ => return Err("TypeError".to_string()),
                };
                Ok(TVal::Num(cash + q_a + q_b))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("risk_score(") {
        let inner = rest.strip_suffix(')').ok_or("bad risk_score call")?;
        let vp = eval_expr(inner)?;
        return match vp {
            TVal::List(pf) if pf.len() == 3 => {
                let (q_a, q_b) = match (&pf[1], &pf[2]) {
                    (TVal::Num(a), TVal::Num(b)) => (*a, *b),
                    _ => return Err("TypeError".to_string()),
                };
                Ok(TVal::Num(q_a + q_b))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.9 额度制 quota — 每月额度 / 扣减 / 月底清零.
    if let Some(rest) = s.strip_prefix("quota_new(") {
        let inner = rest.strip_suffix(')').ok_or("bad quota_new call")?;
        let vm = eval_expr(inner)?;
        return match vm {
            TVal::Num(monthly) => {
                if monthly < 0 {
                    Err("TypeError".to_string())
                } else {
                    Ok(TVal::List(vec![TVal::Num(monthly), TVal::Num(monthly)]))
                }
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("quota_use(") {
        let inner = rest.strip_suffix(')').ok_or("bad quota_use call")?;
        let (q, a) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad quota_use args: {}", inner))?;
        let vq = eval_expr(q)?;
        let va = eval_expr(a)?;
        return match (vq, va) {
            (TVal::List(quota), TVal::Num(amount)) if quota.len() == 2 => {
                let (monthly, remaining) = match (&quota[0], &quota[1]) {
                    (TVal::Num(m), TVal::Num(r)) => (*m, *r),
                    _ => return Err("TypeError".to_string()),
                };
                if amount > remaining {
                    return Err("QuotaExhausted".to_string());
                }
                Ok(TVal::List(vec![TVal::Num(monthly), TVal::Num(remaining - amount)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("quota_reset(") {
        let inner = rest.strip_suffix(')').ok_or("bad quota_reset call")?;
        let vq = eval_expr(inner)?;
        return match vq {
            TVal::List(quota) if quota.len() == 2 => {
                let monthly = match &quota[0] {
                    TVal::Num(m) => *m,
                    _ => return Err("TypeError".to_string()),
                };
                Ok(TVal::List(vec![TVal::Num(monthly), TVal::Num(monthly)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.10 积分制 points — 托管 / 释放 / 提现.
    if s == "points_new()" {
        return Ok(TVal::List(vec![TVal::Num(0), TVal::Num(0)]));
    }
    if let Some(rest) = s.strip_prefix("points_hold(") {
        let inner = rest.strip_suffix(')').ok_or("bad points_hold call")?;
        let (p, x) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad points_hold args: {}", inner))?;
        let vp = eval_expr(p)?;
        let vx = eval_expr(x)?;
        return match (vp, vx) {
            (TVal::List(points), TVal::Num(amount)) if points.len() == 2 => {
                let (escrow, available) = match (&points[0], &points[1]) {
                    (TVal::Num(e), TVal::Num(a)) => (*e, *a),
                    _ => return Err("TypeError".to_string()),
                };
                Ok(TVal::List(vec![TVal::Num(escrow + amount), TVal::Num(available)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("points_release(") {
        let inner = rest.strip_suffix(')').ok_or("bad points_release call")?;
        let (p, x) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad points_release args: {}", inner))?;
        let vp = eval_expr(p)?;
        let vx = eval_expr(x)?;
        return match (vp, vx) {
            (TVal::List(points), TVal::Num(amount)) if points.len() == 2 => {
                let (escrow, available) = match (&points[0], &points[1]) {
                    (TVal::Num(e), TVal::Num(a)) => (*e, *a),
                    _ => return Err("TypeError".to_string()),
                };
                if amount > escrow {
                    return Err("InsufficientEscrow".to_string());
                }
                Ok(TVal::List(vec![TVal::Num(escrow - amount), TVal::Num(available + amount)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("points_withdraw(") {
        let inner = rest.strip_suffix(')').ok_or("bad points_withdraw call")?;
        let (p, x) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad points_withdraw args: {}", inner))?;
        let vp = eval_expr(p)?;
        let vx = eval_expr(x)?;
        return match (vp, vx) {
            (TVal::List(points), TVal::Num(amount)) if points.len() == 2 => {
                let (escrow, available) = match (&points[0], &points[1]) {
                    (TVal::Num(e), TVal::Num(a)) => (*e, *a),
                    _ => return Err("TypeError".to_string()),
                };
                if amount > available {
                    return Err("InsufficientPoints".to_string());
                }
                Ok(TVal::List(vec![TVal::Num(escrow), TVal::Num(available - amount)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.11 勋章制 badge_level — 0=铜 1=银 2=金 3=钻石.
    if let Some(rest) = s.strip_prefix("badge_level(") {
        let inner = rest.strip_suffix(')').ok_or("bad badge_level call")?;
        let vs = eval_expr(inner)?;
        return match vs {
            TVal::Num(score) => {
                let badge = if score < 100 {
                    0
                } else if score < 300 {
                    1
                } else if score < 600 {
                    2
                } else {
                    3
                };
                Ok(TVal::Num(badge))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.12 核验师签发勋章 badge_issue — v ≥ 1000 授权核验师.
    if let Some(rest) = s.strip_prefix("badge_issue(") {
        let inner = rest.strip_suffix(')').ok_or("bad badge_issue call")?;
        let (v, rest2) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad badge_issue args: {}", inner))?;
        let (u, sc) = split_top_level(rest2, ',')
            .ok_or_else(|| format!("bad badge_issue args: {}", inner))?;
        let vv = eval_expr(v)?;
        let vu = eval_expr(u)?;
        let vsc = eval_expr(sc)?;
        return match (vv, vu, vsc) {
            (TVal::Num(verifier), TVal::Num(user), TVal::Num(score)) => {
                if verifier < 1000 {
                    // 授权核验师编号段
                    return Err("AuthError".to_string());
                }
                let level = if score < 100 {
                    0
                } else if score < 300 {
                    1
                } else if score < 600 {
                    2
                } else {
                    3
                };
                Ok(TVal::List(vec![TVal::Num(verifier), TVal::Num(user), TVal::Num(level)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.13 督导处理纠纷 dispute_review — 加权支持 ≥ 加权驳回.
    if let Some(rest) = s.strip_prefix("dispute_review(") {
        let inner = rest.strip_suffix(')').ok_or("bad dispute_review call")?;
        let v = eval_expr(inner)?;
        return match v {
            TVal::List(evidence) => {
                let mut w_support = 0i64;
                let mut w_reject = 0i64;
                for e in &evidence {
                    match e {
                        TVal::List(fields) if fields.len() == 3 => {
                            match (&fields[1], &fields[2]) {
                                (TVal::Num(side), TVal::Num(weight)) => {
                                    if *side == 1 {
                                        w_support += weight;
                                    } else if *side == 0 {
                                        w_reject += weight;
                                    } else {
                                        return Err("TypeError".to_string());
                                    }
                                }
                                _ => return Err("TypeError".to_string()),
                            }
                        }
                        _ => return Err("ShapeError".to_string()),
                    }
                }
                Ok(TVal::Num(if w_support >= w_reject { 1 } else { 0 }))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.14 团机制 team_create / team_join — Team = [owner, kind, size, capacity].
    if let Some(rest) = s.strip_prefix("team_create(") {
        let inner = rest.strip_suffix(')').ok_or("bad team_create call")?;
        let (o, rest2) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad team_create args: {}", inner))?;
        let (k, c) = split_top_level(rest2, ',')
            .ok_or_else(|| format!("bad team_create args: {}", inner))?;
        let vo = eval_expr(o)?;
        let vk = eval_expr(k)?;
        let vc = eval_expr(c)?;
        return match (vo, vk, vc) {
            (TVal::Num(owner), TVal::Num(kind), TVal::Num(capacity)) => {
                if capacity < 1 {
                    return Err("TypeError".to_string());
                }
                Ok(TVal::List(vec![
                    TVal::Num(owner), TVal::Num(kind), TVal::Num(1), TVal::Num(capacity),
                ]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("team_join(") {
        let inner = rest.strip_suffix(')').ok_or("bad team_join call")?;
        let (t, m) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad team_join args: {}", inner))?;
        let vt = eval_expr(t)?;
        let vm = eval_expr(m)?;
        return match (vt, vm) {
            (TVal::List(team), TVal::Num(_member)) if team.len() == 4 => {
                let (owner, kind, size, capacity) = match (&team[0], &team[1], &team[2], &team[3]) {
                    (TVal::Num(o), TVal::Num(k), TVal::Num(sz), TVal::Num(cp)) => (*o, *k, *sz, *cp),
                    _ => return Err("TypeError".to_string()),
                };
                if size >= capacity {
                    return Err("TeamFull".to_string());
                }
                Ok(TVal::List(vec![
                    TVal::Num(owner), TVal::Num(kind), TVal::Num(size + 1), TVal::Num(capacity),
                ]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.15 团内收益按贡献分配 team_share — shareᵢ = floor(r·cᵢ/Σc).
    if let Some(rest) = s.strip_prefix("team_share(") {
        let inner = rest.strip_suffix(')').ok_or("bad team_share call")?;
        let (c, r) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad team_share args: {}", inner))?;
        let vc = eval_expr(c)?;
        let vr = eval_expr(r)?;
        return match (vc, vr) {
            (TVal::List(contribs), TVal::Num(reward)) => {
                let mut total = 0i64;
                let mut parsed: Vec<(i64, i64)> = Vec::new();
                for e in &contribs {
                    match e {
                        TVal::List(fields) if fields.len() == 2 => {
                            match (&fields[0], &fields[1]) {
                                (TVal::Num(m), TVal::Num(cc)) => {
                                    parsed.push((*m, *cc));
                                    total += *cc;
                                }
                                _ => return Err("TypeError".to_string()),
                            }
                        }
                        _ => return Err("ShapeError".to_string()),
                    }
                }
                if total == 0 {
                    return Err("DivByZero".to_string());
                }
                Ok(TVal::List(parsed.iter()
                    .map(|(m, cc)| TVal::List(vec![TVal::Num(*m), TVal::Num(reward * *cc / total)]))
                    .collect()))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.16 额度预支 quota_advance — [m, r] → [m, r + m].
    if let Some(rest) = s.strip_prefix("quota_advance(") {
        let inner = rest.strip_suffix(')').ok_or("bad quota_advance call")?;
        let vq = eval_expr(inner)?;
        return match vq {
            TVal::List(quota) if quota.len() == 2 => {
                let (monthly, remaining) = match (&quota[0], &quota[1]) {
                    (TVal::Num(m), TVal::Num(r)) => (*m, *r),
                    _ => return Err("TypeError".to_string()),
                };
                Ok(TVal::List(vec![TVal::Num(monthly), TVal::Num(remaining + monthly)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §SK.3.17 积分来源可追溯 points_ledger — [[entry_id, source_id, amount], …].
    if let Some(rest) = s.strip_prefix("points_ledger(") {
        let inner = rest.strip_suffix(')').ok_or("bad points_ledger call")?;
        let v = eval_expr(inner)?;
        return match v {
            TVal::List(entries) => {
                let mut ledger = Vec::new();
                for (i, e) in entries.iter().enumerate() {
                    match e {
                        TVal::List(fields) if fields.len() == 3 => {
                            match (&fields[0], &fields[1], &fields[2]) {
                                (TVal::Num(_kind), TVal::Num(amount), TVal::Num(source)) => {
                                    if *source < 1 {
                                        return Err("NotTraceable".to_string());
                                    }
                                    if *amount < 0 {
                                        return Err("TypeError".to_string());
                                    }
                                    ledger.push(TVal::List(vec![
                                        TVal::Num((i + 1) as i64),
                                        TVal::Num(*source),
                                        TVal::Num(*amount),
                                    ]));
                                }
                                _ => return Err("TypeError".to_string()),
                            }
                        }
                        _ => return Err("ShapeError".to_string()),
                    }
                }
                Ok(TVal::List(ledger))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    // §IN — Inventory Protocol operations (spec_p0_inventory.md §IN.3).
    // Third novel domain: supply chain. Real function calls, mirrors
    // verify_consensus.py so the consensus gate verifies inventory semantics.
    if let Some(rest) = s.strip_prefix("inventory_new(") {
        let inner = rest.strip_suffix(')').ok_or("bad inventory_new call")?;
        let (a, b) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad inventory_new args: {}", inner))?;
        let va = eval_expr(a)?;
        let vb = eval_expr(b)?;
        return match (va, vb) {
            (TVal::Num(qa), TVal::Num(qb)) => {
                if qa < 0 || qb < 0 {
                    return Err("TypeError".to_string());
                }
                Ok(TVal::List(vec![TVal::Num(qa), TVal::Num(qb)]))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("receive_stock(") {
        let inner = rest.strip_suffix(')').ok_or("bad receive_stock call")?;
        let (i, rest2) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad receive_stock args: {}", inner))?;
        let (x, q) = split_top_level(rest2, ',')
            .ok_or_else(|| format!("bad receive_stock args: {}", inner))?;
        let vi = eval_expr(i)?;
        let vx = eval_expr(x)?;
        let vq = eval_expr(q)?;
        return match (vi, vx, vq) {
            (TVal::List(inv), TVal::Num(item), TVal::Num(qty)) if inv.len() == 2 => {
                if item != 0 && item != 1 {
                    return Err("UnknownItem".to_string());
                }
                if qty < 0 {
                    return Err("TypeError".to_string());
                }
                let held = match &inv[item as usize] {
                    TVal::Num(h) => *h,
                    _ => return Err("TypeError".to_string()),
                };
                let mut items = inv.clone();
                items[item as usize] = TVal::Num(held + qty);
                Ok(TVal::List(items))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("ship_stock(") {
        let inner = rest.strip_suffix(')').ok_or("bad ship_stock call")?;
        let (i, rest2) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad ship_stock args: {}", inner))?;
        let (x, q) = split_top_level(rest2, ',')
            .ok_or_else(|| format!("bad ship_stock args: {}", inner))?;
        let vi = eval_expr(i)?;
        let vx = eval_expr(x)?;
        let vq = eval_expr(q)?;
        return match (vi, vx, vq) {
            (TVal::List(inv), TVal::Num(item), TVal::Num(qty)) if inv.len() == 2 => {
                if item != 0 && item != 1 {
                    return Err("UnknownItem".to_string());
                }
                if qty < 0 {
                    return Err("TypeError".to_string());
                }
                let held = match &inv[item as usize] {
                    TVal::Num(h) => *h,
                    _ => return Err("TypeError".to_string()),
                };
                if qty > held {
                    return Err("InsufficientStock".to_string());
                }
                let mut items = inv.clone();
                items[item as usize] = TVal::Num(held - qty);
                Ok(TVal::List(items))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("stock_level(") {
        let inner = rest.strip_suffix(')').ok_or("bad stock_level call")?;
        let (i, x) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad stock_level args: {}", inner))?;
        let vi = eval_expr(i)?;
        let vx = eval_expr(x)?;
        return match (vi, vx) {
            (TVal::List(inv), TVal::Num(item)) if inv.len() == 2 => {
                if item != 0 && item != 1 {
                    return Err("TypeError".to_string());
                }
                Ok(inv[item as usize].clone())
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if let Some(rest) = s.strip_prefix("fill_rate(") {
        let inner = rest.strip_suffix(')').ok_or("bad fill_rate call")?;
        let (sh, de) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad fill_rate args: {}", inner))?;
        let vs = eval_expr(sh)?;
        let vd = eval_expr(de)?;
        return match (vs, vd) {
            (TVal::Num(shipped), TVal::Num(demanded)) => {
                if demanded == 0 {
                    return Err("DivByZero".to_string());
                }
                Ok(TVal::FNum(shipped as f64 / demanded as f64))
            }
            _ => Err("TypeError".to_string()),
        };
    }
    if s == "I₂" {
        return Ok(TVal::List(vec![
            TVal::List(vec![TVal::Num(1), TVal::Num(0)]),
            TVal::List(vec![TVal::Num(0), TVal::Num(1)]),
        ]));
    }
    if let Some(v) = resolve_constant(s) {
        return Ok(v);
    }
    parse_val(s).ok_or_else(|| format!("unparseable: {}", s))
}

/// Element-wise addition; shape mismatch is a ShapeError.
fn elemwise_add(a: &TVal, b: &TVal) -> Result<TVal, String> {
    match (a, b) {
        (TVal::Num(x), TVal::Num(y)) => Ok(TVal::Num(x + y)),
        (TVal::FNum(x), TVal::FNum(y)) => Ok(TVal::FNum(x + y)),
        (TVal::Num(x), TVal::FNum(y)) => Ok(TVal::FNum(*x as f64 + y)),
        (TVal::FNum(x), TVal::Num(y)) => Ok(TVal::FNum(x + *y as f64)),
        (TVal::List(xs), TVal::List(ys)) => {
            if xs.len() != ys.len() {
                return Err("ShapeError".to_string());
            }
            let mut out = Vec::with_capacity(xs.len());
            for (x, y) in xs.iter().zip(ys) {
                out.push(elemwise_add(x, y)?);
            }
            Ok(TVal::List(out))
        }
        _ => Err("ShapeError".to_string()),
    }
}

/// Matrix × vector (identity I₂ is handled by eval_expr's literal expansion).
fn mat_mul(a: &TVal, b: &TVal) -> Result<TVal, String> {
    match (a, b) {
        (TVal::List(rows), TVal::List(vec)) => {
            let mut out = Vec::with_capacity(rows.len());
            for row in rows {
                let TVal::List(cells) = row else {
                    return Err("ShapeError".to_string());
                };
                if cells.len() != vec.len() {
                    return Err("ShapeError".to_string());
                }
                let mut acc = 0i64;
                let mut acc_f = 0f64;
                let mut is_float = false;
                for (c, v) in cells.iter().zip(vec) {
                    match (c, v) {
                        (TVal::Num(cn), TVal::Num(vn)) => acc += cn * vn,
                        (TVal::FNum(cn), TVal::FNum(vn)) => {
                            is_float = true;
                            acc_f += cn * vn;
                        }
                        (TVal::Num(cn), TVal::FNum(vn)) => {
                            is_float = true;
                            acc_f += *cn as f64 * vn;
                        }
                        (TVal::FNum(cn), TVal::Num(vn)) => {
                            is_float = true;
                            acc_f += cn * *vn as f64;
                        }
                        _ => return Err("TypeError".to_string()),
                    }
                }
                if is_float {
                    out.push(TVal::FNum(acc_f));
                } else {
                    out.push(TVal::Num(acc));
                }
            }
            Ok(TVal::List(out))
        }
        _ => Err("ShapeError".to_string()),
    }
}

/// Element-wise subtraction (⊖), mirroring elemwise_add.
fn elemwise_sub(a: &TVal, b: &TVal) -> Result<TVal, String> {
    match (a, b) {
        (TVal::Num(x), TVal::Num(y)) => Ok(TVal::Num(x - y)),
        (TVal::FNum(x), TVal::FNum(y)) => Ok(TVal::FNum(x - y)),
        (TVal::Num(x), TVal::FNum(y)) => Ok(TVal::FNum(*x as f64 - y)),
        (TVal::FNum(x), TVal::Num(y)) => Ok(TVal::FNum(x - *y as f64)),
        (TVal::List(xs), TVal::List(ys)) => {
            if xs.len() != ys.len() {
                return Err("ShapeError".to_string());
            }
            let mut out = Vec::with_capacity(xs.len());
            for (x, y) in xs.iter().zip(ys) {
                out.push(elemwise_sub(x, y)?);
            }
            Ok(TVal::List(out))
        }
        _ => Err("ShapeError".to_string()),
    }
}

/// Element-wise division (⊘): num/num -> num when divisible, else fnum;
/// division by zero is a DivByZero error.
fn elemwise_div(a: &TVal, b: &TVal) -> Result<TVal, String> {
    match (a, b) {
        (TVal::Num(x), TVal::Num(y)) => {
            if *y == 0 {
                return Err("DivByZero".to_string());
            }
            if x % y == 0 {
                Ok(TVal::Num(x / y))
            } else {
                Ok(TVal::FNum(*x as f64 / *y as f64))
            }
        }
        (TVal::FNum(x), TVal::FNum(y)) => {
            if *y == 0.0 {
                return Err("DivByZero".to_string());
            }
            Ok(TVal::FNum(x / y))
        }
        (TVal::Num(x), TVal::FNum(y)) => {
            if *y == 0.0 {
                return Err("DivByZero".to_string());
            }
            Ok(TVal::FNum(*x as f64 / y))
        }
        (TVal::FNum(x), TVal::Num(y)) => {
            if *y == 0 {
                return Err("DivByZero".to_string());
            }
            Ok(TVal::FNum(x / *y as f64))
        }
        (TVal::List(xs), TVal::List(ys)) => {
            if xs.len() != ys.len() {
                return Err("ShapeError".to_string());
            }
            let mut out = Vec::with_capacity(xs.len());
            for (x, y) in xs.iter().zip(ys) {
                out.push(elemwise_div(x, y)?);
            }
            Ok(TVal::List(out))
        }
        _ => Err("ShapeError".to_string()),
    }
}

/// Element-wise multiplication (⊙, Hadamard), mirroring elemwise_add.
fn elemwise_mul(a: &TVal, b: &TVal) -> Result<TVal, String> {
    match (a, b) {
        (TVal::Num(x), TVal::Num(y)) => Ok(TVal::Num(x * y)),
        (TVal::FNum(x), TVal::FNum(y)) => Ok(TVal::FNum(x * y)),
        (TVal::Num(x), TVal::FNum(y)) => Ok(TVal::FNum(*x as f64 * y)),
        (TVal::FNum(x), TVal::Num(y)) => Ok(TVal::FNum(x * *y as f64)),
        (TVal::List(xs), TVal::List(ys)) => {
            if xs.len() != ys.len() {
                return Err("ShapeError".to_string());
            }
            let mut out = Vec::with_capacity(xs.len());
            for (x, y) in xs.iter().zip(ys) {
                out.push(elemwise_mul(x, y)?);
            }
            Ok(TVal::List(out))
        }
        _ => Err("ShapeError".to_string()),
    }
}

/// ≡ — structural equality, returns num 1/0; mixed kinds are TypeError.
fn value_eq(a: &TVal, b: &TVal) -> Result<TVal, String> {
    match (a, b) {
        (TVal::Num(x), TVal::Num(y)) => Ok(TVal::Num(i64::from(x == y))),
        (TVal::FNum(x), TVal::FNum(y)) => Ok(TVal::Num(i64::from(x == y))),
        (TVal::List(xs), TVal::List(ys)) => {
            if xs.len() != ys.len() {
                return Ok(TVal::Num(0));
            }
            for (x, y) in xs.iter().zip(ys) {
                if value_eq(x, y)? == TVal::Num(0) {
                    return Ok(TVal::Num(0));
                }
            }
            Ok(TVal::Num(1))
        }
        _ => Err("TypeError".to_string()),
    }
}

/// ≥ / ≤ — scalar comparison, returns num 1/0; lists are TypeError.
/// `ge=true` for ≥, `ge=false` for ≤.
fn value_cmp(a: &TVal, b: &TVal, ge: bool) -> Result<TVal, String> {
    let x = match a {
        TVal::Num(n) => *n as f64,
        TVal::FNum(f) => *f,
        _ => return Err("TypeError".to_string()),
    };
    let y = match b {
        TVal::Num(n) => *n as f64,
        TVal::FNum(f) => *f,
        _ => return Err("TypeError".to_string()),
    };
    if ge {
        Ok(TVal::Num(i64::from(x >= y)))
    } else {
        Ok(TVal::Num(i64::from(x <= y)))
    }
}

/// ∈ — membership: element a in list b, returns num 1/0; non-list is TypeError.
fn value_in(a: &TVal, b: &TVal) -> Result<TVal, String> {
    let TVal::List(items) = b else {
        return Err("TypeError".to_string());
    };
    for e in items {
        if value_eq(a, e)? == TVal::Num(1) {
            return Ok(TVal::Num(1));
        }
    }
    Ok(TVal::Num(0))
}

/// index(target, idx) — follow the index path through nested lists.
fn index_into(target: &TVal, idx: &TVal) -> Result<TVal, String> {
    let mut cur = target;
    let mut path = Vec::new();
    collect_index_path(idx, &mut path);
    for i in path {
        let TVal::List(items) = cur else {
            return Err("TypeError".to_string());
        };
        cur = items.get(i).ok_or_else(|| "OutOfBounds".to_string())?;
    }
    Ok(cur.clone())
}

fn collect_index_path(idx: &TVal, out: &mut Vec<usize>) {
    match idx {
        TVal::Num(n) => out.push(*n as usize),
        TVal::FNum(_) => {} // float index is not a path
        TVal::List(items) => {
            for it in items {
                collect_index_path(it, out);
            }
        }
    }
}

/// Normalize common Unicode minus/hyphen variants to ASCII `-` so numeric
/// literals parse uniformly (M-4: U+2212 −, U+FE63 ﹣, U+FF0D －, U+2010 ‐,
/// U+2011 ‑).
pub fn normalize_minus(s: &str) -> String {
    s.replace(['−', '﹣', '－', '‐', '‑'], "-")
}

/// True if `s` is a plain integer literal `-?\d+`, matching the Python/Elixir
/// parsers so integer handling agrees across implementations. Notably rejects
/// a leading `+` (Rust's `parse::<i64>()` would otherwise accept `+5`, which
/// Python's `-?\d+` and Elixir's `^-?\d+$` both reject).
fn looks_like_int(s: &str) -> bool {
    let digits = s.strip_prefix('-').unwrap_or(s);
    !digits.is_empty() && digits.chars().all(|c| c.is_ascii_digit())
}

/// True if `s` is a plain decimal literal `-?\d+\.\d+` (no exponent), matching
/// the Python/Elixir parsers so float handling agrees across implementations.
fn looks_like_decimal(s: &str) -> bool {
    let digits = s.strip_prefix('-').unwrap_or(s);
    let mut parts = digits.split('.');
    match (parts.next(), parts.next()) {
        (Some(int_part), Some(frac_part)) => {
            !int_part.is_empty()
                && !frac_part.is_empty()
                && int_part.chars().all(|c| c.is_ascii_digit())
                && frac_part.chars().all(|c| c.is_ascii_digit())
                && parts.next().is_none()
        }
        _ => false,
    }
}

/// Parse a literal value: `2`, `0.5`, `[1,2,3]`, `[[1,2],[3,4]]`, `(1,0)`.
pub fn parse_val(s: &str) -> Option<TVal> {
    let s = normalize_minus(s);
    let s = s.trim();
    if looks_like_int(s) {
        if let Ok(n) = s.parse::<i64>() {
            return Some(TVal::Num(n));
        }
    }
    if looks_like_decimal(s) {
        if let Ok(f) = s.parse::<f64>() {
            return Some(TVal::FNum(f));
        }
    }
    if s.starts_with('[') && s.ends_with(']') {
        let inner = &s[1..s.len() - 1];
        if inner.trim().is_empty() {
            return Some(TVal::List(vec![]));
        }
        let mut items = Vec::new();
        let mut rest = inner;
        while !rest.trim().is_empty() {
            let (head, tail) = split_top_level(rest, ',').unwrap_or((rest, ""));
            items.push(parse_val(head)?);
            rest = tail;
        }
        return Some(TVal::List(items));
    }
    if s.starts_with('(') && s.ends_with(')') {
        let inner = &s[1..s.len() - 1];
        let mut items = Vec::new();
        let mut rest = inner;
        while !rest.trim().is_empty() {
            let (head, tail) = split_top_level(rest, ',').unwrap_or((rest, ""));
            items.push(parse_val(head)?);
            rest = tail;
        }
        return Some(TVal::List(items));
    }
    None
}

/// §C Real-World Constants (spec_top_rules.md §C) — resolvable by fingerprint.
/// Reference values (non-normative precision) held as IEEE-754 doubles so the
/// Python/Elixir evaluators agree on float handling.
fn resolve_constant(s: &str) -> Option<TVal> {
    Some(match s {
        // C.1 Mathematical (0xK0xx)
        "0xK001" => TVal::FNum(3.141592653589793), // π
        "0xK002" => TVal::FNum(2.718281828459045), // e
        "0xK003" => TVal::FNum(1.618033988749895), // φ
        "0xK004" => TVal::FNum(0.5772156649015329), // γ
        "0xK005" => TVal::FNum(1.4142135623730951), // √2
        "0xK006" => TVal::FNum(0.6931471805599453), // ln2
        "0xK007" => TVal::FNum(0.915965594177219), // G_𝒦
        "0xK008" => TVal::FNum(1.2020569031595942), // ζ3
        "0xK009" => TVal::FNum(4.66920160910299), // δ_ℱ
        // C.2 Physics (0xQ0xx)
        "0xQ001" => TVal::Num(299_792_458), // c (exact SI integer)
        "0xQ002" => TVal::FNum(6.62607015e-34), // h
        "0xQ003" => TVal::FNum(1.054571817e-34), // ℏ
        "0xQ004" => TVal::FNum(6.67430e-11), // G_𝔫
        "0xQ005" => TVal::FNum(8.8541878128e-12), // ε₀
        "0xQ006" => TVal::FNum(1.25663706212e-6), // μ₀
        "0xQ007" => TVal::FNum(1.602176634e-19), // e
        "0xQ008" => TVal::FNum(1.380649e-23), // k_B
        "0xQ009" => TVal::FNum(6.02214076e23), // N_A
        "0xQ00A" => TVal::FNum(8.314462618), // R
        "0xQ00B" => TVal::FNum(9.1093837015e-31), // mₑ
        "0xQ00C" => TVal::FNum(1.67262192369e-27), // mₚ
        "0xQ00D" => TVal::FNum(7.2973525693e-3), // α (fine-structure constant)
        "0xQ00E" => TVal::FNum(5.670374419e-8), // σ (Stefan–Boltzmann)
        "0xQ00F" => TVal::FNum(9.80665), // g₀ (standard gravity, exact SI)
        "0xQ010" => TVal::FNum(10973731.568160), // R_∞ (Rydberg constant)
        _ => return None,
    })
}

/// Split at the first top-level (depth-0) occurrence of `sep`.
fn split_top_level(s: &str, sep: char) -> Option<(&str, &str)> {
    let mut depth = 0i32;
    for (i, c) in s.char_indices() {
        match c {
            '[' | '(' => depth += 1,
            ']' | ')' => depth -= 1,
            c if c == sep && depth == 0 => return Some((&s[..i], &s[i + c.len_utf8()..])),
            _ => {}
        }
    }
    None
}

/// Human-readable value formatting for failure messages.
pub fn fmt_val(v: &TVal) -> String {
    match v {
        TVal::Num(n) => n.to_string(),
        TVal::FNum(f) => f.to_string(),
        TVal::List(items) => {
            let inner: Vec<String> = items.iter().map(fmt_val).collect();
            format!("[{}]", inner.join(","))
        }
    }
}
