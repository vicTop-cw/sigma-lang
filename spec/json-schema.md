# ΣLang Spec JSON Schema v1.0

> 依据 ROADMAP.md §4.1 的格式设计定稿。所有 spec JSON 必须符合本 schema。
> 类型语法：`nat`（非负整数）、`int`（整数）、`str`（字符串）、`bool`、
> `List<T>`、`Option<T>`、`unit`，以及 spec 内 `types` 中声明的别名。
>
> 类型扩展（整改项 4.7）：
> * `Str` — 字符串。与参数名引用的区分沿用既有规则：字符串命中 definition.params 中的
>   名字 → 参数引用；否则一律按 Str 字面量求值。内置 `str_len` / `str_concat` / `str_contains`。
> * `Time` — 时间，unix epoch 整数（秒）。本质是整数，可直接参与算术运算；
>   内置 `time_now_epoch` 返回固定种子值（确定性测试用，不依赖真实时钟）。
> * `Option<T>` — 可选值。引擎表示：`None` = none，非 None 值 = some(T)；
>   构造用 `option_some` / `option_none`，取值即取回 some 的 payload 本身。
> * `Map<K,V>` — 键值表。JSON 对象字面量 `{"map": {k: expr, ...}}` 构造（键为字符串，
>   值为表达式节点），`map_get` 取键；未命中键返回 `None`（配合 Option 语义）。

## 顶层结构

```json
{
  "spec": "§SK",
  "version": "0.7.0",
  "fingerprint_prefix": "0xF000",
  "constants": [ConstantDecl...],  // 可选：集中声明魔法常量（v0.31 起）
  "types": [TypeDecl...],
  "operations": [OperationDecl...]
}
```

## ConstantDecl（v0.31 起，可选）

```json
{
  "status": {"open": 0, "in_progress": 1, "pending_review": 2, "completed": 3},
  "decision": {"reject": 0, "accept": 1},
  "badge": {"levels": {"bronze": 0, "silver": 1, "gold": 2, "diamond": 3},
            "thresholds": [100, 300, 600]},
  "verifier_min_id": 1000,
  "credit": {"initial": 100, "kind0_per_completion": 5,
             "kind1_floor_ratio": {"num": 7, "den": 10}, "floor": 0},
  "contribution": {"floor": 0},
  "team": {"min_capacity": 1},
  "ledger": {"entry_id_start": 1, "min_source_id": 1}
}
```

`constants` 区集中声明散落在 operations 的 definition / laws / preconditions 中的魔法常量
（状态值、徽章阈值、验证者门槛、契分系数、初始 credit 等）。规则：

1. 所有实现必须使用 `constants` 中的数值，不得自行另设；
2. `constants` 是**描述性声明**，引擎不依赖它求值（求值语义仍由 operations 的 definition 决定）；
3. 若 definition / laws 中的字面量与 `constants` 冲突，以 `constants` 为准并视为 spec 错误；
4. 可选字段：未提供 `constants` 区的旧 spec 仍合法。

## TypeDecl

```json
{
  "name": "Task",
  "kind": "alias" | "list" | "enum" | "option" | "map",
  "target": "List<nat>",        // kind=alias 时：目标类型
  "element": "nat",             // kind=list 时：元素类型
  "values": [{"name": "open", "value": 0}],  // kind=enum 时
  "key": "nat", "value": "nat"  // kind=map 时
}
```

## OperationDecl

```json
{
  "name": "task_create",
  "fingerprint": "0xF001",
  "signature": {"params": ["nat", "nat"], "returns": "Task"},
  "definition": {
    "kind": "lambda" | "table" | "expression",
    "params": ["a", "b"],
    "body": ["a", "b", 0, 0],      // kind=lambda：字面量/参数引用/嵌套调用
    "table": [                      // kind=table：状态机转移表
      {"when": {"field": 2, "eq": 0}, "set": {"field": 2, "value": 1}, "guard": {...}}
    ]
  },
  "preconditions": [
    {"expr": "b >= 0", "error": "BountyErr", "description": "reserve must be >= 0"}
  ],
  "laws": [
    {"forall": ["a", "b"], "predicate": "index(task_create(a,b), 2) == 0",
     "description": "freshly created task is open"}
  ],
  "tests": [
    {"input": [7, 100], "output": [7, 100, 0, 0], "description": "basic create"},
    {"input": [1, -5], "output": null, "error": "BountyErr"}
  ]
}
```

## definition 表达式的语法

