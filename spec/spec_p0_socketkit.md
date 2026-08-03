# §SK — SocketKit Protocol: Auditable App Behavior

> **Status**: P0 — Promoted via RFC → spec section → Verifier check → tests (MASTER_PLAN §6.2)
> **Depends**: core@1.0, error@1.0, math.base@1.0
> **Fingerprint prefix**: `0xF000`–`0xF0FF`
> **Motivation**: 「来找茬」App business logic must be **mathematically auditable** —
> the MVP flow (post → claim → submit → accept), contribution scoring, and credit
> scoring are defined as ΣLang semantics verified identically across Python / Rust / Elixir.
> Semantics aligned to the product requirements doc (`D:\Desktop\来找茬_需求文档.md` v1.0).

---

## SK.1 Motivation

「来找茬」 is a peer-review marketplace. Its MVP core flow (需求文档 §五) is:

- **Post a task**: an author (受茬人) posts a demand with a bounty (赏金, may be 0).
- **Claim a task**: a hunter (找茬人) claims the task; work is in progress.
- **Submit work**: the hunter submits the deliverable.
- **Accept / reject**: the author confirms completion (受茬人确认完成).

Two score systems (需求文档 §四):

- **Contribution** (贡献制): post / complete / find bugs / invite / share cost → points.
- **Credit** (契分制): base 100, completion +5 per order, breach ×0.7.

Without ΣLang semantics, these behaviors are opaque business code. With them, every
post / claim / submit / accept / score is a checkable ΣLang obligation:

```md
- Task posting:       task_create(author, bounty) → Task
- Task claiming:      accept_task(task, hunter) → Task
- Work submission:    task_submit(task) → Task
- Acceptance:         task_accept(task) → Task
- Contribution:       contribution_score(actions[]) → points
- Review resolution:  review_merge(opinions[]) → decision   # growth-phase (核验师)
- Credit scoring:     credit_score(events[]) → credit
```

> **review_merge 定位（v0.17 修正）**: MVP 验收是受茬人单人确认（`task_accept`）。
> `review_merge`（多人加权意见合并）属于增长期核验师/督导评审场景，保留为独立操作，
> 不再承担 MVP 验收职责。

---

## SK.2 Core Types

```md
Author   : Type           # 受茬人 identity (encoded to ℕ)
Hunter   : Type           # 找茬人 identity (encoded to ℕ)
Bounty   : Type ≝ ℕ       # 赏金, must be ≥ 0 (可为 0)
Status   : Type ≝ ℕ       # 0=open · 1=in_progress · 2=pending_review · 3=completed
Task     : List⟨ℕ⟩        # [author_id, bounty, status, hunter_id]  (hunter 0 = unclaimed)
Opinion  : List⟨ℕ⟩        # [reviewer_id, vote, weight]
Decision : Type ≝ ℕ       # 1 = accept, 0 = reject
Action   : List⟨ℕ⟩        # [actor_id, kind, delta]
Event    : List⟨ℕ⟩        # [kind, count] — credit events (0=complete, 1=breach)
Points   : Type ≝ ℕ       # contribution score, must be ≥ 0
Credit   : Type ≝ ℕ       # credit score, must be ≥ 0
```

**Task 状态机**（对齐 MVP 状态流：待接单 → 进行中 → 待验收 → 已完成）:

```md
0 = open            (task_create)
1 = in_progress     (accept_task)
2 = pending_review  (task_submit)
3 = completed       (task_accept)
```

---

## SK.3 Operations

### SK.3.1 task_create — Task Posting (发布需求)

```md
task_create : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩      # (author, bounty) → Task
Fingerprint: 0xF001
Definition: task_create(a, b) ≡ [a, b, 0, 0]  # status 0 = open, hunter 0 = unclaimed
```

**Laws**

```md
∀ a b . 0 ≤ task_create(a, b)               # bounty ≥ 0 (赏金可为 0)
∀ a b . index(task_create(a, b), 2) ≡ 0     # freshly created task is open
∀ a b . index(task_create(a, b), 3) ≡ 0     # freshly created task is unclaimed
```

**Tests**

| Input | Output |
|-------|--------|
| task_create(7, 100) | [7,100,0,0] |
| task_create(2, 0) | [2,0,0,0] |
| task_create(1, -5) | ⊥ BountyErr |

### SK.3.2 accept_task — Task Claiming (接单)

```md
accept_task : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩        # (task, hunter) → Task
Fingerprint: 0xF004
Definition: accept_task([a, b, 0, 0], h) ≡ [a, b, 1, h]
            # status 0 → 1 (in_progress), hunter recorded
```

**Laws**

