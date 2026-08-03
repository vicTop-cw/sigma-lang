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

### SK.3.9 quota — 额度制 (需求文档 §四.1)

每人每月固定额度（发单 + 接单分开计算），月底清零不累计；可预支下月额度但必须
隔月才能再预支。额度 = 基础值 × 契分系数 × 活跃系数 × 违规惩罚。

```md
Quota    : List⟨ℕ⟩        # [monthly_limit, remaining]
quota_new   : ℕ → List⟨ℕ⟩     # monthly → Quota
Fingerprint: 0xF008
Definition: quota_new(m) ≡ [m, m]            # 本月额度 = 剩余额度
quota_use   : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩   # (quota, amount) → Quota
Fingerprint: 0xF009
Definition: quota_use([m, r], a) ≡ [m, r−a]  if a ≤ r，否则 ⊥ QuotaExhausted
quota_reset : List⟨ℕ⟩ → List⟨ℕ⟩       # quota → Quota（月底清零，恢复满额）
Fingerprint: 0xF00A
Definition: quota_reset([m, r]) ≡ [m, m]
```

**Laws**

```md
∀ q a . index(q, 1) ≥ a ⇒ index(quota_use(q, a), 1) ≡ index(q, 1) − a   # 扣减正确
∀ q . 0 ≤ index(q, 1) ≤ index(q, 0)                                    # 剩余 ∈ [0, 月额]
∀ q . quota_reset(q) ≡ [index(q, 0), index(q, 0)]                      # 月底清零恢复
```

**Tests**

| Input | Output |
|-------|--------|
| quota_new(50) | [50,50] |
| quota_use(quota_new(50), 20) | [50,30] |
| quota_reset(quota_use(quota_new(50), 20)) | [50,50] |
| quota_use(quota_new(50), 60) | ⊥ QuotaExhausted |

### SK.3.10 points — 积分制 (需求文档 §四.2)

1 积分 = ¥1，不可充值；积分状态：托管中（冻结）/ 可用（可提现）；每笔积分来源可追溯。

```md
Points    : List⟨ℕ⟩        # [escrow, available]
points_new   : → List⟨ℕ⟩            # → Points
Fingerprint: 0xF00B
Definition: points_new() ≡ [0, 0]             # 无托管、无可用
points_hold  : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩  # (points, amount) → Points
Fingerprint: 0xF00C
Definition: points_hold([e, a], x) ≡ [e+x, a]           # 冻结（托管中）
points_release : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩  # (points, amount) → Points
Fingerprint: 0xF00D
Definition: points_release([e, a], x) ≡ [e−x, a+x]  if x ≤ e，否则 ⊥ InsufficientEscrow
points_withdraw : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩  # (points, amount) → Points
Fingerprint: 0xF00E
Definition: points_withdraw([e, a], x) ≡ [e, a−x]  if x ≤ a，否则 ⊥ InsufficientPoints
```

**Laws**

```md
∀ p x . index(points_hold(p, x), 0) ≡ index(p, 0) + x          # 托管增加（冻结进 escrow）
∀ p x . index(points_hold(p, x), 1) ≡ index(p, 1)              # 可用不变（hold 不动 available）
∀ p x . index(p, 0) ≥ x ⇒ index(points_release(p, x), 1) ≡ index(p, 1) + x   # 释放入可用
∀ p . 0 ≤ index(p, 0) ∧ 0 ≤ index(p, 1)                       # 托管/可用非负
∀ p x . index(points_release(p, x), 0) + index(points_release(p, x), 1) ≡
        index(p, 0) + index(p, 1)                             # 释放守恒（escrow→available 总额不变）
```

**Tests**

| Input | Output |
|-------|--------|
| points_new() | [0,0] |
| points_hold(points_new(), 100) | [100,0] |
| points_release(points_hold(points_new(), 100), 100) | [0,100] |
| points_withdraw(points_release(points_hold(points_new(), 100), 100), 40) | [0,60] |
| points_release(points_new(), 10) | ⊥ InsufficientEscrow |
| points_withdraw(points_new(), 10) | ⊥ InsufficientPoints |

### SK.3.11 badge_level — 勋章制 (需求文档 §四.5)

铜→银→金→钻石四级，核验师签发，用于企业人才推荐。

```md
badge_level : ℕ → ℕ            # accumulated_score → badge (0=铜 1=银 2=金 3=钻石)
Fingerprint: 0xF00F
Definition: badge_level(s) ≡ 0  if s < 100
            badge_level(s) ≡ 1  if 100 ≤ s < 300
            badge_level(s) ≡ 2  if 300 ≤ s < 600
            badge_level(s) ≡ 3  if s ≥ 600
```

**Laws**

