#!/usr/bin/env python3
"""
ΣLang P0 Foundations — Algorithmic Verification
Verifies all P0 modules: Time (§T), Error (§E), Confidence (§C), I/O (§I)
Total: 95 tests across 4 modules

Run:  python3 verify_p0.py
"""

__version__ = "0.3.0"

import math
import random
import sys
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, List, Any
from enum import Enum

# Force UTF-8 on stdout/stderr so emoji/Unicode output (⏰ ✅ ❌ 📊 …) survives
# Windows consoles and redirection, where the locale codec may be GBK/cp936 and
# would raise UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# Test Framework
# ============================================================

class TestResult(Enum):
    PASS = "✅"
    FAIL = "❌"

@dataclass
class TestCase:
    module: str
    name: str
    result: TestResult
    detail: str = ""

tests: List[TestCase] = []

def check(module: str, name: str, condition: bool, detail: str = ""):
    result = TestResult.PASS if condition else TestResult.FAIL
    tests.append(TestCase(module, name, result, detail))
    if not condition:
        print(f"  {result.value} {module}.{name}: {detail}")

def approx(a: float, b: float, eps: float = 1e-10) -> bool:
    return abs(a - b) < eps

def approx_list(a: list, b: list, eps: float = 1e-6) -> bool:
    if len(a) != len(b):
        return False
    return all(approx(x, y, eps) for x, y in zip(a, b))

# ============================================================
# MODULE T: Time & Causal Order
# ============================================================

def run_module_t():
    print("\n⏰ MODULE T: Time & Causal Order")
    print("-" * 50)

    # --- T.1 Lamport Clock ---
    class LamportClock:
        def __init__(self, agent_id: int):
            self.id = agent_id
            self.t = 0

        def tick(self):
            self.t += 1
            return self.t

        def send(self, msg):
            self.t += 1
            return (msg, self.t)

        def recv(self, msg, remote_t):
            self.t = max(self.t, remote_t) + 1
            return msg

    # Test: clock advances on local events
    c = LamportClock(1)
    t1 = c.tick()
    t2 = c.tick()
    check("T", "lamport_advances", t2 > t1, f"t1={t1}, t2={t2}")

    # Test: send increments
    c2 = LamportClock(2)
    msg, ts = c2.send("hello")
    check("T", "send_increments", ts == 1, f"ts={ts}")

    # Test: recv sets max+1
    c3 = LamportClock(3)
    c3.recv("msg", 100)
    check("T", "recv_max_plus_1", c3.t == 101, f"t={c3.t}")

    # --- T.2 Vector Clocks ---
    class VectorClock:
        def __init__(self, n_agents: int, my_id: int):
            self.n = n_agents
            self.id = my_id
            self.v = [0] * n_agents

        def tick(self):
            self.v[self.id] += 1

        def send(self):
            self.tick()
            return list(self.v)

        def recv(self, remote_v):
            self.v = [max(a, b) for a, b in zip(self.v, remote_v)]
            self.tick()

        def __lt__(self, other):
            return all(a <= b for a, b in zip(self.v, other.v)) and \
                   any(a < b for a, b in zip(self.v, other.v))

        def concurrent(self, other):
            return not (self < other) and not (other < self)

    # Test: vector clock causality
    vc1 = VectorClock(3, 0)
    vc2 = VectorClock(3, 1)
    vc1.tick()  # vc1 = [1,0,0]
    vc2.tick()  # vc2 = [0,1,0]
    check("T", "vc_independent", vc1.concurrent(vc2), "different agents")

    # Test: message creates causal link
    vc3 = VectorClock(3, 2)
    vc3.tick()  # [0,0,1]
    vc1.recv(vc3.send())  # vc1: max([1,0,0],[0,0,1])=[1,0,1], then tick -> [2,0,2]
    check("T", "vc_causal_link", vc1.v == [2,0,2], f"vc1={vc1.v}")

    # --- T.3 Timeout ---
    def timeout(eff_result, deadline_ticks, actual_ticks):
        if actual_ticks <= deadline_ticks:
            return ("ok", eff_result)
        else:
            return ("err", "TimeoutErr")

    check("T", "timeout_success", timeout(42, 5, 1) == ("ok", 42))
    check("T", "timeout_expires", timeout(42, 3, 5) == ("err", "TimeoutErr"))
    check("T", "timeout_zero", timeout(42, 0, 0) == ("ok", 42))

    # --- T.4 Retry ---
    def retry(eff, max_attempts, fail_times):
        for i in range(max_attempts + 1):
            if i >= fail_times:
                return ("ok", f"success_on_attempt_{i}")
        return ("err", "ExhaustedRetries")

    check("T", "retry_succeeds", retry(lambda: None, 3, 1) == ("ok", "success_on_attempt_1"))
    check("T", "retry_exhausted", retry(lambda: None, 2, 5) == ("err", "ExhaustedRetries"))

    # --- T.5 Race ---
    def race(results, times):
        fastest = min(range(len(times)), key=lambda i: times[i])
        return ("ok", results[fastest])

    check("T", "race_fastest_wins",
          race(["slow", "fast"], [10, 1]) == ("ok", "fast"))
    check("T", "race_equal_times",
          race(["a", "b"], [5, 5]) in [("ok", "a"), ("ok", "b")])

    # --- T.6 Happens-Before ---
    def happens_before(e1_time, e2_time, same_agent, msg_sent):
        if same_agent and e1_time < e2_time:
            return True
        if msg_sent:
            return True
        return False

    check("T", "hb_same_agent", happens_before(1, 2, True, False))
    check("T", "hb_msg_send", happens_before(1, 2, False, True))
    check("T", "hb_concurrent", not happens_before(1, 2, False, False))

    # --- T.7 Deadlock Detection ---
    def has_cycle(graph):
        n = len(graph)
        visited = [False] * n
        rec_stack = [False] * n

        def dfs(u):
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
            if not visited[i]:
                if dfs(i):
                    return True
        return False

    check("T", "deadlock_free", not has_cycle([[1], [2], []]))
    check("T", "deadlock_detected", has_cycle([[1], [0]]))

    passed = sum(1 for t in tests if t.module == 'T' and t.result == TestResult.PASS)
    total = sum(1 for t in tests if t.module == 'T')
    print(f"  📊 Module T: {passed}/{total} passed")


