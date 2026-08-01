# ΣLang Top-Level Rules — Extension Candidates

> **Status**: MIXED — Laws XIII–XVI are **normative** (promoted 2026-08-01); the remaining entries
> are CANDIDATE (NOT normative) and require RFC + Verifier support + spec adoption before
> enforcement.
> **Source**: MASTER_PLAN Phase 7 backlog (decided 2026-08-01)
> **Adoption path**: RFC → spec section → Verifier check → tests
> **License**: MIT

---

## E.0 Candidate Index

| ID | Rule | Proposed level | Verifier-checkable | Status |
|----|------|----------------|--------------------|--------|
| E-01 | Verifier Consensus | Iron Law (XIII) | ✅ | ✅ **PROMOTED** |
| E-02 | Negative Test Mandatory | Iron Law (XIV) | ✅ | ✅ **PROMOTED** |
| E-03 | Test Portability | Meta-rule | ✅ | ✅ **PROMOTED** |
| E-04 | Export Completeness | Iron Law (XV) | ✅ | ✅ **PROMOTED** |
| E-05 | Compatibility Proof | Iron Law (XVI) | ✅ | ✅ **PROMOTED** |
| E-06 | Internal Consistency Adjudication | Meta-rule | ⚠️ partial (shape checks ✅) | ✅ **PROMOTED** (v0.1: signature/test consistency) |
| E-07 | Conflict Adjudication Process | Meta-rule | ❌ (governance) | ✅ **PROMOTED** (§G, registry-gated) |
| E-08 | Strategy Bundle (Trust/Provenance, Human Escalation, Eval Determinism) | Strategy | ❌ | candidate |
| E-09 | Probabilistic Guarantee | Iron Law (XVII) | ⚠️ partial (declaration ✅) | ✅ **PROMOTED** (v0.1: declaration check) |
| E-10 | Evaluation Determinism | Law VIII extension | ⚠️ partial (declaration ✅) | ✅ **PROMOTED** (v0.1: declaration check) |
| P-01 | Proof-Carrying Spec Structure | Meta-rule (spec_top_proofs.md) | ✅ | ✅ **ENFORCED** |

---

## E-01 Verifier Consensus (PROMOTED — Law XIII)

### Motivation

MASTER_PLAN Phase 1 declares "the Verifier is the only authority" — but nothing constrains
**Verifier implementations themselves**. Two conforming verifiers (Python + Rust already exist) can
disagree on the same spec, silently re-introducing cross-AI inconsistency at the meta level.
Authority must be self-consistent: the authority itself must agree with itself.

### Proposed rule

```md
Law XIII — Verifier Consensus
同一 spec 在任何合格 Verifier 实现上判定一致（pass/fail 一致、violations 一致）。
同一判定必须可复现：时间无关、机器无关、Verifier 实现无关。
```

### Verifier check

- Cross-run: same spec → same verdict twice (deterministic, no randomness, no wall-clock input).
- Cross-implementation: Python verifier vs Rust verifier on the shared test corpus must produce
  identical pass/fail per module.
- CI gate: any change to a Verifier must re-run the cross-implementation suite.

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| V-01 | Run Python verifier twice on same spec | identical verdict |
| V-02 | Run Python + Rust + Elixir verifier on same spec | identical verdict |
| V-03 | Spec with 1 injected violation | all verifiers flag it |

### Adoption criteria

- [x] Dual-verifier CI job exists (`verify_consensus.py` — three verifiers: Python / Rust / Elixir)
- [x] §V Verifier Architecture updated with conformance clause (§V.4, promoted 2026-08-01)

### Verification record (2026-08-01) — consensus NOT yet established

First dual-verifier run on `examples/tensor_ops.md`:

| Verifier | Result | Verdict |
|----------|--------|---------|
| Python `verify_p0.py` | 95/95 passed (T 17, E 16, C 37, I 25) — **real execution** | ✅ genuine |
| Rust `impl/verifier` | "CERTIFIED: 95 tests passed" (exit 0) | ❌ **hardcoded** |

Root cause found in `impl/verifier/src/main.rs`:

- `Certification::new()` hardcodes `tests_passed: 95, tests_total: 95, laws_checked: 12`.
- `run_tests()` is an empty stub ("we trust the Python prototype's 95/95 results").
- `parse_sigma_module()` returns an empty `Module` (no symbols, no tests).

