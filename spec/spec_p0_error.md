# §E — Error Algebra (Result Type & Error Combinators)

> **Status**: P0 — Foundational (without this, AI communication cannot handle failure)
> **Depends**: core@1.0
> **Fingerprint prefix**: `0xE000`–`0xE0FF`

---

## E.1 Motivation

AI systems fail. Always. They:
- Return malformed data
- Hit network errors
- Timeout
- Run out of memory
- Produce NaN / ⊥

A language for AI **must** give errors first-class treatment:
- Errors are **values**, not exceptions
- Error handling is **algebraic**, not imperative
- Error composition is **verifiable**

---

## E.2 The Result Type

### E.2.1 Definition

```md
## Result⟨V, E⟩
Result⟨V, E⟩ ≝ V + E

Constructors:
  ok  : V → Result⟨V, E⟩
  err : E → Result⟨V, E⟩

## Interpretation
ok(v)  ≝ inject₁ v    # success, carrying value v
err(e) ≝ inject₂ e    # failure, carrying error e
```

### E.2.2 Error Types (Built-in)

```md
Error : Type   # sum of all error variants

## Primitive errors
TimeoutErr   : Error   # operation timed out
NetworkErr   : Error   # network failure
DecodeErr    : Error   # parsing/decoding failed
EncodeErr    : Error   # encoding failed
NotFound     : Error   # resource not found
PermissionErr: Error   # access denied
OutOfMem     : Error   # memory exhausted
OverflowErr  : Error   # numeric overflow
UnderflowErr : Error   # numeric underflow
NaNErr       : Error   # not-a-number encountered
AssertErr    : Error   # assertion failed
PanicErr     : Error   # unrecoverable state
UnknownErr   : Error   # unspecified failure
```

### E.2.3 Custom Error Types

```md
## Users can define domain errors
data ParseError
  | UnexpectedToken(Sym)
  | UnexpectedEOF
  | InvalidNumber(ℚ)

data SqlError
  | ConnectionLost
  | QueryTimeout
  | ConstraintViolation(Sym)
```

---

## E.3 Core Combinators

| Glyph | Name | Type | Fingerprint | Meaning |
|-------|------|------|-------------|---------|
| `>>=` | Bind | `Result⟨V,E⟩ → (V → Result⟨W,E⟩) → Result⟨W,E⟩` | `0xE001` | Monadic bind |
| `>>` | Sequence | `Result⟨V,E⟩ → Result⟨W,E⟩ → Result⟨W,E⟩` | `0xE002` | Discard left value |
| `\|>` | Pipe | `V → (V → Result⟨W,E⟩) → Result⟨W,E⟩` | `0xE003` | Thread value |
| `try` | Try-catch | `Effect → Result⟨V,E⟩` | `0xE004` | Catch exceptions |
| `throw` | Throw | `E → Result⟨V,E⟩` | `0xE005` | Inject error |
| `catch` | Recover | `Result⟨V,E₁⟩ → (E₁ → Result⟨V,E₂⟩) → Result⟨V,E₂⟩` | `0xE006` | Error recovery |
| `map` | Value map | `Result⟨V,E⟩ → (V → W) → Result⟨W,E⟩` | `0xE007` | Transform ok |
| `map_err` | Error map | `Result⟨V,E₁⟩ → (E₁ → E₂) → Result⟨V,E₂⟩` | `0xE008` | Transform err |
| `flatten` | Flatten | `Result⟨Result⟨V,E⟩,E⟩ → Result⟨V,E⟩` | `0xE009` | Remove nesting |
| `or_else` | Alternative | `Result⟨V,E₁⟩ → Result⟨V,E₂⟩ → Result⟨V,E₁+E₂⟩` | `0xE00A` | Try fallback |
| `unwrap_or` | Default | `Result⟨V,E⟩ → V → V` | `0xE00B` | Extract with default |
| `expect` | Force unwrap | `Result⟨V,E⟩ → String → V` | `0xE00C` | Panic if err |

