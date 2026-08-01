# ΣLang Implementations

This directory contains reference implementations of the ΣLang Verifier
and runtime components.

## Structure

```
impl/
├── verifier/            # Rust reference Verifier
│   ├── src/main.rs      # MD parser + Iron Laws + test evaluator + CLI
│   └── Cargo.toml
├── elixir_rt/           # Elixir/BEAM runtime + verifier
│   ├── lib/
│   ├── mix.exs
│   └── sigma_verify.exs # Standalone Elixir verifier (no deps)
└── python_verify.py     # Python prototype (algorithmic checks)
```

## Implementation Status

| Component | Language | Status |
|-----------|----------|--------|
| Algorithmic verification | Python | ✅ `verify_p0.py` (95/95) |
| MD parser | Rust | ✅ `parse_sigma_module` (both `## Operation:` and `###` styles) |
| Law checker (I–IV, XIII–XVI) | Rust | ✅ `check_*` in `src/main.rs` |
| Test evaluator | Rust | ✅ `eval_test` (⊕, ⊗, index, I₂, ⊥) |
| Verifier CLI | Rust | ✅ `sigma-verifier` (text/json output) |
| Verifier | Elixir | ✅ `sigma_verify.exs` (same contract) |
| Consensus gate | Python | ✅ `verify_consensus.py` (3 verifiers × 12 corpus modules, 12/12 agree) |
| Elixir runtime | Elixir | ✅ `Sigma` / `SigmaRT` (Result monad, confidence, clocks, I/O) |
| Race detector | Rust | 📋 Planned |
| Resource checker | Rust | 📋 Planned |

## The Python Prototype

`verify_p0.py` is the **algorithmic proof-of-concept**:
- Verifies all 95 tests across 4 P0 modules
- Implements Lamport clocks, vector clocks
- Implements Result monad laws
- Implements confidence operations
- Implements I/O effect system
- Implements capability system

Run it:

```bash
python3 verify_p0.py
```
