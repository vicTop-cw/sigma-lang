---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 9f2a11add43fbf12a546606fb2b962ab_ba8d07568d7d11f196d8525400f8a581
    ReservedCode1: mDw4RkGQhmoXriChPW1y8uAeGLTUKR7LTtVVK6shiaXc2rZ3XsgXQEMKxkPer/PCdZcb5aucga996aYUlulURYZoOAQ7LrPIfXvtjpmHWTDG2xZ8OCOyXkCpRkO/TBYnsMyzEBGfCubT1uNVhrlJdRjXn3g8+eQxQmjHyG3hNkpBppdOWszZymfJUV0=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 9f2a11add43fbf12a546606fb2b962ab_ba8d07568d7d11f196d8525400f8a581
    ReservedCode2: mDw4RkGQhmoXriChPW1y8uAeGLTUKR7LTtVVK6shiaXc2rZ3XsgXQEMKxkPer/PCdZcb5aucga996aYUlulURYZoOAQ7LrPIfXvtjpmHWTDG2xZ8OCOyXkCpRkO/TBYnsMyzEBGfCubT1uNVhrlJdRjXn3g8+eQxQmjHyG3hNkpBppdOWszZymfJUV0=
---

# ΣLang — AI-Native Semantic Protocol

> **Sigma Language** — A deterministic semantic protocol for AI systems.
> One symbol, one meaning, one result — across all models.

> **Sigma Language（ΣLang）** — 面向 AI 系统的确定性语义协议。
> 一个符号，一种含义，一个结果 — 跨所有模型一致。

---

## What is ΣLang? / 什么是 ΣLang？

ΣLang is **not a programming language** in the traditional sense.
It is a **contract between intelligences**.

ΣLang 不是传统意义上的编程语言，而是**智能体之间的合约**。

- ✅ Deterministic semantics / 确定性语义
- ✅ Symbol-anchored meaning / 符号锚定的含义
- ✅ Markdown as source code / Markdown 即源码
- ✅ Ownership-aware dataflow / 所有权感知的数据流
- ✅ Zero syntactic ambiguity / 零语法歧义
- ✅ Verifier-enforced consistency / 验证器强制一致性

---

## Quick Start / 新人 30 分钟上手（v0.47）

ΣLang 用一句话介绍：**给 AI 立的"度量衡"协议——同一份规则文档，
Python / Rust / Elixir 三个独立验证器必须给出完全一样的结论。**

### 三域概览（协议已承载三个独立领域）

| 域 | 规范 | 语义 | 语料 |
|----|------|------|------|
| §SK 找茬业务（App 行为） | `spec/spec_p0_socketkit.md` | task_create / accept_task / task_submit / task_accept + 五大制度 + 增长期（核验师/督导/团机制/预支/可追溯） | `corpus/socketkit_ok.md` + `socketkit_growth_ok.md` |
| §PF 金融（投资组合） | `spec/spec_p0_portfolio.md` | portfolio_new / buy / sell / portfolio_value / risk_score | `corpus/portfolio_ok.md` |
| §IN 供应链（库存） | `spec/spec_p0_inventory.md` | inventory_new / receive_stock / ship_stock / stock_level / fill_rate | `corpus/inventory_ok.md` |

### 快速开始命令

```sh
python3 verify_consensus.py                  # 三端共识门禁（47/47 全绿）
python3 verify_p0.py                         # 算法正确性（109/109）
python3 tools/sigma-runtime.py --domains     # 三域审计故事线一次跑通（35/35）
python3 tools/sigma-prove.py corpus/socketkit_ok.md corpus/portfolio_ok.md corpus/inventory_ok.md  # z3 义务消解（53 项 PROVED）
python3 impl/python/sigma_app.py --smoke     # 找茬 MVP 参考后端 HTTP 冒烟（25/25）
```

### 验证清单（任何改动后必须全绿）

```sh
# 1. 三端共识（Law XIII 门禁）
python3 verify_consensus.py                    # 47/47
# 2. 三端 §SK 自检
cd impl/verifier && cargo run -q -- --sk-self-check      # 88/88
cd impl/elixir_rt && elixir sigma_verify.exs --sk-self-check  # 88/88
python3 impl/python/sigma_core.py              # 167/167
# 3. 三端编译
cd impl/verifier && cargo build                # 0 error / 0 warning
# 4. 证明与运行时
python3 tools/sigma-prove.py corpus/socketkit_ok.md corpus/portfolio_ok.md corpus/inventory_ok.md
python3 tools/sigma-runtime.py --domains       # 35/35
```

> 三端一致（Law XIII）是 ΣLang 的核心承诺：**一个符号、一种含义、一个结果——
> 谁来算都一样。**

---

## Architecture / 架构与数据流（v0.59）

ΣLang 的语义如何从规范一路走到共识门禁？全景如下：

