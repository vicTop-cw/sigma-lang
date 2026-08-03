# ΣLang Tools

This directory contains reference implementations of ΣLang tools.

## Planned Tools

### `sigma-fmt`
Formats ΣLang MD files according to spec conventions.

```bash
sigma-fmt file.md          # format in place
sigma-fmt --check file.md  # CI mode (exit 1 if not formatted)
```

### `sigma-test`
Runs canonical tests for a ΣLang module.

```bash
sigma-test module.md
# ✅ 7/7 tests passed
```

### `sigma-pkg`
Package manager for ΣLang.

```bash
python3 tools/sigma-cli.py install math.base@1.0   # install std package
python3 tools/sigma-cli.py verify math.base        # run its verifier test set
python3 tools/sigma-cli.py list                     # list installed packages
python3 tools/sigma-cli.py search confidence        # search std/ + registry
python3 tools/sigma-cli.py fingerprint std/math.base.md  # show sha256
```

- Registry: `~/.sigma/registry.json` (version / path / sha256 fingerprint /
  exported modules / deps). Dependency resolution honors Iron Law VII —
  circular deps are rejected at install time.

### `sigma-verify`
The main Verifier binary.

```bash
sigma-verify spec.md
# 🏆 ALL CHECKS PASSED — ΣLang module certified
```

### `sigma-prove`
SMT-backed proof discharge for proof-carrying specs (spec_top_proofs.md).

```bash
python3 tools/sigma-prove.py corpus/proof_ok.md
#   proof_ok.md:
#     • P-01 structure OK
#     • ⊕: obligation generated → tools/_sigma_prove_out/proof_ok__⊕.smt2
#          (no SMT solver on PATH — unverified)
```

- Runs the P-01 structural check (Model/Invariant/Pre/Post) and emits SMT-LIB2
  obligations for each contract. Discharges via z3 when installed; degrades to
  "obligation generated (unverified)" otherwise. §SK operations (task_create /
  review_merge / contribution_score) get their own law obligations
  (`gen_sk_obligation`) — no Pre/Post needed.

### `sigma-runtime`
SocketKit audit runtime — runs the canonical business trace (task_create →
review_merge → contribution_score) against the §SK reference implementation and
emits a per-event ΣLang obligation log.

```bash
python3 tools/sigma-runtime.py          # human-readable audit log
python3 tools/sigma-runtime.py --json   # machine-readable audit log
# Audit: 10/10 obligations satisfied — trace is ΣLang-auditable
```

- Every event output is checked against the §SK laws from
  `spec/spec_p0_socketkit.md`; exit code 0 = all obligations satisfied.

## Implementation Status

| Tool | Language | Status |
|------|----------|--------|
| `sigma-verify` | Rust (reference) | ✅ `impl/verifier` (`sigma-verifier`) |
| `sigma-verify` | Python (prototype) | ✅ `verify_p0.py` |
| `sigma-verify` | Elixir | ✅ `impl/elixir_rt/sigma_verify.exs` |
| `sigma-prove` | Python | ✅ `sigma-prove.py` (SMT obligations; z3 optional) |
| `sigma-moonbit` | Python | ✅ `sigma-moonbit.py` (Proof → `.mbtp` translation bridge, 2026-08-01) |
| `sigma-pkg` | Python | ✅ `sigma-cli.py` (install/verify/list/search/fingerprint + registry + Iron Law VII, 2026-08-02) |
| `sigma-bootstrap` | Python | ✅ `sigma-bootstrap.py` (AI bootstrapping loop test: spec→impl→verify→pass, 2026-08-02) |
| `sigma-runtime` | Python | ✅ `sigma-runtime.py` (SocketKit audit trace → ΣLang obligation log, 2026-08-03) |
| `sigma-fmt` | Rust | 📋 Planned |
| `sigma-test` | Rust | 📋 Planned |
