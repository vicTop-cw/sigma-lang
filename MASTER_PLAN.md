# ΣLang Master Plan v0.5

> Target audience: **AI agents**.  
> Goal: This document is sufficient for ANY AI to understand, implement, and extend ΣLang.  
> Principle: Spec lives in spec files; this plan tells you what to DO with them.

---

## 状态快照（2026-08-02）

- ✅ **REACHED v0.10**: 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）、基本操作（`index()`/`I₂`、矩阵运算）、
  常量包（§C `0xK0xx`/`0xQ0xx`）三端求值器实现；consensus 35/35 → 38/38、p0 95/95。
- ✅ **REACHED v0.11**: 包管理器 `tools/sigma-cli.py` + 标准库 3 包
  （`std/math.base.md` / `std/data.transform.md` / `std/ai.confidence.md`）+ 三端共识覆盖。
- ✅ **REACHED**: AI Implementation Guide（4 个 spec 模块） + 参考实现 `impl/python/sigma_core.py`（59/59）
  + **AI bootstrapping test**（`tools/sigma-bootstrap.py` 一次干净跑通 spec→impl→verify→pass）。
- ✅ **REACHED**: Verifier format (json output) —— `verify_p0.py --json` 输出结构化 JSON（§1.2：
  spec/pass/modules/fingerprint），`sigma-cli verify --p0` 打通 CLI。
- ✅ **REACHED v0.12 (2026-08-02)**: Novel Spec Test —— `corpus/novel_gene_ok.md`（DNA 对齐语义，
  §5.2）三端验证器一致（consensus 39/39），跑通完整闭环；v0.10/v0.11 不回归。
- ✅ **REACHED v0.13 (2026-08-02)**: SocketKit Protocol —— `spec/spec_p0_socketkit.md`（§SK：
  task_create / review_merge / contribution_score 的 ΣLang 语义）+ `corpus/socketkit_ok.md`
  三端一致（consensus 40/40），走通 RFC → spec → 验证器 → 测试 晋升路径；v0.10–v0.12 不回归。
- ✅ **REACHED v0.14 (2026-08-03)**: SocketKit Runtime（审计闭环）—— §SK 参考实现进入
  `impl/python/sigma_core.py`（自检 75/75）· 审计运行时 `tools/sigma-runtime.py`（业务 trace →
  逐事件 ΣLang obligation 日志，10/10 满足）· `sigma-prove` 新增 §SK 六条定律义务全部
  `PROVED (unsat)` · 负例 `corpus/socketkit_break.md`（E-02，三端一致 FAIL，consensus 41/41）·
  §SK 行为测试进 `verify_p0.py`（109/109）；v0.10–v0.13 不回归。
- ✅ **REACHED v0.15 (2026-08-03)**: 三端 §SK 语义执行层—— §SK 参考实现从 Python 单侧
  同步到 Rust（`impl/verifier/src/sk.rs` + `--sk-self-check`，16/16）与 Elixir
  （`sigma_verify.exs` §SK + `--sk-self-check`，16/16）；三端行为一致（Python 75/75 含 §SK 16 项），
  0 warning；consensus 41/41、p0 109/109 不回退，v0.10–v0.14 全部保持全绿。
- ✅ **REACHED v0.16 (2026-08-03)**: SocketKit 语料执行化—— 三端求值器（verify_consensus.py /
  evaluator.rs / sigma_verify.exs）的 eval_expr 直接支持 §SK 三操作真实调用
  （`task_create(a,b)` / `review_merge([...])` / `contribution_score([...])`，含 ⊥ BountyErr /
  TypeError / ShapeError 错误路径）；`corpus/socketkit_ok.md` 的 Tests 从规范表达式
  （⊕ ∈ ⊘）升级为真实调用，consensus 门禁（Law XIII）直接验证业务语义本身；
  9/9 三端一致（consensus 41/41）、p0 109/109、三端 0 warning，v0.10–v0.15 不回归。