---

## E.4 Laws

### E.4.1 Monad Laws (for `>>=`)

```md
## Left identity
∀ v f . ok(v) >>= f ≡ f(v)

## Right identity
∀ m . m >>= ok ≡ m

## Associativity
∀ m f g . (m >>= f) >>= g ≡ m >>= (λx. f(x) >>= g)
```

### E.4.2 Short-circuit Law

```md
## Error short-circuits
∀ e f . err(e) >>= f ≡ err(e)

## ok passes through
∀ v f . ok(v) >>= (λx. ok(f(x))) ≡ ok(f(v))
```

### E.4.3 map / map_err Laws

```md
map(ok(v), f) ≡ ok(f(v))
map(err(e), f) ≡ err(e)

map_err(ok(v), g) ≡ ok(v)
map_err(err(e), g) ≡ err(g(e))
```

### E.4.4 or_else Law

```md
or_else(ok(v), _) ≡ ok(v)
or_else(err(e₁), ok(v)) ≡ ok(v)
or_else(err(e₁), err(e₂)) ≡ err(e₁ + e₂)
```

### E.4.5 try / throw Laws

```md
try(ok(v)) ≡ ok(v)
try(throwing(e)) ≡ err(e)

throw(e) ≡ err(e)
```

---

## E.5 Error Composition

### E.5.1 Sum Type for Errors

```md
## Combining different error types
E₁ + E₂ : ErrorSum

## Injections
left  : E₁ → E₁ + E₂
right : E₂ → E₁ + E₂

## Extraction
match_err : Result⟨V, E₁+E₂⟩ → Either⟨E₁, E₂⟩
```

### E.5.2 Error Transformer (Bifunctor)

```md
## bimap : (V→W) → (E₁→E₂) → Result⟨V,E₁⟩ → Result⟨W,E₂⟩
bimap(f, g, ok(v))  ≡ ok(f(v))
bimap(f, g, err(e)) ≡ err(g(e))
```

### E.5.3 Laws for Error Composition

```md
## Distributivity of map over >>= 
map(m, f) >>= g ≡ m >>= (λx. g(f(x)))

## Error preservation in composition
∀ e . (err(e) >>= f) ≡ err(e)

## catch restores flow
catch(err(e), λ_. ok(v)) ≡ ok(v)
catch(ok(v), f) ≡ ok(v)
```

---

## E.6 Do-Notation (Syntactic Sugar)

```md
## do-notation desugaring

do {
  x ← ok(1);
  y ← ok(2);
  return (x + y)
}
≡ ok(1) >>= (λx. ok(2) >>= (λy. ok(x+y)))


do {
  x ← might_fail();
  y ← also_might_fail(x);
  return (x + y)
}
≡ might_fail() >>= (λx. also_might_fail(x) >>= (λy. ok(x+y)))
```

### Laws for do-notation

```md
## Every `←` is a bind
## Every `return` is ok
## First error stops the chain
```

---

## E.7 Effect System Integration

### E.7.1 Effect Annotations

```md
## Functions declare their error effects

f : A → Result⟨B, E₁+E₂⟩
# means: f may fail with E₁ or E₂

g : A → B    # pure, no Result = no failure possible
```

### E.7.2 Effect Inference

```md
## Verifier infers error types

f(x) ≝
  if x > 0 then ok(1/x)    # no error
  else err(DivideByZero)    # explicit error

# Verifier infers: f : ℝ → Result⟨ℝ, DivErr⟩
```

### E.7.3 Effect Polymorphism

```md
## Function that works for any error type
safe_head : List⟨T⟩ → Result⟨T, EmptyListErr⟩

## Composing with different errors
combine : Result⟨A,E₁⟩ → Result⟨B,E₂⟩
        → Result⟨(A,B), E₁+E₂⟩
combine(ra, rb) ≝
  do {
    a ← ra;
    b ← rb;
    return (a, b)
  }
```

---

## E.8 Canonical Tests

