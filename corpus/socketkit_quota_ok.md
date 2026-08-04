# Module: socketkit_quota_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」— quota system)
# Intent: verifier test set for the §SK.3.9 quota system (spec_p0_socketkit.md)
# — quota_new / quota_use / quota_reset. The Tests exercise the §SK operations
# as real function calls, so the consensus gate (Law XIII) verifies the app
# behavior itself. Split from socketkit_ok at v0.57 (corpus expansion).

## Imports

```md
import core
```

## Exports

```md
quota_new
quota_use
quota_reset
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

## Functions

### encode_quota

```md
encode_quota : List⟨ℕ⟩ → ℕ
```
