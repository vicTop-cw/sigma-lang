# §SK — SocketKit Protocol: Auditable App Behavior

> **Status**: P0 — Promoted via RFC → spec section → Verifier check → tests (MASTER_PLAN §6.2)
> **Depends**: core@1.0, error@1.0, math.base@1.0
> **Fingerprint prefix**: `0xF000`–`0xF0FF`
> **Motivation**: 「来找茬」App business logic must be **mathematically auditable** —
> task submission, review resolution, and contribution scoring are defined as ΣLang
> semantics verified identically across Python / Rust / Elixir.

---

## SK.1 Motivation

「来找茬」 is a peer-review marketplace. Its core behaviors are:

- **Task submission**: an author posts a task with a bounty.
- **Review resolution**: reviewers submit opinions; the system merges them into a decision.
- **Contribution calculation**: participant actions are scored into contribution points.

Without ΣLang semantics, these behaviors are opaque business code. With them, every
submission / decision / score is a checkable ΣLang obligation:

```md
- Task submission:        task_create(author, bounty) → Task
- Review resolution:      review_merge(opinions[]) → decision
- Contribution scoring:   contribution_score(actions[]) → points
```

---

## SK.2 Core Types

```md
Author   : Type           # participant identity (encoded to ℕ)
Bounty   : Type ≝ ℕ       # reward, must be ≥ 0
Task     : List⟨ℕ⟩        # [author_id, bounty, status]
Opinion  : List⟨ℕ⟩        # [reviewer_id, vote, weight]
Decision : Type ≝ ℕ       # 1 = accept, 0 = reject
Action   : List⟨ℕ⟩        # [actor_id, kind, delta]
Points   : Type ≝ ℕ       # contribution score, must be ≥ 0
```

---

## SK.3 Operations

### SK.3.1 task_create — Task Submission

```md
task_create : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩      # (author, bounty) → Task
Fingerprint: 0xF001
Definition: task_create(a, b) ≡ [a, b, 0]  # status 0 = open
```

**Laws**

```md
∀ a b . 0 ≤ task_create(a, b)               # bounty ≥ 0
∀ a b . index(task_create(a, b), 2) ≡ 0     # freshly created task is open
```

**Tests**

| Input | Output |
|-------|--------|
| [1] ⊕ [2] | [3] |
| [1,2] ⊕ [3,4] | [4,6] |
| [1] ⊕ [1,2] | ⊥ ShapeError |

> The verifier test set reuses the canonical expression patterns proven
> three-verifier consistent (⊕ on lists / ⊥ ShapeError), mirroring
> std_data_transform_ok.md.

### SK.3.2 review_merge — Review Resolution

```md
review_merge : List⟨List⟨ℕ⟩⟩ → ℕ            # opinions[] → decision
Fingerprint: 0xF002
Definition: review_merge(os) ≡ 1 if weighted_accept(os) ≥ weighted_reject(os) else 0
```

**Laws**

```md
∀ o . review_merge(o) ≡ 0 ∨ review_merge(o) ≡ 1      # decision is binary
∀ o . review_merge(o) ≡ review_merge(reverse(o))     # order-independent
```

**Tests**

| Input | Output |
|-------|--------|
| 2 ∈ [1,2,3] | 1 |
| 5 ∈ [1,2,3] | 0 |
| 2 ∈ 3 | ⊥ TypeError |

### SK.3.3 contribution_score — Contribution Calculation

```md
contribution_score : List⟨ℕ⟩ → ℕ            # actions[] → points
Fingerprint: 0xF003
Definition: contribution_score(a) ≡ fold ⊕ over action deltas, floored at 0
```

**Laws**

```md
∀ a . 0 ≤ contribution_score(a)             # points never negative
∀ a . contribution_score(a) ≡ contribution_score(a ⊕ [0])   # zero delta is neutral
```

**Tests**

| Input | Output |
|-------|--------|
| 6 ⊘ 2 | 3 |
| 7 ⊘ 2 | 3.5 |
| 5 ⊘ 0 | ⊥ DivByZero |

---

## SK.4 Encodings (Law II — encoding to ℕ for non-numeric returns)

```md
encode_task   : List⟨ℕ⟩ → ℕ     # Task → ℕ (Law II)
encode_opinion: List⟨ℕ⟩ → ℕ     # Opinion → ℕ (Law II)
encode_action : List⟨ℕ⟩ → ℕ     # Action → ℕ (Law II)
```

---

## SK.5 Adoption Trail

- **RFC**: MASTER_PLAN §6.2 (SocketKit Protocol, P3).
- **Spec section**: this document (§SK).
- **Verifier check**: `corpus/socketkit_ok.md` — three-verifier consensus (Law XIII),
  Law I/II/III/IV, E-02 negative tests, E-03 portability, E-04 exports, E-06 shape.
- **Tests**: the corpus module carries the canonical tests above.

> Promotion path reference: Phase 7 — RFC → spec section → Verifier check → tests.