| Expression | Expected |
|-----------|----------|
| `ok(3) >>= (λx. ok(x+1))` | `ok(4)` |
| `err(TimeoutErr) >>= f` | `err(TimeoutErr)` |
| `map(ok(3), (λx. x*2))` | `ok(6)` |
| `map_err(err(1), (λx. x+1))` | `err(2)` |
| `or_else(err(1), ok(42))` | `ok(42)` |
| `or_else(err(1), err(2))` | `err(1+2)` (or `err(1)`) |
| `flatten(ok(ok(3)))` | `ok(3)` |
| `flatten(ok(err(e)))` | `err(e)` |
| `flatten(err(e))` | `err(e)` |
| `do { x←ok(1); y←ok(2); return (x+y) }` | `ok(3)` |
| `do { x←ok(1); y←err(e); return (x+y) }` | `err(e)` |

---

## Implementation Checklist (for AI)

### To pass this module, implement exactly these

1. `Ok(v)` / `Err(e)` — `bind(f)`, `map(f)`, `map_err(f)`, `unwrap_or(d)`; must satisfy the three monad laws (left identity, right identity, associativity)  [E-01]
2. `flatten` — `ok(ok(v)) → ok(v)`, `ok(err(e)) → err(e)`, `err(e) → err(e)`  [E-02]
3. `err_plus(e1, e2)` — error sum type: combine two error domains  [E-03]
4. Do-notation is sugar over `bind`: every `←` is a bind, every `return` is `ok`, the first error stops the chain  [E-04]

Reference implementation: `impl/python/sigma_core.py` (§E), self-check via `python3 impl/python/sigma_core.py`.

### What NOT to implement
- Do NOT catch exceptions implicitly — errors must flow through the `Result` type explicitly.
- Do NOT add stack traces or exception causality — ΣLang errors are values.
- Do NOT implement `or_else` by swallowing errors; composition must preserve the first error.

---

## E.9 Verifier Rules for Error Module

```rust
impl Verifier {
    /// Check monad laws hold for a given Result implementation
    fn verify_result_laws(&self, impl: &dyn ResultImpl) -> Result<(), Violation> {
        // Left identity: ok(v) >>= f ≡ f(v)
        for (v, f) in self.test_pairs() {
            let lhs = impl.bind(impl.ok(v), &f);
            let rhs = f(v);
            if !impl.equiv(&lhs, &rhs) {
                return Err(Violation::MonadLaw {
                    law: "left_identity".to_string(),
                    counterexample: format!("v={:?}, f={:?}", v, f),
                });
            }
        }

        // Right identity: m >>= ok ≡ m
        for m in self.result_values() {
            let lhs = impl.bind(m.clone(), &|x| impl.ok(x));
            if !impl.equiv(&lhs, &m) {
                return Err(Violation::MonadLaw {
                    law: "right_identity".to_string(),
                    counterexample: format!("{:?}", m),
                });
            }
        }

        // Short-circuit: err(e) >>= f ≡ err(e)
        for (e, f) in self.err_test_pairs() {
            let lhs = impl.bind(impl.err(e.clone()), &f);
            let rhs = impl.err(e);
            if !impl.equiv(&lhs, &rhs) {
                return Err(Violation::ShortCircuitFailure {
                    e: format!("{:?}", e),
                });
            }
        }

        Ok(())
    }
}
```

---

## E.10 Error Best Practices (Non-Normative)

```md
## Guideline: Use specific error types
❌ Result⟨V, String⟩       # stringly-typed errors
✅ Result⟨V, ParseError⟩   # typed errors

## Guideline: Combine errors with +
❌ return err("timeout or network")
✅ return err(TimeoutErr + NetworkErr)

## Guideline: Don't catch everything
❌ catch(m, λ_. ok(default))   # silently swallows
✅ catch(m, λe. if retryable(e) then retry(m) else err(e))

## Guideline: Effects are part of the type
❌ f : A → B   (but actually can fail)
✅ f : A → Result⟨B, FError⟩
```
