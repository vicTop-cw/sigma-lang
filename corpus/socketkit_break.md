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

## Operation: task_create (Task Posting)

### Signature

```md
task_create : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF001
```

### Laws

```md
∀ a b . 0 ≤ task_create(a, b)
∀ a b . index(task_create(a, b), 2) ≡ 0
∀ a b . index(task_create(a, b), 3) ≡ 0
```

### Tests

| Input | Output |
|-------|--------|
| task_create(7, 100) | [7,100,0,0] |
| task_create(2, 0) | [2,0,0,0] |

> E-02: no ⊥ (error-path) test present — a negative test is mandatory.

## Functions

### encode_task

```md
encode_task : List⟨ℕ⟩ → ℕ
```
