# ΣLang 整改路线图 · Roadmap v1.0

> **日期**：2026-08-12
> **现状**：Phase 0 已完成（consensus 56/56、z3 358 PROVED）；Phase 1 进行中——5 个独立 AI 模型已实证 60/60 通过（2026-08-12，见 `docs/cross_tool_report.html`）
> **目标**：Phase 3 — 任何 AI 模型可消费 spec 并自主产出通过 consensus gate 的实现

---

## 一、现状诊断

### 1.1 已经做到的事情（值得保留）

| 资产 | 状态 | 价值 |
|------|------|------|
| 形式化规约体系（spec/） | ✅ spec 0.7.0，三域（§SK/§PF/§IN） | 规约写作方法论成熟 |
| 三端参考实现（Python/Rust/Elixir） | ✅ 56/56 consensus | **"一致性"的 ground truth 标尺已建立** |
| z3 义务消解（tools/sigma-prove.py） | ✅ 358 PROVED | 规约→SMT 翻译层可用 |
| CI 门禁（sigma-accept.py） | ✅ 10/10 | 自动化验证体系就绪 |
| 找茬 Demo 产品 | ✅ 一条命令可启动 | 规约→产品的闭环参考 |
| PyPI 发布 | ✅ `pip install sigma-lang` | 分发渠道已通 |

### 1.2 核心问题

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| **定位错位** | 🔴 严重 | "AI-Native Semantic Protocol"名不副实：协议和 AI 之间没有运行时通路 |
| **无 AI 闭环验证** | ✅ 已闭环（2026-08-12） | 5 个独立 AI 模型已各自仅凭 JSON spec 实现 §SK 全部操作并 60/60 通过（见 `docs/cross_tool_report.html`）；自动化工具链（sigma-ai-bench.py）仍待完善 |
| **spec 不可机器解析** | 🟡 中等 | Markdown 是人读格式，无 JSON/YAML 等价物，AI 解析不稳定 |
| **Demo 体量的过度仪式感** | 🟡 中等 | 三端 verifier + z3 的维护成本远超找茬产品的复杂度 |
| **类型系统极弱** | 🟢 后续 | ℕ-only 无法表达字符串、时间、泛型等现实业务 |

---

## 二、重新定位

```diff
- "AI-Native Semantic Protocol — One symbol, one meaning, one result, across all models."
+ "ΣLang — A Specification Protocol for Verifiable AI Consensus."
+ 通过可验证的规约 + 共识门禁，让不同 AI 系统对同一份业务规则产出完全一致的行为。
+ 当前阶段：Phase 0 人工参考实现已对齐，Phase 1 AI 自主实现验证中。
```

核心叙事变化：

| 之前 | 之后 |
|------|------|
| "AI 原生语义协议"（暗示已实现） | "面向可验证 AI 共识的规约协议"（描述目标） |
| 找茬产品是旗舰应用 | 找茬是规约的最小可行 demo |
| 三端一致是最终成果 | 三端一致是 ground truth 标尺——用来测量 AI 的语义理解能力 |

---

## 三、四阶段路线图

```
Phase 0 ──────→ Phase 1 ──────→ Phase 2 ──────→ Phase 3
[已完成]        [进行中]         [中期]           [远期]
人工参考对齐    AI 替代 1 个     AI 替代 2 个     协议原生
56/56 consensus  verifier         verifier         无需人工翻译
```

### Phase 0（已完成）— 建立地面真值 ✅

**做了什么**：三个独立人工实现（Python / Rust / Elixir）对同一份 spec 逐项一致。

**意义**：证明了 spec 对**人类**没有歧义。三个不同语言、不同思维方式的程序员，读同一份规则书，得出的结论完全一样。这是后续所有 AI 实验的基准线。

### Phase 1（进行中 🚀）— AI 替代一个 verifier

**目标**：让 LLM 读 spec → 自动生成 Python 实现 → 通过 consensus gate → 与人工参考结果一致。

**进展（2026-08-12）**：跨工具实证已完成——五个独立 AI 实现者（DeepSeek / zai
子代理 / Qwen3dot8Max / Seed2dot1Turbo / Hy3）各自仅凭 `spec_p0_socketkit.json`
实现 §SK 全部 22 个操作，同一套 60 条测试全部 60/60 通过（300 次测试 0 失败）。
汇总见 `docs/cross_tool_report.html`，机器可读明细见 `bench/leaderboard.json`。

**具体动作**：

1. **AI Verifier Benchmark**
   - 选 3-5 个主流模型（Claude / GPT / Gemini / DeepSeek / 国产）
   - 给每个模型同一份 spec，要求生成 `impl/python/sigma_core_ai.py`
   - 自动跑 `verify_consensus.py` 对比 AI 实现 vs 人工参考
   - 产出跨模型一致性矩阵（哪个模型对哪些操作出错？哪个模型全过？）

2. **Benchmark 数据格式**
   - 每轮测试记录：模型名、spec 版本、consensus 通过率、失败操作清单、尝试次数
   - 失败时允许模型自我修正（读 diff → 修正 → 重跑，最多 3 轮）
   - 最终输出排行榜：哪个模型在"从规约中提取精确语义"这项能力上最强

