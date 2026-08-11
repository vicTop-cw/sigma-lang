# ΣLang 整改项目 · 交叉复核报告

复核时间：2026-08-11 16:30 (GMT+8)
复核方式：逐项文件比对 + 实证运行（引擎 / judge / bench / 验证器回归）

---

## 1. 4.1 §SK JSON ↔ MD 一致性 — ✅ 通过（含 2 处小注）

`spec/spec_p0_socketkit.json` (v0.30.0, 22 ops) vs `spec/spec_p0_socketkit.md`

抽查 5 个操作，tests 逐条一致（输入 / 输出 / 错误名）：

| 操作 | JSON tests | MD Tests 表格 | 错误名 | 一致 |
|------|-----------|---------------|--------|------|
| task_create (0xF001) | 3 条（含 [1,-5]→⊥BountyErr） | SK.3.1 3 条 | BountyErr | ✅ |
| accept_task (0xF004) | 3 条（含嵌套 op 输入） | SK.3.2 3 条 | StateError | ✅ |
| task_submit (0xF005) | 3 条 | SK.3.3 3 条 | StateError | ✅ |
| task_accept (0xF006) | 4 条（AuthError + StateError 各 1） | SK.3.4 4 条 | AuthError / StateError | ✅ |
| quota_use (0xF009) | 2 条 | SK.3.9 2 条 | QuotaExhausted | ✅ |

（另抽查 credit_score：JSON 6 条 ↔ SK.3.7 6 条，含 75/49 链式值，一致 ✅）

laws 数量：
- task_create 3=3、accept_task 5=5（SK.3.2 两条 + SK.3.8 INV-1/2/3 三条）、task_submit 5=5、task_accept 6=6（SK.3.4 三条 + INV 三条）— 全部对应 ✅
- quota_use：JSON 2 条；MD SK.3.9 合并块展示 3 条（其中"月底清零恢复"属 quota_reset，JSON 中 quota_reset 自带 2 条含重复的 bounds 定律）— 语义一致，仅合并展示差异。

小注（不影响交付）：
1. MD SK.3.1 定律 1 写作 `0 ≤ task_create(a, b)`（对列表整体比较的简写），JSON 为精确的 `0 <= index(task_create(a, b), 1)` — 意图一致，MD 是缩写。
2. MD 章节按业务流排序（SK.3.2 accept_task 先于 SK.3.5 contribution_score），JSON 按指纹序 — 非偏差。

## 2. 4.4 引擎 — ✅ 通过（实证 102/102）

`impl/python/sigma_engine.py`：
- 表达式求值器支持 schema 全部节点：lambda / table 状态机 / list 构造 / if 条件（field / expr / fn / not / and / or）/ fn 调用 / 嵌套 op / `$_` 序列 — 代码确认 + 内置自检 42/42 ✅
- 20 个命名错误类（ERROR_NAMES 含 §SK 全部用到的 BountyErr / StateError / AuthError / TypeError / QuotaExhausted / InsufficientEscrow / InsufficientPoints / TeamFull / DivByZero / NotTraceable）— 错误名映射正确 ✅
- **实证运行**：加载真实 spec JSON → `corpus: 60/60 passed, engine: 42/42 passed, AGENT_ENGINE COMPLETE: 102/102 passed` ✅
- 前置条件先于求值校验（_check_precondition → _raise_error(pc.error)）✅

## 3. 4.5 corpus JSON — ✅ 通过

`corpus/socketkit_taskflow_ok.json`（25 条测试，PASS 期望）：
- `$_` 占位符：12 个 sequence 块全部正确指向序列内上一条操作结果（如 task_create → accept_task($_,3) → task_submit($_) → task_accept($_,5)），与 spec JSON 的嵌套 op 表达等价 ✅
- expect/error 字段：25 条全部与 spec JSON tests 值一致；错误名 BountyErr / StateError / AuthError / TypeError 均与 spec JSON 相同 ✅
- JSON 解析有效（module=socketkit_taskflow_ok, expected_verdict=PASS）✅

## 4. 4.2 基准工具 — ✅ 通过（原偏差已修复）

