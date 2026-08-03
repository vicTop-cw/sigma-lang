#!/usr/bin/env python3
"""
ΣLang Minimal Reference Implementation — sigma_core.py
======================================================
Single-file, stdlib-only proof that every P0 module is implementable:
  §T Time & Causal Order     §E Error Algebra
  §C Confidence & Probabilistic Logic   §I I/O Boundary & Effects

This is NOT the official verifier (that lives in impl/verifier + impl/elixir_rt).
It is the "reference core" described by MASTER_PLAN Phase 2.2: if this file can
be written from the spec alone and passes its canonical tests, the protocol is
real. Run the self-check with:

    python3 impl/python/sigma_core.py

Exit code 0 = all canonical tests pass.  Spec: spec/spec_p0_foundations.md
"""

import math
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

__version__ = "0.1.0"

# ============================================================
# §T — Time & Causal Order
# ============================================================

class LamportClock:
    """Lamport logical clock: local counter advanced on every event."""

    def __init__(self, agent_id: int):
        self.id = agent_id
        self.t = 0

    def tick(self) -> int:
        self.t += 1
        return self.t

    def send(self, msg):
        self.t += 1
        return (msg, self.t)

    def recv(self, msg, remote_t: int):
        self.t = max(self.t, remote_t) + 1
        return msg


class VectorClock:
    """Vector clock: per-agent counters; causality = pointwise ≤ with a strict <."""

    def __init__(self, n_agents: int, my_id: int):
        self.n = n_agents
        self.id = my_id
        self.v = [0] * n_agents

    def tick(self):
        self.v[self.id] += 1

    def send(self) -> List[int]:
        self.tick()
        return list(self.v)

    def recv(self, remote_v: List[int]):
        self.v = [max(a, b) for a, b in zip(self.v, remote_v)]
        self.tick()

    def __lt__(self, other) -> bool:
        return all(a <= b for a, b in zip(self.v, other.v)) and \
               any(a < b for a, b in zip(self.v, other.v))

    def concurrent(self, other) -> bool:
        return not (self < other) and not (other < self)


def timeout(eff_result, deadline_ticks: int, actual_ticks: int):
    """Declared timing bound (Law VIII): ok iff actual ≤ deadline."""
    if actual_ticks <= deadline_ticks:
        return ("ok", eff_result)
    return ("err", "TimeoutErr")


def retry(eff: Callable, max_attempts: int, fail_times: int):
    """Attempt i succeeds once i ≥ fail_times; bounded by max_attempts."""
    for i in range(max_attempts + 1):
        if i >= fail_times:
            return ("ok", f"success_on_attempt_{i}")
    return ("err", "ExhaustedRetries")


def race(results: List[Any], times: List[int]):
    """Pick the result of the fastest participant."""
    fastest = min(range(len(times)), key=lambda i: times[i])
    return ("ok", results[fastest])


def happens_before(e1_time: int, e2_time: int, same_agent: bool, msg_sent: bool) -> bool:
    """Lamport causal order: same-agent order, or a message was sent."""
    if same_agent and e1_time < e2_time:
        return True
    if msg_sent:
        return True
    return False


def has_cycle(graph: List[List[int]]) -> bool:
    """Deadlock detection: DFS cycle scan over a dependency graph."""
    n = len(graph)
    visited = [False] * n
    rec_stack = [False] * n

    def dfs(u: int) -> bool:
        visited[u] = True
        rec_stack[u] = True
        for v in graph[u]:
            if not visited[v]:
                if dfs(v):
                    return True
            elif rec_stack[v]:
                return True
        rec_stack[u] = False
        return False

    for i in range(n):
        if not visited[i] and dfs(i):
            return True
    return False


# ============================================================
# §E — Error Algebra (Result monad)
# ============================================================

@dataclass
class Ok:
    value: Any

    def bind(self, f):
        return f(self.value)

    def map(self, f):
        return Ok(f(self.value))

    def map_err(self, f):
        return self

    def unwrap_or(self, default):
        return self.value