- ✅ **REACHED v0.17 (2026-08-03)**: §SK 对齐真实业务（MVP 语义扩展）—— 依据
  `D:\Desktop\来找茬_需求文档.md` v1.0 校准：Task 扩展为 4 元组 `[author, bounty, status, hunter]`
  并引入 4 态状态机（0=待接单 → 1=进行中 → 2=待验收 → 3=已完成）；新增 `accept_task`（接单）、
  `task_submit`（提交成果）、`task_accept`（受茬人单人验收）、`credit_score`（契分制：基础 100、
  完成 +5/单、违约 ×0.7）；`review_merge` 修正定位为增长期核验师多人评审场景；三端执行层与
  eval_expr 同步（sigma_core 91/91、三端 §SK 自检 32/32、socketkit_ok 24/24 三端一致）、
  sigma-prove 18 项 §SK 义务全部 PROVED (unsat)、sigma-runtime 完整业务 trace 23/23；
  consensus 41/41、p0 109/109、三端 0 warning，v0.10–v0.16 不回归。
- ⏳ **待办队列（avatar_loop 目标来源，一天一个）**:
  1. ⏸️ P3 — Lang-Zone backend integration（§6.1，**DEFERRED**：LZ 尚在原型期，待自举稳定后再融入）。
  2. （无）— v0.17 达成后 P3 待办已清空，进入新里程碑规划。

---

## Phase 1 — Verifier as the Single Source of Truth (Week 1)

The verifier is the **only authority** on what ΣLang means. No human text overrides it.

### 1.1 Extend verify_p0.py to validate ALL Iron Laws

> ✅ **DONE 2026-08-02**: Iron Laws automated checks live in `impl/verifier/src/main.rs`
> (`check_*`, 20 项覆盖：fingerprint / n_encoding / law_declaration / tests_mandatory /
> negative_tests / export_completeness / test_portability / proof_structure /
> internal_consistency / guarantee / eval_determinism / signature / backward_compat /
> calibration / shadowing / no_implementation / dependencies / timing_contract /
> effect_transparency / capabilities)，三端（Python/Rust/Elixir）一致。

Current: 109 tests covering Time/Error/Confidence/I/O/SocketKit.  
✅ **DONE 2026-08-02**: `verify_p0.py --json` 输出结构化 JSON（§1.2：spec/pass/modules/total/
fingerprint），`sigma-cli verify --p0` 打通 CLI（P0 队列）。

```
verify_p0.py → validate_spec("your_spec.md")
               ├── §T Time          17/17
               ├── §E Error         16/16
               ├── §C Confidence    37/37
               ├── §I I/O           25/25
               ├── §SK SocketKit    14/14
               └── §L Iron Laws     ✅ done (check_* in impl/verifier)
```

### 1.2 Verifier output format

```json
{
  "spec": "math.calculus@1.0",
  "pass": true,
  "modules": {
    "time": {"pass": 17, "fail": 0},
    "error": {"pass": 16, "fail": 0},
    "confidence": {"pass": 37, "fail": 0},
    "io": {"pass": 25, "fail": 0},
    "iron_laws": {"pass": 0, "fail": 12}
  },
  "fingerprint": "sha256:abc123..."
}
```

This JSON is the **protocol handshake** between AI and spec.

---

## Phase 2 — AI Implementation Guide (Week 1)

### 2.1 For every spec module, add an IMPLEMENTATION section

> ✅ **DONE 2026-08-02**: `## Implementation Checklist (for AI)` added to all 4 spec
> modules (`spec_p0_time.md` §T / `spec_p0_error.md` §E / `spec_p0_confidence.md` §C /
> `spec_p0_io.md` §I) — each lists the exact API to implement and what NOT to implement.

```markdown
## §T: Time & Causal Order

### Implementation Checklist (for AI)

To pass this module, implement exactly these:

1. `tick() -> Time`                           [T-01]
2. `happens_before(a: Time, b: Time) -> bool` [T-02]
3. ...

### What NOT to implement
- Do NOT assume monotonic clock
- Do NOT implement wall-clock synchronization
```

