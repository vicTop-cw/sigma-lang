# §I — I/O Boundary & Effect Semantics

> **Status**: P0 — Foundational (without this, AI cannot interact with the world)
> **Depends**: core@1.0, error@1.0, time@1.0
> **Fingerprint prefix**: `0xI000`–`0xI0FF`

---

## I.1 Motivation

AI Agents must interact with the world:
- Read files
- Send HTTP requests
- Write to databases
- Print to terminals
- Communicate with other agents

But "side effects" are the #1 source of:
- Non-determinism
- Unverifiable behavior
- Cross-AI inconsistency

ΣLang's approach: **Effects are first-class types, not afterthoughts.**

---

## I.2 Effect System

### I.2.1 Effect Type

```md
Effect : Type   # the type of all effects

## Effect Tags (from §T)
Pure        : Effect   # no observable effect
IO(String)  : Effect   # input/output with resource
Comm(Ch)    : Effect   # communication on channel
Spawn       : Effect   # create agent
Die         : Effect   # terminate
Net(Addr)   : Effect   # network call
FS(Path)    : Effect   # file system
Time        : Effect   # time-dependent
Rand        : Effect   # random number
```

### I.2.2 Effect Composition

```md
## Effect Sum
⊕ₑ : Effect × Effect → Effect
IO(a) ⊕ₑ IO(b) ≝ IO(a+b)
IO(a) ⊕ₑ Comm(c) ≝ IO(a) + Comm(c)

## Effect Ordering
≤ₑ : Effect × Effect → 𝔹
Pure ≤ₑ IO    # Pure is "smaller" (safer)
Comm ≤ₑ IO    # Communication is weaker than full IO

## Effect Laws
∀ e . Pure ⊕ₑ e ≡ e
∀ e . e ⊕ₑ e ≡ e          # idempotent
∀ a b c . (a⊕ₑb)⊕ₑc ≡ a⊕ₑ(b⊕ₑc)  # associative
```

---

## I.3 Core I/O Primitives

| Glyph | Name | Type | Fingerprint | Meaning |
|-------|------|------|-------------|---------|
| `print` | Print | `String → IO Unit` | `0xI001` | Write to stdout |
| `readln` | Read line | `IO String` | `0xI002` | Read from stdin |
| `read_file` | Read file | `Path → IO Result⟨String,IOErr⟩` | `0xI003` | File read |
| `write_file` | Write file | `Path → String → IO Result⟨Unit,IOErr⟩` | `0xI004` | File write |
| `append_file` | Append | `Path → String → IO Result⟨Unit,IOErr⟩` | `0xI005` | File append |
| `delete_file` | Delete | `Path → IO Result⟨Unit,IOErr⟩` | `0xI006` | File delete |
| `exists` | Exists? | `Path → IO 𝔹` | `0xI007` | File exists check |
| `mkdir` | Make dir | `Path → IO Result⟨Unit,IOErr⟩` | `0xI008` | Create directory |
| `list_dir` | List | `Path → IO Result⟨List⟨Path⟩,IOErr⟩` | `0xI009` | Directory listing |
| `send` | Send msg | `Addr → Msg → IO Result⟨Unit,NetErr⟩` | `0xI00A` | Network send |
| `recv` | Recv msg | `Addr → IO Result⟨Msg,NetErr⟩` | `0xI00B` | Network receive |
| `connect` | Connect | `Addr → IO Result⟨Conn,NetErr⟩` | `0xI00C` | Open connection |
| `close` | Close | `Conn → IO Unit` | `0xI00D` | Close connection |
| `http_get` | HTTP GET | `URL → IO Result⟨Response,NetErr⟩` | `0xI00E` | HTTP request |
| `http_post` | HTTP POST | `URL → Body → IO Result⟨Response,NetErr⟩` | `0xI00F` | HTTP request |
| `now` | Current time | `IO Time` | `0xI010` | Wall clock |
| `rand` | Random | `IO ℝ` | `0xI011` | Random [0,1) |
| `rand_int` | Random int | `ℕ → ℕ → IO ℕ` | `0xI012` | Random [a,b] |
| `sleep` | Sleep | `ℕ → IO Unit` | `0xI013` | Block n ticks |
| `spawn_io` | Spawn | `IO() → IO AgentID` | `0xI014` | Create agent |
| `kill` | Kill agent | `AgentID → IO Unit` | `0xI015` | Terminate agent |
| `log` | Structured log | `Level → String → IO Unit` | `0xI016` | Logging |

