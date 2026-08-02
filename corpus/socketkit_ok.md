# Module: socketkit_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」)
# Intent: verifier test set for the v0.13 SocketKit protocol (spec_p0_socketkit.md
# §SK) — task_create / review_merge / contribution_score must behave identically
# across Python / Rust / Elixir. Reuses the canonical expression patterns proven
# three-verifier consistent (⊕ ∈ ⊘ on lists / literals / ⊥ errors).

## Imports

```md
import core
import math.base
```

## Exports

```md
task_create
review_merge
contribution_score
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
| [1] ⊕ [1,2] | ⊥ ShapeError |

## Operation: review_merge (Review Merge)

### Signature

```md
review_merge : List⟨List⟨ℕ⟩⟩ → ℕ
Fingerprint: 0xF002
```

### Laws

```md
∀ o . review_merge(o) ≡ 0 ∨ review_merge(o) ≡ 1
∀ o . review_merge(o) ≡ review_merge(reverse(o))
```

### Tests

| Input | Output |
|-------|--------|
| 2 ∈ [1,2,3] | 1 |
| 5 ∈ [1,2,3] | 0 |
| 2 ∈ 3 | ⊥ TypeError |

## Operation: contribution_score (Contribution Score)

### Signature

```md
contribution_score : List⟨ℕ⟩ → ℕ
Fingerprint: 0xF003
```

### Laws

```md
∀ a . 0 ≤ contribution_score(a)
∀ a . contribution_score(a) ≡ contribution_score(a ⊕ [0])
```

### Tests

| Input | Output |
|-------|--------|
| 6 ⊘ 2 | 3 |
| 7 ⊘ 2 | 3.5 |
| 5 ⊘ 0 | ⊥ DivByZero |

## Functions

### encode_task

```md
encode_task : List⟨ℕ⟩ → ℕ
```

### encode_opinion

```md
encode_opinion : List⟨ℕ⟩ → ℕ
```

### encode_action

```md
encode_action : List⟨ℕ⟩ → ℕ
```
