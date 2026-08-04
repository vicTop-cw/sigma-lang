# Module: socketkit_taskflow_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」— task flow)
# Intent: verifier test set for the §SK task-flow semantics (spec_p0_socketkit.md
# §SK.3.1–3.8) — task_create → accept_task → task_submit → task_accept, plus
# contribution (贡献制) and credit (契分制). The Tests exercise the §SK
# operations as real function calls, so the consensus gate (Law XIII) verifies
# the app behavior itself. Split from socketkit_ok at v0.57 (corpus expansion).

## Imports

```md
import core
import math.base
```

## Exports

```md
task_create
accept_task
task_submit
task_accept
review_merge
contribution_score
credit_score
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
| task_create(1, -5) | ⊥ BountyErr |

## Operation: accept_task (Task Claiming)

### Signature

```md
accept_task : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF004
```

### Laws

```md
∀ t h . index(t, 2) ≡ 0 ⇒ index(accept_task(t, h), 2) ≡ 1
∀ t h . index(t, 2) ≡ 0 ⇒ index(accept_task(t, h), 3) ≡ h
```

### Tests

| Input | Output |
|-------|--------|
| accept_task(task_create(7, 100), 3) | [7,100,1,3] |
| accept_task(task_create(2, 0), 9) | [2,0,1,9] |
| accept_task([7,100,1,3], 5) | ⊥ StateError |

## Operation: task_submit (Work Submission)

### Signature

```md
task_submit : List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xF005
```

### Laws

```md
∀ t . index(t, 2) ≡ 1 ⇒ index(task_submit(t), 2) ≡ 2
∀ t . index(t, 2) ≡ 1 ⇒ index(task_submit(t), 3) ≡ index(t, 3)
```

### Tests

| Input | Output |
|-------|--------|
| task_submit(accept_task(task_create(5, 50), 3)) | [5,50,2,3] |
| task_submit(accept_task(task_create(2, 0), 9)) | [2,0,2,9] |
| task_submit(task_create(5, 50)) | ⊥ StateError |

## Operation: task_accept (Acceptance Confirmation)

### Signature

```md
task_accept : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF006
```

### Laws

```md
∀ t c . index(t, 2) ≡ 2 ⇒ index(task_accept(t, c), 2) ≡ 3
∀ t c . index(t, 2) ≡ 2 ⇒ index(task_accept(t, c), 3) ≡ index(t, 3)
∀ t c . index(t, 2) ≡ 2 ∧ c ≢ index(t, 0) ⇒ task_accept(t, c) ≡ ⊥ AuthError
```

### Tests

| Input | Output |
|-------|--------|
| task_accept(task_submit(accept_task(task_create(5, 50), 3)), 5) | [5,50,3,3] |
| task_accept(task_submit(accept_task(task_create(2, 0), 9)), 2) | [2,0,3,9] |
| task_accept(task_submit(accept_task(task_create(5, 50), 3)), 9) | ⊥ AuthError |
| task_accept(task_create(5, 50), 5) | ⊥ StateError |

## Operation: review_merge (Review Resolution)

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

## Operation: contribution_score (Contribution Calculation)

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

## Operation: credit_score (Credit Scoring)

### Signature

```md
credit_score : List⟨List⟨ℕ⟩⟩ → ℕ
Fingerprint: 0xF007
```

### Laws

```md
∀ e . 0 ≤ credit_score(e)
credit_score([]) ≡ 100
credit_score([[0,1]]) ≡ 105
credit_score([[1,1]]) ≡ 70
```

### Tests

| Input | Output |
|-------|--------|
| credit_score([]) | 100 |
| credit_score([[0,1]]) | 105 |
| credit_score([[1,1]]) | 70 |
| credit_score([[1,1],[0,1]]) | 75 |
| credit_score([[1,2]]) | 49 |
| credit_score(5) | ⊥ TypeError |

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

### encode_event

```md
encode_event : List⟨ℕ⟩ → ℕ
```