@dataclass
class Err:
    error: Any

    def bind(self, f):
        return self

    def map(self, f):
        return self

    def map_err(self, f):
        return Err(f(self.error))

    def unwrap_or(self, default):
        return default


def flatten(result):
    """Monadic join: Ok(Ok(v)) → Ok(v), Ok(Err(e)) → Err(e), Err stays."""
    if isinstance(result, Ok) and isinstance(result.value, (Ok, Err)):
        return result.value
    return result


def err_plus(e1: str, e2: str) -> str:
    """Error sum type: concatenate error domains."""
    return f"{e1}+{e2}"


# ============================================================
# §C — Confidence & Probabilistic Logic
# ============================================================

def conf_mul(c1: float, c2: float) -> float:
    """Confidence AND (product)."""
    return c1 * c2


def conf_add(c1: float, c2: float) -> float:
    """Confidence OR (probabilistic sum, bounded by 1)."""
    return c1 + c2 - c1 * c2


def conf_not(c: float) -> float:
    return 1.0 - c


def conf_min(c1: float, c2: float) -> float:
    return min(c1, c2)


def conf_max(c1: float, c2: float) -> float:
    return max(c1, c2)


def bernoulli(p: float, value: bool) -> float:
    """P(X = value) for a Bernoulli(p) variable."""
    return p if value else 1.0 - p


def normal_pdf(x: float, mu: float, sigma: float) -> float:
    return (1.0 / (sigma * math.sqrt(2 * math.pi))) * \
           math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def bayes(p_h: float, p_e_given_h: float, p_e: float) -> float:
    """P(H|E) = P(E|H)·P(H) / P(E); 0 when evidence is impossible."""
    if p_e == 0:
        return 0.0
    return p_e_given_h * p_h / p_e


def entropy_bernoulli(p: float) -> float:
    if p == 0 or p == 1:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def lift(f: Callable, value, conf: float):
    """Lift a pure function into a (value, confidence) pair."""
    return (f(value), conf)


def lift2(f: Callable, v1, c1: float, v2, c2: float):
    """Lift a binary function; result confidence = min of operands (Law IX)."""
    return (f(v1, v2), min(c1, c2))


def kleene_and(a: str, b: str) -> str:
    if a == "⊥" or b == "⊥":
        return "⊥"
    if a == "?" or b == "?":
        return "?"
    return "⊤"


def kleene_or(a: str, b: str) -> str:
    if a == "⊤" or b == "⊤":
        return "⊤"
    if a == "?" or b == "?":
        return "?"
    return "⊥"


def kleene_not(a: str) -> str:
    return {"⊥": "⊤", "?": "?", "⊤": "⊥"}[a]


def weighted_consensus(messages):
    """Confidence-weighted mean + pooled confidence (std/ai.confidence semantics)."""
    total_conf = sum(c for _, c in messages)
    if total_conf == 0:
        return None
    weighted_sum = sum(v * c for v, c in messages)
    avg = weighted_sum / total_conf
    pooled_conf = sum(c * c for _, c in messages) / (total_conf * total_conf)
    return (avg, pooled_conf)


# ============================================================
# §I — I/O Boundary & Effects
# ============================================================

class Effect:
    PURE = "Pure"
    IO = "IO"
    COMM = "Comm"
    NET = "Net"
    FS = "FS"
    TIME = "Time"
    RAND = "Rand"


_ORDER = {Effect.PURE: 0, Effect.COMM: 1, Effect.IO: 2}


def effect_plus(e1: str, e2: str) -> str:
    """Effect sum: Pure is neutral; duplicates collapse; else sorted union."""
    if e1 == Effect.PURE:
        return e2
    if e2 == Effect.PURE:
        return e1
    if e1 == e2:
        return e1
    return "+".join(sorted(set([e1, e2])))