```md
∀ s . 0 ≤ badge_level(s) ≤ 3                      # 四级有界
∀ s . badge_level(s) ≤ badge_level(s + 100)       # 单调（分数越高勋章不降）
badge_level(0) ≡ 0                                # 起始铜牌
```

**Tests**

| Input | Output |
|-------|--------|
| badge_level(0) | 0 |
| badge_level(50) | 0 |
| badge_level(150) | 1 |
| badge_level(450) | 2 |
| badge_level(900) | 3 |

### SK.3.12 badge_issue — 核验师签发勋章 (需求文档 §八)

核验师（内部/外部）验证技能后为用户签发勋章，用于企业人才推荐。等级复用
`badge_level`（SK.3.11 铜银金钻四级）。只有授权核验师（verifier ≥ 1000，
内部员工/签约核验师编号段）可签发，否则 ⊥ AuthError。

```md
Badge     : List⟨ℕ⟩        # [verifier, user, level]
badge_issue : ℕ × ℕ × ℕ → List⟨ℕ⟩   # (verifier, user, score) → Badge
Fingerprint: 0xF010
Definition: badge_issue(v, u, s) ≡ [v, u, badge_level(s)]  if v ≥ 1000
            # 授权核验师按契分 s 为用户 u 签发勋章；否则 ⊥ AuthError
```

**Laws**

```md
∀ v u s . v ≥ 1000 ⇒ index(badge_issue(v, u, s), 2) ≡ badge_level(s)   # 等级正确
∀ v u s . v ≥ 1000 ⇒ 0 ≤ index(badge_issue(v, u, s), 2) ≤ 3           # 四级有界
∀ v u s . v < 1000 ⇒ badge_issue(v, u, s) ≡ ⊥ AuthError               # 授权核验师
```

**Tests**

| Input | Output |
|-------|--------|
| badge_issue(1001, 3, 105) | [1001,3,1] |
| badge_issue(1002, 3, 450) | [1002,3,2] |
| badge_issue(999, 3, 105) | ⊥ AuthError |

### SK.3.13 dispute_review — 督导处理纠纷 (需求文档 §三角色)

督导（增长期）专业处理纠纷。纠纷由双方提交证据（每条证据 = [weight, side]，
side 0 = 驳回方，1 = 支持方）；督导裁决 = 加权支持 ≥ 加权驳回 → 1，否则 0。
与 `review_merge`（核验师评审）同构，但语义场景为纠纷仲裁。

```md
dispute_review : List⟨List⟨ℕ⟩⟩ → ℕ        # evidence[] → decision
Fingerprint: 0xF011
Definition: dispute_review(e) ≡ 1 if weighted_support(e) ≥ weighted_reject(e) else 0
```

**Laws**

```md
∀ e . dispute_review(e) ≡ 0 ∨ dispute_review(e) ≡ 1     # decision is binary
∀ e . dispute_review(e) ≡ dispute_review(reverse(e))    # order-independent
```

**Tests**

| Input | Output |
|-------|--------|
| dispute_review([[1,1,3],[2,1,2]]) | 1 |
| dispute_review([[1,0,5],[2,1,2]]) | 0 |
| dispute_review(3) | ⊥ TypeError |

### SK.3.14 team_create / team_join — 团机制 (需求文档 §七)

受茬团（多人分摊赏金发需求）与找茬团（多人组团接单）。Team =
[owner, kind, size, capacity]（kind 0 = 受茬团，1 = 找茬团）。创始人为成员
（size 从 1 起）；加入需未满员，否则 ⊥ TeamFull。规则：单人受茬团不可对接
单人找茬团（防绕过，v0.30 team_share 验证）。

```md
Team     : List⟨ℕ⟩        # [owner, kind, size, capacity]
team_create : ℕ × ℕ × ℕ → List⟨ℕ⟩   # (owner, kind, capacity) → Team
Fingerprint: 0xF012
Definition: team_create(o, k, c) ≡ [o, k, 1, c]   if c ≥ 1
            # 创始人即成员 (size=1)；capacity ≥ 1，否则 ⊥ TypeError
team_join    : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩   # (team, member) → Team
Fingerprint: 0xF013
Definition: team_join([o, k, s, c], m) ≡ [o, k, s+1, c]  if s < c
            # 未满员则加入；满员 → ⊥ TeamFull
```

**Laws**

```md
∀ o k c . c ≥ 1 ⇒ index(team_create(o, k, c), 2) ≡ 1          # 创始人即成员
∀ o k c . c ≥ 1 ⇒ index(team_create(o, k, c), 2) ≤ index(team_create(o, k, c), 3)  # size ≤ capacity
∀ t m . index(t, 2) < index(t, 3) ⇒ index(team_join(t, m), 2) ≡ index(t, 2) + 1   # 加入 +1
∀ t m . index(t, 2) ≥ index(t, 3) ⇒ team_join(t, m) ≡ ⊥ TeamFull                 # 满员拒绝
```

