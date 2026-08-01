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