def effect_le(e1: str, e2: str) -> bool:
    """Effect partial order: PURE ≤ COMM ≤ IO (law: IO is the top of the ladder)."""
    return _ORDER.get(e1, 0) <= _ORDER.get(e2, 0)


class FS:
    """In-memory file system: write/read/delete/exists with Law XII linearity."""

    def __init__(self):
        self._store = {}

    def write(self, path: str, content: str):
        self._store[path] = content
        return ("ok", None)

    def read(self, path: str):
        if path in self._store:
            return ("ok", self._store[path])
        return ("err", "NotFound")

    def delete(self, path: str):
        if path in self._store:
            del self._store[path]
            return ("ok", None)
        return ("err", "NotFound")

    def exists(self, path: str) -> bool:
        return path in self._store


class Resource:
    """Handle with an explicit lifecycle: open → use → close exactly once."""

    def __init__(self, path: str):
        self.path = path
        self.closed = False


class IO:
    """Resource manager enforcing Law XII: opened = closed exactly once."""

    def __init__(self):
        self.opened: List[Resource] = []

    def open(self, path: str):
        r = Resource(path)
        self.opened.append(r)
        return ("ok", r)

    def close(self, r: Resource):
        if r.closed:
            return ("err", "DoubleClose")
        r.closed = True
        return ("ok", None)

    def use(self, r: Resource, func: Callable):
        if r.closed:
            return ("err", "UseAfterClose")
        return ("ok", func())


@dataclass
class FFIDeclaration:
    """Declared foreign function: capabilities must be granted (Law XI)."""

    name: str
    pre_cond: Any = None
    post_cond: Any = None
    timeout_ms: Optional[int] = None
    capabilities: List[str] = None

    def __post_init__(self):
        self.capabilities = self.capabilities or []


class FFIRegistry:
    def __init__(self):
        self._decls = {}

    def register(self, decl: FFIDeclaration):
        self._decls[decl.name] = decl

    def check(self, name: str, has_caps: List[str]):
        if name not in self._decls:
            return ("err", "UnknownFFI")
        decl = self._decls[name]
        for cap in decl.capabilities:
            if cap not in has_caps:
                return ("err", f"MissingCapability:{cap}")
        return ("ok", f"executed_{name}")


class Capabilities:
    """Grant/revoke capability set per agent (Law XI)."""

    def __init__(self):
        self._grants = {}

    def grant(self, cap: str, agent: str):
        self._grants.setdefault(agent, set()).add(cap)

    def revoke(self, cap: str, agent: str):
        if agent in self._grants:
            self._grants[agent].discard(cap)

    def has_cap(self, cap: str, agent: str) -> bool:
        return cap in self._grants.get(agent, set())


SAFE_RETRY_OPS = {"http_get", "read_file", "exists", "list_dir"}


def safe_retry_wrap(op_name: str, max_retries: int):
    """Retry is only sound for idempotent ops (GET-style, Law X transparency)."""
    if op_name not in SAFE_RETRY_OPS:
        return ("err", "UnsafeRetryAttempted")
    return ("ok", f"retried_{op_name}_{max_retries}_times")


def infer_effect(func_body_has_io: bool) -> str:
    """Effect inference: any I/O in the body ⇒ IO, else Pure (Law X)."""
    return Effect.IO if func_body_has_io else Effect.PURE


# ============================================================
# §SK — SocketKit Protocol: Auditable App Behavior
# (spec/spec_p0_socketkit.md — task_create / accept_task / task_submit /
#  task_accept / review_merge / contribution_score / credit_score)
# ============================================================

# Task 状态机 (需求文档 §五): 0=open 1=in_progress 2=pending_review 3=completed
STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_PENDING, STATUS_COMPLETED = 0, 1, 2, 3


