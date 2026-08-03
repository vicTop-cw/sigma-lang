# Module: socketkit_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」)
# Intent: verifier test set for the v0.13 SocketKit protocol (spec_p0_socketkit.md
# §SK) — task_create / review_merge / contribution_score must behave identically
# across Python / Rust / Elixir. The Tests exercise the §SK operations as real
# function calls (task_create / review_merge / contribution_score), so the
# consensus gate (Law XIII) verifies the app behavior itself, not just
# spec-expression aliases.

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
| task_create(7, 100) | [7,100,0] |
| task_create(2, 0) | [2,0,0] |
| task_create(1, -5) | ⊥ BountyErr |

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
| review_merge([[1,1,3],[2,1,2]]) | 1 |
| review_merge([[1,0,5],[2,1,2]]) | 0 |
| review_merge(3) | ⊥ TypeError |

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
| contribution_score([[1,1,3],[2,2,4]]) | 7 |
| contribution_score([[1,1,-5],[2,2,3]]) | 0 |
| contribution_score(5) | ⊥ TypeError |

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
