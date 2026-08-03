# Module: inventory_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: supply chain (inventory management)
# Intent: third Novel Spec Test (MASTER_PLAN §5.2, v0.40–v0.42) — a brand-new
# domain (supply chain: inventory open/receive/ship/level/fill-rate) expressed
# in ΣLang and proven three-verifier consistent. The Tests exercise the §IN
# operations as real function calls, so the consensus gate verifies inventory
# semantics itself.

## Imports

```md
import core
```

## Exports

```md
inventory_new
receive_stock
ship_stock
stock_level
fill_rate
```

## Operation: inventory_new (Inventory Opening)

### Signature

```md
inventory_new : ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xD001
```

### Laws

```md
∀ a b . 0 ≤ inventory_new(a, b)
∀ a b . index(inventory_new(a, b), 0) ≡ a
∀ a b . index(inventory_new(a, b), 1) ≡ b
```

### Tests

| Input | Output |
|-------|--------|
| inventory_new(10, 20) | [10,20] |
| inventory_new(0, 0) | [0,0] |
| inventory_new(-5, 10) | ⊥ TypeError |

## Operation: receive_stock (Inbound Delivery)

### Signature

```md
receive_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xD002
```

### Laws

```md
∀ i x q . index(receive_stock(i, x, q), x+1) ≡ index(i, x+1) + q
∀ i x q . 0 ≤ index(receive_stock(i, x, q), x+1)
```

### Tests

| Input | Output |
|-------|--------|
| receive_stock(inventory_new(10, 20), 0, 5) | [15,20] |
| receive_stock(inventory_new(10, 20), 1, 3) | [10,23] |
| receive_stock(inventory_new(10, 20), 2, 5) | ⊥ UnknownItem |

## Operation: ship_stock (Outbound Order)

### Signature

```md
ship_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xD003
```

### Laws

```md
∀ i x q . index(i, x+1) ≥ q ⇒ index(ship_stock(i, x, q), x+1) ≡ index(i, x+1) − q
∀ i x q . index(i, x+1) ≥ q ⇒ 0 ≤ index(ship_stock(i, x, q), x+1)
∀ i x q . index(i, x+1) < q ⇒ ship_stock(i, x, q) ≡ ⊥ InsufficientStock
```

### Tests

| Input | Output |
|-------|--------|
| ship_stock(inventory_new(10, 20), 0, 4) | [6,20] |
| ship_stock(inventory_new(10, 20), 1, 20) | [10,0] |
| ship_stock(inventory_new(10, 20), 0, 11) | ⊥ InsufficientStock |
| ship_stock(inventory_new(10, 20), 2, 5) | ⊥ UnknownItem |

## Operation: stock_level (Stock Level)

### Signature

```md
stock_level : List⟨ℕ⟩ × ℕ → ℕ
Fingerprint: 0xD004
```

### Laws

```md
∀ i x . 0 ≤ stock_level(i, x)
∀ i . stock_level(i, 0) + stock_level(i, 1) ≡ index(i, 0) + index(i, 1)
```

### Tests

| Input | Output |
|-------|--------|
| stock_level(inventory_new(10, 20), 0) | 10 |
| stock_level(inventory_new(10, 20), 1) | 20 |
| stock_level(5, 0) | ⊥ TypeError |

## Operation: fill_rate (Fill Rate)

### Signature

```md
fill_rate : ℕ × ℕ → ℚ
Fingerprint: 0xD005
```

### Laws

```md
∀ s d . d > 0 ⇒ 0 ≤ fill_rate(s, d) ≤ 1
∀ s . fill_rate(s, 0) ≡ ⊥ DivByZero
```

### Tests

| Input | Output |
|-------|--------|
| fill_rate(6, 10) | 0.6 |
| fill_rate(10, 10) | 1.0 |
| fill_rate(6, 0) | ⊥ DivByZero |

## Functions

### encode_inventory

```md
encode_inventory : List⟨ℕ⟩ → ℕ
```
