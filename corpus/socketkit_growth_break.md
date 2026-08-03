# Module: socketkit_growth_break
# Version: 1.0.0
# Expected: FAIL (E-02 — No Negative Test)
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」增长期)
# Intent: negative counterpart of socketkit_growth_ok.md — badge_issue declares
# fingerprint, laws, and success tests but NO negative (⊥/error-path) test,
# so Law XIV (E-02) must reject it identically across Python / Rust / Elixir.

## Imports

```md
import core
```

## Exports

```md
badge_issue
```

## Operation: badge_issue (Badge Issue)

### Signature

```md
badge_issue : ℕ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF010
```

### Laws

```md
∀ v u s . v ≥ 1000 ⇒ index(badge_issue(v, u, s), 2) ≡ badge_level(s)
```

### Tests

| Input | Output |
|-------|--------|
| badge_issue(1001, 3, 105) | [1001,3,1] |
| badge_issue(1002, 3, 450) | [1002,3,2] |

> E-02: no ⊥ (error-path) test present — a negative test is mandatory.