---

## I.4 Effect-Typed Functions

### I.4.1 Syntax

```md
## Function with declared effects

f : A →ᵢₒ B    # f has IO effect
g : A → B       # g is pure (no effect)
h : A →ᶜ B      # h has communication effect

## Multiple effects
k : A →^{IO + Comm} B
```

### I.4.2 Effect Inference Rules

```md
## Pure function
f : A → B
∀ x:A . no_effect(f(x))

## IO function
f : A →ᵢₒ B
∃ x:A . has_effect(f(x), IO)

## Effect propagation
g : B →ᵢₒ C
f : A → B
g ∘ f : A →ᵢₒ C          # effect composes

## Pure composition preserves purity
f : A → B
g : B → C
g ∘ f : A → C             # still pure
```

### I.4.3 Effect Subsumption

```md
## If f is pure, it can be used where IO is expected
f : A → B
wrap_io : (A → B) → (A →ᵢₒ B)
wrap_io(f) ≝ λx. pure_io(f(x))

## But NOT vice versa
❌ g : A →ᵢₒ B  cannot be used as A → B
```

---

## I.5 I/O Laws

### I.5.1 Determinism of Pure Code

```md
## Pure functions: same input → same output, ALWAYS
∀ f:A→B . pure(f) ⇒
  ∀ x:A . f(x) ≡ f(x)  (referential transparency)

## IO functions: same input → possibly different output
∀ f:A→ᵢₒB . impure(f) ⇒
  ∃ x:A . f(x) ≠ f(x)  (non-deterministic)
```

### I.5.2 File System Laws

```md
## Write-then-read (causal)
write_file(p, s); read_file(p) ≡ ok(s)

## Delete-then-exists
delete_file(p); exists(p) ≡ ok(⊥)

## Append associativity
write_file(p, a); append_file(p, b)
  ≡ write_file(p, a⊕b)

## Overwrite
write_file(p, a); write_file(p, b)
  ≡ write_file(p, b)  # last write wins
```

### I.5.3 Network Laws

```md
## Send-then-recv (on same channel)
send(addr, msg); recv(addr) ≡ ok(msg)

## Connect-then-send
connect(addr); send(addr, msg) succeeds
  ⇒ was_connected(addr)

## Idempotency (GET)
http_get(url); http_get(url)
  ≡ http_get(url)  # GET is idempotent

## Non-idempotency (POST)
http_post(url, body); http_post(url, body)
  ≠ http_post(url, body)  # POST is NOT idempotent
```

### I.5.4 Logging Laws

```md
## Log never fails
∀ level msg . log(level, msg) ≡ ok(unit)

## Log ordering (same agent)
log(L, "a"); log(L, "b")
  ⇒ output order is "a" then "b"

## Log across agents: no ordering guarantee
log_agent₁(L, "a"); log_agent₂(L, "b")
  ⇒ output order undefined
```

---

## I.6 Resource Safety

### I.6.1 Resource Type

```md
Resource : Type   # file handle, connection, lock, etc.

## Resource lifecycle
open  : Path → IO Result⟨Resource,IOErr⟩
use   : Resource → (Handle → IO A) → IO A
close : Resource → IO Unit

## RAII-style (borrow checker for IO)
with_file : Path → (Handle → IO A) → IO Result⟨A,IOErr⟩
with_file(p, f) ≝
  do {
    h ← open(p);
    result ← f(h);
    close(h);
    return result
  }
```

### I.6.2 Resource Laws

