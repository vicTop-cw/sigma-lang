# §PF — Portfolio Protocol: Auditable Investment Semantics

> **Status**: P0 — Second Novel Spec Test (MASTER_PLAN §5.2, v0.19)
> **Depends**: core@1.0, error@1.0
> **Fingerprint prefix**: `0xE000`–`0xE0FF`
> **Motivation**: prove ΣLang generalizes beyond bioinformatics (v0.12 gene)
> and app behavior (§SK) — a second brand-new domain (finance: portfolio
> management) expressed as ΣLang semantics verified identically across
> Python / Rust / Elixir.

---

## PF.1 Motivation

A portfolio holds cash and positions in two assets (A, B). Its core behaviors:

- **Create**: open a portfolio with starting cash.
- **Buy**: spend cash to acquire a position (unit price 1).
- **Sell**: liquidate a position back into cash (unit price 1).
- **Value**: total assets (cash + positions).
- **Risk**: total position exposure (positions held).

Key business rules to make auditable:

- **Conservation**: buying/selling moves value between cash and positions
  but never changes total value (no money created or destroyed).
- **No negative cash**: you cannot buy more than you have (⊥ InsufficientFunds).
- **No naked shorts**: you cannot sell more than you hold (⊥ InsufficientShares).
- **Value / risk never negative**.

```md
- Portfolio creation:  portfolio_new(cash) → Portfolio
- Buy:                 buy(portfolio, asset, qty) → Portfolio
- Sell:                sell(portfolio, asset, qty) → Portfolio
- Valuation:           portfolio_value(portfolio) → ℕ
- Risk exposure:       risk_score(portfolio) → ℕ
```

---

## PF.2 Core Types

```md
Portfolio : List⟨ℕ⟩        # [cash, qtyA, qtyB]
Cash      : Type ≝ ℕ       # must be ≥ 0
Qty       : Type ≝ ℕ       # position size, must be ≥ 0
Asset     : Type ≝ ℕ       # 0 = A, 1 = B
```

---

## PF.3 Operations

### PF.3.1 portfolio_new — Portfolio Creation (开户)

```md
portfolio_new : ℕ → List⟨ℕ⟩              # cash → Portfolio
Fingerprint: 0xE001
Definition: portfolio_new(c) ≡ [c, 0, 0]  # empty positions
```

**Laws**

```md
∀ c . 0 ≤ portfolio_new(c)                # cash ≥ 0
∀ c . index(portfolio_new(c), 1) ≡ 0      # qtyA starts at 0
∀ c . index(portfolio_new(c), 2) ≡ 0      # qtyB starts at 0
```

**Tests**

| Input | Output |
|-------|--------|
| portfolio_new(100) | [100,0,0] |
| portfolio_new(0) | [0,0,0] |
| portfolio_new(-5) | ⊥ TypeError |

### PF.3.2 buy — Buy Asset (买入)

```md
buy : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩          # (portfolio, asset, qty) → Portfolio
Fingerprint: 0xE002
Definition: buy([c, qA, qB], 0, q) ≡ [c−q, qA+q, qB]   if c ≥ q
            buy([c, qA, qB], 1, q) ≡ [c−q, qA, qB+q]   if c ≥ q
            # unit price 1; insufficient cash → ⊥ InsufficientFunds
```

**Laws**

```md
∀ p a q . index(p, 0) ≥ q ⇒ portfolio_value(buy(p, a, q)) ≡ portfolio_value(p)   # 守恒
∀ p a q . index(p, 0) ≥ q ⇒ index(buy(p, a, q), 0) ≥ 0                          # cash ≥ 0
```

**Tests**

| Input | Output |
|-------|--------|
| buy(portfolio_new(100), 0, 30) | [70,30,0] |
| buy(portfolio_new(100), 1, 25) | [75,0,25] |
| buy(portfolio_new(10), 0, 30) | ⊥ InsufficientFunds |
| buy(portfolio_new(100), 2, 5) | ⊥ UnknownAsset |

### PF.3.3 sell — Sell Asset (卖出)

```md
sell : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩          # (portfolio, asset, qty) → Portfolio
Fingerprint: 0xE003
Definition: sell([c, qA, qB], 0, q) ≡ [c+q, qA−q, qB]   if q ≤ qA
            sell([c, qA, qB], 1, q) ≡ [c+q, qA, qB−q]   if q ≤ qB
            # unit price 1; insufficient position → ⊥ InsufficientShares
```

**Laws**

```md
∀ p a q . index(p, a+1) ≥ q ⇒ portfolio_value(sell(p, a, q)) ≡ portfolio_value(p)   # 守恒
∀ p a q . index(p, a+1) ≥ q ⇒ index(sell(p, a, q), a+1) ≥ 0                        # no naked shorts
```

**Tests**

| Input | Output |
|-------|--------|
| sell(buy(portfolio_new(100), 0, 30), 0, 20) | [90,10,0] |
| sell([70,30,0], 0, 30) | [100,0,0] |
| sell([70,30,0], 0, 40) | ⊥ InsufficientShares |
| sell([70,30,0], 2, 5) | ⊥ UnknownAsset |

### PF.3.4 portfolio_value — Total Valuation (估值)

```md
portfolio_value : List⟨ℕ⟩ → ℕ              # portfolio → ℕ
Fingerprint: 0xE004
Definition: portfolio_value([c, qA, qB]) ≡ c + qA + qB   # unit price 1
```

**Laws**

```md
∀ p . 0 ≤ portfolio_value(p)               # never negative
∀ p . portfolio_value(p) ≡ portfolio_value(p ⊕ [0])   # zero qty neutral? (no-op)
```

**Tests**

| Input | Output |
|-------|--------|
| portfolio_value(portfolio_new(100)) | 100 |
| portfolio_value([70,30,0]) | 100 |
| portfolio_value([50,20,30]) | 100 |

### PF.3.5 risk_score — Position Exposure (风险敞口)

```md
risk_score : List⟨ℕ⟩ → ℕ                   # portfolio → ℕ
Fingerprint: 0xE005
Definition: risk_score([c, qA, qB]) ≡ qA + qB   # total position exposure
```

**Laws**

```md
∀ p . 0 ≤ risk_score(p)                    # never negative
∀ p . risk_score(p) ≤ portfolio_value(p)   # exposure bounded by total value
```

**Tests**

| Input | Output |
|-------|--------|
| risk_score(portfolio_new(100)) | 0 |
| risk_score([70,30,0]) | 30 |
| risk_score([50,20,30]) | 50 |

---

## PF.4 Encodings (Law II — encoding to ℕ for non-numeric returns)

```md
encode_portfolio : List⟨ℕ⟩ → ℕ     # Portfolio → ℕ (Law II)
```

---

## PF.5 Adoption Trail

- **RFC**: MASTER_PLAN §5.2 (Novel Spec Test, P2 — second domain: finance).
- **Spec section**: this document (§PF).
- **Verifier check**: `corpus/portfolio_ok.md` — three-verifier consensus
  (Law XIII), Law I/II/III/IV, E-02 negative tests, E-03 portability,
  E-04 exports, E-06 shape.
- **Tests**: the corpus module carries the canonical tests above as real
  §PF function calls.

> Promotion path reference: Phase 7 — RFC → spec section → Verifier check → tests.