3. **价值**：
   - ΣLang 立刻获得一个独特定位：**不是又一个 benchmark 数据集——是衡量 AI 语义理解精确度的工具**
   - 对模型厂商有吸引力：你的模型能读懂形式化规约吗？来这里测

### Phase 2（中期）— AI 替代多个 verifier

**目标**：不同模型各自独立读 spec、各自独立生成实现，跨模型互相对齐且与人工参考对齐。

**意义**：当 Claude 的实现和 GPT 的实现对同一个业务操作给出完全相同的判定，而两者都从未见过对方的代码——这才是真正的"AI 之间通过协议达成共识"。

### Phase 3（远期）— AI 原生协议

**目标**：spec 格式足够标准化和机器可消费，任何 AI 系统都可以直接解析 spec 并产生执行行为，无需人工翻译。

**关键能力**：
- spec JSON 格式成为 canonical（Markdown 作为人类可读的衍生品）
- 通用 verifier 引擎：读 JSON spec → 解析定律 → 求值/验证
- AI 的输入/输出直接对接 JSON spec——不再经过"生成 Python 代码"这一中间层
- spec → judge 二进制一键生成（sandbox + time/memory limit）

---

## 四、整改清单（按优先级）

### 🔴 P0 — 必须做（解锁 Phase 1）

#### 4.1 设计 spec 的机器可解析格式

在每份 `spec_p0_*.md` 旁增加等价的 `spec_p0_*.json`。

**JSON 格式设计**：

```json
{
  "spec": "§SK",
  "version": "0.7.0",
  "fingerprint_prefix": "0xF000",
  "types": [
    {"name": "Author", "kind": "alias", "target": "nat"},
    {"name": "Task", "kind": "list", "element": "nat"},
    {"name": "Status", "kind": "enum", "values": [
      {"name": "open", "value": 0},
      {"name": "in_progress", "value": 1},
      {"name": "pending_review", "value": 2},
      {"name": "completed", "value": 3}
    ]}
  ],
  "operations": [
    {
      "name": "task_create",
      "fingerprint": "0xF001",
      "signature": {"params": ["nat", "nat"], "returns": "Task"},
      "definition": {
        "kind": "lambda",
        "params": ["a", "b"],
        "body": ["a", "b", 0, 0]
      },
      "preconditions": [
        {"expr": "b >= 0", "error": "BountyErr"}
      ],
      "laws": [
        {"forall": ["a", "b"], "predicate": "index(task_create(a, b), 2) == 0",
         "description": "freshly created task is open"},
        {"forall": ["a", "b"], "predicate": "index(task_create(a, b), 3) == 0",
         "description": "freshly created task is unclaimed"}
      ],
      "tests": [
        {"input": [7, 100], "output": [7, 100, 0, 0]},
        {"input": [2, 0], "output": [2, 0, 0, 0]},
        {"input": [1, -5], "output": null, "error": "BountyErr"}
      ]
    }
  ]
}
```

**好处**：
- AI 直接从结构化 JSON 提取语义，不再依赖 Markdown 解析的模糊性
- consensus gate 可以直接消费 JSON spec，不再需要手写 verifier 的函数映射
- spec 和 verifier 之间"翻译出错"这个 bug 源头被消除

#### 4.2 搭建 AI Verifier Benchmark 工具链

**新工具**：`tools/sigma-ai-bench.py`

**功能**：
```
python3 tools/sigma-ai-bench.py --model claude-4 --spec spec_p0_socketkit.json --rounds 3

→ 第 1 轮: 生成实现 → 43/56 passed → 反馈 diff
→ 第 2 轮: 修正实现 → 52/56 passed → 反馈 diff
→ 第 3 轮: 修正实现 → 56/56 PASSED ✅
```

**输出**：`bench/` 目录下的 JSON 结果文件，包含每轮的详细记录。

**架构**：
1. Prompt 模板：融合 spec JSON + 少量示例 + 输出格式约束
2. LLM 调用层：统一接口，适配不同模型 API
3. 验证层：复用现有 `verify_consensus.py`（对比 AI 输出 vs 参考输出）
4. 反馈层：失败操作清单 + 正确期望 → 作为修正轮次的上下文

#### 4.3 找茬产品定位降级

README 结构调整：
- 第一节：项目定位（什么是 ΣLang、为什么需要它）
- 第二节：快速体验（`pip install sigma-lang` 三行代码看语义）
- 第三节：AI Benchmark（怎么用 ΣLang 评测 AI 的语义理解能力）← **新增核心**
- 第四节：找茬 Demo（规约→产品的最小可行闭环）← **降级为 demo 级**
- 第五节：协议编写指南（给自己的业务写规约）

### 🟡 P1 — 应该做（完善基础设施）

#### 4.4 通用 spec→verifier 引擎

**新文件**：`impl/python/sigma_engine.py`

不再为每个操作手写 Python 实现。引擎直接读 JSON spec，自动构建求值环境：