```text
  spec/ 规范（英文为准 + spec/zh 中文参考）
   │  定义操作：指纹 / 签名 / 定律 / 测试（真实函数调用）
   ▼
  corpus/ 语料（51 个模块：ok 期望 PASS，break 期望 FAIL）
   │  三端验证器独立解析 + 求值（eval_expr 真实调用 §SK/§PF/§IN）
   ├──▶ Python verify_consensus.py ─┐
   ├──▶ Rust  impl/verifier        ├──▶ Law XIII 共识门禁（51/51 全绿）
   └──▶ Elixir impl/elixir_rt      ─┘
   │
   ├──▶ tools/sigma-prove.py     z3 义务消解（53 项 PROVED）
   ├──▶ tools/sigma-runtime.py   审计运行时（trace 59/59 + --domains 35/35）
   ├──▶ impl/python/sigma_app.py 找茬参考后端（自检 15/15 + 冒烟 36/36 + 持久化/审计）
   └──▶ tools/sigma-accept.py    一键验收（9 道门禁）→ GitHub Actions CI
```

**工具链职责**

| 工具 | 职责 | 结果 |
|------|------|------|
| `verify_consensus.py` | 三端验证器对 51 个语料模块独立判定（Python/Rust/Elixir/Expected） | 51/51 一致 |
| `verify_p0.py` | 算法正确性（含 §SK 语义检查） | 109/109 |
| `tools/sigma-prove.py` | 把语料定律编码为 z3 义务并消解 | 53 项 PROVED |
| `tools/sigma-runtime.py` | 审计运行时：逐事件复核定律（trace / --story / --growth / --inventory / --domains） | 59/59 + 35/35 |
| `impl/python/sigma_app.py` | 找茬 MVP 参考后端：业务全委托 §SK，App 只管状态 | 自检 15/15 + 冒烟 36/36 |
| `tools/sigma-accept.py` | 九道门禁一键验收（本地与 CI 同一条命令） | 9/9 |
| `.github/workflows/ci.yml` | push/PR 自动验收，全绿才算过 | CI 门禁 |

**一条语义的旅程**（以 §SK `task_create` 为例）：

1. `spec/spec_p0_socketkit.md` 定义指纹 `0xF001`、签名、定律与测试；
2. `corpus/socketkit_taskflow_ok.md` 把它写成**真实函数调用**测试；
3. Python / Rust / Elixir 三个独立验证器各自求值，结果必须逐项一致（Law XIII）；
4. `tools/sigma-prove.py` 把定律编码为 z3 义务，证明不可违反（P-01 结构 + 义务 PROVED）；
5. `tools/sigma-runtime.py` 在业务故事线里审计它的行为（input/output/定律复核）；
6. `impl/python/sigma_app.py` 的 `post_task` 直接委托它，并记录审计事件；
7. 任何改动后 `tools/sigma-accept.py` 九道门禁全绿，CI 放行。

> 整条链路的含义：**业务规则先以 ΣLang 语义存在并被证明，然后才是任何语言
> 的实现**——实现只是语义的投影。

---

## Status / 项目状态

| Module / 模块 | Tests / 测试 | Status / 状态 |
|---------------|-------------|---------------|
| §T Time & Causal Order / 时间与因果序 | 17/17 | ✅ |
| §E Error Algebra / 错误代数 | 16/16 | ✅ |
| §C Confidence & Probabilistic Logic / 置信度与概率逻辑 | 37/37 | ✅ |
| §I I/O Boundary & Effects / I/O 边界与效应 | 25/25 | ✅ |
| §SK SocketKit Protocol / SocketKit 协议 | 14/14 | ✅ |
| **Total / 总计** | **109/109** | **✅** |

Verifier Consensus / 验证器共识: **41/41** corpus modules agree across Python / Rust / Elixir verifiers.
41/41 语料库模块在 Python / Rust / Elixir 三个验证器上达成一致。

**v0.10 可用 (2026-08-02)**: 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）、基本操作（`index()`/`I₂`、元素级/矩阵运算）、常量包（§C `0xK0xx`/`0xQ0xx` 按指纹解析，Opaque 类不可遮蔽）已在三个验证器求值器全部实现并有语料覆盖；`sigma-prove` 义务消解 `PROVED (unsat)`，`sigma-moonbit` 生成 `.mbtp`；共识门禁 35/35 全绿。

**v0.11 可用 (2026-08-02)**: 包管理器 `tools/sigma-cli.py`（install/verify/list/search/fingerprint，`~/.sigma/registry.json` 注册表，Iron Law VII 无环依赖解析）+ 标准库 3 包（`std/math.base.md` / `std/data.transform.md` / `std/ai.confidence.md`，各配 `corpus/std_*_ok.md` 验证器测试集）；共识门禁 38/38 全绿、p0 95/95、三端 0 warning，v0.10 不回归。见 `MASTER_PLAN.md` Phase 3–4 与 `AUTOPILOT.md` §6。