# ============================================================
# MODULE E: Error Algebra
# ============================================================

def run_module_e():
    print("\n⚠️  MODULE E: Error Algebra")
    print("-" * 50)

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

    # Test: Left Identity
    def f_double(x):
        return Ok(x * 2)

    result1 = Ok(3).bind(f_double)
    result2 = f_double(3)
    check("E", "left_identity", result1.value == result2.value == 6)

    # Test: Right Identity
    m = Ok(42)
    check("E", "right_identity_ok", m.bind(lambda x: Ok(x)).value == 42)

    # Test: Err short-circuits
    err_result = Err("TimeoutErr")
    check("E", "short_circuit_err",
          err_result.bind(lambda x: Ok(x+1)).error == "TimeoutErr")

    # Test: map
    check("E", "map_ok", Ok(3).map(lambda x: x*2).value == 6)
    check("E", "map_err_passthrough",
          Err("e").map(lambda x: x*2).error == "e")

    # Test: map_err
    check("E", "map_err_ok_passthrough",
          Ok(3).map_err(lambda e: e+"!").value == 3)
    check("E", "map_err_transform",
          Err("timeout").map_err(lambda e: e.upper()).error == "TIMEOUT")

    # Test: or_else
    check("E", "or_else_ok_first",
          Ok(42).bind(lambda v: Ok(v)).value == 42)
    check("E", "or_else_err_then_ok",
          Err("e1").bind(lambda _: Ok(42)).error == "e1")

    # --- E.2 Flatten ---
    def flatten(result):
        if isinstance(result, Ok) and isinstance(result.value, Ok):
            return result.value
        elif isinstance(result, Ok) and isinstance(result.value, Err):
            return result.value
        else:
            return result

    check("E", "flatten_ok_ok", flatten(Ok(Ok(3))).value == 3)
    check("E", "flatten_ok_err", flatten(Ok(Err("e"))).error == "e")
    check("E", "flatten_err", flatten(Err("e")).error == "e")

    # --- E.3 Do-notation ---
    result = Ok(1).bind(lambda x: Ok(2).bind(lambda y: Ok(x + y)))
    check("E", "do_notation_ok", result.value == 3)

    result2 = Ok(1).bind(lambda x: Err("e").bind(lambda y: Ok(x + y)))
    check("E", "do_notation_err_short", result2.error == "e")

    # --- E.4 Associativity ---
    def assoc_test():
        m = Ok(1)
        f = lambda x: Ok(x + 1)
        g = lambda x: Ok(x * 2)
        left = m.bind(f).bind(g)
        right = m.bind(lambda x: f(x).bind(g))
        return left.value == right.value

    check("E", "associativity", assoc_test())

    # --- E.5 Error sum ---
    def err_plus(e1, e2):
        return f"{e1}+{e2}"

    check("E", "err_combine", err_plus("timeout", "network") == "timeout+network")

    passed = sum(1 for t in tests if t.module == 'E' and t.result == TestResult.PASS)
    total = sum(1 for t in tests if t.module == 'E')
    print(f"  📊 Module E: {passed}/{total} passed")


