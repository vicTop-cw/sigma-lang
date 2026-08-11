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
  "types": [TypeDecl...],
  "operations": [OperationDecl...]
}
```

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

## 错误名约定

错误名必须与现有实现一致：`BountyErr` / `StateError` / `AuthError` / `TypeError` /
`ShapeError` / `QuotaExhausted` / `InsufficientEscrow` / `InsufficientPoints` /
`InsufficientStock` / `TeamFull` / `InsufficientFunds` / `UnknownAsset` /
`InsufficientShares` / `UnknownItem` / `DivByZero` / `NotTraceable` / `ReserveErr` /
`BidAmountErr` / `ClosedErr` / `TimeoutErr`。

## 一致性要求

1. spec JSON 中每个操作的 `tests` 必须覆盖 spec Markdown 中该操作的全部 Tests 表格。
2. 每个操作至少 1 条 `laws`（与 Markdown 定律一一对应）。
3. `preconditions` 中的错误名必须与 `tests` 中的 `error` 一致。
4. 引擎实现（sigma_engine.py）不修改本 schema；若 schema 有缺陷，更新本文件并记录版本。