**AI Bootstrapping Test (P2, 2026-08-02)**: `tools/sigma-bootstrap.py` — 一键闭环验证 spec→impl→verify→pass：4 个 P0 spec 均携带 `## Implementation Checklist (for AI)`、`impl/python/sigma_core.py` 自检 59/59、`verify_p0.py` 95/95。证明「新鲜 AI 只凭规范+验证器即可从零实现并通过验证」。见 `MASTER_PLAN.md` Phase 5。

**v0.12 Novel Spec Test (2026-08-02)**: `corpus/novel_gene_ok.md`（DNA 对齐语义）三端验证器一致（consensus 39/39），跑通 AI 读 spec → 写实现 → 验证 → 发布的完整闭环。见 `MASTER_PLAN.md` Phase 5.2。

**v0.13 SocketKit Protocol (2026-08-02)**: `spec/spec_p0_socketkit.md`（§SK：task_create / review_merge / contribution_score 的 ΣLang 语义）+ `corpus/socketkit_ok.md` 三端一致（consensus 40/40），走通 RFC → spec → 验证器 → 测试 晋升路径。见 `MASTER_PLAN.md` §6.2。

**v0.14 SocketKit Runtime (2026-08-03)**: §SK 参考实现进入 `impl/python/sigma_core.py`（自检 75/75）· 审计运行时 `tools/sigma-runtime.py`（业务 trace → ΣLang obligation 日志，10/10 满足）· `sigma-prove` 对 §SK 六条定律义务消解全部 `PROVED (unsat)` · 负例 `corpus/socketkit_break.md`（E-02，三端一致 FAIL）· §SK 行为测试进 `verify_p0.py`（109/109）；共识门禁 41/41 全绿、三端 0 warning，v0.10–v0.13 不回归。

**v0.15 三端 §SK 执行层 (2026-08-03)**: §SK 参考实现从 Python 单侧同步到 Rust（`impl/verifier/src/sk.rs` + `--sk-self-check`，16/16）与 Elixir（`sigma_verify.exs` §SK + `--sk-self-check`，16/16）——同一组 §SK 用例三端判定一致（Law XIII 业务语义层），`cargo build` 0 error/0 warning；consensus 41/41、p0 109/109 不回退，v0.10–v0.14 不回归。

**v0.16 SocketKit 语料执行化 (2026-08-03)**: 三端求值器（`verify_consensus.py` / `evaluator.rs` / `sigma_verify.exs`）的 eval_expr 直接支持 §SK 三操作真实调用（`task_create(a,b)` / `review_merge([...])` / `contribution_score([...])`，含 ⊥ BountyErr / TypeError / ShapeError 错误路径）；`corpus/socketkit_ok.md` 的 Tests 从规范表达式（⊕ ∈ ⊘）升级为真实调用——**Law XIII 共识门禁从此直接验证业务语义本身**，9/9 三端一致（consensus 41/41）、0 warning，v0.10–v0.15 不回归。

**v0.17 §SK 对齐真实业务 (2026-08-03)**: 依据找茬需求文档（`D:\Desktop\来找茬_需求文档.md` v1.0）校准 §SK——Task 扩展为 4 元组 `[author, bounty, status, hunter]` + 4 态状态机（待接单→进行中→待验收→已完成）；新增 `accept_task`（接单）/ `task_submit`（提交成果）/ `task_accept`（受茬人单人验收）/ `credit_score`（契分制：基础 100、完成 +5/单、违约 ×0.7）；`review_merge` 修正为增长期核验师场景。三端执行层同步（sigma_core 91/91、三端 §SK 自检 32/32、socketkit_ok 24/24 三端一致），sigma-prove 18 项 §SK 义务全部 PROVED (unsat)，sigma-runtime 完整 MVP 业务 trace 23/23；consensus 41/41、p0 109/109、三端 0 warning，v0.10–v0.16 不回归。

**v0.18 状态机不变量证明 (2026-08-03)**: `task_accept` 增加作者授权参数（只有受茬人本人 caller ≡ author 可验收，否则 ⊥ AuthError），spec 新增 §SK.3.8 不变量章节——**INV-1 状态单调**（状态只前进不后退）、**INV-2 终态不可变**（completed 不可再被任何状态操作改变）、**INV-3 守恒**（bounty 与 hunter 流转中不变）、**INV-4 作者授权**。三端执行层与 eval_expr 同步授权校验（sigma_core 92/92、三端 §SK 自检 33/33、socketkit_ok 25/25 三端一致），sigma-prove 新增 6 项不变量义务全部 `PROVED (unsat)`（§SK 共 23 项），sigma-runtime 审计 trace 增加不变量逐条复核（31/31）；consensus 41/41、p0 109/109、三端 0 warning，v0.10–v0.17 不回归。