### 2.2 Minimal Reference Implementation

> ✅ **DONE 2026-08-02**: `impl/python/sigma_core.py` (~540 lines incl. self-check,
> stdlib only) implements ALL P0 modules; `python3 impl/python/sigma_core.py` → 59/59.

Place a single-file reference impl in `impl/python/`:

```python
# impl/python/sigma_core.py  (~200 lines)
# Implements ALL P0 modules
# Used by verify_p0.py to prove the spec is implementable
```

No dependencies except stdlib. This is NOT the "official" implementation — it's proof that the protocol is real.

---

## Phase 3 — Package Manager (Week 2)

> ✅ **REACHED 2026-08-02 (v0.11)**: `tools/sigma-cli.py` — `install / verify / list / search /
> fingerprint` 五个命令，`~/.sigma/registry.json` 注册表，Iron Law VII 无环依赖。
> ✅ **REACHED 2026-08-02**: `verify_p0.py --json` 输出结构化 JSON（§1.2）与 CLI 的
> `verify --p0` 子命令打通（P0 队列）。

### 3.1 CLI Design

```bash
sigma install <spec.md>          # Install a ΣLang package
sigma verify <package_name>       # Run its verifier
sigma list                        # List installed packages
sigma search <keyword>            # Search installed specs
sigma fingerprint <package>       # Show hash
```

### 3.2 Package Registry Format

```json
// ~/.sigma/registry.json
{
  "packages": {
    "math.calculus": {
      "version": "1.0.0",
      "path": "/home/user/.sigma/math.calculus/",
      "fingerprint": "sha256:...",
      "modules": ["time", "error", "confidence"],
      "deps": []
    }
  }
}
```

### 3.3 Dependency Resolution (Iron Law VII)

```python
def check_circular(pkg, visited=None):
    """No circular deps allowed. Returns True if clean."""
    visited = visited or set()
    if pkg.fingerprint in visited: return False  # circular!
    visited.add(pkg.fingerprint)
    return all(check_circular(d, visited) for d in pkg.deps)
```

---

## Phase 4 — Standard Library (Week 3)

> ✅ **REACHED 2026-08-02 (v0.11)**: 3 个标准包已落地 —— `std/math.base.md` /
> `std/data.transform.md` / `std/ai.confidence.md`，各配验证器测试集
> `corpus/std_*_ok.md`，三端共识覆盖（consensus 38/38）。

Ship with exactly 3 reference packages that prove the system works:

### 4.1 `math.base@1.0`

```
⊕ ⊖ ⊗ ⊘ — arithmetic with associativity/commutativity laws
√ pow log — transcendental with precision bounds
```

### 4.2 `data.transform@1.0`

```
map ∥ filter ∥ reduce — with lazy/eager semantics
sort group — with ordering laws
```

### 4.3 `ai.confidence@1.0`

```
calibrate(confidence, actual) -> calibrated_confidence
combine(opinions: List[Message]) -> consensus
```

Each package = 1 `.md` spec + 1 verifier test set.

---

## Phase 5 — AI Self-Bootstrapping (Week 4)

The ultimate test: **give ΣLang to a fresh AI session and see if it can implement a new spec without human help.**

### 5.1 Bootstrapping Protocol

```
1. Human: "Here is ΣLang spec and verifier"
2. AI reads spec/spec_p0_foundations.md
3. AI runs verify_p0.py → 0/95 passed (no implementation yet)
4. AI reads Implementation Guide for each module
5. AI writes impl/python/sigma_core.py
6. AI runs verify_p0.py → 95/95 passed
7. AI now "understands" ΣLang
```

### 5.2 Novel Spec Test

> ✅ **DONE 2026-08-02（v0.12）** — 验收标准已全部满足：
> 1. 新建 `corpus/novel_gene_ok.md`（DNA 对齐语义，ΣLang 格式）；
> 2. 三端验证器（Python/Rust/Elixir）判定一致，`verify_consensus.py` 计入 39/39；
> 3. 跑通完整流程：AI 读 spec → 写实现 → `verify_p0.py` 全绿 → 发布。

