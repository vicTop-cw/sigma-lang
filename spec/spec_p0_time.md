# §T — Time & Causal Order Model

> **Status**: P0 — Foundational (without this, ΣLang cannot express Agents)
> **Depends**: core@1.0
> **Fingerprint prefix**: `0xT000`–`0xT0FF`

---

## T.1 Motivation

AI Agents exist in time. They:
- Send messages and wait for replies
- Retry failed operations
- Race against deadlines
- Coordinate across distributed nodes

A language for AI **must** define:
- What "before" and "after" mean
- When two events are concurrent
- What "timeout" and "retry" guarantee
- How to prove a system is race-free

Without this module, `⏳` (async) is decoration, not semantics.

---

## T.2 Core Concepts

### T.2.1 Event

```md
Event : Type
```

An **Event** is an indivisible occurrence. It has:
- A unique identity `eid : ℕ`
- A logical timestamp `ltime : ℕ`
- A vector clock `vclock : ℕ^∞`
- An effect tag `effect : EffectTag`

### T.2.2 Timeline

```md
Timeline : Type ≝ ℕ → Event
```

A timeline is a sequence of events indexed by logical time.

### T.2.3 EffectTag

```md
EffectTag : Type ≝ {
  Pure,        # no observable effect
  IO,          # input/output
  Comm(String),# communication on channel
  Spawn,       # create new agent
  Die          # agent termination
}
```

---

## T.3 Time Primitives

| Glyph | Name | Type | Fingerprint | Meaning |
|-------|------|------|-------------|---------|
| `⏰` | Now | `Unit → Time` | `0xT001` | Current logical time |
| `⏳` | Await | `Future⟨T⟩ → T` | `0xT002` | Block until ready |
| `⏱` | Deadline | `Time → Effect` | `0xT003` | Absolute timeout |
| `⌛` | Duration | `Time × Time → ℕ` | `0xT004` | Time difference |
| `→ᵢₒ` | Causal order | `Event × Event → 𝔹` | `0xT005` | Happens-before |
| `∥ᵢₒ` | Concurrent | `Event × Event → 𝔹` | `0xT006` | No causal relation |
| `clock` | Logical clock | `Agent → ℕ` | `0xT007` | Lamport timestamp |
| `vc` | Vector clock | `Agent → ℕ^∞` | `0xT008` | Causal history |
| `tick` | Advance clock | `Agent → Effect` | `0xT009` | Increment logical time |
| `timeout` | Timeout wrapper | `Effect × ℕ → Result⟨T, TimeoutErr⟩` | `0xT00A` | Bounded wait |
| `retry` | Retry wrapper | `Effect × ℕ → Effect` | `0xT00B` | Retry n times |
| `race` | Race two effects | `Effect × Effect → Effect` | `0xT00C` | First to complete wins |
| `after` | Delay | `Effect × ℕ → Effect` | `0xT00D` | Delay by n ticks |
| `periodic` | Periodic | `Effect × ℕ → Effect` | `0xT00E` | Every n ticks |

---

## T.4 Causal Order (Happens-Before)

### T.4.1 Definition

```md
## Causal Order →ᵢₒ

### Axiom (irreflexivity)
∀ e . ¬(e →ᵢₒ e)

### Axiom (transitivity)
∀ a b c . a →ᵢₒ b ∧ b →ᵢₒ c ⇒ a →ᵢₒ c

### Axiom (antisymmetry)
∀ a b . a →ᵢₒ b ⇒ ¬(b →ᵢₒ a)

### Rule (message send → receive)
∀ send recv . send_msg(m) →ᵢₒ recv_msg(m)

### Rule (same-agent ordering)
∀ e₁ e₂ : same_agent(e₁, e₂) ∧ ltime(e₁) < ltime(e₂)
  ⇒ e₁ →ᵢₒ e₂
```

### T.4.2 Vector Clock Encoding

```md
## Vector Clock Update Rules

### Initial
vc_init(a) ≝ λx. if x ≡ a then 1 else 0

### Local event
vc_local(vc) ≝ vc[a ↦ vc(a) + 1]  where a = current_agent

### Send
vc_send(vc) ≝ vc_local(vc)

### Receive
vc_receive(vc_local, vc_remote) ≝
  λx. max(vc_local(x), vc_remote(x))  then local +1

### Causal comparison
a →ᵢₒ b ⇔ vc(a) < vc(b)  (component-wise ≤, and strictly < somewhere)
```

### T.4.3 Concurrent Events

```md
## Concurrency
∥ᵢₒ(a, b) ≝ ¬(a →ᵢₒ b) ∧ ¬(b →ᵢₒ a) ∧ ¬(a ≡ b)
```

---

## T.5 Timeout & Retry Semantics

### T.5.1 Timeout

```md
## timeout : Effect × ℕ → Result⟨T, TimeoutErr⟩

### Definition
timeout(eff, n) ≝
  race(
    eff,
    after(raise(TimeoutErr), n)
  )

### Laws
∀ eff n . timeout(eff, 0) ≡ err(TimeoutErr)

∀ eff . ∃ t . eff completes in t ticks
  ⇒ timeout(eff, t+1) ≡ ok(result)

∀ eff . ¬∃ t . eff completes in ≤ n ticks
  ⇒ timeout(eff, n) ≡ err(TimeoutErr)
```

