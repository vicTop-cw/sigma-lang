# Module: portfolio_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: finance (portfolio management)
# Intent: second Novel Spec Test (MASTER_PLAN §5.2, v0.19) — a brand-new domain
# (finance: portfolio buy/sell/valuation/risk) expressed in ΣLang and proven
# three-verifier consistent. The Tests exercise the §PF operations as real
# function calls (portfolio_new / buy / sell / portfolio_value / risk_score),
# so the consensus gate (Law XIII) verifies investment semantics itself.

## Imports

```md
import core
```

## Exports

```md
portfolio_new
buy
sell
portfolio_value
risk_score
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
∀ c . index(portfolio_new(c), 2) ≡ 0
```

### Tests

| Input | Output |
|-------|--------|
| portfolio_new(100) | [100,0,0] |
| portfolio_new(0) | [0,0,0] |
| portfolio_new(-5) | ⊥ TypeError |

## Operation: buy (Buy Asset)

### Signature

```md
buy : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xE002
```

### Laws

```md
∀ p a q . index(p, 0) ≥ q ⇒ portfolio_value(buy(p, a, q)) ≡ portfolio_value(p)
∀ p a q . index(p, 0) ≥ q ⇒ index(buy(p, a, q), 0) ≥ 0
```

### Tests

| Input | Output |
|-------|--------|
| buy(portfolio_new(100), 0, 30) | [70,30,0] |
| buy(portfolio_new(100), 1, 25) | [75,0,25] |
| buy(portfolio_new(10), 0, 30) | ⊥ InsufficientFunds |
| buy(portfolio_new(100), 2, 5) | ⊥ UnknownAsset |

## Operation: sell (Sell Asset)

### Signature

```md
sell : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xE003
```

### Laws

```md
∀ p a q . index(p, a+1) ≥ q ⇒ portfolio_value(sell(p, a, q)) ≡ portfolio_value(p)
∀ p a q . index(p, a+1) ≥ q ⇒ index(sell(p, a, q), a+1) ≥ 0
```

### Tests

| Input | Output |
|-------|--------|
| sell(buy(portfolio_new(100), 0, 30), 0, 20) | [90,10,0] |
| sell([70,30,0], 0, 30) | [100,0,0] |
| sell([70,30,0], 0, 40) | ⊥ InsufficientShares |
| sell([70,30,0], 2, 5) | ⊥ UnknownAsset |

## Operation: portfolio_value (Total Valuation)

### Signature

```md
portfolio_value : List⟨ℕ⟩ → ℕ
Fingerprint: 0xE004
```

### Laws

```md
∀ p . 0 ≤ portfolio_value(p)
```

### Tests

| Input | Output |
|-------|--------|
| portfolio_value(portfolio_new(100)) | 100 |
| portfolio_value([70,30,0]) | 100 |
| portfolio_value([50,20,30]) | 100 |
| portfolio_value(5) | ⊥ TypeError |

## Operation: risk_score (Position Exposure)

### Signature

```md
risk_score : List⟨ℕ⟩ → ℕ
Fingerprint: 0xE005
```

### Laws

```md
∀ p . 0 ≤ risk_score(p)
∀ p . risk_score(p) ≤ portfolio_value(p)
```

### Tests

| Input | Output |
|-------|--------|
| risk_score(portfolio_new(100)) | 0 |
| risk_score([70,30,0]) | 30 |
| risk_score([50,20,30]) | 50 |
| risk_score(5) | ⊥ TypeError |

## Functions

### encode_portfolio

```md
encode_portfolio : List⟨ℕ⟩ → ℕ
```
