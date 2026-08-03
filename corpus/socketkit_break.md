# Module: socketkit_break
# Version: 1.0.0
# Expected: FAIL (E-02 — No Negative Test)
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」)
# Intent: negative counterpart of socketkit_ok.md — task_create declares
# fingerprint, laws, and success tests but NO negative (⊥/error-path) test,
# so Law XIV (E-02) must reject it identically across Python / Rust / Elixir.

## Imports

```md
import core
import math.base
```

## Exports

```md
task_create
```

## Operation: task_create (Task Create)

### Signature

```md
task_create : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF001
```

### Laws

```md
∀ a b . 0 ≤ task_create(a, b)
∀ a b . index(task_create(a, b), 2) ≡ 0
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |

> E-02: no ⊥ (error-path) test present — a negative test is mandatory.

## Functions

### encode_task

```md
encode_task : List⟨ℕ⟩ → ℕ
```