**v0.19 第二个自举新域（金融 portfolio@1.0）(2026-08-03)**: 验证 ΣLang 协议泛化性——第二个全新领域（金融投资组合）走通 spec→三端→语料→证明 全流程：`spec/spec_p0_portfolio.md`（§PF：portfolio_new / buy / sell / portfolio_value / risk_score，单位价格 1 使总资产守恒可证）+ `corpus/portfolio_ok.md`（19/19 三端一致 PASS）与 `corpus/portfolio_break.md`（E-02 三端一致 FAIL）；三端 eval_expr 支持新域真实调用（sigma_core 111/111、0 warning）；sigma-prove 新增 10 项 §PF 义务全部 `PROVED (unsat)`（§SK+§PF 共 33 项）；sigma-runtime 审计 trace 增加 §PF 段（45/45）；consensus 43/43、p0 109/109，v0.10–v0.18 不回归。

**v0.20 找茬五大制度补齐 (2026-08-03)**: 依据找茬需求文档（`D:\Desktop\来找茬_需求文档.md` §四）把剩余三制度纳入 §SK——**SK.3.9 额度制**（`quota_new/quota_use/quota_reset`：月额/扣减/月底清零）、**SK.3.10 积分制**（`points_hold/points_release/points_withdraw`：托管冻结/释放/提现，⊥ InsufficientEscrow / InsufficientPoints）、**SK.3.11 勋章制**（`badge_level`：铜银金钻四级）。三端执行层与 eval_expr 同步（sigma_core 130/130、三端 §SK 自检 52/52、socketkit_ok 50/50 三端一致、0 warning），sigma-prove 新增 8 项三制度义务全部 `PROVED (unsat)`（共 41 项），sigma-runtime 审计 trace 增加三制度段（59/59）；consensus 43/43、p0 109/109，v0.10–v0.19 不回归。

**v0.21 找茬 MVP 全链路审计剧本 (2026-08-03)**: spec 新增 **§SK.6 MVP 业务剧本**——12 步端到端验收场景（开户额度→发布需求→扣减额度→赏金托管→接单→提交成果→验收确认→释放赏金→找茬人提现→契分奖励→贡献累计→勋章升级）；`sigma-runtime --story`（run_mvp_story）一次跑通完整业务故事线并逐事件复核不变量（INV-1 状态单调 / INV-3 守恒 / INV-4 作者授权 / 额度扣减 / 积分托管守恒），**18/18 义务满足**——作为 App 开工的「验收剧本」；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.20 不回归。

**v0.22 找茬 MVP 参考实现 (2026-08-03)**: `impl/python/sigma_app.py`（MVPApp）——找茬 MVP 真正"开工"的第一步：业务方法**全部委托** sigma_core §SK 语义（App 层只管状态、零业务规则重写），stdlib-only HTTP JSON API（`--serve` 暴露 `/post /claim /submit /accept /withdraw /badge`）；自检跑通 §SK.6 十二步剧本（**15/15**），步骤与 `sigma-runtime --story`（18/18）一一对应——被审计的验收剧本可直接实现为可运行后端；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.21 不回归。

**v0.23 MVP 端到端 HTTP 冒烟测试 (2026-08-03)**: `sigma_app.py` 增加 `/quota` 端点（开户额度，补全 HTTP 全链路）与 `--smoke` 模式（run_http_smoke：起服务→HTTP 七步全链路 `/quota → /post → /claim → /submit → /accept → /withdraw → /badge` → 逐响应断言 → 关服务，**13/13 通过**）——参考实现"作为 HTTP 服务的可用性"被可重复执行的冒烟测试固化；自检 15/15 不回归；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.22 不回归。

**v0.24 三端 §SK.6 story 一致性 (2026-08-03)**: §SK.6 MVP 业务剧本从 Python 单侧扩到三端——Rust `sk.rs story()` + `--sk-story`（**15/15**）、Elixir `sk_story()` + `--sk-story`（**15/15**），与 Python `sigma_app.py`（**15/15**）逐项一致：三把独立的尺子审计**同一条业务故事线**（开户→发单→扣额度→托管→接单→交成果→验收→释放→提现→加契分→加贡献→升勋章），Law XIII 在"产品层"收官；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.23 不回归。

**v0.25 Rust 参考实现 (2026-08-03)**: `impl/verifier/src/app.rs`（MVPApp 的 Rust 版，贴近生产部署）——业务方法**全部委托** sk.rs §SK 语义（App 层零业务规则重写），CLI 新增 `--app-self-check`（**15/15**）；与 Python `sigma_app.py`（15/15）、Rust `--sk-story`（15/15）、Elixir `--sk-story`（15/15）**四端逐项一致**——同一业务故事线在 Python 参考后端与 Rust 生产级实现上算出同一个答案；`cargo build` 0 error/0 warning；consensus 43/43、p0 109/109，v0.10–v0.24 不回归。

**v0.26 Rust HTTP 服务 + 冒烟对账 (2026-08-03)**: `app.rs` 增加 stdlib-only HTTP JSON API（手写 TcpListener + serde_json，`--app-serve`，端点 `/quota /post /claim /submit /accept /withdraw /badge` 与 Python `sigma_app.py --serve` 一致，业务全部委托 App 层 → §SK）+ `--app-smoke`（run_smoke：HTTP 七步全链路，**13/13**）——与 Python `sigma_app.py --smoke`（**13/13**）**双端逐项一致**，HTTP 层也同尺；`cargo build` 0 error/0 warning；consensus 43/43、p0 109/109，v0.10–v0.25 不回归。

