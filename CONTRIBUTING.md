# Contributing to ΣLang

Thanks for helping build **ΣLang — the AI-Native Semantic Protocol**. This project is a
formal spec plus three independent verifier implementations; the correctness gate is
**Law XIII (Verifier Consensus)**.

## Ground Rules

1. **Spec first.** Normative change = RFC in `spec/spec_top_extensions.md` → promote →
   Verifier check → corpus test. Do not implement before the spec section exists.
2. **Three-verifier consensus.** Every feature must land in **all three** verifiers
   (Python `verify_consensus.py`, Rust `impl/verifier`, Elixir `impl/elixir_rt/sigma_verify.exs`).
   A feature that only one verifier implements is not done.
3. **Corpus is the gate.** Add a corpus module for every new check (see `corpus/`
   `# Expected: PASS/FAIL` convention). The CI gate is `python3 verify_consensus.py` —
   all modules must agree across the three verifiers.
4. **No hidden behavior.** Tests, laws, and signatures are normative; prose is not.

## Development Loop

```sh
# 1. Full test suite (must pass before and after your change)
python3 verify_consensus.py     # 35/35 modules, 3 verifiers agree (Law XIII gate)
python3 verify_p0.py            # 95/95 algorithmic checks (P0 soundness)

# 2. Proof backend (optional, requires z3 via pip install z3-solver)
python3 tools/sigma-prove.py corpus/proof_ok.md

# 3. Build the Rust verifier when touching impl/verifier
cd impl/verifier && cargo build && cd ../..
```

## Where Things Live

| Area | Path |
|------|------|
| English specs (normative) | `spec/` (foundations, top rules, proofs) |
| Chinese translations | `spec/zh/` (reference; English prevails) |
| Three verifiers | `verify_consensus.py`, `impl/verifier/`, `impl/elixir_rt/` |
| Proof tools | `tools/sigma-prove.py` (z3), `tools/sigma-moonbit.py` (MoonBit bridge) |
| Shared corpus | `corpus/` (PASS/FAIL × 3 verifiers) |
| Roadmap & backlog | `MASTER_PLAN.md` |

## Pull Request Checklist

- [ ] Spec section updated (or RFC filed) for normative changes
- [ ] All three verifiers implement the change
- [ ] Corpus module added/updated with correct `# Expected:`
- [ ] `verify_consensus.py` passes (35/35 agree)
- [ ] `verify_p0.py` passes (95/95)
- [ ] No compiler warnings (Rust `cargo build`, Elixir script, `py_compile`)

## License

MIT — see `LICENSE`.