Conclusion: **E-01 cannot be declared satisfied.** The Rust verifier is a skeleton — it certifies
anything it is given without parsing or executing. Cross-implementation consensus is untestable
until the Rust verifier implements real parsing + test execution. This is the top blocker for E-01.

Build fixes applied during this run (offline, crates.io unreachable):

- Removed unused `colored` dependency (not referenced in source; absent from local registry cache).
- Enabled `tracing-subscriber` `env-filter` feature (required by `with_env_filter`).

Next step for E-01: implement `parse_sigma_module` (real MD parsing) and `run_tests` (execute
canonical tests against a reference evaluator), then re-run the comparison.

### Follow-up run (same day) — real parsing + execution implemented

Both blockers from the first run are now fixed (`parse_sigma_module` is a real line parser;
`run_tests` executes canonical tests via a minimal evaluator; the hardcoded 95 is gone):

| Verifier | Target | Result | Verdict |
|----------|--------|--------|---------|
| Python `verify_p0.py` | internal algorithm tests | 95/95 passed | ✅ genuine |
| Rust `sigma-verifier` | `examples/tensor_ops.md` | 3 ops parsed, 9 tests executed **all passed** (no TestFailed), but **3× MissingEncoding** → VERIFICATION FAILED | ⚠️ real, stricter |
| Rust `sigma-verifier` | `examples/demographics.md` | CERTIFIED, **0 tests parsed** | ⚠️ format gap |

Key findings:

1. **Rust is now a real verifier** — it parses, checks Iron Laws, and executes tests. No more
   hardcoded results.
2. **The two verifiers verify different artifacts.** Python verifies internal algorithm properties
   (clock monotonicity, confidence normalization, …) and never parses MD. Rust verifies MD structure
   + Iron Laws + canonical tests. **Consensus is undefined until a shared corpus exists** — a set of
   MD modules both verifiers must judge identically. This is the real E-01 deliverable.
3. **Rust found a genuine Law II gap in `tensor_ops.md`**: it declares `Tensor⟨D,R⟩ : Type` and
   claims "Encoding to ℕ ✓" but defines no `encode` function — the verifier correctly flags
   MissingEncoding. Either the example must add an encoding op or relax the claim.
4. **Parser format gap**: `demographics.md` uses `### Surname Encoding` blocks, which the parser
   (expecting `## Operation:`) does not capture → 0 tests parsed. Parser needs the `###` form too.

Next step: define the shared corpus (3–5 MD modules covering all four P0 module styles), extend the
parser to both `## Operation:` and `###` block forms, then require identical verdicts from both
verifiers in CI.

### Follow-up run (same day) — consensus ESTABLISHED on shared corpus

All three follow-up steps are now done: `corpus/` created (5 modules), Rust parser extended to both
block styles, `verify_consensus.py` written (independent Python-side MD check + Rust driver + the
`# Expected:` marker). Full run:

| Module | Expected | Python | Rust | Agree |
|--------|----------|--------|------|-------|
| `arith_ok.md` | PASS | PASS | PASS (3 tests) | ✅ |
| `conf_ok.md` | PASS | PASS | PASS (2 tests) | ✅ |
| `encoding_ok.md` | PASS | PASS | PASS (4 tests) | ✅ |
| `missing_laws.md` | FAIL (Law III) | FAIL | FAIL | ✅ |
| `missing_tests.md` | FAIL (Law IV) | FAIL | FAIL | ✅ |

**`🏆 E-01 VERIFIER CONSENSUS ESTABLISHED on the shared corpus`** — 5/5 modules agree
(Python == Rust == Expected).

Bugs found and fixed during this run:

1. **Imports-section swallow bug (both parsers)**: `## Imports` set `in_imports` but neither parser
   reset it on a non-import line, so every heading after imports was consumed → 0 ops parsed, every
   module falsely PASS. Fixed: exit imports mode and reprocess the line on the first non-import line.
2. **Python/Rust block-classification divergence**: Rust's `flush_block` demotes fingerprint-less
   signed blocks to `Function` (encodings) and discards unsigned blocks; Python appended all blocks
   as ops → false `MissingFingerprint`. Fixed: Python `flush()` now mirrors Rust semantics
   (fp → op, signed-no-fp → fn, unsigned → discard).