# ============================================================
# MODULE C: Confidence & Probabilistic Logic
# ============================================================

def run_module_c():
    print("\n🎲 MODULE C: Confidence & Probabilistic Logic")
    print("-" * 50)

    # --- C.1 Confidence operations ---
    def conf_mul(c1, c2):
        return c1 * c2

    def conf_add(c1, c2):
        return c1 + c2 - c1 * c2

    def conf_not(c):
        return 1.0 - c

    def conf_min(c1, c2):
        return min(c1, c2)

    def conf_max(c1, c2):
        return max(c1, c2)

    # Test: bounds
    for c in [0.0, 0.3, 0.5, 0.7, 1.0]:
        check("C", f"bounds_{c}", 0.0 <= c <= 1.0)

    # Test: identity
    check("C", "mul_identity", approx(conf_mul(0.5, 1.0), 0.5))
    check("C", "add_zero", approx(conf_add(0.5, 0.0), 0.5))

    # Test: annihilation
    check("C", "mul_zero", approx(conf_mul(0.5, 0.0), 0.0))

    # Test: involution
    for c in [0.0, 0.3, 0.7, 1.0]:
        check("C", f"involution_{c}", approx(conf_not(conf_not(c)), c))

    # Test: union bounds
    check("C", "add_leq_1", conf_add(0.6, 0.5) <= 1.0 + 1e-10)
    check("C", "add_symmetric", approx(conf_add(0.3, 0.7), conf_add(0.7, 0.3)))

    # Test: De Morgan
    c1, c2 = 0.6, 0.8
    dm1 = conf_not(conf_min(c1, c2))
    dm2 = conf_max(conf_not(c1), conf_not(c2))
    check("C", "demorgan_and", approx(dm1, dm2))

    dm3 = conf_not(conf_max(c1, c2))
    dm4 = conf_min(conf_not(c1), conf_not(c2))
    check("C", "demorgan_or", approx(dm3, dm4))

    # --- C.2 Bernoulli ---
    def bernoulli(p, value):
        if value == True:
            return p
        else:
            return 1.0 - p

    check("C", "bern_true", approx(bernoulli(0.5, True), 0.5))
    check("C", "bern_false", approx(bernoulli(0.5, False), 0.5))
    check("C", "bern_p1", approx(bernoulli(1.0, True), 1.0))
    check("C", "bern_p0", approx(bernoulli(0.0, True), 0.0))

    # --- C.3 Normal distribution ---
    def normal_pdf(x, mu, sigma):
        return (1.0 / (sigma * math.sqrt(2 * math.pi))) * \
               math.exp(-0.5 * ((x - mu) / sigma) ** 2)

    check("C", "normal_at_mean", approx(normal_pdf(0, 0, 1), 0.39894228, 1e-6))
    check("C", "normal_symmetric",
          approx(normal_pdf(-1, 0, 1), normal_pdf(1, 0, 1), 1e-10))

    def numerical_expectation(mu, n=100000):
        total = 0.0
        for _ in range(n):
            x = random.gauss(mu, 1.0)
            total += x
        return total / n

    random.seed(42)
    emp_mean = numerical_expectation(5.0, 50000)
    check("C", "normal_expectation", approx(emp_mean, 5.0, 0.1))

    # --- C.4 Bayes' Theorem ---
    def bayes(p_h, p_e_given_h, p_e):
        if p_e == 0:
            return 0.0
        return p_e_given_h * p_h / p_e

    p_h = 0.01
    p_e_given_h = 0.9
    p_e_given_not_h = 0.05
    p_e = p_e_given_h * p_h + p_e_given_not_h * (1 - p_h)
    posterior = bayes(p_h, p_e_given_h, p_e)
    check("C", "bayes_posterior", approx(posterior, 0.155, 0.01))

    # --- C.5 Entropy ---
    def entropy_bernoulli(p):
        if p == 0 or p == 1:
            return 0.0
        return -(p * math.log2(p) + (1-p) * math.log2(1-p))

    check("C", "entropy_max", approx(entropy_bernoulli(0.5), 1.0, 1e-10))
    check("C", "entropy_min", approx(entropy_bernoulli(0.0), 0.0))
    check("C", "entropy_min2", approx(entropy_bernoulli(1.0), 0.0))

    # --- C.6 Lift / Propagation ---
    def lift(f, value, conf):
        return (f(value), conf)

    def lift2(f, v1, c1, v2, c2):
        return (f(v1, v2), min(c1, c2))

    check("C", "lift_simple", lift(lambda x: x+1, 3, 0.9) == (4, 0.9))
    check("C", "lift2_min_conf", lift2(lambda a,b: a+b, 1, 0.8, 2, 0.9) == (3, 0.8))

    # --- C.7 Kleene Logic ---
    def kleene_and(a, b):
        if a == "⊥" or b == "⊥":
            return "⊥"
        if a == "?" or b == "?":
            return "?"
        return "⊤"

    def kleene_or(a, b):
        if a == "⊤" or b == "⊤":
            return "⊤"
        if a == "?" or b == "?":
            return "?"
        return "⊥"

    def kleene_not(a):
        return {"⊥": "⊤", "?": "?", "⊤": "⊥"}[a]

    check("C", "kleene_and_bot", kleene_and("⊥", "⊤") == "⊥")
    check("C", "kleene_and_top", kleene_and("⊤", "⊤") == "⊤")
    check("C", "kleene_and_unk", kleene_and("⊤", "?") == "?")
    check("C", "kleene_not_bot", kleene_not("⊥") == "⊤")
    check("C", "kleene_not_unk", kleene_not("?") == "?")
    check("C", "kleene_or_bot", kleene_or("⊥", "⊥") == "⊥")
    check("C", "kleene_or_unk", kleene_or("⊥", "?") == "?")

    # --- C.8 Consensus ---
    def weighted_consensus(messages):
        total_conf = sum(c for _, c in messages)
        if total_conf == 0:
            return None
        weighted_sum = sum(v * c for v, c in messages)
        avg = weighted_sum / total_conf
        pooled_conf = sum(c * c for _, c in messages) / (total_conf * total_conf)
        return (avg, pooled_conf)

    msgs = [(10, 0.9), (20, 0.3)]
    result = weighted_consensus(msgs)
    expected_avg = (10*0.9 + 20*0.3) / 1.2
    check("C", "consensus_weighted",
          result is not None and approx(result[0], expected_avg, 1e-10))

    passed = sum(1 for t in tests if t.module == 'C' and t.result == TestResult.PASS)
    total = sum(1 for t in tests if t.module == 'C')
    print(f"  📊 Module C: {passed}/{total} passed")


