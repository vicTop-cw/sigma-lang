# ΣLang Spec 编写模板与最佳实践 v1.0

> 配套：`spec/json-schema.md`（机器格式）· `spec/spec_p0_*.md`（人类格式）
> 原则：**先消除歧义，再写规则**——spec 里没写出来的东西等于不存在。

---

## 一、什么时候用 ΣLang 写规范

**适合**：

- 多个 AI / 多个团队 / 多种语言需要执行完全一致的业务规则
- 规则有明确的状态机、前置条件、可枚举的错误
- 规则的结果可以被"输入 → 输出"或"输入 → 错误"精确判定

**不适合**：

- 需要人类主观判断的规则（"内容质量好不好"）
- 结果开放（"任意一条可行路径"）
- 规则经常变的探索期——每个操作都要过门禁，改动成本高

---

## 二、模板（Markdown 版）

每份 spec 按以下骨架编写：

```markdown
# §XX — <Domain> Protocol

> **Status**: P0 — <promoted via RFC → spec section → verifier check → tests>
> **Depends**: core@1.0, error@1.0, math.base@1.0
> **Fingerprint prefix**: `0xF000`–`0xF0FF`
> **Motivation**: <为什么需要这个协议，解决的业务问题>

## XX.1 Core Types

<类型表：名称、定义、含义。所有非数值概念必须给出 ℕ 编码（Law II）>

## XX.2 Operations

### XX.2.1 op_name — <操作名>

```md
op_name : <签名>
Fingerprint: 0xF001
Definition: <形式化定义>
```

**Laws**

```md
∀ ... . <定律 1>
∀ ... . <定律 2>
```

**Tests**

| Input | Output |
|-------|--------|
| op_name(1, 2) | <期望输出> |
| op_name(-1, 2) | ⊥ <错误名> |

### XX.2.2 ...

## XX.3 Design Decisions

<记录所有有意为之的决策与"规范留白"——不同实现者可能做出不同选择的地方>

## XX.4 Composite Scenario

<完整业务生命周期场景，多操作串联，写清每步期望>
```

---

## 三、模板（JSON 版）

按 `spec/json-schema.md` 编写同名 JSON。转换规则：

| Markdown 元素 | JSON 字段 |
|---------------|-----------|
| 类型定义 | `types[]`（alias/list/enum/option/map） |
| 操作签名 | `operations[].signature` |
| Fingerprint | `operations[].fingerprint` |
| Definition | `operations[].definition`（lambda/table/expression） |
| 前置条件 | `operations[].preconditions[]`（expr + error + description） |
| Laws | `operations[].laws[]`（forall + predicate + description） |
| Tests | `operations[].tests[]`（input/output 或 input/error） |

---

## 四、编写最佳实践（从错误中学到的）

### 4.1 消除歧义：填空检查表

写完后逐条自查，**没有写 = 不存在**：

- [ ] 每个操作在哪些状态下合法？其他状态调用返回什么？
- [ ] 每个操作的调用者（caller）是谁？权限约束写了吗？
- [ ] 边界值：0、负数、最大值——哪些合法哪些报错？报什么错？
- [ ] 集合/列表操作的顺序语义：插入顺序、去重规则、排序规则？
- [ ] 平局怎么办？（两个相同出价、两个相同时间戳）
- [ ] 幂等性：重复调用同一操作是返回相同结果还是报错？
- [ ] 空输入：空列表、空字符串、null——每个操作都定义了吗？
- [ ] 同一实体多次操作（同人多次出价、同一任务重复提交）规则是什么？

### 4.2 测试覆盖规则

- 每个操作至少 3 条测试：正常路径 + 边界值 + 错误路径
- 每个错误分支至少 1 条测试
- 组合场景（多操作串联）至少 1 条
- **测试样例本身就是语义的一部分**——样例隐含的顺序/格式约定会被实现者反推，因此样例必须与定义严格一致

### 4.3 错误命名

错误名保持稳定、全局唯一，与已有实现一致。新增错误类型时先查现有清单（见 json-schema.md §错误名约定），避免语义重复。

### 4.4 定律写作

- 每条定律必须是可判定的谓词（能对任意合法输入求真/假）
- 定律不要重复定义（定义已表达的约束不需要再写定律）
- 每条定律配 `description` 说明业务含义——这是给人看的，不是给机器看的

---

## 五、验收前检查清单

- [ ] Markdown 与 JSON 语义等价（tests 一一对应）
- [ ] `python3 impl/python/sigma_engine.py` 能消费该 spec 的 JSON 并全部求值通过
- [ ] 三端共识门禁通过（若该域有三端实现）
- [ ] 无歧义自查表全勾