### Two verification modes / 两种验证模式

ΣLang ships **two distinct verification tools** with different purposes:

| Tool / 工具 | Mode / 模式 | What it checks / 检查内容 |
|------------|------------|--------------------------|
| `verify_p0.py` | **Algorithm correctness** / 算法正确性 | 109 tests over §T/§E/§C/§I/§SK module *algorithms* (Lamport clocks, Result monad, confidence ops, I/O effects, SocketKit app behavior) — proves the P0 semantics are implementable. Does NOT parse `.md` specs. |
| `verify_consensus.py` | **Spec conformance** / 规范一致性 | Parses `.md` specs, applies Laws I–XVII + E-03/06/07/10 + §S/P-01 checks, and requires **41/41 corpus modules** to agree across Python / Rust / Elixir (Law XIII gate). |

> These are complementary, not redundant: `verify_p0.py` proves the **semantics** are sound;
> `verify_consensus.py` proves the **specs** conform and that independent implementations agree
> on the same verdict (one symbol, one meaning, one result — across all models).
> 两者互补而非冗余：前者证明语义可靠，后者证明规范合规且跨实现判定一致。

---

## Repository Structure / 目录结构

```
sigma-lang/
├── README.md                       # Project entry (this file) / 项目入口（本文件）
├── LICENSE                         # MIT
├── MASTER_PLAN.md                  # Development roadmap / 开发路线图
├── verify_p0.py                    # Algorithmic verification (109 tests) / 算法验证
├── verify_consensus.py             # Three-verifier consensus check / 三验证器共识检查
│
├── spec/                           # English specifications (normative) / 英文规范（规范性）
│   ├── spec_p0_foundations.md      # ⭐ Main P0 specification (整合版核心入口)
│   ├── spec_p0_time.md             # §T Full time & causality spec
│   ├── spec_p0_error.md            # §E Full error algebra spec
│   ├── spec_p0_confidence.md       # §C Full confidence & probability spec
│   ├── spec_p0_io.md               # §I Full I/O & effects spec
│   ├── spec_top_rules.md           # ⭐ Top-level rules: §S shadowing + §C constants + §G conflict
│   ├── spec_top_extensions.md      # Top-level rules: Law XIII–XVII + E-10 extensions
│   ├── spec_top_proofs.md          # Proof-carrying spec structure (P-01 enforced)
│   └── zh/                         # Chinese translations / 中文翻译
│       ├── spec_p0_foundations_zh.md
│       ├── spec_top_rules_zh.md
│       ├── spec_top_extensions_zh.md
│       └── spec_top_proofs_zh.md
│
├── archive/                        # Deprecated / superseded specs / 废弃/已替代的规范
│   ├── spec.md                     # v0.1 Initial Draft (superseded by spec_p0_foundations.md)
│   └── spec_p0_shadowing.md        # §S v0.2 (merged into spec_top_rules.md §S)
│
├── corpus/                         # Shared test corpus (38 modules) / 共享测试语料库
├── examples/                       # Usage examples / 使用示例
├── impl/                           # Verifier implementations / 验证器实现
│   ├── verifier/                   # Rust reference Verifier
│   ├── elixir_rt/                  # Elixir/BEAM verifier + runtime
│   └── python/                     # sigma_core.py — minimal reference core
├── tools/                          # Tooling (sigma-prove, etc.) / 工具
└── .github/workflows/              # CI: consensus gate
```

---

## Quick Navigation / 快速导航

### Getting Started / 入门

| Document / 文档 | Description / 说明 |
|----------------|-------------------|
| [spec_p0_foundations.md](spec/spec_p0_foundations.md) | **Main P0 specification** — start here. Covers all 17 Iron Laws, core types, package system, §T/§E/§C/§I modules, and Verifier architecture. / **P0 核心规范** — 从这里开始。涵盖全部 17 条铁律、核心类型、包系统、四大模块和验证器架构。 |

### Core Modules / 核心模块

| Document / 文档 | Module / 模块 | Tests / 测试 |
|----------------|---------------|-------------|
| [spec_p0_time.md](spec/spec_p0_time.md) | §T Time & Causal Order / 时间与因果序 | 17/17 |
| [spec_p0_error.md](spec/spec_p0_error.md) | §E Error Algebra / 错误代数 | 16/16 |
| [spec_p0_confidence.md](spec/spec_p0_confidence.md) | §C Confidence & Probabilistic Logic / 置信度与概率逻辑 | 37/37 |
| [spec_p0_io.md](spec/spec_p0_io.md) | §I I/O Boundary & Effects / I/O 边界与效应 | 25/25 |

### Top-Level Governance / 顶层治理

