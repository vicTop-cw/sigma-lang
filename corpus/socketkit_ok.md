# Module: socketkit_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」)
# Intent: verifier test set for the v0.13+ SocketKit protocol (spec_p0_socketkit.md
# §SK) — the full MVP flow (task_create → accept_task → task_submit → task_accept),
# contribution (贡献制), credit (契分制) and growth-phase review must behave
# identically across Python / Rust / Elixir. The Tests exercise the §SK operations
# as real function calls, so the consensus gate (Law XIII) verifies the app
# behavior itself, not just spec-expression aliases.

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
quota_new
quota_use
quota_reset
points_new
points_hold
points_release
points_withdraw
badge_level
badge_issue
dispute_review
team_create
team_join
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

## Operation: quota_new (Quota Creation)

### Signature

```md
quota_new : ℕ → List⟨ℕ⟩
Fingerprint: 0xF008
```

### Laws

```md
∀ q . 0 ≤ index(q, 1) ≤ index(q, 0)
```

### Tests

| Input | Output |
|-------|--------|
| quota_new(50) | [50,50] |
| quota_new(0) | [0,0] |
| quota_new(-5) | ⊥ TypeError |

## Operation: quota_use (Quota Use)

### Signature

```md
quota_use : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF009
```

### Laws

```md
∀ q a . index(q, 1) ≥ a ⇒ index(quota_use(q, a), 1) ≡ index(q, 1) − a
```

### Tests

| Input | Output |
|-------|--------|
| quota_use(quota_new(50), 20) | [50,30] |
| quota_use(quota_new(50), 50) | [50,0] |
| quota_use(quota_new(50), 60) | ⊥ QuotaExhausted |

## Operation: quota_reset (Quota Reset)

### Signature

```md
quota_reset : List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xF00A
```

### Laws

```md
∀ q . quota_reset(q) ≡ [index(q, 0), index(q, 0)]
```

### Tests

| Input | Output |
|-------|--------|
| quota_reset(quota_use(quota_new(50), 20)) | [50,50] |
| quota_reset(quota_new(50)) | [50,50] |
| quota_reset(5) | ⊥ TypeError |

## Operation: points_new (Points Creation)

### Signature

```md
points_new : → List⟨ℕ⟩
Fingerprint: 0xF00B
```

### Laws

```md
points_new() ≡ [0, 0]
```

### Tests

| Input | Output |
|-------|--------|
| points_new() | [0,0] |
| points_new(5) | ⊥ TypeError |

## Operation: points_hold (Points Hold)

### Signature

```md
points_hold : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00C
```

### Laws

```md
∀ p x . index(points_hold(p, x), 0) ≡ index(p, 0) + x
```

### Tests

| Input | Output |
|-------|--------|
| points_hold(points_new(), 100) | [100,0] |
| points_hold(points_new(), 0) | [0,0] |
| points_hold(5, 100) | ⊥ TypeError |

## Operation: points_release (Points Release)

### Signature

```md
points_release : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00D
```

### Laws

```md
∀ p x . index(p, 0) ≥ x ⇒ index(points_release(p, x), 1) ≡ index(p, 1) + x
```

### Tests

| Input | Output |
|-------|--------|
| points_release(points_hold(points_new(), 100), 100) | [0,100] |
| points_release(points_hold(points_new(), 50), 50) | [0,50] |
| points_release(points_new(), 10) | ⊥ InsufficientEscrow |

## Operation: points_withdraw (Points Withdraw)

### Signature

```md
points_withdraw : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00E
```

### Laws

```md
∀ p x . index(p, 1) ≥ x ⇒ index(points_withdraw(p, x), 1) ≡ index(p, 1) − x
```

### Tests

| Input | Output |
|-------|--------|
| points_withdraw(points_release(points_hold(points_new(), 100), 100), 40) | [0,60] |
| points_withdraw([0,100], 100) | [0,0] |
| points_withdraw(points_new(), 10) | ⊥ InsufficientPoints |

## Operation: badge_level (Badge Level)

### Signature

```md
badge_level : ℕ → ℕ
Fingerprint: 0xF00F
```

### Laws

```md
∀ s . 0 ≤ badge_level(s) ≤ 3
∀ s . badge_level(s) ≤ badge_level(s + 100)
```

### Tests

| Input | Output |
|-------|--------|
| badge_level(0) | 0 |
| badge_level(150) | 1 |
| badge_level(450) | 2 |
| badge_level(900) | 3 |
| badge_level([5]) | ⊥ TypeError |

## Operation: badge_issue (Badge Issue)

### Signature

```md
badge_issue : ℕ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF010
```

### Laws

```md
∀ v u s . v ≥ 1000 ⇒ index(badge_issue(v, u, s), 2) ≡ badge_level(s)
∀ v u s . v ≥ 1000 ⇒ 0 ≤ index(badge_issue(v, u, s), 2) ≤ 3
∀ v u s . v < 1000 ⇒ badge_issue(v, u, s) ≡ ⊥ AuthError
```

### Tests

| Input | Output |
|-------|--------|
| badge_issue(1001, 3, 105) | [1001,3,1] |
| badge_issue(1002, 3, 450) | [1002,3,2] |
| badge_issue(999, 3, 105) | ⊥ AuthError |

## Operation: dispute_review (Dispute Review)

### Signature

```md
dispute_review : List⟨List⟨ℕ⟩⟩ → ℕ
Fingerprint: 0xF011
```

### Laws

```md
∀ e . dispute_review(e) ≡ 0 ∨ dispute_review(e) ≡ 1
∀ e . dispute_review(e) ≡ dispute_review(reverse(e))
```

### Tests

| Input | Output |
|-------|--------|
| dispute_review([[1,1,3],[2,1,2]]) | 1 |
| dispute_review([[1,0,5],[2,1,2]]) | 0 |
| dispute_review(3) | ⊥ TypeError |

## Operation: team_create (Team Create)

### Signature

```md
team_create : ℕ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF012
```

### Laws

```md
∀ o k c . c ≥ 1 ⇒ index(team_create(o, k, c), 2) ≡ 1
∀ o k c . c ≥ 1 ⇒ index(team_create(o, k, c), 2) ≤ index(team_create(o, k, c), 3)
```

### Tests

| Input | Output |
|-------|--------|
| team_create(7, 0, 3) | [7,0,1,3] |
| team_create(3, 1, 2) | [3,1,1,2] |
| team_create(7, 0, 0) | ⊥ TypeError |

## Operation: team_join (Team Join)

### Signature

```md
team_join : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF013
```

### Laws

```md
∀ t m . index(t, 2) < index(t, 3) ⇒ index(team_join(t, m), 2) ≡ index(t, 2) + 1
∀ t m . index(t, 2) ≥ index(t, 3) ⇒ team_join(t, m) ≡ ⊥ TeamFull
```

### Tests

| Input | Output |
|-------|--------|
| team_join(team_create(7, 0, 3), 5) | [7,0,2,3] |
| team_join(team_create(7, 0, 3), 5) | [7,0,2,3] |
| team_join([7,0,2,2], 5) | ⊥ TeamFull |

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

### encode_quota

```md
encode_quota : List⟨ℕ⟩ → ℕ
```

### encode_points

```md
encode_points : List⟨ℕ⟩ → ℕ
```