```md
∀ t h . index(t, 2) ≡ 0 ⇒ index(accept_task(t, h), 2) ≡ 1     # claim moves to in_progress
∀ t h . index(t, 2) ≡ 0 ⇒ index(accept_task(t, h), 3) ≡ h     # hunter recorded
```

**Tests**

| Input | Output |
|-------|--------|
| accept_task(task_create(7, 100), 3) | [7,100,1,3] |
| accept_task(task_create(2, 0), 9) | [2,0,1,9] |
| accept_task([7,100,1,3], 5) | ⊥ StateError |

### SK.3.3 task_submit — Work Submission (提交成果)

```md
task_submit : List⟨ℕ⟩ → List⟨ℕ⟩            # task → Task
Fingerprint: 0xF005
Definition: task_submit([a, b, 1, h]) ≡ [a, b, 2, h]
            # status 1 → 2 (pending_review), hunter preserved
```

**Laws**

```md
∀ t . index(t, 2) ≡ 1 ⇒ index(task_submit(t), 2) ≡ 2     # submit moves to pending_review
∀ t . index(t, 2) ≡ 1 ⇒ index(task_submit(t), 3) ≡ index(t, 3)   # hunter preserved
```

**Tests**

| Input | Output |
|-------|--------|
| task_submit(accept_task(task_create(5, 50), 3)) | [5,50,2,3] |
| task_submit(accept_task(task_create(2, 0), 9)) | [2,0,2,9] |
| task_submit(task_create(5, 50)) | ⊥ StateError |

### SK.3.4 task_accept — Acceptance Confirmation (验收确认)

```md
task_accept : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩            # (task, caller) → Task
Fingerprint: 0xF006
Definition: task_accept([a, b, 2, h], c) ≡ [a, b, 3, h]  if c ≡ a
            # status 2 → 3 (completed) — 受茬人单人验收确认 (MVP)
            # 授权约束 (INV-2): 只有受茬人本人 (c ≡ a) 可验收自己的单，否则 ⊥ AuthError
```

**Laws**

```md
∀ t c . index(t, 2) ≡ 2 ⇒ index(task_accept(t, c), 2) ≡ 3     # accept moves to completed
∀ t c . index(t, 2) ≡ 2 ⇒ index(task_accept(t, c), 3) ≡ index(t, 3)   # hunter preserved
∀ t c . index(t, 2) ≡ 2 ∧ c ≢ index(t, 0) ⇒ task_accept(t, c) ≡ ⊥ AuthError   # INV-2 授权
```

**Tests**

| Input | Output |
|-------|--------|
| task_accept(task_submit(accept_task(task_create(5, 50), 3)), 5) | [5,50,3,3] |
| task_accept(task_submit(accept_task(task_create(2, 0), 9)), 2) | [2,0,3,9] |
| task_accept(task_submit(accept_task(task_create(5, 50), 3)), 9) | ⊥ AuthError |
| task_accept(task_create(5, 50), 5) | ⊥ StateError |

### SK.3.5 contribution_score — Contribution Calculation (贡献制)

```md
contribution_score : List⟨ℕ⟩ → ℕ            # actions[] → points
Fingerprint: 0xF003
Definition: contribution_score(a) ≡ fold ⊕ over action deltas, floored at 0
            # 贡献值终身累计，负数不参与分红 (需求文档 §四.3)
```

**Laws**

```md
∀ a . 0 ≤ contribution_score(a)             # points never negative
∀ a . contribution_score(a) ≡ contribution_score(a ⊕ [0])   # zero delta is neutral
```

**Tests**

| Input | Output |
|-------|--------|
| contribution_score([[1,1,3],[2,2,4]]) | 7 |
| contribution_score([[1,1,-5],[2,2,3]]) | 0 |
| contribution_score(5) | ⊥ TypeError |

### SK.3.6 review_merge — Review Resolution (增长期评审)

```md
review_merge : List⟨List⟨ℕ⟩⟩ → ℕ            # opinions[] → decision
Fingerprint: 0xF002
Definition: review_merge(os) ≡ 1 if weighted_accept(os) ≥ weighted_reject(os) else 0
            # 增长期核验师/督导多人评审场景 — MVP 验收走 task_accept (SK.3.4)
```

**Laws**

```md
∀ o . review_merge(o) ≡ 0 ∨ review_merge(o) ≡ 1      # decision is binary
∀ o . review_merge(o) ≡ review_merge(reverse(o))     # order-independent
```

**Tests**

| Input | Output |
|-------|--------|
| review_merge([[1,1,3],[2,1,2]]) | 1 |
| review_merge([[1,0,5],[2,1,2]]) | 0 |
| review_merge(3) | ⊥ TypeError |

