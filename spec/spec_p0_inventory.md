# §IN — Inventory Protocol: Auditable Supply-Chain Semantics

> **Status**: P0 — Third Novel Spec Test (MASTER_PLAN §5.2, v0.40)
> **Depends**: core@1.0, error@1.0
> **Fingerprint prefix**: `0xD000`–`0xD0FF`
> **Motivation**: prove ΣLang generalizes beyond bioinformatics (v0.12 gene),
> app behavior (§SK) and finance (v0.19 portfolio) — a third brand-new domain
> (supply chain: inventory management) expressed as ΣLang semantics verified
> identically across Python / Rust / Elixir.

---

## IN.1 Motivation

An inventory holds stock of items (A, B). Its core behaviors:

- **Open**: initialize an inventory with starting stock.
- **Receive**: add stock (inbound delivery).
- **Ship**: remove stock (outbound order) — cannot ship more than held.
- **Level**: current stock level.
- **Fill rate**: shipped / demanded over a period.

Key business rules to make auditable:

- **No negative stock**: you cannot ship more than you hold (⊥ InsufficientStock).
- **Conservation**: received stock is additive; shipped stock never exceeds
  received + initial (no stock created from nothing).
- **Level / fill rate never negative**.

```md
- Inventory opening:  inventory_new(stockA, stockB) → Inventory
- Inbound:            receive_stock(inventory, item, qty) → Inventory
- Outbound:           ship_stock(inventory, item, qty) → Inventory
- Stock level:        stock_level(inventory, item) → ℕ
- Fill rate:          fill_rate(shipped, demanded) → ℚ
```

---

## IN.2 Core Types

```md
Inventory : List⟨ℕ⟩        # [qtyA, qtyB]
Item      : Type ≝ ℕ       # 0 = A, 1 = B
Qty       : Type ≝ ℕ       # must be ≥ 0
```

---

## IN.3 Operations

### IN.3.1 inventory_new — Inventory Opening (开仓)

```md
inventory_new : ℕ × ℕ → List⟨ℕ⟩              # (qtyA, qtyB) → Inventory
Fingerprint: 0xD001
Definition: inventory_new(a, b) ≡ [a, b]      # opening stock levels
```

**Laws**

```md
∀ a b . 0 ≤ inventory_new(a, b)               # stock levels ≥ 0
∀ a b . index(inventory_new(a, b), 0) ≡ a     # qtyA preserved
∀ a b . index(inventory_new(a, b), 1) ≡ b     # qtyB preserved
```

**Tests**

| Input | Output |
|-------|--------|
| inventory_new(10, 20) | [10,20] |
| inventory_new(0, 0) | [0,0] |
| inventory_new(-5, 10) | ⊥ TypeError |

### IN.3.2 receive_stock — Inbound Delivery (入库)

```md
receive_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩    # (inventory, item, qty) → Inventory
Fingerprint: 0xD002
Definition: receive_stock([a, b], 0, q) ≡ [a+q, b]
            receive_stock([a, b], 1, q) ≡ [a, b+q]
            # additive; unknown item → ⊥ UnknownItem
```

**Laws**

```md
∀ i x q . index(receive_stock(i, x, q), x+1) ≡ index(i, x+1) + q   # additive
∀ i x q . 0 ≤ index(receive_stock(i, x, q), x+1)                  # never negative
```

**Tests**

| Input | Output |
|-------|--------|
| receive_stock(inventory_new(10, 20), 0, 5) | [15,20] |
| receive_stock(inventory_new(10, 20), 1, 3) | [10,23] |
| receive_stock(inventory_new(10, 20), 2, 5) | ⊥ UnknownItem |

### IN.3.3 ship_stock — Outbound Order (出库)

```md
ship_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩       # (inventory, item, qty) → Inventory
Fingerprint: 0xD003
Definition: ship_stock([a, b], 0, q) ≡ [a−q, b]   if q ≤ a
            ship_stock([a, b], 1, q) ≡ [a, b−q]   if q ≤ b
            # insufficient stock → ⊥ InsufficientStock; unknown item → ⊥ UnknownItem
```

**Laws**

```md
∀ i x q . index(i, x+1) ≥ q ⇒ index(ship_stock(i, x, q), x+1) ≡ index(i, x+1) − q   # decrement
∀ i x q . index(i, x+1) ≥ q ⇒ 0 ≤ index(ship_stock(i, x, q), x+1)                  # no naked shorts
∀ i x q . index(i, x+1) < q ⇒ ship_stock(i, x, q) ≡ ⊥ InsufficientStock           # no negative stock
```

**Tests**

| Input | Output |
|-------|--------|
| ship_stock(inventory_new(10, 20), 0, 4) | [6,20] |
| ship_stock(inventory_new(10, 20), 1, 20) | [10,0] |
| ship_stock(inventory_new(10, 20), 0, 11) | ⊥ InsufficientStock |
| ship_stock(inventory_new(10, 20), 2, 5) | ⊥ UnknownItem |

### IN.3.4 stock_level — Stock Level (库存水位)

```md
stock_level : List⟨ℕ⟩ × ℕ → ℕ                 # (inventory, item) → ℕ
Fingerprint: 0xD004
Definition: stock_level([a, b], 0) ≡ a
            stock_level([a, b], 1) ≡ b
```

**Laws**

```md
∀ i x . 0 ≤ stock_level(i, x)                 # never negative
∀ i . stock_level(i, 0) + stock_level(i, 1) ≡ index(i, 0) + index(i, 1)   # total preserved
```

**Tests**

| Input | Output |
|-------|--------|
| stock_level(inventory_new(10, 20), 0) | 10 |
| stock_level(inventory_new(10, 20), 1) | 20 |
| stock_level(5, 0) | ⊥ TypeError |

### IN.3.5 fill_rate — Fill Rate (履约率)

```md
fill_rate : ℕ × ℕ → ℚ                         # (shipped, demanded) → ℚ
Fingerprint: 0xD005
Definition: fill_rate(s, d) ≡ s / d   if d > 0
            # demanded = 0 → ⊥ DivByZero
```

**Laws**

```md
∀ s d . d > 0 ⇒ 0 ≤ fill_rate(s, d) ≤ 1   # rate bounded 0..1 (s ≤ d by construction)
∀ s . fill_rate(s, 0) ≡ ⊥ DivByZero       # zero demand rejected
```

**Tests**

| Input | Output |
|-------|--------|
| fill_rate(6, 10) | 0.6 |
| fill_rate(10, 10) | 1 |
| fill_rate(6, 0) | ⊥ DivByZero |

---

## IN.4 Encodings (Law II — encoding to ℕ for non-numeric returns)

```md
encode_inventory : List⟨ℕ⟩ → ℕ     # Inventory → ℕ (Law II)
```

---

## IN.5 Adoption Trail

- **RFC**: MASTER_PLAN §5.2 (Novel Spec Test, P2 — third domain: supply chain).
- **Spec section**: this document (§IN).
- **Verifier check**: `corpus/inventory_ok.md` — three-verifier consensus
  (Law XIII), Law I/II/III/IV, E-02 negative tests, E-03 portability,
  E-04 exports, E-06 shape.
- **Tests**: the corpus module carries the canonical tests above as real
  §IN function calls.

> Promotion path reference: Phase 7 — RFC → spec section → Verifier check → tests.
