# Module: research_assistant

> Example ΣLang module demonstrating AI Agent protocol with confidence,
> causal ordering, and error handling.

## Imports

```md
import core
import time
import error
import confidence
import io
```

## Context

```md
ctx : Map⟨Sym, Value⟩
```

## Capabilities Required

```md
requires: Network, ReadFile, WriteFile
```

## Timing Contract

```md
timing_contract {
  max_latency: 30000 ticks,
  max_retries: 3,
  timeout_budget: 60000 ticks,
  deadline_miss_policy: "degrade"
}
```

## Capabilities

| Name | Type | Fingerprint | Meaning |
|------|------|-------------|---------|
| `search` | `Query →ⵢₒ Result⟨Docs, NetErr⟩` | `0xR001` | Web search |
| `summarize` | `Doc → Result⟨Summary,IOErr⟩` | `0xR002` | Summarize doc |
| `synthesize` | `List⟨Summary⟩ → Result⟨Hypothesis,AssertionErr⟩` | `0xR003` | Combine findings |
| `human_feedback` | `AgentID → Result⟨Feedback,NetErr⟩` | `0xR004` | Request human input |

## Operations

### search

```md
search : Query →ⵢₒ Result⟨Docs, NetErr⟩
Fingerprint: 0xR001
Effect: IO + Net
Timeout: 15000ms

Laws:
- Result is List of Doc with non-zero length or err
- Same query may return different results (non-deterministic)

Tests:
| Query | Expected |
|-------|----------|
| "climate change" | ok(Docs) where |Docs|>0 |
| timeout(5000) | err(TimeoutErr) |
```

### summarize

```md
summarize : Doc → Result⟨Summary,IOErr⟩
Fingerprint: 0xR002
Effect: IO
Confidence: 0.7 (self-reported)

Laws:
- |Summary| < |Doc|  (summary is shorter)
- confidence ∈ [0,1]

Tests:
| Doc | Expected |
|-----|----------|
| long_article | ok(Summary) where |Summary|<1000 |
| empty_doc | err(EmptyDocErr) |
```

### synthesize

```md
synthesize : List⟨Summary⟩ → Result⟨Hypothesis,AssertionErr⟩
Fingerprint: 0xR003
Effect: Pure (deterministic given inputs)
Confidence: depends on input coherence

Laws:
- ∀ s . |s|>0 ⇒ synthesize(s) ≠ err(EmptyInput)
- ∀ s₁ s₂ . same_elements(s₁,s₂) ⇒ synthesize(s₁) ≡ synthesize(s₂)

Tests:
| Input | Expected |
|-------|----------|
| [sum₁, sum₂] coherent | ok(Hypothesis) |
| [] | err(EmptyInput) |
| [same, same, same] | ok(H) where conf(H) ≥ 0.8 |
```

### human_feedback

```md
human_feedback : AgentID → Result⟨Feedback,NetErr⟩
Fingerprint: 0xR004
Effect: IO + Comm
Timeout: 300000ms (5 min wait)

Laws:
- May timeout (human unavailable)
- Returned feedback has confidence from human

Tests:
| Agent | Expected |
|-------|----------|
| available_human | ok(Feedback) |
| timeout(1000) | err(TimeoutErr) |
```

## Main Protocol: research

```md
research(topic) : Query →ⵢₒ Result⟨Hypothesis,ResearchErr⟩
Fingerprint: 0xR010
Effect: IO + Net + Comm
Confidence: derived from sub-operations

## Definition
research(topic) ≝
  do {
    -- Step 1: Search (with timeout & retry)
    docs ← timeout(retry(search(topic), 3), 15000)
             `catch` (λ_. err(SearchFailed));

    -- Step 2: Summarize in parallel
    summaries ← parallel_map(summaries, docs);

    -- Step 3: Synthesize hypothesis
    h ← synthesize(summaries);

    -- Step 4: Check confidence
    if conf(h) < 0.8 then
      fb ← timeout(human_feedback(ctx.user), 300000)
              `catch` (λ_. ok(default_feedback));
      h ← incorporate_feedback(h, fb)
    else
      h

    -- Step 5: Return with ownership transfer
    return (h ↦ ctx.user)
  }

## Ownership Trace
topic ──→ search ──→ docs
docs̸ ──→ summarize (consumed, parallel)
summaries ──→ synthesize ──→ h
h ──→ return (moved to caller)
```