| Document / 文档 | Content / 内容 |
|----------------|---------------|
| [spec_top_rules.md](spec/spec_top_rules.md) | §S Shadowing & Binding Discipline, §C Real-World Constants, §G Conflict Adjudication, Rule Index / §S 遮蔽与绑定纪律、§C 现实常量、§G 冲突裁决、规则索引 |
| [spec_top_extensions.md](spec/spec_top_extensions.md) | Laws XIII–XVII (Verifier Consensus, Negative Tests, Export Completeness, Compatibility Proof, Probabilistic Guarantee) + Law VIII-ext E-10 (Eval Determinism) + E-08 S-01 Level 1 (package signature) + E-08 Strategy Bundle candidate / Law XIII–XVII 扩展 + E-10 评估确定性 + E-08 S-01 Level 1 包签名 + E-08 策略包候选 |
| [spec_pki_feasibility.md](spec/spec_pki_feasibility.md) | E-08 S-01 PKI Feasibility Study (Trust & Provenance: signatures, author identity, anti-poisoning) / 信任与溯源 PKI 可行性研究 |
| [spec_top_proofs.md](spec/spec_top_proofs.md) | Proof-Carrying Spec Structure (P-01 enforced) / 证明携带规范结构（P-01 已强制执行） |

### Chinese Translations / 中文翻译

| Document / 文档 | Original / 原文 |
|----------------|-----------------|
| [spec_p0_foundations_zh.md](spec/zh/spec_p0_foundations_zh.md) | spec_p0_foundations.md |
| [spec_top_rules_zh.md](spec/zh/spec_top_rules_zh.md) | spec_top_rules.md |
| [spec_top_extensions_zh.md](spec/zh/spec_top_extensions_zh.md) | spec_top_extensions.md |
| [spec_top_proofs_zh.md](spec/zh/spec_top_proofs_zh.md) | spec_top_proofs.md |

> **Note**: `spec/` contains the authoritative English originals. `spec/zh/` contains Chinese translations for reference. In case of discrepancy, the English version prevails.
> **注意**: `spec/` 目录为权威英文原版。`spec/zh/` 为中文参考翻译。如有出入，以英文原版为准。

---

## Quick Start / 快速开始

### Run the verifier / 运行验证器

```bash
python3 verify_p0.py
```

Expected output / 预期输出:
```
⏰ MODULE T: 17/17 passed
⚠️  MODULE E: 16/16 passed
🎲 MODULE C: 37/37 passed
🔌 MODULE I: 25/25 passed
📋 MODULE SK: 14/14 passed

  🎯 TOTAL: 109/109 tests passed
  🏆 ALL P0 FOUNDATIONS VERIFIED — ΣLang is sound!
```

### Read the spec / 阅读规范

Start with `spec/spec_p0_foundations.md` — it ties all four P0 modules together.

从 `spec/spec_p0_foundations.md` 开始 — 它聚合了全部四个 P0 模块。

---

## Design Philosophy / 设计理念

### Three-Layer Architecture / 三层架构

```
L0 — Core (core@1.0)        ← immutable, always loaded / 不可变，始终加载
     ℕ ℤ ℚ ℝ ℂ 𝔹 Sym Prop λ ∀ ∃
     + Iron Laws + Verifier interface

L1 — Standard Library          ← community maintained, versioned / 社区维护，版本化
     math.calculus / math.linear / finance.base
     signal.fourier / stat.prob / opt.gradient

L2 — User Packages            ← anyone can publish / 任何人可发布
     emoji.finance / tcm.wuzang / physics.qft
     must pass Verifier Iron Laws / 必须通过验证器铁律
```

### The 17 Iron Laws / 十七条铁律

```
Law I    — Fingerprint Uniqueness / 指纹唯一性
Law II   — Encoding to ℕ (everything → number) / 编码到 ℕ
Law III  — Law Declaration (every op has laws) / 定律声明
Law IV   — Test Mandatory (≥1 canonical test per op) / 测试强制
Law V    — No Implementation in Spec / 规范中无实现
Law VI   — Backward Compatibility (published = frozen) / 向后兼容
Law VII  — Explicit Dependencies (no circular deps) / 显式依赖
Law VIII — Temporal Determinism (timing bounds declared) / 时序确定性
Law IX   — Calibration Requirement (confidence matches accuracy) / 校准要求
Law X    — Effect Transparency (all effects declared) / 效应透明
Law XI   — Capability Discipline (FFI needs explicit caps) / 能力纪律
Law XII  — Resource Linearity (open = closed exactly once) / 资源线性
Law XIII — Verifier Consensus / 验证器共识
Law XIV  — Negative Test Mandatory / 负向测试强制
Law XV   — Export Completeness / 导出完整性
Law XVI  — Compatibility Proof / 兼容性证明
Law XVII — Probabilistic Guarantee / 概率保证
```

Laws I–XII are defined in `spec/spec_p0_foundations.md` §0. Laws XIII–XVII plus the Law VIII
extension E-10 (Evaluation Determinism) are promoted extensions defined in
`spec/spec_top_extensions.md`, enforced by all three verifiers (Python / Rust / Elixir).

