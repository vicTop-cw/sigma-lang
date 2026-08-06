# Module: inventory_systems_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (Inventory supply-chain domain — cross-operation chain)
# Intent: verifier test set for the §IN supply chain working as one
# pipeline — open (inventory_new) → inbound chain (receive_stock ×2) →
# outbound chain (ship_stock ×2) → stock level → fill rate. The Tests
# exercise real function calls chaining one operation's output into the
# next, so the consensus gate (Law XIII) verifies cross-operation
# integration semantics. Added at v0.154.

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
inventory_new(a, b) ≡ [a, b]
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
index(receive_stock(inv, 0, q), 0) ≡ index(inv, 0) + q
```

### Tests

| Input | Output |
|-------|--------|
| receive_stock(inventory_new(10, 20), 0, 5) | [15,20] |
| receive_stock(receive_stock(inventory_new(10, 20), 0, 5), 1, 3) | [15,23] |
| receive_stock(inventory_new(10, 20), 2, 5) | ⊥ UnknownItem |

## Operation: ship_stock (Outbound Order)

### Signature

```md
ship_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xD003
```

### Laws

```md
index(ship_stock(inv, 0, q), 0) ≡ index(inv, 0) − q
```

### Tests

| Input | Output |
|-------|--------|
| ship_stock(inventory_new(10, 20), 0, 4) | [6,20] |
| ship_stock(ship_stock(inventory_new(10, 20), 0, 4), 1, 8) | [6,12] |
| ship_stock(inventory_new(10, 20), 0, 11) | ⊥ InsufficientStock |

## Operation: stock_level (Stock Level)

### Signature

```md
stock_level : List⟨ℕ⟩ × ℕ → ℕ
Fingerprint: 0xD004
```

### Laws

```md
stock_level(inv, 0) ≡ index(inv, 0)
```

### Tests

| Input | Output |
|-------|--------|
| stock_level(inventory_new(10, 20), 0) | 10 |
| stock_level(ship_stock(receive_stock(inventory_new(10, 20), 0, 5), 0, 4), 0) | 11 |
| stock_level(5, 0) | ⊥ TypeError |

## Operation: fill_rate (Fill Rate)

### Signature

```md
fill_rate : ℕ × ℕ → ℝ
Fingerprint: 0xD005
```

### Laws

```md
fill_rate(s, d) ≡ s / d
```

### Tests

| Input | Output |
|-------|--------|
| fill_rate(6, 10) | 0.6 |
| fill_rate(10, 10) | 1.0 |
| fill_rate(6, 0) | ⊥ DivByZero |

### encode_inventory

```md
encode_inventory : List⟨ℕ⟩ → ℕ
```
