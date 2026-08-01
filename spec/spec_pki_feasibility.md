# ΣLang Trust & Provenance — PKI Feasibility Study (E-08 S-01)

> **Status**: FEASIBILITY — research outcome, not yet normative.
> **Date**: 2026-08-01
> **Scope**: package signatures, author identity, supply-chain anti-poisoning for the ΣLang
> package system (`sigma-pkg`, §2 Package System).
> **Verdict (TL;DR)**: Level 1 (author signatures, Ed25519) is **fully feasible** with pure
> software and no external PKI; Level 2 (registry trust, TUF-lite) is feasible once the
> `sigma-pkg` registry backend exists; Level 3 (transparency log / Sigstore) needs an external
> ecosystem and stays a roadmap item.

---

## F.1 Threat Model

| Threat | Description | Severity |
|--------|-------------|----------|
| Impersonation | An attacker publishes a package under a trusted name/prefix | High |
| Tampering | Package body edited after publication (fingerprint no longer matches) | High |
| Poisoning | A compromised or malicious author publishes a bad version | High |
| Replay / downgrade | An old, vulnerable version is re-presented as current | Medium |

## F.2 Requirements

- **R1 Integrity** — a package's content is bound to its fingerprint (already true: Law I,
  `fingerprint = SHA-256(definition)`).
- **R2 Authenticity** — a package can be attributed to a claimed author.
- **R3 Non-repudiation** — the author cannot deny having published the version.
- **R4 Revocation** — a leaked key can stop signing / mark old signatures invalid.

R1 is satisfied today by Law I + Law VI (published = frozen). R2–R4 need a signature layer.

## F.3 Solution Sketch — Graded Adoption

### Level 0 (now): fingerprint integrity — no PKI

- Content integrity already exists: change the body → fingerprint changes → corpus / Law I
  reject it.
- **Blocks**: tampering. **Does not block**: impersonation, poisoning (anyone may claim any name).

### Level 1: author signatures (Ed25519) — pure software, feasible

```md
## Signature
signer: alice@sigma-registry
pubkey_fp: sha256:0x…
algorithm: ed25519
signature: <base64(Ed25519(sk, fingerprint ‖ version ‖ metadata))>
```

- Registry maps `name → pubkey` (author identity).
- Verifier `check_signature` verifies the signature against `pubkey_fp` (Level 1+);
  modules without a signature still verify (backward compatible — Law VI).
- **Blocks**: impersonation (needs the private key), tampering (signature covers the
  fingerprint). **Does not block**: a malicious-but-real author.

### Level 2: registry trust (TUF-lite) — feasible with the sigma-pkg backend

- Registry maintains: author pubkeys, allowed signers per package, version manifest.
- Revocation list: leaked keys stop being trusted; threshold signing (maintainer + CI).
- `sigma-pkg publish` enforces Level 2 on the registry side.
- **Blocks**: some poisoning (organization-level trust), replay/downgrade (version manifest).

### Level 3: transparency log (Sigstore-style) — external ecosystem, roadmap

- Append-only log of all signatures; audit trail; historical-tamper resistance.
- Requires external infrastructure; keep as a roadmap item, not a P0/P1 dependency.

## F.4 Integration Points with ΣLang

| Mechanism | Where |
|-----------|-------|
| `## Signature` block | §2.2 package format extension |
| `provenance` registry field | §G.4 (`adjudication`) adjacent field |
| `check_signature` verifier check | new Iron-Law-style check (Level 1+); skipped when absent |
| Signature fingerprint chain | `content_fp` (Law I) vs `pubkey_fp` (identity) — kept separate |

## F.5 Feasibility Verdict

| Level | Feasibility | Dependency | Verifier check |
|-------|-------------|------------|----------------|
| L0 | ✅ already shipped | none | Law I fingerprint |
| L1 | ✅ feasible, pure software | ed25519 (Rust `ed25519-dalek` / Python `cryptography` / Elixir `:crypto`) | `check_signature` |
| L2 | ⚠️ feasible after registry backend | `sigma-pkg` registry | registry-side |
| L3 | ⏳ roadmap | Sigstore / transparency infra | external |

## F.6 Decision & Next Steps

1. **S-01 is no longer "blocked on PKI ecosystem"** — Level 1 is implementable today with
   standard libraries.
2. Recommended v0.3 slice: **Level 1 author signatures** + `check_signature` in the three
   verifiers (reuse the declaration-check pattern of E-09/E-10), linked with §G adjudication
   (a disputed signature goes through the conflict process).
3. Level 2/3 stay candidates with the updated adoption criteria below.

### Updated adoption criteria (E-08 S-01)

- [ ] RFC for `## Signature` block syntax (F.3 Level 1)
- [ ] `check_signature` in all three verifiers (skip when no signature)
- [ ] Registry `provenance` field (Level 2)
- [ ] PKI feasibility study — ✅ **this document**

---

*End of PKI Feasibility Study — v0.1 (2026-08-01)*
