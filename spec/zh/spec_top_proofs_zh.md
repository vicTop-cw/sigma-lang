---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 9f2a11add43fbf12a546606fb2b962ab_bf553daa8d7d11f196d8525400f8a581
    ReservedCode1: 9auoNRJJaHbdykodrFHME7o4h36/xhSmc+3sOAI402N+Gw3oCvDvf/TqDSvAwSlEBfeuIcgUySIJodiqdT1K+Rhk6eg04SFqf5a82rvp+6qP7kmClF4VmOWFWZakuWj/LYJ5mdhgbXPvh9cl/UPncpVP93rnx4+bhD48T89OiMeq0lH7ccDPR8XqX9Y=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 9f2a11add43fbf12a546606fb2b962ab_bf553daa8d7d11f196d8525400f8a581
    ReservedCode2: 9auoNRJJaHbdykodrFHME7o4h36/xhSmc+3sOAI402N+Gw3oCvDvf/TqDSvAwSlEBfeuIcgUySIJodiqdT1K+Rhk6eg04SFqf5a82rvp+6qP7kmClF4VmOWFWZakuWj/LYJ5mdhgbXPvh9cl/UPncpVP93rnx4+bhD48T89OiMeq0lH7ccDPR8XqX9Y=
---

# ΣLang 证明携带规范 — 形式化验证

> **状态**: 部分规范 — P-01（证明结构检查）由全部三个验证器**强制执行**（2026-08-01）；
> SMT 消解后端已落地：`sigma-prove.py`（z3）+ `sigma-moonbit.py`（MoonBit 翻译桥，2026-08-01）。
> **来源**: 改编自 MoonBit 的形式化验证设计
> （`moon prove` + `.mbt`/`.mbtp` 分离，docs.moonbitlang.cn/language/verification.html）。
> **关系**: 以**证明式编写约定**扩展 Law XIII–XVI
> （P-01 结构检查是 Verifier 合约的一部分）；不改变语料库合约。

---

## P.1 为什么 ΣLang 需要形式化验证

ΣLang 的铁律和规范测试提供**基于测试的**语义（元规则 4：Equality by Test）。
测试在*采样*输入上证明行为。形式化验证在*所有*声明形状的输入上证明行为——
弥合"95 个测试通过"与"定律对所有规范允许的输入成立"之间的差距。

MoonBit 在通用语言中展示了可行的形态：
- 可执行代码（`.mbt`）与逻辑谓词和引理（`.mbtp`）分离
- 命名谓词（`model`、`*_inv`、`*_pre`、`*_post`）而非内联公式
- 合约（`proof_require` / `proof_ensure`）、循环不变量（`proof_invariant`）、
  局部事实（`proof_assert`）以及显式信任边界（`proof_axiomatized`）
- 义务由 SMT 支持的证明器消解（`moon prove`）

ΣLang 适配此方案：**规范即证明界面**，验证器同时裁判测试和证明块。

---

## P.2 方法映射（MoonBit → ΣLang）

| MoonBit 概念 | ΣLang 等价 | 作用 |
|-------------|-----------|------|
| `.mbt`（可执行） | 规范模块操作 + 测试 | 程序侧 |
| `.mbtp`（谓词/引理） | `## Proof` 节（定律、不变量、模型） | 逻辑侧 |
| `model(x)` 抽象 | `## Model` 块：值的语义视图 | 桥接具体→抽象 |
| `*_inv` 表示不变量 | `## Invariant` 块 | 状态的良构性 |
| `proof_require`（前置条件） | 操作上的 `## Pre` 块 | 入口必须满足的条件 |
| `proof_ensure`（后置条件） | 操作上的 `## Post` 块 | 出口必须满足的条件 |
| `proof_assert`（局部事实） | 规范测试行 | 步骤的具体见证 |
| `proof_invariant`（循环） | 有状态操作的 `## Invariant` 块 | 归纳假设 |
| `proof_axiomatized`（信任桥） | `## Trusted` 块 | 显式的、狭窄的信任边界 |
| `moon prove`（SMT 消解） | `sigma-prove.py`（z3 后端）+ `sigma-moonbit.py`（翻译桥，2026-08-01） | 消解义务 — 同一 `## Proof` 的双独立后端 |
| `moon check`（类型/解析） | Verifier 铁律 | 结构门 |
| `moon test`（运行时） | 规范测试执行 | 行为门 |

---

## P.3 证明携带规范结构

携带证明的模块声明 `## Proof` 节：

```md
# Module: balance@1.0
# Version: 1.0.0

## Proof

### Model
balance(m) : Fmap[CoinId, ℤ]
  # 具体账本的抽象语义视图

### Invariant
ledger_inv(l) : 𝔹
  # 形状：每项余额为正
  ∀ c . c ∈ keys(l) ⇒ balance(c) > 0

### Operation: deposit
# Pre:  amount > 0
# Post: balance' = balance ⊕ {coin ↦ balance(coin) + amount}
#       ledger_inv(l')

### Trusted
init_ledger : Unit → Ledger
  # proof_axiomatized — 在验证核心之外构造
```

规则：