### T.5.2 Retry

```md
## retry : Effect × ℕ → Effect

### Definition (recursive)
retry(eff, 0) ≝ eff
retry(eff, n+1) ≝
  eff; if failed then retry(eff, n) else ok

### Laws
retry(eff, 0) ≡ eff

∀ eff . deterministic(eff) ∧ failed(eff)
  ⇒ retry(eff, n) fails for all n

retry(idempotent(eff), n) ≡ eff  (if eff succeeds once)
```

### T.5.3 Race

```md
## race : Effect × Effect → Effect

### Definition
race(eff₁, eff₂) ≝ first to complete (by real wall-clock)

### Laws
∀ a b . deterministic(a) ∧ deterministic(b)
  ⇒ race(a, b) ≡ a  (if a always faster)

race(a, b) ≡ race(b, a)  # commutative (idealized)
```

> ⚠️ **Note**: `race` is the only non-deterministic primitive.
> Verifier treats it as: "result ∈ {result(a), result(b)}".

---

## T.6 Agent Lifecycle

```md
## Spawn
spawn : Agent → Effect
Postcondition: new agent exists with fresh timeline

## Die
die : Agent → Effect
Postcondition: agent's timeline ends

## Join
join : Agent → Effect
Postcondition: waits until agent dies

## Link
link : Agent × Agent → Effect
Postcondition: if parent dies, child dies (supervision)
```

### Supervision Tree Laws

```md
## Supervision (Erlang-style)
∀ parent child . linked(parent, child)
  ⇒ child_dies ⇒ parent_notified
  ⇒ parent_dies ⇒ child_dies

## No orphaned agents
∀ a . ∃! p . parent(p, a)  (except root)
```

---

## T.7 Race-Freedom Verification

### T.7.1 Definition

```md
## Race-Free Program

A program is race-free iff:
∀ e₁ e₂ . access_same_resource(e₁, e₂)
          ∧至少一个 write(e₁) ∨ write(e₂)
          ⇒ e₁ →ᵢₒ e₂ ∨ e₂ →ᵢₒ e₁
```

### T.7.2 Verifier Algorithm

```rust
fn check_race_free(program: &Program) -> Result<(), RaceError> {
    let events = extract_events(program);
    let ordering = compute_happens_before(events);

    for e1 in &events {
        for e2 in &events {
            if accesses_same_resource(e1, e2)
                && (is_write(e1) || is_write(e2))
                && !ordering.happens_before(e1, e2)
                && !ordering.happens_before(e2, e1)
            {
                return Err(RaceError::PotentialRace {
                    event1: e1.id,
                    event2: e2.id,
                    resource: e1.resource,
                });
            }
        }
    }
    Ok(())
}
```

---

## T.8 Canonical Tests

| Input | Expected |
|-------|----------|
| `timeout(ok(42), 5)` with instant OK | `ok(42)` |
| `timeout(sleep(10), 3)` | `err(TimeoutErr)` |
| `retry(fail_then_succeed, 3)` | succeeds |
| `retry(always_fail, 3)` | fails after 3 attempts |
| Two events on same agent, t1<t2 | e1 →ᵢₒ e2 |
| Two events on different agents, no msg | ∥ᵢₒ(e1, e2) |
| `race(a, b)` where a=1tick, b=5tick | result = a's result |

---

## Implementation Checklist (for AI)

### To pass this module, implement exactly these

1. `LamportClock` — `tick() -> ℕ`, `send(msg) -> (msg, ℕ)`, `recv(msg, remote_t) -> msg` with `t := max(t, remote_t) + 1`  [T-01]
2. `VectorClock` — `tick()`, `send() -> ℕⁿ`, `recv(remote_v)` with pointwise `max` then local increment; causal `<` and `concurrent(other)`  [T-02]
3. `timeout(eff, deadline, actual) -> ok(v) | err(TimeoutErr)` — ok iff `actual ≤ deadline` (Law VIII)  [T-03]
4. `retry(eff, max_attempts, fail_times)` — attempt `i` succeeds once `i ≥ fail_times`, else `err(ExhaustedRetries)`  [T-04]
5. `race(results, times)` — pick the result of the fastest participant  [T-05]
6. `happens_before(e1_time, e2_time, same_agent, msg_sent) -> bool` — same-agent order or message causality  [T-06]
7. `has_cycle(graph) -> bool` — DFS cycle scan for deadlock detection  [T-07]

Reference implementation: `impl/python/sigma_core.py` (§T), self-check via `python3 impl/python/sigma_core.py`.

### What NOT to implement
- Do NOT assume a monotonic wall clock; logical time is sufficient.
- Do NOT implement wall-clock synchronization or a real scheduler.
- Do NOT add performance heuristics — the module is about causal semantics only.

---

## T.9 Iron Law for Time Module

> **Law VIII (Temporal Determinism)**:  
> Any program using `⏳`, `race`, or `timeout` MUST declare  
> its expected timing bounds. Undeclared timing = Verifier rejection.

```md
## Timing Contract (mandatory for async code)
timing_contract {
  max_latency: 1000 ticks,
  max_retries: 3,
  timeout_budget: 5000 ticks,
  deadline_miss_policy: "fail_fast"  # or "degrade" or "retry"
}
```