```md
## Linearity: resource used exactly once
∀ r . (open(p) >>= f) ⇒ f called exactly once

## No double-close
close(r); close(r) ≡ err(AlreadyClosed)

## Use-after-close
use(r, f); close(r); use(r, g) ≡ err(UseAfterClose)

## Borrow during use
use(r, λh. do { x ← borrow(h); return f(x) })
  ⇒ r not available to others during borrow
```

### I.6.3 Verifier Check

```rust
fn check_resource_safety(program: &Program) -> Result<(), IOViolation> {
    let resources = track_resources(program);

    for r in resources {
        match r.lifecycle() {
            Lifecycle::DoubleClose => {
                return Err(IOViolation::DoubleClose(r.id));
            }
            Lifecycle::UseAfterClose => {
                return Err(IOViolation::UseAfterClose(r.id));
            }
            Lifecycle::NeverClosed => {
                return Err(IOViolation::ResourceLeak(r.id));
            }
            Lifecycle::Proper => continue,
        }
    }
    Ok(())
}
```

---

## I.7 Causal I/O (Integrating §T)

### I.7.1 Causal I/O Ordering

```md
## I/O events have causal order
∀ e₁ e₂ : IOEvent .
  e₁ →ᵢₒ e₂ ⇒ e₁ completes before e₂ starts

## Concurrent I/O
∀ e₁ e₂ . ∥ᵢₒ(e₁, e₂) ⇒ no guaranteed ordering

## Atomic I/O
∀ e . Atomic(e) ⇒ no other event interleaves with e
```

### I.7.2 Transaction Semantics

```md
## Transaction
txn : IO A → IO Result⟨A,TxnErr⟩

## ACID-lite properties
∀ t . Atomic(t)           # A
∀ t . Consistent(t)        # C
∀ t₁ t₂ . ∥ᵢₒ(t₁,t₂) ⇒ Serializable(t₁,t₂)  # I
∀ t . Durable(t) after commit  # D

## Rollback
txn(f) fails ⇒ all effects of f are undone
```

---

## I.8 FFI (Foreign Function Interface)

### I.8.1 Declaration Syntax

```md
## FFI Import
foreign import "rust"   sqrt : ℝ → ℝ
  ensures: result ≥ 0
  ensures: result² ≈ input (within 1e-10)
  effect: Pure

foreign import "python" torch_infer : Tensor → Tensor
  effect: IO
  ensures: output.shape ≡ input.shape
  timeout: 30000  # ms

foreign import "sql" query : String → IO Result⟨Rows, SqlErr⟩
  effect: IO + Comm
  ensures: query is read-only if starts with "SELECT"
  timeout: 5000

foreign import "system" exec : String → IO Result⟨String, ExecErr⟩
  effect: IO + FS + Net
  ensures: nothing (opaque)
  ⚠️ requires: capability(CmdExec)
```

### I.8.2 FFI Laws

```md
## Opaque functions: only contracts matter
∀ f:foreign . cannot_reason_about(f's internals)

## Pre-conditions must be checked
foreign import "x" f : A → B requires: pre(A)
caller must prove: pre(a) before calling f

## Post-conditions are enforced
foreign import "x" f : A → B ensures: post(B)
Verifier checks: post(f(a)) holds (via testing)

## Effects must be declared
foreign "x" f : A →ᵢₒ B
caller's effect type must include IO
```

### I.8.3 Capability System

```md
## Capabilities (permissions)
Capability : Type

ReadFile  : Capability
WriteFile : Capability
Network   : Capability
CmdExec   : Capability   # dangerous!
SpawnAgent: Capability

## Capability-checked FFI
foreign import "system" rm_rf : Path → IO Unit
  requires: capability(CmdExec) + capability(WriteFile)

## Granting capabilities
grant : Capability → Agent → Effect
revoke : Capability → Agent → Effect

## Capability laws
∀ c a . grant(c,a); revoke(c,a) ≡ unit
∀ c a . ¬has_cap(c,a) ⇒ foreign_call_requiring(c) fails
```

---

## I.9 Idempotency & Safety