`tools/sigma-ai-bench.py`：
- **默认 mock 链路实证通过**：3 轮行为完整（R1 5/11 带 2 个种子 bug → R2 8/11 修正 1 个 → R3 11/11 全对，`AGENT_BENCH COMPLETE: mock pipeline 3 rounds ok`），结果写入 `bench/results.json` + `bench/leaderboard.json`（已在磁盘确认）✅
- **真实 §SK spec mock 链路实证通过（修复后）**：`--mock --spec spec_p0_socketkit.json` → R1 54/60 → R2 57/60 → R3 60/60 全对，`spec_consistency_warnings: 0`，最终 PASS ✅
- 修复内容（2026-08-11）：① mock codegen（node_to_py）补齐 §SK 全部内置函数（weighted_accept/reject/support、fold_credit、split_floor、enumerate_ledger、sub/add/mul/floordiv/mod、eq/ne/lt/le/gt/ge 比较、fold_add 末列折叠）；② 候选模块 header 辅助函数全部改为抛 SigmaError（含类型检查），新增 sum_contribs/min_source_id 供前置条件编译；③ RESTRICTED_BUILTINS 补 all/any；④ reference 求值器（eval_body/eval_call）同步补齐上述 fn（消除 spec 一致性告警）；⑤ verify_round 增加嵌套 op 测试输入解析（resolve_input，参考求值器构造合法输入，候选实现原子操作）。

## 5. 4.6 judge — ✅ 通过

`tools/sigma-spec2judge.py`：
- TLE：单测子进程 `subprocess.run(timeout=...)` → 超时判定 `verdict: "TLE"` ✅
- MLE：POSIX `preexec_fn` + setrlimit(RLIMIT_AS/RLIMIT_DATA) → worker 捕获 MemoryError → `mle=True` → `_classify` 判 MLE；Windows 无 resource 模块自动降级为仅时间限制（代码注释与运行时 note 均明确）✅
- WA：值不匹配 / 错误名不匹配 / 意外异常 / 函数缺失 / 加载失败 / 协议错误 均归类 WA ✅
- **实证自检通过**：正确提交 6/6 PASS；带 1 bug 提交 4/6、检出 2 条 WA（exit 0/1）✅

## 6. 4.3 README — ✅ 通过

`README.md`：
- 五节结构齐全：§1 项目定位 / §2 快速体验 / §3 AI Benchmark / §4 找茬 Demo / §5 协议编写指南（另有原有 §6 项目状态，不冲突）✅
- 主标题无 "AI-Native"：H1 为 `# ΣLang — A Specification Protocol for Verifiable AI Consensus`；定位说明表格明确记录旧定位 "AI-Native Semantic Protocol" → 新定位的调整 ✅
- 关键数据保留：consensus **56/56**（§1、§2.4、§2.5、§5.3、§6.1 多处）✅、p0 **109/109**（§2.4 verify_p0 + §6.1 状态表）✅、**358 PROVED**（§1、§2.4、§6.1）✅、`--launch`（`python3 impl/python/sigma_app.py --launch`，§2.2 / §4.3）✅

## 7. 回归检查 — ✅ 通过

- `impl/python/sigma_core.py`：git status 无此文件（未改动）；文件头注释保持原样（v0.1.0、§T/§E/§C/§I reference core 描述）✅
- 验证器文件未破坏 + 实证回归：
  - `verify_consensus.py`：未改动，运行 **Consensus: 56/56 modules agree** ✅
  - `verify_p0.py`：未改动，运行 **109/109 tests passed** ✅
- 小注：存在未跟踪的杂散文件 `impl/python/tmp_run1.txt`、`tmp_run2.txt`（疑似测试残留，建议清理，不影响功能）

---

## 总体结论

**可交付**（7/7 通过，第 4 项偏差已于 2026-08-11 修复并实证）。

### 需修复项清单

1. ~~**[已修复] sigma-ai-bench.py mock codegen 覆盖不全**（项 4）~~：`--mock --spec spec_p0_socketkit.json` 现可跑通 3 轮（54/60 → 57/60 → 60/60，0 告警）。
2. **[清理建议] 杂散文件**：删除 `impl/python/tmp_run1.txt`、`tmp_run2.txt`。
3. **[可选打磨] quota 定律展示**：JSON 中 quota_reset 重复声明 bounds 定律，与 MD 合并展示略有出入，可统一（不影响语义）。

### 已实证的关键数据

| 检查点 | 结果 |
|--------|------|
| 引擎 + spec JSON corpus | 102/102（corpus 60/60 + selftest 42/42）|
| judge 自检 | 正确 6/6，buggy 4/6（2 WA 检出）|
| bench mock 默认链路 | 5/11 → 8/11 → 11/11，写入 bench/ |
| bench mock + 真实 §SK spec | ✅ 54/60 → 57/60 → 60/60（修复后，0 告警）|
| verify_consensus.py | 56/56 |
| verify_p0.py | 109/109 |
| sigma_core.py | 未改动 |

AGENT_REVIEW COMPLETE: 7/7
