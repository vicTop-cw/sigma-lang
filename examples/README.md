# ΣLang Examples

This directory contains example ΣLang modules demonstrating various features.

## Files

### `tensor_ops.md`
Tensor operations with semantic laws and canonical tests.
Demonstrates: type definitions, operation contracts, algebraic laws.

### `demographics.md`
Surname statistics using the "everything → ℕ" encoding principle.
Demonstrates: encoding functions, grouping, aggregation, sorting by encoded values.

### `agent_protocol.md`
AI Agent protocol with confidence propagation and causal ordering.
Demonstrates: async operations, confidence combination, consensus.

## How to Read

Each example is a valid ΣLang module. The Verifier can check them:

```bash
# From repo root
python3 verify_p0.py
```

## Adding Examples

1. Create a new `.md` file
2. Follow the structure: imports → types → operations → laws → tests
3. Ensure all symbols have fingerprints
4. Include at least one canonical test per operation
5. Run the verifier
