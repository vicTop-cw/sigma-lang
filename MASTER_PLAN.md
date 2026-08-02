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
- ✅ **REACHED**: AI Implementation Guide（4 个 spec 模块） + 参考实现 `impl/python/sigma_core.py`（59/59）。
- ⏳ **待办队列（avatar_loop 目标来源，一天一个）**:
  1. P0 — Verifier format (json output)：`verify_p0.py` 输出结构化 JSON（§1.2）。
  2. P2 — AI bootstrapping test：一次干净跑通 AI→spec→impl→verify→pass（§5.1）。
  3. P3 — Lang-Zong backend integration：`lzc --target sigma`（§6.1）。
  4. P3 — SocketKit integration：spec 驱动行为契约（§6.2）。

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

Current: 95 tests covering Time/Error/Confidence/I/O.  
Missing (剩余工作): `verify_p0.py` 输出结构化 JSON（见 §1.2 与 Priority Order P0）。

```
verify_p0.py → validate_spec("your_spec.md")
               ├── §T Time          17/17
               ├── §E Error         16/16
               ├── §C Confidence    37/37
               ├── §I I/O           25/25
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

```
8. Human gives AI a new domain: "biomedical.gene@1.0 — DNA alignment semantics"
9. AI writes the spec in ΣLang format
10. AI writes the verifier tests
11. Human reviews, publishes
```

---

## Phase 6 — Backend Integration (Week 5+)

### 6.1 Lang-Zong as ΣLang Compiler

```
ΣLang spec → Lang-Zone → Cython → .pyd
                          OR
                          → Rust → .so
```

The spec defines WHAT; LZ compiles it to HOW.

### 6.2 SocketKit Protocol

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
| P0 | Verifier format (json output) | modified verify_p0.py |
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
| P3 | Lang-Zong backend integration | lzc --target sigma |
| P3 | SocketKit integration | spec-driven behavior contracts |

---

## What you (Victor) should NOT do

- ❌ Don't implement every ΣLang package personally
- ❌ Don't optimize performance yet
- ❌ Don't build a GUI

You design the **protocol grammar** (the Iron Laws + verifier). AI fills in the implementations.