Law I–XII 定义于 `spec/spec_p0_foundations.md` §0。Law XIII–XVII 及 Law VIII 扩展 E-10（评估确定性）为已推广的扩展，定义于 `spec/spec_top_extensions.md`，由全部三个验证器强制执行。

---

## Why ΣLang? / 为什么需要 ΣLang？

### The Problem / 问题

Today, when you give the same Markdown document to different AIs:
- GPT-4 interprets it one way
- Claude interprets it another way
- Gemini interprets it a third way

**Same input, different outputs. This is unacceptable for production AI systems.**

如今，把同一份 Markdown 文档交给不同的 AI：
- GPT-4 按一种方式解读
- Claude 按另一种方式解读
- Gemini 按第三种方式解读

**同样的输入，不同的输出。这对生产级 AI 系统来说是不可接受的。**

### The Solution / 解决方案

ΣLang replaces ambiguous natural language with **mathematically anchored symbols**:

ΣLang 用**数学锚定的符号**替换歧义的自然语言：

| Traditional / 传统 | ΣLang |
|--------------------|--------|
| "add the numbers" / "把数字加起来" | `a ⊕ b` with associativity law / 带结合律 |
| "if score >= 90" / "如果分数 >= 90" | `grade(s) ≝ if s<60 then 𝗀𝖣 else…` + boundary tests / 边界测试 |
| "probably true" / "大概是真的" | `⊢_0.73 P` with calibration law / 带校准律 |
| "send message" / "发送消息" | `send(addr, msg)` with causal ordering / 带因果序 |

---

## Deprecated & Archived / 废弃与归档

The following files have been moved to `archive/` as they are superseded by newer specifications:

以下文件已被移至 `archive/` 目录，因为它们已被更新的规范所取代：

| File / 文件 | Reason / 原因 |
|------------|---------------|
| `archive/spec.md` | v0.1 Initial Draft — superseded by `spec/spec_p0_foundations.md` (v0.3.0). The v0.1 spec uses an older chapter-based structure (chapters 1–17) and lacks the §T/§E/§C/§I modular architecture, promoted Laws XIII–XVII, and three-verifier consensus enforcement. / v0.1 初稿 — 已被 `spec/spec_p0_foundations.md` (v0.3.0) 取代。v0.1 使用旧的章节目录结构（第 1–17 章），缺少 §T/§E/§C/§I 模块化架构、Law XIII–XVII 推广和三验证器共识。 |
| `archive/spec_p0_shadowing.md` | §S Shadowing v0.2 — explicitly marked SUPERSEDED. Content merged into `spec/spec_top_rules.md` §S on 2026-08-01. / §S 遮蔽 v0.2 — 明确标记为 SUPERSEDED。内容已于 2026-08-01 合并到 `spec/spec_top_rules.md` §S。 |

---

## Version / 版本

