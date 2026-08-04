# §IN — 库存协议：可审计的供应链语义（中文参考版）

> **状态**: P0 — 第三个自举新域测试（MASTER_PLAN §5.2，v0.40）
> **依赖**: core@1.0、error@1.0
> **指纹前缀**: `0xD000`–`0xD0FF`
> **动机**: 证明 ΣLang 的泛化性超越生物信息学（v0.12 gene）、应用行为（§SK）
> 与金融（v0.19 portfolio）——第三个全新领域（供应链：库存管理）以 ΣLang
> 语义表达，并在 Python / Rust / Elixir 三端一致验证。
> **本文件为中文参考版；英文原版 `spec/spec_p0_inventory.md` 为准。**

---

## IN.1 动机

库存持有货品（A、B）的存量。核心行为：

- **开仓**：以初始存量初始化库存。
- **入库**：增加存量（入库交付）。
- **出库**：扣减存量（出库订单）——不能超卖。
- **水位**：当前存量水平。
- **履约率**：一段时期内已履约 / 需求量。

需要审计化的关键业务规则：

- **库存非负**：不能卖出多于持有量（⊥ InsufficientStock）。
- **守恒**：入库可加；出库永不超过入库 + 初始（库存不会凭空产生）。
- **水位 / 履约率永不为负**。

```md
- 开仓:            inventory_new(stockA, stockB) → Inventory
- 入库:            receive_stock(inventory, item, qty) → Inventory
- 出库:            ship_stock(inventory, item, qty) → Inventory
- 库存水位:        stock_level(inventory, item) → ℕ
- 履约率:          fill_rate(shipped, demanded) → ℚ
```

---

## IN.2 核心类型

```md
Inventory : List⟨ℕ⟩        # [qtyA, qtyB]
Item      : Type ≝ ℕ       # 0 = A, 1 = B
Qty       : Type ≝ ℕ       # 必须 ≥ 0
```

---

## IN.3 操作

### IN.3.1 inventory_new — 开仓

```md
inventory_new : ℕ × ℕ → List⟨ℕ⟩              # (qtyA, qtyB) → Inventory
Fingerprint: 0xD001
Definition: inventory_new(a, b) ≡ [a, b]      # 开仓存量
```

**定律**

```md
∀ a b . 0 ≤ inventory_new(a, b)               # 存量 ≥ 0
∀ a b . index(inventory_new(a, b), 0) ≡ a     # qtyA 保持
∀ a b . index(inventory_new(a, b), 1) ≡ b     # qtyB 保持
```

**测试**

| 输入 | 输出 |
|-------|--------|
| inventory_new(10, 20) | [10,20] |
| inventory_new(0, 0) | [0,0] |
| inventory_new(-5, 10) | ⊥ TypeError |

### IN.3.2 receive_stock — 入库

```md
receive_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩    # (inventory, item, qty) → Inventory
Fingerprint: 0xD002
Definition: receive_stock([a, b], 0, q) ≡ [a+q, b]
            receive_stock([a, b], 1, q) ≡ [a, b+q]
            # 可加；未知货品 → ⊥ UnknownItem
```

**定律**

```md
∀ i x q . index(receive_stock(i, x, q), x+1) ≡ index(i, x+1) + q   # 可加性
∀ i x q . 0 ≤ index(receive_stock(i, x, q), x+1)                  # 永不为负
```

**测试**

| 输入 | 输出 |
|-------|--------|
| receive_stock(inventory_new(10, 20), 0, 5) | [15,20] |
| receive_stock(inventory_new(10, 20), 1, 3) | [10,23] |
| receive_stock(inventory_new(10, 20), 2, 5) | ⊥ UnknownItem |

### IN.3.3 ship_stock — 出库

```md
ship_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩       # (inventory, item, qty) → Inventory
Fingerprint: 0xD003
Definition: ship_stock([a, b], 0, q) ≡ [a−q, b]   if q ≤ a
            ship_stock([a, b], 1, q) ≡ [a, b−q]   if q ≤ b
            # 存量不足 → ⊥ InsufficientStock；未知货品 → ⊥ UnknownItem
```

**定律**

```md
∀ i x q . index(i, x+1) ≥ q ⇒ index(ship_stock(i, x, q), x+1) ≡ index(i, x+1) − q   # 扣减
∀ i x q . index(i, x+1) ≥ q ⇒ 0 ≤ index(ship_stock(i, x, q), x+1)                  # 不裸卖空
∀ i x q . index(i, x+1) < q ⇒ ship_stock(i, x, q) ≡ ⊥ InsufficientStock           # 库存非负
```

**测试**

| 输入 | 输出 |
|-------|--------|
| ship_stock(inventory_new(10, 20), 0, 4) | [6,20] |
| ship_stock(inventory_new(10, 20), 1, 20) | [10,0] |
| ship_stock(inventory_new(10, 20), 0, 11) | ⊥ InsufficientStock |
| ship_stock(inventory_new(10, 20), 2, 5) | ⊥ UnknownItem |

### IN.3.4 stock_level — 库存水位

```md
stock_level : List⟨ℕ⟩ × ℕ → ℕ                 # (inventory, item) → ℕ
Fingerprint: 0xD004
Definition: stock_level([a, b], 0) ≡ a
            stock_level([a, b], 1) ≡ b
```

**定律**

```md
∀ i x . 0 ≤ stock_level(i, x)                 # 永不为负
∀ i . stock_level(i, 0) + stock_level(i, 1) ≡ index(i, 0) + index(i, 1)   # 总量保持
```

**测试**

| 输入 | 输出 |
|-------|--------|
| stock_level(inventory_new(10, 20), 0) | 10 |
| stock_level(inventory_new(10, 20), 1) | 20 |
| stock_level(5, 0) | ⊥ TypeError |

### IN.3.5 fill_rate — 履约率

```md
fill_rate : ℕ × ℕ → ℚ                         # (shipped, demanded) → ℚ
Fingerprint: 0xD005
Definition: fill_rate(s, d) ≡ s / d   if d > 0
            # demanded = 0 → ⊥ DivByZero
```

**定律**

```md
∀ s d . d > 0 ⇒ 0 ≤ fill_rate(s, d) ≤ 1   # 履约率有界 0..1（构造上 s ≤ d）
∀ s . fill_rate(s, 0) ≡ ⊥ DivByZero       # 零需求拒绝
```

**测试**

| 输入 | 输出 |
|-------|--------|
| fill_rate(6, 10) | 0.6 |
| fill_rate(10, 10) | 1.0 |
| fill_rate(6, 0) | ⊥ DivByZero |

---

## IN.4 编码（Law II — 非数值返回编码为 ℕ）

```md
encode_inventory : List⟨ℕ⟩ → ℕ     # Inventory → ℕ (Law II)
```

---

## IN.5 推广路径

- **RFC**: MASTER_PLAN §5.2（Novel Spec Test，P2 — 第三域：供应链）。
- **规范章节**: 本文件（§IN）。
- **验证器检查**: `corpus/inventory_ok.md` — 三端共识（Law XIII）、Law I/II/III/IV、
  E-02 负例、E-03 可移植性、E-04 导出、E-06 形状。
- **测试**: 语料模块以上述规范测试作为真实 §IN 函数调用承载。

> 推广路径参考：Phase 7 — RFC → 规范章节 → 验证器检查 → 测试。