```python
# 不再需要手写:
# def task_create(a, b): return [a, b, 0, 0]

# 引擎从 spec JSON 自动推导:
engine = SigmaEngine.from_spec("spec_p0_socketkit.json")
result = engine.eval("task_create", [7, 100])  # → [7, 100, 0, 0]
```

**意义**：
- 新增操作只需要改 spec JSON，不需要改 verifier
- 手写 verifier 的"翻译错误"风险归零
- 为 Phase 3 的"AI 直接消费 JSON"铺路

#### 4.5 简化 corpus 格式

当前 corpus 是 Markdown 混合测试 + 期望。改为纯 JSON 格式（或 YAML），
与 spec JSON 共用同一份操作定义，语料只负责提供测试用例。

```json
{
  "module": "socketkit_taskflow_ok",
  "expected_verdict": "PASS",
  "spec": "spec_p0_socketkit.json",
  "tests": [
    {"sequence": [
      {"op": "task_create", "args": [7, 100], "expect": [7, 100, 0, 0]},
      {"op": "accept_task", "args": ["$_", 3], "expect": [7, 100, 1, 3]},
      {"op": "task_submit", "args": ["$_"], "expect": [7, 100, 2, 3]},
      {"op": "task_accept", "args": ["$_", 7], "expect": [7, 100, 3, 3]}
    ]}
  ]
}
```

### 🔵 P2 — 远期（生态与扩展）

#### 4.6 spec → judge 二进制

对接你提出的"自动生成 LeetCode 式评测系统"的想法：

1. 从 spec JSON 的操作签名自动生成 Hypothesis generator
2. 随机生成合法输入 → 参考实现产生期望输出
3. 打包成独立二进制：`spec2judge --spec spec_p0_socketkit.json --output judge_socketkit`
4. 用法：`./judge_socketkit --submission user.py --time-limit 2 --memory-limit 256`

#### 4.7 类型系统扩展

从 ℕ-only 扩展到：
- `Str`：字符串（有限字母表上的序列）
- `Time`：时间（编码为 unix epoch ℕ）
- `List⟨T⟩`：泛型列表
- `Option⟨T⟩`：可选值
- `Map⟨K, V⟩`：键值映射

#### 4.8 社区建设

- 发布 AI Benchmark 的首批结果（跨模型排行榜）
- 提供 spec 编写模板和最佳实践文档
- 开放 benchmark 提交（模型厂商可以来"打榜"）

---

## 五、Phase 1 的工期估算

| 任务 | 复杂度 | 工期 |
|------|--------|------|
| 4.1 spec JSON 格式设计 + 为 §SK 生成第一份 JSON | 中等（设计 + 格式），约 500 行 JSON | 2-3 天 |
| 4.2 AI Verifier Benchmark 工具链 (sigma-ai-bench.py) | 中等（约 300 行 Python），依赖 LLM API | 3-4 天 |
| 4.3 README 重构 + 定位调整 | 低（文档改动） | 1 天 |
| 4.4 通用 spec→verifier 引擎 (sigma_engine.py) | 中高（约 500 行 Python），需正确实现 ℕ 子集操作 | 4-5 天 |
| 4.5 corpus JSON 格式迁移工具 | 低（格式转换脚本） | 1-2 天 |

**总计**：约 2 周可完成 Phase 1 全链路（从 JSON spec → AI 生成实现 → 通过 consensus gate）。

---

## 六、成功标准

### Phase 1 验收条件

- [ ] 至少 1 份 spec（§SK）有完整的 JSON 格式，与 Markdown 语义等价
- [ ] `sigma-ai-bench.py` 可跑通至少 1 个模型的自动化测试
- [x] 至少 1 个 AI 模型能在 ≤ 3 轮自我修正后通过 consensus gate（≥ 50/56）——✅ **已完成（2026-08-12）**：5 个模型实证（deepseek-chat / zai-subagent / qwen3dot8max / seed2dot1turbo / hy3）全部 60/60 通过，详见 `docs/cross_tool_report.html` 与 `bench/leaderboard.json`
- [ ] README 定位已修正

### Phase 2 验收条件

- [ ] 至少 2 个不同 AI 模型各自独立通过 consensus gate
- [ ] 跨模型一致性矩阵已发布
- [ ] 通用 verifier 引擎可消费 JSON spec 并正确求值

### Phase 3 验收条件

- [ ] spec JSON 成为 canonical（不再依赖 Markdown spec 正本）
- [ ] spec → judge 二进制可一键生成
- [ ] 至少 3 个外部项目/团队使用 ΣLang spec 定义自己的业务规则

---

## 七、不做的事

以下方向在 Phase 1-2 明确**不投入**：

- ❌ 扩展更多业务域（spec 数量从 3 个扩到 N 个）——先解决 AI 通路，再扩域
- ❌ 优化找茬产品（加功能/改 UI）——它是 demo，不是产品目标
- ❌ 给 corpus 加更多模块（56 → 100）——converge 了就别刷数
- ❌ 完善 z3 证明（358 → 500）——优先度低于 AI pipeline
- ❌ Rust/Elixir verifier 功能开发——三端参考实现已足够作为 ground truth

**一句话**：当前阶段所有精力聚焦于一件事——**让 AI 能消费 spec 并自证一致**。