Residual gaps (accepted for v0.1 of the check): Law II encoding detection only recognizes functions
whose *name* contains "encode"; corpus modules were written with numeric return types so the check
is exercised only structurally. The corpus covers `## Operation:` and `###` block styles and
PASS/FAIL verdicts; §T/§E semantics are not yet directly represented (conf_ok covers §C).

### Follow-up run (same day) — THIRD verifier: Elixir (BEAM backend)

Per the master plan's L0 philosophy ("one symbol, one meaning, one result — across all models"),
a third, language-independent implementation was added: `impl/elixir_rt/sigma_verify.exs`
(standalone script, no mix deps, run via `elixir sigma_verify.exs <module.md>`; exit 0 = PASS).
`verify_consensus.py` now drives **three** verifiers (Python MD-check, Rust, Elixir).

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `arith_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `conf_ok.md` | PASS | PASS | PASS (2) | PASS (2/2) | ✅ |
| `encoding_ok.md` | PASS | PASS | PASS (4) | PASS (4/4) | ✅ |
| `missing_laws.md` | FAIL (Law III) | FAIL | FAIL | FAIL | ✅ |
| `missing_tests.md` | FAIL (Law IV) | FAIL | FAIL | FAIL | ✅ |

**`🏆 E-01 VERIFIER CONSENSUS ESTABLISHED — 5/5 modules agree (Python == Rust == Elixir == Expected)`**

Two Elixir-side fixes were needed before consensus held:

1. `String.slice(t, 6..-2//-1)` (reverse step) wrongly sliced `index(...)` arguments → fixed to
   `6..-2//1` (forward step).
2. `split_all_top_level/6` collected separator byte indices instead of substrings → rewritten as a
   start/position walker that cuts pieces at depth-0 separators.

Cross-platform note: on Windows, `elixir` resolves to a bash shim that Python's `CreateProcess`
cannot launch directly; `run_elixir` uses `shutil.which("elixir.bat" | "elixir.exe" | "elixir")`.

The three implementations are deliberately independent (different languages, different parsers,
different test evaluators) — that is what makes their agreement meaningful for Law XIII.

---

## E-02 Negative Test Mandatory (PROMOTED — Law XIV)

### Motivation

Law IV requires ≥1 canonical test per op, but success-only suites miss the error paths — exactly
where AI implementations break (wrong error type, missing boundary check, silent fallback).
`tensor_ops.md` already shows the pattern (`[1]⊕[1,2] → ⊥ BroadcastError`); it must become law.

### Proposed rule

```md
Law — Negative Test Mandatory
每个操作至少 1 个成功用例 且 至少 1 个失败/边界用例（错误路径）。
失败用例必须断言错误值（Error 代数，§E），不得仅断言 "不崩溃"。
```

### Verifier check

- Per symbol: ≥1 test whose expected output is an error/⊥ value.
- Boundary inputs (empty, min/max, 0, NaN-adjacent) count as negative when they exercise a guard.

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| N-01 | `⊕` with only success tests | ❌ missing negative test |
| N-02 | `⊕` with `[1]⊕[1,2] → ⊥` | ✅ |

### Adoption criteria

- [x] Scan all existing tests; add negative cases where missing (conf_ok + nth gained ⊥ cases)
- [x] Verifier `run_tests` counts positive vs negative per symbol (`check_negative_tests` in all three)

### Promotion record (2026-08-01) — PROMOTED to Iron Law

E-02 is now enforced by all three verifiers. Each operation must have ≥1 test whose expected
output starts with `⊥` (error path); otherwise `NoNegativeTest` is reported.

Corpus update: `negative_missing.md` (FAIL, E-02) added; `conf_ok.md` and `encoding_ok.md` gained
negative cases so they remain PASS. Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `arith_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `conf_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `encoding_ok.md` | PASS | PASS | PASS (5) | PASS (5/5) | ✅ |
| `error_ok.md` | PASS | PASS | PASS (2) | PASS (2/2) | ✅ |
| `time_ok.md` | PASS | PASS | PASS (2) | PASS (2/2) | ✅ |
| `missing_laws.md` | FAIL | FAIL | FAIL | FAIL | ✅ |
| `missing_tests.md` | FAIL | FAIL | FAIL | FAIL | ✅ |
| `negative_missing.md` | FAIL (E-02) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 8/8 modules agree (Python == Rust == Elixir == Expected)`**

---

## E-03 Test Portability (candidate Meta-rule)

### Motivation

"Equality by Test" is only meaningful if the test suite itself is implementation-independent.
Tests asserting on implementation-specific output formats (JSON dump order, float formatting,
internal error codes) make two conforming implementations fail each other's tests.

### Proposed rule

```md
Meta-rule — Test Portability
测试只依据 spec 定义的语义判定（值、错误代数、效应），
不得依赖任何实现的输出格式、内部表示或错误消息文本。
```

### Verifier check

- Reject test assertions that reference implementation details (e.g. string-match on error messages).
- Preferred: structured assertions (value equality, `Result⟨V,E⟩` shape) only.

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| P-01 | Test asserting a raw Map rendering `Map{scode → [p₁,p₂]}` | ❌ format-dependent |
| P-02 | Test asserting `{:err, :broadcast_error}` shape | ✅ semantic |

### Adoption criteria

- [x] Test authoring guide (IMPLEMENTATION sections) states structured assertions only
      (`check_test_portability` in all three verifiers)

### Promotion record (2026-08-01) — PROMOTED to Meta-rule

E-03 is now enforced by all three verifiers. Every test's expected output must be semantically
structured — an error (`⊥`-prefixed) or a parseable literal — never an implementation-specific
format (float string, Map rendering, error message text). Violations report
`UnportableAssertion(op, expected)`.

Corpus update: `portability_break.md` (FAIL, E-03 — asserts `1 ⊕ 2 | Map{scode → [p₁,p₂]}`) added. Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `arith_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `compat_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `conf_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `encoding_ok.md` | PASS | PASS | PASS (5) | PASS (5/5) | ✅ |
| `error_ok.md` | PASS | PASS | PASS (2) | PASS (2/2) | ✅ |
| `time_ok.md` | PASS | PASS | PASS (2) | PASS (2/2) | ✅ |
| `portability_break.md` | FAIL (E-03) | FAIL | FAIL | FAIL | ✅ |
| `compat_break.md` | FAIL (E-05) | FAIL | FAIL | FAIL | ✅ |
| `ghost_export.md` | FAIL (E-04) | FAIL | FAIL | FAIL | ✅ |
| `hidden_export.md` | FAIL (E-04) | FAIL | FAIL | FAIL | ✅ |
| `missing_laws.md` | FAIL (Law III) | FAIL | FAIL | FAIL | ✅ |
| `missing_tests.md` | FAIL (Law IV) | FAIL | FAIL | FAIL | ✅ |
| `negative_missing.md` | FAIL (E-02) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 13/13 modules agree (Python == Rust == Elixir == Expected)`**

Design note: portability is decided structurally (`⊥` or parseable literal) in v0.1; full
semantic-type checking of expected values is a future extension (E-06 territory).

---

## E-04 Export Completeness (PROMOTED — Law XV)

### Motivation

Packages declare `## Exports` (§2.2) but nothing enforces it matches definitions. Ghost symbols
(declared, undefined) break downstream imports; hidden symbols (defined, undeclared) leak
unintended API surface. Both are silent supply-chain breaks.

### Proposed rule

```md
Law — Export Completeness
包的 Exports 列表与实际定义符号一一对应：
无幽灵符号（声明未定义）、无隐藏符号（定义未声明）。
```

### Verifier check

- Set-difference: `exports - definitions` → ghost; `definitions - exports` → hidden. Both are violations.

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| E-01 | Exports lists `PV` but no definition | ❌ ghost symbol |
| E-02 | Defines `secret_op` not in Exports | ❌ hidden symbol |
| E-03 | Exports == definitions | ✅ |

### Adoption criteria

- [x] Verifier `check_export_completeness(module)` added (all three verifiers)
- [x] Examples updated to satisfy it (arith_ok gained `## Exports`; ghost/hidden corpus added)

### Promotion record (2026-08-01) — PROMOTED to Iron Law

E-04 is now enforced by all three verifiers. If a module declares `## Exports`, every exported
name must be a defined symbol (no ghost) and every defined symbol must be exported (no hidden).
Modules without an `## Exports` block are not checked (v0.1 policy).

Corpus update: `ghost_export.md` (FAIL, E-04 ghost) and `hidden_export.md` (FAIL, E-04 hidden)
added; `arith_ok.md` gained a matching `## Exports` block as a positive case. Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `arith_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `conf_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `encoding_ok.md` | PASS | PASS | PASS (5) | PASS (5/5) | ✅ |
| `error_ok.md` | PASS | PASS | PASS (2) | PASS (2/2) | ✅ |
| `time_ok.md` | PASS | PASS | PASS (2) | PASS (2/2) | ✅ |
| `ghost_export.md` | FAIL (E-04) | FAIL | FAIL | FAIL | ✅ |
| `hidden_export.md` | FAIL (E-04) | FAIL | FAIL | FAIL | ✅ |
| `missing_laws.md` | FAIL | FAIL | FAIL | FAIL | ✅ |
| `missing_tests.md` | FAIL | FAIL | FAIL | FAIL | ✅ |
| `negative_missing.md` | FAIL (E-02) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 10/10 modules agree (Python == Rust == Elixir == Expected)`**

Implementation notes (bugs found during promotion):

1. **Rust name source**: the parser kept the block heading (`⊕ (Add)`) as the symbol name while
   Python/Elixir used the signature name (`⊕`), breaking export matching. Fixed: signature name
   now always overrides the heading when it is a single token.
2. **Elixir exports heading swallow**: `## Exports`-mode consumed the following heading line
   instead of replaying it → operations after Exports were lost. Fixed: replay on heading.
3. **Elixir scope bug**: E-04 violations computed inside `if`'s `else` branch were locally
   rebound and never returned. Fixed: if-expression assignment form.

---

## E-05 Compatibility Proof (PROMOTED — Law XVI, Law VI enforcement)

### Motivation

Law VI says "published = frozen / backward compatible" but it's a promise with no mechanism.
Declaring "compatible" costs nothing; proving it costs a test run. Compatibility must be
checkable fact, not intent.

### Proposed rule

```md
Law — Compatibility Proof
任何声明 "向后兼容" 的新版本，必须通过旧版本的完整 canonical 测试集，
并以 Verifier 报告为证据（无新增 violation）。
```

### Verifier check

- `verify(pkg@new)` with `--against pkg@old` runs old test suite against new definitions.
- Violations in old suite under new pkg → compatibility claim rejected.

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| C-01 | New version drops a symbol, old suite references it | ❌ incompatible |
| C-02 | New version adds op, old suite passes | ✅ compatible (additive) |

### Adoption criteria

- [x] Verifier `--against` flag implemented (`## Compat Tests` block in all three verifiers)
- [ ] §Z Breaking Change Protocol references this proof

### Promotion record (2026-08-01) — PROMOTED to Iron Law

E-05 is now enforced by all three verifiers. A module declaring `## Compat Tests` (the previous
version's canonical suite) must pass all of them; any failure rejects the "backward compatible"
claim (`CompatTestFailed`). This implements the "checkable fact, not intent" requirement of Law VI.

Corpus update: `compat_ok.md` (PASS, all compat tests pass) and `compat_break.md` (FAIL, one
compat test breaks) added. Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `compat_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `compat_break.md` | FAIL (E-05) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 12/12 modules agree (Python == Rust == Elixir == Expected)`**

Implementation notes (bugs found during promotion):

1. **Compat-block fence handling**: the `## From v1.0 …` comment line inside the compat-test code
   fence was mistaken for a section-ending heading in all three parsers → compat tests were never
   parsed (empty list, check silently skipped). Fixed: heading detection inside `in_compat_tests`
   only fires outside fences.
2. **Elixir heading swallow**: the compat-tests section consumed the following `## Operation:`
   heading instead of replaying it. Fixed: `{:replay, …}` on heading exit (same fix as E-04's
   exports section).

Design note: `## Compat Tests` is the inline form of `--against pkg@old` — the old suite is
embedded in the new version's spec rather than loaded from a separate file. The `--against` CLI
flag remains a future convenience; the normative mechanism is the inline block.

---

## E-06 Internal Consistency Adjudication (candidate Meta-rule)

### Motivation

Meta-Rule 6 (human text non-normative) says prose doesn't define semantics — but doesn't say what
happens when signature, law, test, and prose **contradict each other**. Today that's a vacuum;
AIs must know the resolution order.

### Proposed rule

```md
Meta-rule — Internal Consistency
类型签名、定律、测试、自然语言四者冲突时：
优先级 测试 ≥ 定律 ≥ 类型签名 > 自然语言。
Verifier 应检测明显冲突（如测试输入类型与签名不符）并告警。
```

### Verifier check

- Type-check test inputs against symbol signature (obvious mismatches → violation).
- Law-vs-test contradiction detection (best-effort; declarative checks only).

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| I-01 | Test feeds `ℝ` to a `ℕ → ℕ` op | ❌ signature mismatch |
| I-02 | Prose contradicts test; test passes | ✅ tests win |

### Adoption criteria

- [x] Verifier type-checks test fixtures (`SignatureMismatch` in all three verifiers)
- [x] §0 Meta-Rules updated with priority order (§0.1 rule 11 — Internal Consistency Adjudication)

### Promotion record (2026-08-01) — PROMOTED to Meta-rule

E-06 is now enforced by all three verifiers at the **obvious-conflict** level: a test's expected
value must match the operation's declared return-type shape (numeric return → numeric
expectation; container return like `List`/`Tensor`/`Map` → list expectation; `⊥` error paths and
unparseable expectations are skipped — the latter is E-03's territory). Violations report
`SignatureMismatch(op, expected)`.

Corpus update: `signature_mismatch.md` (FAIL, E-06 — `⊕ : ℕ × ℕ → ℕ` with a test expecting
`[5,7,9]`) added. Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `signature_mismatch.md` | FAIL (E-06) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 16/16 modules agree (Python == Rust == Elixir == Expected)`**

Scope note (v0.1): the structural "resolution order" half of E-06 — when signature, law, test,
and prose all disagree, tests ≥ laws ≥ signature > prose — is now codified as Meta-Rule 11 in
`spec_p0_foundations.md` §0.1; the machine-checkable half is the shape-level signature/test
consistency enforced here (adoption criteria 2 closed).

---

## E-07 Conflict Adjudication Process (candidate Meta-rule)

### Motivation

Law I forbids fingerprint conflicts but defines no path when one *happens* (two packages claim the
same fingerprint; semantic dispute over a symbol). This is governance, not code — but it must be
specified or the ecosystem has no resolution mechanism.

### Proposed rule

```md
Meta-rule — Conflict Adjudication
指纹冲突或语义争议的处置路径：
1. RFC 提交（冲突描述 + 双方证据）
2. 仲裁委员会评审（人工 + 双 Verifier 互证）
3. 裁决结果写入 registry（winner 保留指纹，loser 重分配）
4. 争议期旧版本保持可加载（Law VI 不因争议失效）
```

### Verifier check

- None (process). Registry records adjudication outcomes; verifiers refuse to certify a conflict
  until resolved.

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| A-01 | Fingerprint collision detected | ❌ blocked, RFC required |

### Adoption criteria

- [x] Registry schema gains `adjudication` field (`spec_top_rules.md` §G.4)
- [x] Governance doc (RFC template) published (`spec_top_rules.md` §G.3)

### Promotion record (2026-08-01) — PROMOTED to Meta-rule

E-07 is now normative governance in `spec_top_rules.md` §G (Conflict Adjudication Process):
RFC submission (§G.3 template), arbitration with dual-verifier cross-check (Law XIII),
registry verdict recording (§G.4 `adjudication` field), and Law VI protection during disputes.

Verifier interaction (§G.5): a module importing a `disputed` fingerprint is **not certified**
until the registry marks it `decided`. This is a hard fail, not a warning. The corpus contains
no disputed fingerprints; the mechanism is exercised by the registry, not the corpus.

Draft test A-01 (fingerprint collision → blocked, RFC required) is satisfied by §G.5 +
§G.2 step 1. Remaining adoption item: the `sigma-pkg` registry backend implementation.

---

## E-08 Strategy Bundle (candidate Strategy)

### Motivation

Long-term robustness needs three non-semantic guarantees. Deferred — they require external
ecosystems (PKI, monitoring), not just spec changes.

### Proposed items

| ID | Strategy | Content | Blocked on |
|----|----------|---------|------------|
| S-01 | Trust & Provenance | Package signatures, author identity, supply-chain anti-poisoning | **Level 1 feasible** (see study); L2 registry, L3 Sigstore |
| S-02 | Human Escalation | High-risk semantic ops must declare human confirmation points | App-layer policy |
| S-03 | Eval Determinism | **→ PROMOTED as E-10 (2026-08-01)**: numeric precision / rounding / sort stability declaration | — |

> S-03 was split out and promoted separately as **E-10 — Evaluation Determinism** (below),
> because it is the only machine-checkable item in this bundle. S-02 remains deferred
> (app-layer policy).
>
> **S-01 feasibility study published (2026-08-01)**: `spec/spec_pki_feasibility.md` concludes
> Level 1 (author signatures, Ed25519) is fully feasible with pure software; Level 2 (registry
> trust, TUF-lite) is feasible after the `sigma-pkg` registry backend; Level 3 (transparency
> log) stays roadmap. S-01 is therefore **no longer blocked on PKI ecosystem** at Level 1.

### Verifier check

- **Level 1 implemented (2026-08-01)**: `check_signature` in all three verifiers — a module
  declaring `## Signature` must provide a well-formed `signer`, `pubkey_fp` (sha256: prefix),
  `algorithm` (ed25519), and a non-empty `signature`. Skipped when a module has no
  `## Signature` block (backward compatible — Law VI).

### Adoption criteria

- [ ] RFC for `## Signature` block syntax (spec_pki_feasibility.md F.3 Level 1) — syntax stable in practice
- [x] `check_signature` in all three verifiers (skip when absent) — 23/23 agree
- [ ] Registry `provenance` field (Level 2)
- [x] PKI feasibility study — `spec/spec_pki_feasibility.md` (F.6)

### S-01 Level 1 implementation record (2026-08-01)

The PKI feasibility study's Level 1 (author signatures, Ed25519) is now enforced by all three
verifiers as a declaration check: a `## Signature` block must be well-formed (`signer` non-empty,
`pubkey_fp` with `sha256:` prefix, `algorithm: ed25519`, non-empty `signature`). Violations
report `MalformedSignature(detail)`. Modules without a signature still verify (Law VI).

Corpus update: `signature_ok.md` (PASS — well-formed signature) and `signature_break.md`
(FAIL — missing signer, bad pubkey_fp, wrong algorithm, empty signature) added. Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `signature_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `signature_break.md` | FAIL (S-01) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 23/23 modules agree (Python == Rust == Elixir == Expected)`**

Note: a real cryptographic verification of the signature value (Level 1+ crypto check) remains
future work — this is the declaration-level check only, mirroring E-09/E-10.

---

## E-09 Probabilistic Guarantee (PROMOTED — Law XVII)

### Motivation

Law IX calibrates confidence to accuracy (internal consistency). Missing: an **external performance
floor** — a prediction op must guarantee a minimum bound (e.g. direction-accuracy ≥ 0.90).
Statistical claims can't be deterministically checked at verify time, so the law must bound exactly
what the Verifier certifies.

### Proposed rule

```md
Law XVII — Probabilistic Guarantee
预测类操作必须声明最低性能下限（指标 + 阈值 + 评测数据集）。
Verifier 仅认证：(a) 声明存在且格式良好；(b) 在声明数据集上测量结果可复现。
生产环境达标属于运行时监控职责，不由 Verifier 保证。
防作弊：数据集须为 held-out/第三方提供；指标可选 accuracy / F1 / Brier，
默认 Brier/校准误差（普通 accuracy 在失衡数据上失真）。
```

### Verifier check

- Declaration well-formed: `metric`, `threshold`, `dataset` present, values in range.
- Reproducibility: re-running the declared evaluation on the dataset yields the declared result
  (within tolerance).

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| G-01 | Prediction op with no bound declared | ❌ missing declaration |
| G-02 | Declared `acc ≥ 0.90`, dataset run gives 0.87 | ⚠️ reproducible but below bound → report, not hard fail |
| G-03 | Declared metric = `brier`, no dataset given | ❌ malformed declaration |

### Adoption criteria

- [x] Pilot on Phase 4 `ai.confidence@1.0` (calibrate / combine) — declaration check enforced in all three verifiers
- [ ] Runtime monitoring interface defined (out of Verifier scope — deferred)

### Promotion record (2026-08-01) — PROMOTED to Iron Law (XVII)

E-09 is now enforced by all three verifiers at the **declaration** level: a module declaring
`## Guarantee` must provide a well-formed `metric` (accuracy|f1|brier), `threshold` (0..=1), and
`dataset` (non-empty). Violations report `MalformedGuarantee(detail)`. Per the law's own
boundary, the Verifier certifies the declaration only — production conformance remains runtime
monitoring's job, and held-out/third-party datasets remain the anti-gaming requirement.

Corpus update: `guarantee_ok.md` (PASS — brier / 0.90 / held-out-v1.csv) and `guarantee_break.md`
(FAIL — invalid metric `precision` + out-of-range threshold `1.50` + empty dataset) added.
Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `guarantee_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `guarantee_break.md` | FAIL (E-09) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 18/18 modules agree (Python == Rust == Elixir == Expected)`**

Draft-test mapping: G-03 (`metric = brier`, no dataset → malformed) is enforced by the
`dataset` non-empty check; G-02 (reproducible but below bound → report, not hard fail) remains
out of scope for v0.1 (reproducibility needs the external dataset runner).

---

## E-10 Evaluation Determinism (PROMOTED — extends Law VIII)

### Motivation

Law VIII (Temporal Determinism) bounds *when* things happen; numeric evaluation also needs
bounds on *how* values are produced. Two implementations with different float precision,
rounding modes, or unstable sorts produce different outputs for the same spec — a
cross-implementation consistency hole (Law XIII territory).

### Proposed rule

```md
Law VIII extension — Evaluation Determinism
模块若执行数值/排序计算，必须声明：
- precision: 数值精度（正整数，十进制位数）
- rounding: 舍入模式（round | floor | ceil | trunc）
- sort_stability: 排序稳定性（true | false）
Verifier 仅认证声明格式良好；实际精度由实现保证并接受交叉验证（Law XIII）。
```

### Verifier check

- Declaration well-formed: `precision` (positive integer), `rounding`
  (round|floor|ceil|trunc), `sort_stability` (true|false).
- Violations report `MalformedDeterminism(detail)`.

### Draft tests

| # | Scenario | Expect |
|---|----------|--------|
| D-01 | `precision: 0` | ❌ malformed (must be ≥1) |
| D-02 | `rounding: banker` | ❌ malformed |
| D-03 | `precision: 6`, `rounding: round`, `sort_stability: true` | ✅ |

### Adoption criteria

- [x] Declaration check enforced in all three verifiers
- [x] Cross-implementation numeric agreement run (Law XIII gate on float outputs) — `float_ok.md`, 21/21 agree

### Promotion record (2026-08-01) — PROMOTED (Law VIII extension)

E-10 is now enforced by all three verifiers at the **declaration** level: a module declaring
`## Determinism` must provide a well-formed `precision` (positive integer), `rounding`
(round|floor|ceil|trunc), and `sort_stability` (true|false). Violations report
`MalformedDeterminism(detail)`.

Corpus update: `eval_ok.md` (PASS — precision 6 / round / true) and `eval_break.md`
(FAIL — precision 0 / banker / maybe) added. Full run:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `eval_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |
| `eval_break.md` | FAIL (E-10) | FAIL | FAIL | FAIL | ✅ |

**`🏆 Consensus: 20/20 modules agree (Python == Rust == Elixir == Expected)`**

Follow-up (same day): **float literals added to all three evaluators** (`TVal::FNum` /
`fnum`), and `float_ok.md` (IEEE-exact decimals `0.5⊕0.25=0.75`, `0.125⊕0.875=1.0`) exercises
the cross-implementation numeric agreement run (adoption criteria 2). All three verifiers
agree bit-for-bit on these values:

| Module | Expected | Python | Rust | Elixir | Agree |
|--------|----------|--------|------|--------|-------|
| `float_ok.md` | PASS | PASS | PASS (3) | PASS (3/3) | ✅ |

**`🏆 Consensus: 21/21 modules agree (Python == Rust == Elixir == Expected)`**

Side effect noted: since `0.333333` is now a first-class float literal, the E-03 portability
corpus case was changed from a float string to a raw Map rendering
(`Map{scode → [p₁,p₂]}`, unparseable) to keep exercising UnportableAssertion.

---

*End of ΣLang Top-Level Rules — Extension Candidates (backlog)*
