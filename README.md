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

## Status / 项目状态

| Module / 模块 | Tests / 测试 | Status / 状态 |
|---------------|-------------|---------------|
| §T Time & Causal Order / 时间与因果序 | 17/17 | ✅ |
| §E Error Algebra / 错误代数 | 16/16 | ✅ |
| §C Confidence & Probabilistic Logic / 置信度与概率逻辑 | 37/37 | ✅ |
| §I I/O Boundary & Effects / I/O 边界与效应 | 25/25 | ✅ |
| **Total / 总计** | **95/95** | **✅** |

Verifier Consensus / 验证器共识: **38/38** corpus modules agree across Python / Rust / Elixir verifiers.
38/38 语料库模块在 Python / Rust / Elixir 三个验证器上达成一致。

**v0.10 可用 (2026-08-02)**: 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）、基本操作（`index()`/`I₂`、元素级/矩阵运算）、常量包（§C `0xK0xx`/`0xQ0xx` 按指纹解析，Opaque 类不可遮蔽）已在三个验证器求值器全部实现并有语料覆盖；`sigma-prove` 义务消解 `PROVED (unsat)`，`sigma-moonbit` 生成 `.mbtp`；共识门禁 35/35 全绿。

**v0.11 可用 (2026-08-02)**: 包管理器 `tools/sigma-cli.py`（install/verify/list/search/fingerprint，`~/.sigma/registry.json` 注册表，Iron Law VII 无环依赖解析）+ 标准库 3 包（`std/math.base.md` / `std/data.transform.md` / `std/ai.confidence.md`，各配 `corpus/std_*_ok.md` 验证器测试集）；共识门禁 38/38 全绿、p0 95/95、三端 0 warning，v0.10 不回归。见 `MASTER_PLAN.md` Phase 3–4 与 `AUTOPILOT.md` §6。

### Two verification modes / 两种验证模式

ΣLang ships **two distinct verification tools** with different purposes:

| Tool / 工具 | Mode / 模式 | What it checks / 检查内容 |
|------------|------------|--------------------------|
| `verify_p0.py` | **Algorithm correctness** / 算法正确性 | 95 tests over §T/§E/§C/§I module *algorithms* (Lamport clocks, Result monad, confidence ops, I/O effects) — proves the P0 semantics are implementable. Does NOT parse `.md` specs. |
| `verify_consensus.py` | **Spec conformance** / 规范一致性 | Parses `.md` specs, applies Laws I–XVII + E-03/06/07/10 + §S/P-01 checks, and requires **38/38 corpus modules** to agree across Python / Rust / Elixir (Law XIII gate). |

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
├── verify_p0.py                    # Algorithmic verification (95 tests) / 算法验证
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
├── corpus/                         # Shared test corpus (35 modules) / 共享测试语料库
├── examples/                       # Usage examples / 使用示例
├── impl/                           # Verifier implementations / 验证器实现
│   ├── verifier/                   # Rust reference Verifier
│   └── elixir_rt/                  # Elixir/BEAM verifier + runtime
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

  🎯 TOTAL: 95/95 tests passed
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

- **Milestone / 里程碑**: **v0.11 可用 (2026-08-02)** — 包管理器 `sigma-cli.py` + 标准库 3 包，共识门禁 38/38 全绿 · **v0.10 可用 (2026-08-02)** — 数学符号 / 基本操作 / 常量包可用，证明可消解，共识门禁 35/35 全绿
- **Spec Version / 规范版本**: 0.3.0
- **Date / 日期**: 2026-08-02
- **License / 许可证**: MIT

## Citation / 引用

```
ΣLang: An AI-Native Semantic Protocol
Version 0.3.0
https://github.com/sigma-lang/sigma-lang
```
*（内容由AI生成，仅供参考）*