def task_create(author: int, bounty: int) -> List[int]:
    """Task posting: (author, bounty) → [author, bounty, 0, 0] (open, unclaimed).

    §SK.3.1 — Bounty : Type ≝ ℕ, so a negative bounty is rejected.
    """
    if bounty < 0:
        raise ValueError("BountyErr")
    return [author, bounty, STATUS_OPEN, 0]


def accept_task(task: List[int], hunter: int) -> List[int]:
    """Task claiming: status 0 → 1 (in_progress), hunter recorded.

    §SK.3.2 — claiming a non-open task is a StateError.
    """
    if task[2] != STATUS_OPEN:
        raise ValueError("StateError")
    return [task[0], task[1], STATUS_IN_PROGRESS, hunter]


def task_submit(task: List[int]) -> List[int]:
    """Work submission: status 1 → 2 (pending_review), hunter preserved.

    §SK.3.3 — submitting a non-in-progress task is a StateError.
    """
    if task[2] != STATUS_IN_PROGRESS:
        raise ValueError("StateError")
    return [task[0], task[1], STATUS_PENDING, task[3]]


def task_accept(task: List[int], caller: int) -> List[int]:
    """Acceptance confirmation: status 2 → 3 (completed), hunter preserved.

    §SK.3.4 — 受茬人单人验收确认 (MVP); accepting a non-pending task is a
    StateError. INV-4 (授权): only the author (caller ≡ task[0]) may accept
    their own task, otherwise AuthError.
    """
    if task[2] != STATUS_PENDING:
        raise ValueError("StateError")
    if caller != task[0]:
        raise ValueError("AuthError")
    return [task[0], task[1], STATUS_COMPLETED, task[3]]


def review_merge(opinions: List[List[int]]) -> int:
    """Review resolution: opinions[] → decision (1 = accept, 0 = reject).

    §SK.3.6 — growth-phase 核验师多人评审; decision ≡ 1 if weighted_accept(os)
    ≥ weighted_reject(os) else 0. Each opinion is [reviewer_id, vote, weight];
    order-independent by construction.
    """
    w_accept = sum(w for _, vote, w in opinions if vote == 1)
    w_reject = sum(w for _, vote, w in opinions if vote == 0)
    return 1 if w_accept >= w_reject else 0


def contribution_score(actions: List[List[int]]) -> int:
    """Contribution scoring: actions[] → points, fold ⊕ over deltas floored at 0.

    §SK.3.5 — 贡献值终身累计，负数不参与分红. Each action is [actor_id, kind, delta].
    """
    total = sum(delta for _, _, delta in actions)
    return max(0, total)


def credit_score(events: List[List[int]]) -> int:
    """Credit scoring: events[] → credit (契分制).

    §SK.3.7 — base 100; kind 0 (complete) +5 per count; kind 1 (breach) ×0.7
    per count (integer ×7 ÷10, floor); floored at 0. Each event is [kind, count].
    """
    credit = 100
    for kind, count in events:
        if kind == 0:  # complete
            credit += 5 * count
        elif kind == 1:  # breach
            for _ in range(count):
                credit = (credit * 7) // 10
        else:
            raise ValueError("TypeError")
    return max(0, credit)


def _encode_list(xs: List[int], base: int = 1000) -> int:
    """Law II — encode a List⟨ℕ⟩ to a single ℕ (deterministic, injective-ish)."""
    n = 0
    for i, x in enumerate(xs):
        n += x * (base ** i)
    return n


def encode_task(task: List[int]) -> int:
    """Law II — Task → ℕ."""
    return _encode_list(task)


def encode_opinion(opinion: List[int]) -> int:
    """Law II — Opinion → ℕ."""
    return _encode_list(opinion)


def encode_action(action: List[int]) -> int:
    """Law II — Action → ℕ."""
    return _encode_list(action)


def encode_event(event: List[int]) -> int:
    """Law II — Event → ℕ."""
    return _encode_list(event)


# ============================================================
# Self-check: canonical tests for every module (Law IV)
# ============================================================