**Tests**

| Input | Output |
|-------|--------|
| team_create(7, 0, 3) | [7,0,1,3] |
| team_create(3, 1, 2) | [3,1,1,2] |
| team_create(7, 0, 0) | ⊥ TypeError |
| team_join(team_create(7, 0, 3), 5) | [7,0,2,3] |
| team_join([7,0,2,2], 5) | ⊥ TeamFull |

### SK.3.15 team_share — 团内收益按贡献分配 (需求文档 §七)

找茬团 N 人分工完成任务后，收益按贡献比例分配（整数除法向下取整）。若
贡献总和为 0 则 ⊥ DivByZero。

```md
team_share : List⟨List⟨ℕ⟩⟩ × ℕ → List⟨List⟨ℕ⟩⟩   # (contribs[], reward) → shares[]
Fingerprint: 0xF014
Definition: team_share([[m₁,c₁],…,[mₙ,cₙ]], r) ≡ [[mᵢ, ⌊r·cᵢ/Σc⌋], …]
            # shareᵢ = floor(r · cᵢ / total)；total = Σ cᵢ
            # total = 0 → ⊥ DivByZero
```

**Laws**

```md
∀ c r . total(c) > 0 ⇒ Σ shares ≡ ≤ r                     # 不超发
∀ c r . total(c) > 0 ⇒ 每份 share ≥ 0                     # 份额非负
∀ c . total(c) ≡ 0 ⇒ team_share(c, r) ≡ ⊥ DivByZero      # 零贡献拒绝
```

**Tests**

| Input | Output |
|-------|--------|
| team_share([[3,2],[4,4]], 6) | [[3,2],[4,4]] |
| team_share([[3,1],[4,3]], 10) | [[3,2],[4,7]] |
| team_share([[3,0],[4,0]], 5) | ⊥ DivByZero |

---

## SK.4 Encodings (Law II — encoding to ℕ for non-numeric returns)

```md
encode_task   : List⟨ℕ⟩ → ℕ     # Task → ℕ (Law II)
encode_opinion: List⟨ℕ⟩ → ℕ     # Opinion → ℕ (Law II)
encode_action : List⟨ℕ⟩ → ℕ     # Action → ℕ (Law II)
encode_event  : List⟨ℕ⟩ → ℕ     # Event → ℕ (Law II)
encode_quota  : List⟨ℕ⟩ → ℕ     # Quota → ℕ (Law II)
encode_points : List⟨ℕ⟩ → ℕ     # Points → ℕ (Law II)
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

### SK.6 MVP 业务剧本（v0.21，端到端验收场景）

一次「来找茬」MVP 真实交易（受茬人 author=7 发单，找茬人 hunter=3 接单）的完整
ΣLang 调用序列。`sigma-runtime --story` 逐事件审计该剧本；每一步的定律/不变量
（INV-1 状态单调、INV-3 守恒、INV-4 作者授权、额度扣减、积分托管守恒）都必须成立。

```md
# 1. 开户额度      quota_new(50)                          → [50, 50]
# 2. 发布需求      task_create(7, 100)                    → [7, 100, 0, 0]
# 3. 扣减额度      quota_use([50, 50], 1)                 → [50, 49]
# 4. 赏金托管      points_hold(points_new(), 100)         → [100, 0]
# 5. 接单          accept_task([7, 100, 0, 0], 3)         → [7, 100, 1, 3]
# 6. 提交成果      task_submit([7, 100, 1, 3])            → [7, 100, 2, 3]
# 7. 验收确认      task_accept([7, 100, 2, 3], 7)         → [7, 100, 3, 3]
# 8. 释放赏金      points_release([100, 0], 100)          → [0, 100]
# 9. 找茬人提现    points_withdraw([0, 100], 100)         → [0, 0]
# 10. 契分奖励     credit_score([[0, 1]])                 → 105
# 11. 贡献累计     contribution_score([[3, 1, 10]])       → 10
# 12. 勋章升级     badge_level(105)                       → 1
```

**剧本不变量（每一步都必须满足）**

```md
INV-1  状态单调: 任务状态 0 → 1 → 2 → 3，只前进不后退
INV-3  守恒:     bounty 100 全程不变；积分 escrow→available 总额不变
INV-4  授权:     task_accept 的 caller 7 ≡ author 7（受茬人本人验收）
额度制:  quota_use 扣减正确，剩余 ∈ [0, 月额]
积分制:  points_release 释放入可用，可用非负
契分制:  完成 1 单 → 契分 100 → 105
勋章制:  badge_level(105) ≡ 1（银牌，score ≥ 100）
```