```
8. Human gives AI a new domain: "biomedical.gene@1.0 — DNA alignment semantics"
9. AI writes the spec in ΣLang format
10. AI writes the verifier tests
11. Human reviews, publishes
```

---

## Phase 6 — Backend Integration (Week 5+)

### 6.1 Lang-Zone as ΣLang Compiler（⏸️ DEFERRED）

> ⏸️ **搁置（P3）**：Lang-Zone（`E:/IDEProjects/AI/lang-zone`）是 LZ 语言编译器
> （`lzc`→Rust / `lzcyc`→Cython），CLI 无 `--target sigma` 参数，且 README 明示仍处
> IR 路线迁移中（原型期）。**待 LZ 自举且稳定后再考虑融入**，届时验收标准：
> 1. 用 `lzc`/`lzcyc` 将 ΣLang 语义实现（.lz）编译为原生产物（Cython `.pyd` 或 Rust `.so`）；
> 2. 产物可被 Python/Rust 加载并跑通验证器；
> 3. 三端共识不回退（consensus 保持 N/N）。

```
ΣLang spec → Lang-Zone → Cython → .pyd
                          OR
                          → Rust → .so
```

The spec defines WHAT; LZ compiles it to HOW.

### 6.2 SocketKit Protocol

> ✅ **DONE 2026-08-02（v0.13）** — 验收标准已全部满足：
> 1. 在 spec 中定义 `task_create / review_merge / contribution_score` 的 ΣLang 语义；
> 2. 每个行为配 1 个语料模块 + 验证器测试，三端判定一致；
> 3. 走通 RFC → spec 章节 → 验证器检查 → 测试 的晋升路径（参考 Phase 7）。

```
来找茬 App behavior defined in ΣLang:
  - Task submission: task_create(author, bounty) 
  - Review resolution: review_merge(opinions[]) → decision
  - Contribution calculation: contribution_score(actions[]) → points
```

This makes your App's business logic **mathematically auditable**.

---

## Phase 7 — Top-Level Rule Candidates (decided 2026-08-01)

> **Moved to `spec/spec_top_extensions.md`** — full candidate drafts (E-01 … E-09).
> Foundational top-level rules now live in **`spec/spec_top_rules.md`** (§S Shadowing Discipline).
> Candidates become normative via: RFC → spec section → Verifier check → tests.

---

## Priority Order

