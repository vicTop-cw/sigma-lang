# Module: socketkit_quota_break
# Version: 1.0.0
# Expected: FAIL (E-02 — No Negative Test)
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」— quota system)
# Intent: negative counterpart of socketkit_quota_ok.md — quota_new declares
# fingerprint, laws, and success tests but NO negative (⊥/error-path) test,
# so Law XIV (E-02) must reject it identically across Python / Rust / Elixir.
# Created at v0.57 (corpus expansion).

## Imports

```md
import core
```

## Exports

```md
quota_new
```

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

> E-02: no ⊥ (error-path) test present — a negative test is mandatory.