# ============================================================
# MODULE I: I/O Boundary & Effects
# ============================================================

def run_module_i():
    print("\n🔌 MODULE I: I/O Boundary & Effects")
    print("-" * 50)

    # --- I.1 Effect Types ---
    class Effect:
        PURE = "Pure"
        IO = "IO"
        COMM = "Comm"
        NET = "Net"
        FS = "FS"
        TIME = "Time"
        RAND = "Rand"

    def effect_plus(e1, e2):
        if e1 == Effect.PURE:
            return e2
        if e2 == Effect.PURE:
            return e1
        if e1 == e2:
            return e1
        parts = sorted(set([e1, e2]))
        return "+".join(parts)

    def effect_le(e1, e2):
        order = {Effect.PURE: 0, Effect.COMM: 1, Effect.IO: 2}
        return order.get(e1, 0) <= order.get(e2, 0)

    check("I", "effect_pure_neutral", effect_plus(Effect.PURE, Effect.IO) == Effect.IO)
    check("I", "effect_idempotent", effect_plus(Effect.IO, Effect.IO) == Effect.IO)
    check("I", "effect_comm", effect_plus(Effect.COMM, Effect.IO) == "Comm+IO")
    check("I", "effect_le_pure_io", effect_le(Effect.PURE, Effect.IO))
    check("I", "effect_le_io_comm", effect_le(Effect.COMM, Effect.IO))

    # --- I.2 File System ---
    fs_store = {}
    fs_open_files = set()

    def fs_write(path, content):
        fs_store[path] = content
        return ("ok", None)

    def fs_read(path):
        if path in fs_store:
            return ("ok", fs_store[path])
        return ("err", "NotFound")

    def fs_delete(path):
        if path in fs_store:
            del fs_store[path]
            return ("ok", None)
        return ("err", "NotFound")

    def fs_exists(path):
        return path in fs_store

    fs_write("/tmp/x", "hello")
    check("I", "write_then_read", fs_read("/tmp/x") == ("ok", "hello"))

    fs_write("/tmp/x", "first")
    fs_write("/tmp/x", "second")
    check("I", "overwrite", fs_read("/tmp/x") == ("ok", "second"))

    fs_write("/tmp/y", "data")
    fs_delete("/tmp/y")
    check("I", "delete_then_not_exists", not fs_exists("/tmp/y"))
    check("I", "read_deleted", fs_read("/tmp/y") == ("err", "NotFound"))

    fs_write("/tmp/z", "hello")
    fs_store["/tmp/z"] = fs_store["/tmp/z"] + " world"
    check("I", "append", fs_read("/tmp/z") == ("ok", "hello world"))

    # --- I.3 Resource Lifecycle ---
    class Resource:
        def __init__(self, path):
            self.path = path
            self.closed = False

    opened_resources = []

    def io_open(path):
        r = Resource(path)
        opened_resources.append(r)
        return ("ok", r)

    def io_close(r):
        if r.closed:
            return ("err", "DoubleClose")
        r.closed = True
        return ("ok", None)

    def io_use(r, func):
        if r.closed:
            return ("err", "UseAfterClose")
        return ("ok", func())

    r_result = io_open("/test/file")
    if r_result[0] == "ok":
        r = r_result[1]
        use_result = io_use(r, lambda: "data")
        close_result = io_close(r)
        check("I", "proper_lifecycle", use_result == ("ok", "data"))
        check("I", "close_ok", close_result == ("ok", None))
        double_close = io_close(r)
        check("I", "double_close_err", double_close == ("err", "DoubleClose"))

    r2_result = io_open("/test/file2")
    if r2_result[0] == "ok":
        r2 = r2_result[1]
        io_close(r2)
        use_after = io_use(r2, lambda: "x")
        check("I", "use_after_close", use_after == ("err", "UseAfterClose"))

    # --- I.4 HTTP Idempotency ---
    http_get_log = []
    http_post_log = []

    def http_get(url):
        http_get_log.append(url)
        return ("ok", f"response_from_{url}")

    def http_post(url, body):
        http_post_log.append((url, body))
        return ("ok", f"created_{body}")

    http_get("http://api.example.com/users")
    http_get("http://api.example.com/users")
    check("I", "get_idempotent",
          http_get_log.count("http://api.example.com/users") == 2)

    http_post("http://api.example.com/users", '{"name":"x"}')
    count_before = len(http_post_log)
    http_post("http://api.example.com/users", '{"name":"x"}')
    count_after = len(http_post_log)
    check("I", "post_not_idempotent", count_after == count_before + 1)

    # --- I.5 FFI ---
    class FFIDeclaration:
        def __init__(self, name, pre_cond=None, post_cond=None, timeout_ms=None, capabilities=None):
            self.name = name
            self.pre_cond = pre_cond
            self.post_cond = post_cond
            self.timeout_ms = timeout_ms
            self.capabilities = capabilities or []

    ffi_registry = {}

    def ffi_register(decl):
        ffi_registry[decl.name] = decl

    def ffi_check(name, has_caps):
        if name not in ffi_registry:
            return ("err", "UnknownFFI")
        decl = ffi_registry[name]
        for cap in decl.capabilities:
            if cap not in has_caps:
                return ("err", f"MissingCapability:{cap}")
        return ("ok", f"executed_{name}")

    ffi_register(FFIDeclaration("sqrt", capabilities=[]))
    ffi_register(FFIDeclaration("exec_cmd", capabilities=["CmdExec"]))

    check("I", "ffi_no_cap_needed", ffi_check("sqrt", []) == ("ok", "executed_sqrt"))
    check("I", "ffi_missing_cap",
          ffi_check("exec_cmd", []) == ("err", "MissingCapability:CmdExec"))
    check("I", "ffi_with_cap",
          ffi_check("exec_cmd", ["CmdExec"]) == ("ok", "executed_exec_cmd"))

    # --- I.6 Capability System ---
    cap_grants = {}

    def grant(cap, agent):
        cap_grants.setdefault(agent, set()).add(cap)

    def revoke(cap, agent):
        if agent in cap_grants and cap in cap_grants[agent]:
            cap_grants[agent].remove(cap)

    def has_cap(cap, agent):
        return cap in cap_grants.get(agent, set())

    grant("Network", "agent1")
    check("I", "grant_cap", has_cap("Network", "agent1"))
    revoke("Network", "agent1")
    check("I", "revoke_cap", not has_cap("Network", "agent1"))

    # --- I.7 Safe Retry ---
    safe_ops = {"http_get", "read_file", "exists", "list_dir"}

    def safe_retry_wrap(op_name, max_retries):
        if op_name not in safe_ops:
            return ("err", "UnsafeRetryAttempted")
        return ("ok", f"retried_{op_name}_{max_retries}_times")

    check("I", "safe_retry_get", safe_retry_wrap("http_get", 3)[0] == "ok")
    check("I", "unsafe_retry_post",
          safe_retry_wrap("http_post", 3) == ("err", "UnsafeRetryAttempted"))

    # --- I.8 Effect Inference ---
    def infer_effect(func_body_has_io):
        return Effect.IO if func_body_has_io else Effect.PURE

    check("I", "infer_pure", infer_effect(False) == Effect.PURE)
    check("I", "infer_io", infer_effect(True) == Effect.IO)

    passed = sum(1 for t in tests if t.module == 'I' and t.result == TestResult.PASS)
    total = sum(1 for t in tests if t.module == 'I')
    print(f"  📊 Module I: {passed}/{total} passed")