### SK.3.7 credit_score — Credit Scoring (契分制)

```md
credit_score : List⟨List⟨ℕ⟩⟩ → ℕ            # events[] → credit
Fingerprint: 0xF007
Definition: credit_score(e) ≡ fold over events from base 100:
            #   kind 0 (complete): +5 per count
            #   kind 1 (breach):   ×0.7 per count (integer: ×7 ÷10, floor)
            # floored at 0 — 契分制: 基础 100 分, 违约 ×0.7, 每完成 1 单 +5 (需求文档 §四.4)
```

**Laws**

```md
∀ e . 0 ≤ credit_score(e)                   # credit never negative
credit_score([]) ≡ 100                      # base credit
credit_score([[0,1]]) ≡ 105                 # one completion: +5
credit_score([[1,1]]) ≡ 70                  # one breach: ×0.7 (100 → 70)
```

**Tests**

| Input | Output |
|-------|--------|
| credit_score([]) | 100 |
| credit_score([[0,1]]) | 105 |
| credit_score([[1,1]]) | 70 |
| credit_score([[1,1],[0,1]]) | 75 |
| credit_score([[1,2]]) | 49 |
| credit_score(5) | ⊥ TypeError |

### SK.3.8 Invariants — 状态机不变量（v0.18，业务规则固化）

不变量是**所有可达状态**都必须成立的业务规则。`sigma-prove` 将其作为独立义务
消解（PROVED = 定义满足不变量），`sigma-runtime` 在每次审计 trace 中逐条复核。

**INV-1 — 状态单调（状态只前进，不可后退）**

```md
∀ t . index(t, 2) ∈ {0,1,2} ⇒ index(accept_task(t, h), 2) ≥ index(t, 2)
∀ t . index(t, 2) ∈ {0,1,2} ⇒ index(task_submit(t), 2) ≥ index(t, 2)
∀ t c . index(t, 2) ∈ {0,1,2} ⇒ index(task_accept(t, c), 2) ≥ index(t, 2)
```

**INV-2 — 终态不可变（completed 任务不可再被任何状态操作改变）**

```md
∀ t h . index(t, 2) ≡ 3 ⇒ accept_task(t, h) ≡ ⊥ StateError
∀ t . index(t, 2) ≡ 3 ⇒ task_submit(t) ≡ ⊥ StateError
∀ t c . index(t, 2) ≡ 3 ⇒ task_accept(t, c) ≡ ⊥ StateError
```

**INV-3 — 守恒（bounty 与 hunter 在状态流转中不变）**

```md
∀ t h . index(accept_task(t, h), 1) ≡ index(t, 1)      # bounty 不变
∀ t . index(task_submit(t), 1) ≡ index(t, 1)           # bounty 不变
∀ t c . index(task_accept(t, c), 1) ≡ index(t, 1)      # bounty 不变
∀ t . index(task_submit(t), 3) ≡ index(t, 3)           # hunter 保留
∀ t c . index(task_accept(t, c), 3) ≡ index(t, 3)      # hunter 保留
```

**INV-4 — 作者授权（只有受茬人本人可验收自己的单）**

```md
∀ t c . index(t, 2) ≡ 2 ∧ c ≢ index(t, 0) ⇒ task_accept(t, c) ≡ ⊥ AuthError
```

---

## SK.4 Encodings (Law II — encoding to ℕ for non-numeric returns)

```md
encode_task   : List⟨ℕ⟩ → ℕ     # Task → ℕ (Law II)
encode_opinion: List⟨ℕ⟩ → ℕ     # Opinion → ℕ (Law II)
encode_action : List⟨ℕ⟩ → ℕ     # Action → ℕ (Law II)
encode_event  : List⟨ℕ⟩ → ℕ     # Event → ℕ (Law II)
```

---

## SK.5 Adoption Trail

- **RFC**: MASTER_PLAN §6.2 (SocketKit Protocol, P3).
- **Spec section**: this document (§SK).
- **Semantics alignment (v0.17)**: aligned to `D:\Desktop\来找茬_需求文档.md` v1.0 —
  MVP flow (post/claim/submit/accept), 贡献制 (`contribution_score`), 契分制
  (`credit_score`); `review_merge` repositioned to growth-phase review (核验师).
- **Verifier check**: `corpus/socketkit_ok.md` — three-verifier consensus (Law XIII),
  Law I/II/III/IV, E-02 negative tests, E-03 portability, E-04 exports, E-06 shape.
- **Tests**: the corpus module carries the canonical tests above as real §SK calls.

> Promotion path reference: Phase 7 — RFC → spec section → Verifier check → tests.