| Priority | Milestone | Deliverable |
|:---:|------|------|
| P0 | Verifier format (json output) | ✅ **REACHED 2026-08-02**: `verify_p0.py --json` (spec/pass/modules/total/fingerprint) + `sigma-cli verify --p0` |
| P0 | Iron Laws automated check | ✅ `check_*` in `impl/verifier` (I–IV, XIII–XVII, E-03/E-06/E-10); 3 verifiers |
| P0 | **Law XIII — Verifier Consensus** | ✅ **PROMOTED 2026-08-01**: `verify_consensus.py` + `corpus/` (38 modules × 3 verifiers Python/Rust/Elixir, 38/38 agree) |
| P0 | **Law XIV — Negative Test Mandatory** | ✅ **PROMOTED 2026-08-01**: `NoNegativeTest` in all 3 verifiers |
| P0 | **Law XV — Export Completeness** | ✅ **PROMOTED 2026-08-01**: ghost/hidden checks in all 3 verifiers |
| P0 | **Law XVI — Compatibility Proof** | ✅ **PROMOTED 2026-08-01**: `## Compat Tests` in all 3 verifiers |
| P0 | **v0.10 可用 (REACHED 2026-08-02)** | 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）、基本操作（`index()`/`I₂`、矩阵运算）、常量包（§C `0xK0xx`/`0xQ0xx`，Opaque 不可遮蔽）三端求值器全部实现；`sigma-prove` PROVED (unsat)、`sigma-moonbit` 生成 `.mbtp`；consensus 35/35、p0 95/95、0 warning |
| P0 | **v0.11 可用 (REACHED 2026-08-02)** | 包管理器 `tools/sigma-cli.py`（install/verify/list/search/fingerprint + `~/.sigma/registry.json` + Iron Law VII 无环依赖）；标准库 3 包 `std/math.base.md` / `std/data.transform.md` / `std/ai.confidence.md`（各 1 规范 + 1 验证器测试集 `corpus/std_*_ok.md`，三端共识覆盖）；v0.10 不回归；consensus 38/38、p0 95/95、0 warning |
| P0 | **AI Implementation Guide (REACHED 2026-08-02)** | ✅ `## Implementation Checklist (for AI)` in all 4 spec modules (§T/§E/§C/§I) |
| P0 | **Minimal reference impl (REACHED 2026-08-02)** | ✅ `impl/python/sigma_core.py` — stdlib-only core, self-check 59/59 |
| P1 | Package manager CLI | ✅ v0.11: `tools/sigma-cli.py` (REACHED 2026-08-02) |
| P1 | 3 standard packages | ✅ v0.11: `std/math.base.md` + tests (REACHED 2026-08-02) |
| P2 | AI bootstrapping test | ✅ **REACHED 2026-08-02**: `tools/sigma-bootstrap.py` — one clean run closes the loop spec→impl→verify→pass (4 specs carry `## Implementation Checklist (for AI)`, `sigma_core.py` 59/59, `verify_p0.py` 95/95) |
| P2 | **v0.12 Novel Spec Test (REACHED 2026-08-02)** | ✅ `corpus/novel_gene_ok.md`（DNA 对齐语义, §5.2）— consensus 39/39 三端一致 + AI 闭环 |
| P3 | **v0.13 SocketKit integration (REACHED 2026-08-02)** | ✅ `spec/spec_p0_socketkit.md` + `corpus/socketkit_ok.md`（§6.2）— consensus 40/40 三端一致 |
| P3 | **v0.14 SocketKit Runtime (REACHED 2026-08-03)** | ✅ §SK 参考实现（`sigma_core.py` 75/75）+ 审计运行时（`tools/sigma-runtime.py`，obligation 日志 10/10）+ `sigma-prove` §SK 六定律 PROVED (unsat) + 负例 `corpus/socketkit_break.md`（consensus 41/41）+ §SK 进 `verify_p0.py`（109/109） |
| P3 | **v0.15 三端 §SK 执行层 (REACHED 2026-08-03)** | ✅ §SK 参考实现同步到 Rust（`src/sk.rs` + `--sk-self-check` 16/16）与 Elixir（`sigma_verify.exs` §SK + `--sk-self-check` 16/16），三端行为一致、0 warning；consensus 41/41、p0 109/109 不回退 |
| P3 | **v0.16 SocketKit 语料执行化 (REACHED 2026-08-03)** | ✅ 三端求值器 eval_expr 支持 §SK 三操作真实调用；`corpus/socketkit_ok.md` Tests 升级为真实调用（含 ⊥ 错误路径），9/9 三端一致——Law XIII 直接验证业务语义；consensus 41/41、p0 109/109、0 warning |
| P3 | **v0.17 §SK 对齐真实业务 (REACHED 2026-08-03)** | ✅ Task 4 元组 + 4 态状态机；新增 accept_task/task_submit/task_accept/credit_score；review_merge 修正为增长期定位；三端执行层同步（sigma_core 91/91、三端 §SK 32/32、socketkit_ok 24/24）；sigma-prove 18 项义务 PROVED；sigma-runtime 23/23；consensus 41/41、p0 109/109、0 warning |
| P3 | Lang-Zone backend integration | ⏸️ **DEFERRED**：LZ 原型期，待自举稳定后融入（§6.1） |

---

## What you (Victor) should NOT do

- ❌ Don't implement every ΣLang package personally
- ❌ Don't optimize performance yet
- ❌ Don't build a GUI

You design the **protocol grammar** (the Iron Laws + verifier). AI fills in the implementations.