- **Milestone / 里程碑**: **v0.64 三域 story 不变量检查段 (2026-08-04)** — --domains 41/41 含不变量复核 · **v0.63 找茬跨操作不变量 (2026-08-04)** — INV-SK 赏金守恒/不超提 PROVED · **v0.62 金融跨操作不变量 (2026-08-04)** — INV-PF 现金/份额守恒 PROVED · **v0.61 供应链跨操作不变量 (2026-08-04)** — INV-IN 总量守恒/非负链 PROVED · **v0.60 协议版本化 (2026-08-04)** — spec 0.4.0 + RFC 记录 · **v0.59 README 架构数据流全景 (2026-08-04)** — 架构数据流全景章节 · **v0.58 spec 中英对照补全 (2026-08-04)** — §IN 供应链中文参考版 · **v0.57 语料扩容 (2026-08-04)** — 语料按主题拆三模块，consensus 51/51 · **v0.56 一键验收接 CI (2026-08-04)** — Makefile + GitHub Actions · **v0.55 找茬 App 审计日志 (2026-08-04)** — `--audit-log` 可对账审计追踪 · **v0.54 找茬 App HTTP 错误码语义化 (2026-08-04)** — §SK/§IN 错误 → 语义化 4xx · **v0.53 找茬 App 查询端点 (2026-08-04)** — /tasks /users 任务与用户列表 · **v0.52 找茬 App 用户会话层 (2026-08-04)** — /register /me 用户态隔离 · **v0.51 找茬 App 状态持久化 (2026-08-04)** — `--state` JSON 重启不丢 · **v0.50 里程碑达成 (2026-08-03)** — v0.27–v0.50 连续推进收官 · **v0.49 收官验收续 (2026-08-03)** — `sigma-accept.py` 9 道门禁一键验收 · **v0.48 一键收官验收 (2026-08-03)** — `sigma-accept.py` 六道门禁一键跑通 · **v0.47 README 新人上手 (2026-08-03)** — 三域概览 + 快速开始 + 验证清单 · **v0.46 三域协议巩固 (2026-08-03)** — `--domains` 35/35 · **v0.45 供应链 app 参考实现 (2026-08-03)** — §IN HTTP 端点 + 冒烟 25/25 · **v0.44 三端供应链 story 对账 (2026-08-03)** — 供应链故事线三端 6/6 逐项一致 · **v0.43 供应链证明 + runtime (2026-08-03)** — §IN 义务 PROVED + --inventory 6/6 · **v0.42 供应链语料 + 共识 (2026-08-03)** — inventory 语料进共识门禁，47/47 · **v0.41 三端供应链执行层 (2026-08-03)** — §IN 五操作三端实现 · **v0.40 第三个自举新域（供应链 inventory@1.0）(2026-08-03)** — §IN 供应链语义，泛化性三验 · **v0.39 完整业务验收剧本 (2026-08-03)** — `sigma-runtime --all` 29/29 · **v0.38 Rust app 增长期端点 + 冒烟对账 (2026-08-03)** — 增长期 HTTP 双端 20/20 逐项一致 · **v0.37 Python app 增长期端点 (2026-08-03)** — 增长期 HTTP 端点 + 冒烟 20/20 · **v0.36 三端增长期 story 对账 (2026-08-03)** — 增长期故事线三端 11/11 逐项一致 · **v0.35 增长期审计故事线 (2026-08-03)** — `sigma-runtime --growth` 11/11 · **v0.34 增长期义务证明 (2026-08-03)** — sigma-prove 增长期 7 项义务 PROVED · **v0.33 增长期语料模块化 (2026-08-03)** — socketkit_growth 独立语料，consensus 45/45 · **v0.32 增长期语义⑥积分可追溯 (2026-08-03)** — `points_ledger` 积分来源可追溯 · **v0.31 增长期语义⑤额度预支 (2026-08-03)** — `quota_advance` 预支下月额度 · **v0.30 增长期语义④团收益 (2026-08-03)** — `team_share` 团内收益按贡献分配 · **v0.29 增长期语义③团机制 (2026-08-03)** — `team_create/team_join` 受茬团/找茬团 · **v0.28 增长期语义②督导 (2026-08-03)** — `dispute_review` 督导处理纠纷 · **v0.27 增长期语义①核验师 (2026-08-03)** — `badge_issue` 核验师签发勋章 · **v0.26 Rust HTTP 服务 + 冒烟对账 (2026-08-03)** — HTTP 层 Python/Rust 双端同尺 · **v0.25 Rust 参考实现 (2026-08-03)** — `app.rs` 生产级后端，四端 story 逐项一致 · **v0.24 三端 §SK.6 story 一致性 (2026-08-03)** — 业务故事线 Python/Rust/Elixir 三端逐项一致 · **v0.23 MVP 端到端 HTTP 冒烟测试 (2026-08-03)** — `sigma_app --smoke` HTTP 七步全链路可重复验收 · **v0.22 找茬 MVP 参考实现 (2026-08-03)** — `sigma_app.py` 可运行后端，业务全委托 §SK 语义 · **v0.21 找茬 MVP 全链路审计剧本 (2026-08-03)** — §SK.6 十二步业务故事线 + `sigma-runtime --story`，App 开工验收剧本 · **v0.20 找茬五大制度补齐 (2026-08-03)** — 额度制/积分制/勋章制进 ΣLang，业务规则链完整可证明 · **v0.19 第二个自举新域（金融 portfolio@1.0）(2026-08-03)** — 协议泛化性再验证，consensus 43/43 · **v0.18 状态机不变量证明 (2026-08-03)** — 作者授权 + 4 项状态机不变量 z3 可证明 · **v0.17 §SK 对齐真实业务 (2026-08-03)** — Task 4 态状态机 + 契分制，MVP 全流程三端一致可执行可证明 · **v0.16 SocketKit 语料执行化 (2026-08-03)** — 业务语义进入 Law XIII 共识门禁 · **v0.15 三端 §SK 执行层 (2026-08-03)** — §SK 业务语义 Python/Rust/Elixir 三端一致可执行 · **v0.14 SocketKit Runtime (2026-08-03)** — §SK 参考实现 + 审计运行时 + z3 证明闭环，共识门禁 41/41 全绿 · **v0.13 SocketKit Protocol (2026-08-02)** — §SK 语义定义，共识门禁 40/40 全绿 · **v0.12 Novel Spec Test (2026-08-02)** — 新域自举闭环 · **v0.11 可用 (2026-08-02)** — 包管理器 `sigma-cli.py` + 标准库 3 包，共识门禁 38/38 全绿 · **v0.10 可用 (2026-08-02)** — 数学符号 / 基本操作 / 常量包可用，证明可消解，共识门禁 35/35 全绿
- **Spec Version / 规范版本**: 0.4.0
- **Date / 日期**: 2026-08-04
- **License / 许可证**: MIT

## Citation / 引用

```
ΣLang: An AI-Native Semantic Protocol
Version 0.4.0
https://github.com/sigma-lang/sigma-lang
```
*（内容由AI生成，仅供参考）*