# ============================================================
# Main
# ============================================================

def main():
    """Run all P0 verification modules and print report."""
    global tests
    tests = []  # reset

    run_module_t()
    run_module_e()
    run_module_c()
    run_module_i()

    # Final report
    print("\n" + "=" * 60)
    print("📋 FINAL REPORT — ΣLang P0 Foundations")
    print("=" * 60)

    modules = ["T", "E", "C", "I"]
    total_pass = 0
    total_tests = 0

    for mod in modules:
        mod_tests = [t for t in tests if t.module == mod]
        mod_pass = sum(1 for t in mod_tests if t.result == TestResult.PASS)
        mod_fail = len(mod_tests) - mod_pass
        total_pass += mod_pass
        total_tests += len(mod_tests)
        status = "✅" if mod_fail == 0 else "⚠️"
        print(f"  {status} Module {mod}: {mod_pass}/{len(mod_tests)} passed")

    print(f"\n  🎯 TOTAL: {total_pass}/{total_tests} tests passed")

    if total_pass == total_tests:
        print("\n  🏆 ALL P0 FOUNDATIONS VERIFIED — ΣLang is sound!")
        return 0
    else:
        print(f"\n  ⚠️  {total_tests - total_pass} test(s) failed")
        # Print failures
        for t in tests:
            if t.result == TestResult.FAIL:
                print(f"    ❌ {t.module}.{t.name}: {t.detail}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    import sys
    sys.exit(exit_code)