`body` 支持以下节点：
- 整数/字符串/布尔字面量
- 参数名引用（如 `"a"`、`"b"`）
- 嵌套调用：`{"op": "task_create", "args": [7, 100]}`
- 列表构造：`{"list": ["a", "b", 0, 0]}`
- 映射构造：`{"map": {"a": 1, "b": "x"}}`（Map<K,V> 字面量；键为字符串，值为表达式节点）
- 条件：`{"if": {"field": 2, "eq": 2}, "then": {...}, "else": {...}}`
- 内置函数调用：`{"fn": "index", "args": ["t", 2]}`、`{"fn": "min", "args": [...]}`、`{"fn": "fold_add", "args": [...]}`
- 类型扩展内置函数（整改项 4.7）：`str_len` / `str_concat` / `str_contains`（Str）、
  `time_now_epoch`（Time，固定种子）、`option_some` / `option_none`（Option<T>）、
  `map_get`（Map<K,V>）
- 预定义常量：`"$_"` 表示上一个操作的结果（用于 corpus 序列测试）

## 内置函数语义（definition 的 `{"fn": ...}` 节点）

| 函数 | 语义 |
|------|------|
| `index(coll, i)` | 取列表第 i 个元素；**越界抛 `ShapeError`**（见「类型守卫规范」）；非列表/非整数参数抛 `TypeError` |
| `min` / `max` | **重载**：单列表参数 → 取该列表的最值；多参数 → 取所有参数的最值（§SK：`max(0, fold_add(a))`） |
| `add` / `sub` | 整数加 / 左结合减 |
| `ge` / `lt` / `eq` 等 | 比较运算 |
| `fold_add(xs)` | 若 xs 是列表的列表 → 每行**最后一个元素**求和；否则普通求和；非列表抛 `TypeError` |
| `fold_credit(init, events)` | 契分折叠：初始 init；事件 `[kind, count]`：kind=0 → `+5×count`；kind=1 → 逐次 `×7//10`（向下取整）；结果下限 0 |
| `weighted_accept(xs)` / `weighted_support(xs)` | 对 `[reviewer, vote, weight]` 行，vote==1 的 weight 之和 |
| `weighted_reject(xs)` | vote==0 的 weight 之和 |
| `split_floor(contribs, reward)` | 按贡献分账：`share = floor(reward × c / total)`；total==0 抛 `DivByZero` |
| `enumerate_ledger(entries)` | 输入 `[[旧id, 金额, source], ...]` → 输出 `[[1, source, 金额], ...]`（编号 1..n）；source<1 抛 `NotTraceable`；金额<0 抛 `TypeError` |

## 类型守卫规范（v0.31 起固定）

跨工具实现必须使用以下**固定错误名**，不得泄漏原生异常：

1. **类型错误**：列表参数收到非列表（或 nat 参数收到非整数，如 `review_merge(3)`）→ 抛 `TypeError`（固定）；
2. **形状错误**：`index` 越界（索引超出列表长度）→ 抛 `ShapeError`（固定；与操作实参数目不符的 `ShapeError` 同族）；
3. 其余业务错误按各操作 `preconditions` 的 `error` 字段命名（如 `StateError` / `AuthError` / `DivByZero` 等），preconditions 的 `error` 必须与 tests 的 `error` 一致。

## preconditions 表达式的辅助函数

`preconditions[].expr` 是受限表达式串（无 `__builtins__`），除参数名外可用以下白名单辅助函数：
`index` / `min` / `max` / `len` / `abs` / `sum` / `sum_contribs` / `min_source_id`。
其中：
- `sum_contribs(c)`：c 的每行第 2 列（贡献）之和；
- `min_source_id(e)`：e 的每行第 3 列（source）最小值，空列表返回 +∞（不触发 NotTraceable）。

## 错误名约定

错误名必须与现有实现一致：`BountyErr` / `StateError` / `AuthError` / `TypeError` /
`ShapeError` / `QuotaExhausted` / `InsufficientEscrow` / `InsufficientPoints` /
`InsufficientStock` / `TeamFull` / `InsufficientFunds` / `UnknownAsset` /
`InsufficientShares` / `UnknownItem` / `DivByZero` / `NotTraceable` / `ReserveErr` /
`BidAmountErr` / `ClosedErr` / `TimeoutErr`。

错误名分工（v0.31 起固定，见「类型守卫规范」）：
- `TypeError` — 参数类型不符（期望列表收到非列表、期望整数收到非整数）；
- `ShapeError` — 形状类错误：`index` 越界、操作实参数目不符。

## 一致性要求

1. spec JSON 中每个操作的 `tests` 必须覆盖 spec Markdown 中该操作的全部 Tests 表格。
2. 每个操作至少 1 条 `laws`（与 Markdown 定律一一对应）。
3. `preconditions` 中的错误名必须与 `tests` 中的 `error` 一致。
4. 引擎实现（sigma_engine.py）不修改本 schema；若 schema 有缺陷，更新本文件并记录版本。