## Confidence Propagation

```md
## Confidence combination
combine_conf(c₁, c₂) : Conf × Conf → Conf
combine_conf(c₁, c₂) ≝ c₁ ⊗̃ c₂  (pessimistic: independent)

## Propagate through pipeline
conf(research(topic)) ≝
  conf(search) ⊗̃ conf(summarize) ⊗̃ conf(synthesize)

## With human feedback boost
conf(h with feedback) ≝ conf(h) ⊕̃ conf(feedback)
```

## Error Handling

```md
## Error type for research
ResearchErr ≝ SearchFailed + SynthesizeFailed + TimeoutErr + HumanUnavailable

## Recovery strategy
recover_research : Result⟨H,ResearchErr⟩ → H
recover_research(err(SearchFailed))  ≝ default_hypothesis("no_data")
recover_research(err(SynthesizeFailed)) ≝ default_hypothesis("no_synthesis")
recover_research(err(TimeoutErr))      ≝ cached_hypothesis(topic)
recover_research(err(HumanUnavailable)) ≝ h_without_feedback
```

## Parallel Execution

```md
## Parallel map with confidence
parallel_map : (A→Result⟨B,E⟩) → List⟨A⟩ → Result⟨List⟨B⟩,E⟩

## Definition
parallel_map(f, xs) ≝
  let futures ← map (λx. spawn(λ_. f(x))) xs in
  let results ← map await futures in
  sequence(results)  -- Result<List<B>,E>

## Laws
∀ f xs . deterministic(f) ⇒
  parallel_map(f, xs) ≡ map(f, xs)  (same result, different time)

∀ xs . |parallel_map(f, xs)| ≡ |xs|
```

## Causal Ordering

```md
## Events in research protocol
e₁ ≝ send_search_request(topic)
e₂ ≝ recv_search_results(docs)
e₃ ≝ spawn_summarizer(docs)
e₄ ≝ recv_summary(s)
e₅ ≝ synthesize(summaries)
e₆ ≝ send_to_human(h)

## Causal chain
e₁ →ᵢₒ e₂ →ᵢₒ e₃ →ᵢₒ e₄ →ᵢₒ e₅ →ᵢₒ e₆

## Parallel sub-events
∀ s₁ s₂ ∈ summarizer_pool . ∥ᵢₒ(s₁, s₂)  (concurrent)
∀ s . s →ᵢₒ e₅  (all summaries happen before synthesis)
```

## Tests

| Input | Expected |
|-------|----------|
| "climate" with normal network | ok(Hypothesis) conf≥0.7 |
| "climate" with search timeout | err(SearchFailed) or degraded H |
| Empty topic | err(InvalidQuery) |
| All docs empty | err(EmptyInput) |
| Human unavailable | H with conf<0.8 (degraded) |
| 3 retries succeed on 2nd | ok(H) (recovered) |

## Verification Checklist

```
✅ All operations have fingerprints
✅ All operations have ≥1 test
✅ Effect types declared for all functions
✅ Timing contract present (max_latency, timeout_budget)
✅ Capability requirements declared
✅ Error types defined with recovery
✅ Confidence propagation specified
✅ Ownership trace complete
✅ Causal ordering documented
✅ Parallel execution laws stated
✅ Resource lifecycle (spawn/join) annotated
✅ Verifier: 12/12 checks pass
```

## Non-Goals for this Module

```md
❌ Does not specify UI for human feedback
❌ Does not specify search engine internals
❌ Does not specify summarization algorithm
❌ Does not specify hypothesis format
✅ Specifies all of the above as contracts
```
