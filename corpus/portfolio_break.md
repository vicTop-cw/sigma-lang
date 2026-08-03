# Module: portfolio_break
# Version: 1.0.0
# Expected: FAIL (E-02 — No Negative Test)
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: finance (portfolio management)
# Intent: negative counterpart of portfolio_ok.md — portfolio_new declares
# fingerprint, laws, and success tests but NO negative (⊥/error-path) test,
# so Law XIV (E-02) must reject it identically across Python / Rust / Elixir.

## Imports

```md
import core
```

## Exports

```md
portfolio_new
```

## Operation: portfolio_new (Portfolio Creation)

### Signature

```md
portfolio_new : ℕ → List⟨ℕ⟩
Fingerprint: 0xE001
```

### Laws

```md
∀ c . 0 ≤ portfolio_new(c)
∀ c . index(portfolio_new(c), 1) ≡ 0
```

### Tests

| Input | Output |
|-------|--------|
| portfolio_new(100) | [100,0,0] |
| portfolio_new(0) | [0,0,0] |

> E-02: no ⊥ (error-path) test present — a negative test is mandatory.

## Functions

### encode_portfolio

```md
encode_portfolio : List⟨ℕ⟩ → ℕ
```
