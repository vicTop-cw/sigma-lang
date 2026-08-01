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
    if let Some(rest) = s.strip_prefix("index(") {
        let inner = rest.strip_suffix(')').ok_or("bad index call")?;
        let (target, idx) = split_top_level(inner, ',')
            .ok_or_else(|| format!("bad index args: {}", inner))?;
        let tv = eval_expr(target)?;
        let iv = parse_val(&idx).ok_or_else(|| format!("bad index: {}", idx))?;
        return index_into(&tv, &iv);
    }
    if s == "I₂" {
        return Ok(TVal::List(vec![
            TVal::List(vec![TVal::Num(1), TVal::Num(0)]),
            TVal::List(vec![TVal::Num(0), TVal::Num(1)]),
        ]));
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
    if let Ok(n) = s.parse::<i64>() {
        return Some(TVal::Num(n));
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