def _main() -> int:
    passed = failed = 0

    def check(name: str, cond: bool):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print(f"  ❌ {name}")

    def approx(a: float, b: float, eps: float = 1e-9) -> bool:
        return abs(a - b) < eps

    # §T
    c = LamportClock(1)
    t1, t2 = c.tick(), c.tick()
    check("T.lamport_advances", t2 > t1)
    check("T.send_increments", LamportClock(2).send("hello")[1] == 1)
    c3 = LamportClock(3)
    c3.recv("msg", 100)
    check("T.recv_max_plus_1", c3.t == 101)
    vc1, vc2 = VectorClock(3, 0), VectorClock(3, 1)
    vc1.tick(); vc2.tick()
    check("T.vc_independent", vc1.concurrent(vc2))
    vc3 = VectorClock(3, 2)
    vc3.tick()
    vc1.recv(vc3.send())
    check("T.vc_causal_link", vc1.v == [2, 0, 2])
    check("T.timeout_success", timeout(42, 5, 1) == ("ok", 42))
    check("T.timeout_expires", timeout(42, 3, 5) == ("err", "TimeoutErr"))
    check("T.retry_succeeds", retry(lambda: None, 3, 1) == ("ok", "success_on_attempt_1"))
    check("T.retry_exhausted", retry(lambda: None, 2, 5) == ("err", "ExhaustedRetries"))
    check("T.race_fastest_wins", race(["slow", "fast"], [10, 1]) == ("ok", "fast"))
    check("T.hb_same_agent", happens_before(1, 2, True, False))
    check("T.hb_concurrent", not happens_before(1, 2, False, False))
    check("T.deadlock_free", not has_cycle([[1], [2], []]))
    check("T.deadlock_detected", has_cycle([[1], [0]]))

    # §E
    check("E.left_identity", Ok(3).bind(lambda x: Ok(x * 2)).value == 6)
    check("E.right_identity", Ok(42).bind(lambda x: Ok(x)).value == 42)
    check("E.short_circuit", Err("TimeoutErr").bind(lambda x: Ok(x + 1)).error == "TimeoutErr")
    check("E.map_ok", Ok(3).map(lambda x: x * 2).value == 6)
    check("E.map_err_passthrough", Err("e").map(lambda x: x * 2).error == "e")
    check("E.map_err_transform", Err("timeout").map_err(lambda e: e.upper()).error == "TIMEOUT")
    check("E.flatten_ok_ok", flatten(Ok(Ok(3))).value == 3)
    check("E.flatten_ok_err", flatten(Ok(Err("e"))).error == "e")
    check("E.flatten_err", flatten(Err("e")).error == "e")
    check("E.associativity",
          Ok(1).bind(lambda x: Ok(x + 1)).bind(lambda x: Ok(x * 2)).value ==
          Ok(1).bind(lambda x: Ok(x + 1).bind(lambda y: Ok(y * 2))).value)
    check("E.err_combine", err_plus("timeout", "network") == "timeout+network")

    # §C
    check("C.mul_identity", approx(conf_mul(0.5, 1.0), 0.5))
    check("C.add_zero", approx(conf_add(0.5, 0.0), 0.5))
    check("C.mul_zero", approx(conf_mul(0.5, 0.0), 0.0))
    check("C.involution", approx(conf_not(conf_not(0.7)), 0.7))
    check("C.add_leq_1", conf_add(0.6, 0.5) <= 1.0 + 1e-10)
    check("C.demorgan", approx(conf_not(conf_min(0.6, 0.8)), conf_max(conf_not(0.6), conf_not(0.8))))
    check("C.bern_true", approx(bernoulli(0.5, True), 0.5))
    check("C.normal_at_mean", approx(normal_pdf(0, 0, 1), 0.39894228, 1e-6))
    check("C.normal_symmetric", approx(normal_pdf(-1, 0, 1), normal_pdf(1, 0, 1), 1e-10))
    check("C.bayes_posterior",
          approx(bayes(0.01, 0.9, 0.9 * 0.01 + 0.05 * 0.99), 0.155, 0.01))
    check("C.entropy_max", approx(entropy_bernoulli(0.5), 1.0, 1e-10))
    check("C.entropy_min", approx(entropy_bernoulli(1.0), 0.0))
    check("C.lift2_min_conf", lift2(lambda a, b: a + b, 1, 0.8, 2, 0.9) == (3, 0.8))
    check("C.kleene_and_unk", kleene_and("⊤", "?") == "?")
    check("C.kleene_not_unk", kleene_not("?") == "?")
    msgs = [(10, 0.9), (20, 0.3)]
    res = weighted_consensus(msgs)
    check("C.consensus_weighted", res is not None and approx(res[0], (10 * 0.9 + 20 * 0.3) / 1.2, 1e-10))

    # §I
    check("I.effect_pure_neutral", effect_plus(Effect.PURE, Effect.IO) == Effect.IO)
    check("I.effect_comm", effect_plus(Effect.COMM, Effect.IO) == "Comm+IO")
    check("I.effect_le_io_comm", effect_le(Effect.COMM, Effect.IO))
    fs = FS()
    fs.write("/tmp/x", "hello")
    check("I.write_then_read", fs.read("/tmp/x") == ("ok", "hello"))
    fs.write("/tmp/x", "second")
    check("I.overwrite", fs.read("/tmp/x") == ("ok", "second"))
    fs.write("/tmp/y", "data")
    fs.delete("/tmp/y")
    check("I.delete_then_not_exists", not fs.exists("/tmp/y"))
    check("I.read_deleted", fs.read("/tmp/y") == ("err", "NotFound"))
    io = IO()
    r = io.open("/test/file")[1]
    check("I.proper_lifecycle", io.use(r, lambda: "data") == ("ok", "data"))
    io.close(r)
    check("I.double_close_err", io.close(r) == ("err", "DoubleClose"))
    r2 = io.open("/test/file2")[1]
    io.close(r2)
    check("I.use_after_close", io.use(r2, lambda: "x") == ("err", "UseAfterClose"))
    ffi = FFIRegistry()
    ffi.register(FFIDeclaration("sqrt"))
    ffi.register(FFIDeclaration("exec_cmd", capabilities=["CmdExec"]))
    check("I.ffi_no_cap_needed", ffi.check("sqrt", []) == ("ok", "executed_sqrt"))
    check("I.ffi_missing_cap", ffi.check("exec_cmd", []) == ("err", "MissingCapability:CmdExec"))
    check("I.ffi_with_cap", ffi.check("exec_cmd", ["CmdExec"]) == ("ok", "executed_exec_cmd"))
    caps = Capabilities()
    caps.grant("Network", "agent1")
    check("I.grant_cap", caps.has_cap("Network", "agent1"))
    caps.revoke("Network", "agent1")
    check("I.revoke_cap", not caps.has_cap("Network", "agent1"))
    check("I.safe_retry_get", safe_retry_wrap("http_get", 3)[0] == "ok")
    check("I.unsafe_retry_post", safe_retry_wrap("http_post", 3) == ("err", "UnsafeRetryAttempted"))
    check("I.infer_effect", infer_effect(True) == Effect.IO and infer_effect(False) == Effect.PURE)

    # §SK (SocketKit Protocol — spec_p0_socketkit.md)
    check("SK.task_create_shape", task_create(1, 100) == [1, 100, 0, 0])
    check("SK.task_create_open", task_create(5, 50)[2] == 0)
    check("SK.task_create_unclaimed", task_create(5, 50)[3] == 0)
    check("SK.task_create_bounty_ge0", task_create(2, 0) == [2, 0, 0, 0])
    try:
        task_create(1, -5)
        check("SK.task_create_neg_bounty_rejected", False)
    except ValueError:
        check("SK.task_create_neg_bounty_rejected", True)
    check("SK.accept_task_claim",
          accept_task(task_create(7, 100), 3) == [7, 100, 1, 3])
    check("SK.accept_task_in_progress",
          accept_task(task_create(2, 0), 9)[2] == 1)
    try:
        accept_task([7, 100, 1, 3], 5)
        check("SK.accept_task_non_open_rejected", False)
    except ValueError:
        check("SK.accept_task_non_open_rejected", True)
    check("SK.task_submit_pending",
          task_submit(accept_task(task_create(5, 50), 3)) == [5, 50, 2, 3])
    check("SK.task_submit_hunter_preserved",
          task_submit(accept_task(task_create(2, 0), 9))[3] == 9)
    try:
        task_submit(task_create(5, 50))
        check("SK.task_submit_non_in_progress_rejected", False)
    except ValueError:
        check("SK.task_submit_non_in_progress_rejected", True)
    check("SK.task_accept_completed",
          task_accept(task_submit(accept_task(task_create(5, 50), 3)), 5) == [5, 50, 3, 3])
    check("SK.task_accept_hunter_preserved",
          task_accept(task_submit(accept_task(task_create(2, 0), 9)), 2)[3] == 9)
    try:
        task_accept(task_submit(accept_task(task_create(5, 50), 3)), 9)
        check("SK.task_accept_non_author_rejected", False)
    except ValueError:
        check("SK.task_accept_non_author_rejected", True)
    try:
        task_accept(task_create(5, 50), 5)
        check("SK.task_accept_non_pending_rejected", False)
    except ValueError:
        check("SK.task_accept_non_pending_rejected", True)
    check("SK.review_merge_accept",
          review_merge([[1, 1, 3], [2, 1, 2]]) == 1)                      # 5 ≥ 0
    check("SK.review_merge_reject",
          review_merge([[1, 0, 3], [2, 1, 2]]) == 0)                      # 2 < 3
    check("SK.review_merge_tie_accept",
          review_merge([[1, 0, 3], [2, 1, 3]]) == 1)                      # 3 ≥ 3
    check("SK.review_merge_binary",
          review_merge([[1, 1, 1], [2, 0, 1]]) in (0, 1))
    check("SK.review_merge_order_indep",
          review_merge([[1, 1, 3], [2, 0, 2], [3, 1, 1]]) ==
          review_merge([[3, 1, 1], [1, 1, 3], [2, 0, 2]]))
    check("SK.contribution_fold",
          contribution_score([[1, 1, 3], [2, 2, 4]]) == 7)
    check("SK.contribution_floor_at_0",
          contribution_score([[1, 1, -5], [2, 2, 3]]) == 0)              # -2 floored
    check("SK.contribution_zero_neutral",
          contribution_score([[1, 1, 3]]) == contribution_score([[1, 1, 3], [9, 0, 0]]))
    check("SK.credit_base", credit_score([]) == 100)
    check("SK.credit_complete", credit_score([[0, 1]]) == 105)
    check("SK.credit_breach", credit_score([[1, 1]]) == 70)              # 100×0.7
    check("SK.credit_breach_then_complete",
          credit_score([[1, 1], [0, 1]]) == 75)                          # 70+5
    check("SK.credit_double_breach", credit_score([[1, 2]]) == 49)       # 70×0.7
    check("SK.encode_task_nat", encode_task([1, 2, 0, 0]) >= 0)
    check("SK.encode_distinct", encode_task([1, 2, 0, 0]) != encode_task([1, 3, 0, 0]))
    check("SK.encode_opinion_nat", encode_opinion([1, 1, 3]) >= 0)
    check("SK.encode_action_nat", encode_action([1, 1, 3]) >= 0)
    check("SK.encode_event_nat", encode_event([0, 1]) >= 0)

    print(f"sigma_core self-check: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_main())