### I.9.1 Idempotency Classification

```md
## Safe (idempotent) operations
safe_ops ≝ {
  http_get, read_file, exists, list_dir,
  recv, connect, now, rand, log
}

## Unsafe (non-idempotent) operations
unsafe_ops ≝ {
  http_post, http_put, http_delete,
  write_file, delete_file, send,
  exec, kill
}

## Classification law
∀ op . op ∈ safe_ops ⇒ retry(op, n) ≡ op
∀ op . op ∈ unsafe_ops ⇒ retry(op, n) may amplify effect
```

### I.9.2 Safe Retry Wrapper

```md
## Retry only safe operations
safe_retry : IO A → ℕ → IO Result⟨A,RetryErr⟩
safe_retry(op, n) ≝
  if op ∈ safe_ops
    then retry(op, n)
    else err(UnsafeRetryAttempted)
```

---

## I.10 Canonical Tests

| Expression | Expected |
|-----------|----------|
| `write_file("/tmp/x", "hello"); read_file("/tmp/x")` | `ok("hello")` |
| `write_file(p, "a"); write_file(p, "b"); read_file(p)` | `ok("b")` |
| `delete_file(p); exists(p)` | `ok(⊥)` |
| `http_get(url); http_get(url)` (same result) | ✅ idempotent |
| `http_post(url, b); http_post(url, b)` (different) | ✅ non-idempotent |
| `with_file(p, read)` (proper close) | resource not leaked |
| `grant(Network, a); revoke(Network, a)` | capability removed |
| `foreign call without capability` | `err(PermissionErr)` |
| `safe_retry(http_get(url), 3)` | succeeds or times out |
| `safe_retry(http_post(url,b), 3)` | `err(UnsafeRetry)` |

---

## I.11 Verifier Rules for I/O Module

```rust
impl Verifier {
    fn verify_io_effects(&self, program: &Program) -> Result<(), IOViolation> {
        // 1. Check effect types are declared
        for func in program.functions() {
            if func.has_io_calls() && !func.effect_type().includes(IO) {
                return Err(IOViolation::UndeclaredEffect {
                    func: func.name(),
                    missing: IO,
                });
            }
        }

        // 2. Check resource lifecycle
        self.check_resource_safety(program)?;

        // 3. Check capability requirements
        for call in program.foreign_calls() {
            for cap in call.required_capabilities() {
                if !program.has_capability(cap) {
                    return Err(IOViolation::MissingCapability {
                        call: call.name(),
                        capability: cap,
                    });
                }
            }
        }

        // 4. Check FFI contracts
        for ffi in program.ffi_declarations() {
            if !ffi.has_pre_condition() {
                self.warn(Warning::FFINoPreCondition(ffi.name()));
            }
            if !ffi.has_post_condition() {
                self.warn(Warning::FFINoPostCondition(ffi.name()));
            }
            if !ffi.has_timeout() {
                self.warn(Warning::FFINoTimeout(ffi.name()));
            }
        }

        // 5. Check idempotency annotations
        for retry in program.retry_calls() {
            if !retry.target().is_idempotent() {
                return Err(IOViolation::UnsafeRetry {
                    target: retry.target().name(),
                });
            }
        }

        Ok(())
    }
}
```

---

## I.12 Iron Law for I/O Module

> **Law X (Effect Transparency)**:
> Every function that performs I/O **must** declare its
> effect type. Undeclared effects = Verifier rejection.
>
> **Law XI (Capability Discipline)**:
> No foreign call may execute without its required
> capabilities being explicitly granted in the program.
>
> **Law XII (Resource Linearity)**:
> Every opened resource must be closed exactly once,
> or be passed to a `with_*` combinator.

---

## I.13 Non-Goals

```md
❌ This module does NOT provide:
  - GUI / rendering primitives
    → separate package: `ui.core`
  - Audio / video I/O
    → separate package: `media.io`
  - Direct hardware access
    → separate package: `sys.hw`
  - Process management (fork/exec/wait)
    → separate package: `sys.proc`
```