1. **两层、窄桥** — `## Proof` 块是逻辑侧；操作 + 测试是程序侧。二者仅通过 `## Model` 中的命名谓词连接。
2. **命名谓词优于内联公式** — 每个合约引用命名谓词（`ledger_inv`、`deposit_post`），绝不使用原始布尔块。
3. **小而稳定的不变量** — `*_inv` 描述形状/边界/良构性；语义等式放在 `## Post` 块中，不放在不变量内部。
4. **每个与证明相关的有状态操作都声明 `Pre` 和 `Post`。**
5. **信任是显式且临时的** — `## Trusted` 块是带有具体前置条件的窄桥；从构造函数向外收缩，而非设计的终点。
6. **测试仍然强制**（Law IV、XIV）— 证明块不取代测试，而是泛化测试。

---

## P.4 验证义务（`sigma-prove` 将检查的内容）

将 `moon prove` 的义务映射到规范：

| # | 义务 | ΣLang 形式 |
|---|-----|-----------|
| 1 | 前置条件足以安全执行 | 每个 `## Pre` 蕴含操作签名约束 |
| 2 | 后置条件在每个返回路径上成立 | 每个 `## Post` 从操作的定律推导 |
| 3 | 局部事实有效 | 每个测试行是定律的有效实例 |
| 4 | 不变量被建立和维持 | `## Invariant` 初始成立且每次操作后保持 |
| 5 | 终止度量递减 | 为递归/有状态操作声明 |
| 6 | 边界/安全性被消解 | `Model`/`Invariant` 蕴含索引/范围安全性 |

尚未实现：`sigma-prove` SMT 后端属于**未来工作**（P.6）。方法论现已采纳，以便规范按证明就绪方式编写。

---

## P.5 推荐风格与反模式

### 风格

- 首选 `model(...)` 作为语义视图的默认名称。
- 统一使用 `*_inv`、`*_pre`、`*_post` 后缀。
- 在泛化之前，从简单的验证切片（单态）开始。
- 仅在看到具体失败义务**之后**添加辅助引理。
- 保持信任表显式且最小。

### 反模式

- ❌ 在每个合约中重复大量内联公式
- ❌ 将整个语义放入不变量中
- ❌ 在没有失败 VC 证明其必要性时添加大量辅助引理
- ❌ 仅将语义定理存储在 `## Trusted` 块内
- ❌ 在单步中同时更改抽象模型和求解器引导

---

## P.6 采纳路径

1. **RFC** — 批准 `## Proof` 块语法和命名约定。
2. **Verifier 支持** — 扩展全部三个验证器以解析 `## Proof` 块
   （结构：有状态操作必须有 `Model`/`Invariant`/`Pre`/`Post`）。
3. **语料库** — 添加带有 `# Expected:` 判决的证明式模块；要求三验证器一致（Law XIII 门）。
4. **SMT 后端** — `tools/sigma-prove.py`（2026-08-01）：将 Pre/Post 合约降低为
   SMT-LIB2 义务（ℕ→Int, ⊕→+, ⊗→*, ⊖→-）；当 z3 可用时消解，
   否则优雅降级为"义务已生成（未验证）"。

采纳标准：

- [ ] `## Proof` 语法的 RFC（P.3）
- [x] Verifier 解析 `## Proof` 块（全部三个实现）— `check_proof_structure` / P-01
- [x] ≥2 个证明式语料库模块，三验证器一致（proof_ok PASS, proof_break FAIL; 15/15 一致）
- [x] SMT 消解路径已实现（`tools/sigma-prove.py`；完整消解需要 z3）

### sigma-prove（SMT 后端，2026-08-01）

`python3 tools/sigma-prove.py [module.md]` 对每个模块执行：

1. **P-01 结构检查**（复用 `verify_consensus.check_python`）：`## Proof` 必须有
   Model + Invariant；操作必须配对 Pre/Post。
2. **义务生成**：对每个带有 `# Pre:`/`# Post:` + 算术字形的操作，
   发出 SMT-LIB2 查询，断言操作数 ∈ ℕ、Pre 以及 Post 的否定
   （`result` 被操作语义替换）。`check-sat` = unsat ⇒ Post 从 Pre 消解。
3. **消解**：z3 Python API，然后 z3 CLI；PATH 上无求解器时，义务写入
   `tools/_sigma_prove_out/` 并报告未验证。

退出码：0 = 结构 OK（且存在求解器时义务已消解）；1 = 结构失败或义务被证伪。
已在 `proof_ok.md`（义务生成，P-01 OK，exit 0）和 `proof_break.md`
（MissingModel + IncompleteContract，exit 1）上验证。

### P-01 推广记录（2026-08-01）

P-01（证明携带规范结构）现由全部三个验证器强制执行。声明 `## Proof` 的模块必须有
`### Model` 和 `### Invariant`；每个操作必须声明 `# Pre:` 和 `# Post:`（同时出现或都不出现）。
违规：`MissingModel`、`MissingInvariant`、`IncompleteContract`。

语料库：`proof_ok.md`（PASS）和 `proof_break.md`（FAIL — 缺少 Model + 合约不完整）。
完整运行：**15/15 模块一致（Python == Rust == Elixir == Expected）**。

---

*ΣLang 证明携带规范结束 — v0.2（P-01 于 2026-08-01 强制执行）*
*（内容由AI生成，仅供参考）*
