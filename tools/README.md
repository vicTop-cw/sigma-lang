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
# ✅ 12/12 tests passed
```

### `sigma-pkg`
Package manager for ΣLang.

```bash
sigma-pkg install finance.base@1.0
sigma-pkg publish my-pack.md
sigma-pkg verify my-pack.md
sigma-pkg deps my-project.md
```

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
  "obligation generated (unverified)" otherwise.

## Implementation Status

| Tool | Language | Status |
|------|----------|--------|
| `sigma-verify` | Rust (reference) | ✅ `impl/verifier` (`sigma-verifier`) |
| `sigma-verify` | Python (prototype) | ✅ `verify_p0.py` |
| `sigma-verify` | Elixir | ✅ `impl/elixir_rt/sigma_verify.exs` |
| `sigma-prove` | Python | ✅ `sigma-prove.py` (SMT obligations; z3 optional) |
| `sigma-moonbit` | Python | ✅ `sigma-moonbit.py` (Proof → `.mbtp` translation bridge, 2026-08-01) |
| `sigma-pkg` | Elixir | 📋 Planned |
| `sigma-fmt` | Rust | 📋 Planned |
| `sigma-test` | Rust | 📋 Planned |
