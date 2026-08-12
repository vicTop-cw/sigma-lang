---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 9f2a11add43fbf12a546606fb2b962ab_ba8d07568d7d11f196d8525400f8a581
    ReservedCode1: mDw4RkGQhmoXriChPW1y8uAeGLTUKR7LTtVVK6shiaXc2rZ3XsgXQEMKxkPer/PCdZcb5aucga996aYUlulURYZoOAQ7LrPIfXvtjpmHWTDG2xZ8OCOyXkCpRkO/TBYnsMyzEBGfCubT1uNVhrlJdRjXn3g8+eQxQmjHyG3hNkpBppdOWszZymfJUV0=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 9f2a11add43fbf12a546606fb2b962ab_ba8d07568d7d11f196d8525400f8a581
    ReservedCode2: mDw4RkGQhmoXriChPW1y8uAeGLTUKR7LTtVVK6shiaXc2rZ3XsgXQEMKxkPer/PCdZcb5aucga996aYUlulURYZoOAQ7LrPIfXvtjpmHWTDG2xZ8OCOyXkCpRkO/TBYnsMyzEBGfCubT1uNVhrlJdRjXn3g8+eQxQmjHyG3hNkpBppdOWszZymfJUV0=
---

# ΣLang — A Specification Protocol for Verifiable AI Consensus

[![PyPI version](https://img.shields.io/pypi/v/sigma-lang?color=blue&label=PyPI%20version)](https://pypi.org/project/sigma-lang/)
[![PyPI downloads](https://img.shields.io/pypi/dm/sigma-lang?label=PyPI%20downloads)](https://pypi.org/project/sigma-lang/)
[![spec](https://img.shields.io/badge/spec-0.7.0-1a237e)](spec/)

> **ΣLang** — A Specification Protocol for Verifiable AI Consensus.
> Through verifiable specifications + consensus gates, different AI systems produce
> identical behavior on the same business rules.
>
> **ΣLang（中文）** — 面向可验证 AI 共识的规约协议。
> 通过可验证的规约 + 共识门禁，让不同 AI 系统对同一份业务规则产出完全一致的行为。
>
> **当前阶段**：Phase 0 人工参考实现已对齐（consensus 56/56、z3 358 PROVED），
> Phase 1 AI 自主实现验证中。

---

## 1. 项目定位 / What is ΣLang?

**一句话**：ΣLang 是一套"AI 都能看懂、且大家都认账"的业务规则说明书——把"找茬平台
怎么发单、接单、验收、算钱"这类事，写成任何人都能读、任何 AI 都能执行、而且三个
独立验证器结论完全一致的文档。

ΣLang 不是传统意义上的编程语言，而是**智能体之间的合约**：

- ✅ Deterministic semantics / 确定性语义
- ✅ Symbol-anchored meaning / 符号锚定的含义
- ✅ Markdown as source code / Markdown 即源码（Phase 1 起另有 JSON 机器可解析格式）
- ✅ Ownership-aware dataflow / 所有权感知的数据流
- ✅ Zero syntactic ambiguity / 零语法歧义
- ✅ Verifier-enforced consistency / 验证器强制一致性

**打个比方**：想象三个裁判（Python / Rust / Elixir 各一个），同时读同一份规则书，
然后对同一个业务动作下判罚。ΣLang 的要求是：**三个裁判必须给出一模一样的判罚**，
差一个字都不行——这就是"共识门禁"（Law XIII，56/56 全绿）。

**为什么需要它**：现在 AI 各说各话——同一个"验收"动作，不同 AI 可能理解成不同意思。
ΣLang 给业务规则一个**唯一、可验证、可证明**的语义，AI 之间协作时说的"验收"就是
同一个"验收"。

**定位说明（2026-08-11 调整）**：项目定位从 "AI-Native Semantic Protocol"（暗示
协议与 AI 之间已有运行时通路）调整为 **"A Specification Protocol for Verifiable AI
Consensus"**（描述目标与路径）：

| 之前 | 之后 |
|------|------|
| "AI 原生语义协议"（暗示已实现） | "面向可验证 AI 共识的规约协议"（描述目标） |
| 找茬产品是旗舰应用 | 找茬是规约的最小可行 demo |
| 三端一致是最终成果 | 三端一致是 ground truth 标尺——用来测量 AI 的语义理解能力 |

**仓库里有什么**（5 样东西）：

| 东西 | 是啥 | 大白话 |
|------|------|--------|
| `spec/` | 规范 | 规则说明书（业务规则怎么写） |
| `impl/` | 三个验证器 | Python / Rust / Elixir 三个裁判 |
| `corpus/` | 语料 | 考试题（每道题三个裁判都要判一致） |
| `tools/` | 证明工具 | 用数学（z3）证明规则永远不会出错 |
| `web/` + App | 找茬产品 | 一个真的能跑起来的例子：找茬平台 |

**现在做到哪了**：三块业务语义（找茬 / 金融 / 供应链）已全链路打通——三端共识
**56/56**、算法正确性 **109/109**、数学证明 **358 项 PROVED**、一键验收 **10/10
门禁**、找茬产品一条命令启动（`python3 impl/python/sigma_app.py --launch`）、PyPI
发布（`pip install sigma-lang`）。

**接下来做什么（Phase 1）**：Phase 0（人工参考实现对齐）已完成——它证明了 spec 对
**人类**没有歧义。下一步是**让 AI 读 spec 并自主产出通过 consensus gate 的实现**：
用 AI Verifier Benchmark 评测不同模型"从规约中提取精确语义"的能力（见第 3 节），
直至任何 AI 模型可消费 spec 并自证一致（Phase 3）。

---

## 2. 快速体验 / Quick Start

### 2.1 三行代码看语义（pip 安装）

> `pip install sigma-lang`（已在 PyPI 发布：pypi.org/project/sigma-lang）——装完即可
> `import sigma_core`，零第三方依赖的纯函数库。

```python
import sigma_core as core
task = core.task_create(7, 100)    # 发单 → [7, 100, 0, 0]
task = core.accept_task(task, 3)   # 接单 → [7, 100, 1, 3]
task = core.task_accept(task, 7)   # 验收 → [7, 100, 3, 3]
```

你拿到的行为与三端验证器共识一致——就是协议保证的行为。也可走 HTTP：
`curl "http://127.0.0.1:8080/post?author=7&bounty=100"`。

### 2.2 一条命令启动找茬 Demo（不写代码）

> 依赖：Python 3.8+（三端验证可选装 Rust/Elixir，运行 demo 只需 Python）。

```sh
git clone https://github.com/vicTop-cw/sigma-lang.git
cd sigma-lang
make deploy        # 就绪检查通过后自动启动前后端（Windows 无 make，用下面两条）
python3 impl/python/sigma_app.py --launch-ready
python3 impl/python/sigma_app.py --launch
```

浏览器打开 http://127.0.0.1:8000 —— 注册用户、发单、接单、验收、提现、勋章，全流程
可用；API 在 http://127.0.0.1:8080（端点见 `docs/api_zhaocha.md`），运行面板
http://127.0.0.1:8080/panel。

### 2.3 三域概览（协议已承载三个独立领域）

| 域 | 规范 | 语义 | 语料 |
|----|------|------|------|
| §SK 找茬业务（App 行为） | `spec/spec_p0_socketkit.md` | task_create / accept_task / task_submit / task_accept + 五大制度 + 增长期（核验师/督导/团机制/预支/可追溯） | `corpus/socketkit_ok.md` + `socketkit_growth_ok.md` |
| §PF 金融（投资组合） | `spec/spec_p0_portfolio.md` | portfolio_new / buy / sell / portfolio_value / risk_score | `corpus/portfolio_ok.md` |
| §IN 供应链（库存） | `spec/spec_p0_inventory.md` | inventory_new / receive_stock / ship_stock / stock_level / fill_rate | `corpus/inventory_ok.md` |

### 2.4 快速开始命令

```sh
python3 verify_consensus.py                  # 三端共识门禁（56/56 全绿）
python3 verify_p0.py                         # 算法正确性（109/109）
python3 tools/sigma-runtime.py --domains     # 三域审计故事线（96/96）
python3 tools/sigma-prove.py corpus/socketkit_ok.md corpus/portfolio_ok.md corpus/inventory_ok.md  # z3 义务消解（358 项 PROVED）
python3 impl/python/sigma_app.py --smoke     # 找茬 MVP 参考后端 HTTP 冒烟
```

### 2.5 验证清单（任何改动后必须全绿）

```sh
# 1. 三端共识（Law XIII 门禁）
python3 verify_consensus.py                    # 56/56
# 2. 三端 §SK 自检
cd impl/verifier && cargo run -q -- --***      # 88/88
cd impl/elixir_rt && elixir sigma_verify.exs --***  # 88/88
python3 impl/python/sigma_core.py              # 167/167
# 3. 三端编译
cd impl/verifier && cargo build                # 0 error / 0 warning
# 4. 证明与运行时
python3 tools/sigma-prove.py corpus/socketkit_ok.md corpus/portfolio_ok.md corpus/inventory_ok.md
python3 tools/sigma-runtime.py --domains       # 96/96
```

> 三端一致（Law XIII）是 ΣLang 的核心承诺：**一个符号、一种含义、一个结果——谁来算
> 都一样。**

---

## 3. AI Benchmark / 用 ΣLang 评测 AI 的语义理解能力

> 本节是 ΣLang 的新核心定位：三端一致不是终点，而是 ground truth 标尺——用它来
> 测量 AI 的语义理解能力。

### 3.1 为什么需要它

Phase 0 已经证明：同一份 spec，三个**人类**程序员（不同语言、不同思维方式）读完后
结论完全一致（56/56）。下一个问题是：**AI 能不能做到？**

不同 AI 读同一份业务规则，目前各说各话——GPT 一种解读、Claude 另一种、Gemini 又一种。
这不是加 benchmark 数据集能解决的，需要的是"精确语义"的测量标尺。ΣLang 的独特定位：

> **不是又一个 benchmark 数据集——是衡量 AI 语义理解精确度的工具。**
> 对模型厂商的吸引力：你的模型能读懂形式化规约吗？来这里测。

### 3.2 评测流程（Phase 1）

1. 给模型同一份 spec（机器可解析的 spec JSON，见 §5.2）；
2. 模型生成 Python 实现（`impl/python/sigma_core_ai.py`）；
3. 自动跑 `verify_consensus.py`，对比 AI 实现 vs 人工参考（ground truth，56/56）；
4. 失败 → 反馈失败操作清单 + 正确期望（diff）→ 模型自我修正 → 重跑，最多 3 轮；
5. 记录每轮结果，产出跨模型一致性矩阵与排行榜。

给任何 AI（Claude / GPT / 其他 Agent）的标准 prompt 模板：

> 你是 ΣLang 协议的开发者。先读 `README.md` 的"快速体验"和"协议编写指南"，
> 再读 `spec/spec_p0_socketkit.md` 掌握业务规则写法。你的任务：
> 1. 用 `impl/python/sigma_core.py` 的纯函数实现业务逻辑（禁止自己重新定义规则）；
> 2. 用 `python3 verify_consensus.py` 确认语义与三个验证器一致；
> 3. 改完必须 `python3 tools/sigma-accept.py` 十道门禁全绿。
> 规则以 spec/ 为准，语料在 corpus/，任何不一致先查 spec 再改实现。

### 3.3 工具：sigma-ai-bench.py（Phase 1 新增，建设中）

```sh
python3 tools/sigma-ai-bench.py --model claude-4 --spec spec_p0_socketkit.json --rounds 3
```

| 参数 | 说明 |
|------|------|
| `--model` | 目标模型名（Claude / GPT / Gemini / DeepSeek / 国产模型等，统一 LLM 调用层适配） |
| `--spec` | 机器可解析的 spec JSON（§5.2 格式） |
| `--rounds` | 允许的自我修正轮数上限（默认 3） |
| `--mock` | **不调用真实 LLM API**：用确定性脚本模拟"生成 → 修正"链路，跑通整条流水线（工具链自检 / CI 用，不消耗 API 额度） |

输出示例（形如，数字为示意）：

```
→ 第 1 轮: 生成实现 → 43/56 passed → 反馈 diff
→ 第 2 轮: 修正实现 → 52/56 passed → 反馈 diff
→ 第 3 轮: 修正实现 → 56/56 PASSED ✅
```

工具链架构：Prompt 模板（spec JSON + 少量示例 + 输出格式约束）→ LLM 调用层（统一
接口适配不同模型 API）→ 验证层（复用 `verify_consensus.py`）→ 反馈层（失败操作清单
+ 正确期望，作为修正轮次上下文）。

### 3.4 产出物：bench/results.json

每次评测写入 `bench/` 目录下的 JSON 结果文件，每轮记录：

- 模型名、spec 版本、尝试次数；
- 该轮 consensus 通过率（x/56）；
- **失败操作清单**——哪个模型对哪些操作出错，比总分更有诊断价值；
- 是否在 ≤ 3 轮内通过 consensus gate（Phase 1 验收标准：≥ 50/56）。

跨模型汇总后即得到**一致性矩阵**：行是模型、列是操作，格子里是"通过 / 出错"。
哪些操作被普遍误解、哪个模型全过——一目了然，最终输出排行榜：哪个模型在"从规约中
提取精确语义"这项能力上最强。

### 3.5 排行榜：5 模型实证（2026-08-12）

五个完全独立的 AI 实现者（来自不同厂商 / 不同训练生态），各自仅凭同一份
`spec_p0_socketkit.json`（22 个操作）独立实现，跑同一套 60 条测试——**全部 60/60
通过，跨工具一致率 100%（300 次测试，0 失败）**：

| 模型 | 来源 / 工具 | 方式 | 通过率 |
|------|-------------|------|---------|
| deepseek-chat | 真实 API | bench 驱动，3 轮反馈循环（source=api） | 60/60 × 3 轮（100%） |
| zai-subagent | 本机 Agent 集群 | 独立子代理读 JSON 实现（source=agent） | 60/60（100%） |
| qwen3dot8max | Qoder | 手动：读 JSON 手写实现（source=manual） | 60/60（100%） |
| seed2dot1turbo | TRAE（字节） | 手动：读 JSON 手写实现（source=manual） | 60/60（100%） |
| hy3 | WorkBuddy（腾讯） | 手动：通用解释器实现（source=manual） | 60/60（100%） |

> 数据可追溯：三份手动报告与实现文件在 `tests/reports/`（`Hy3.md` /
> `Qwen3dot8Max.md` / `Seed2dot1Turbo.md` 及 `_impl_*.py`）；跨工具汇总与实现差异
> 分析见 `docs/cross_tool_report.html`；机器可读明细见 `bench/leaderboard.json`。
> 结论：**规约"机器可解析"的承诺被五个独立 AI 实证——行为层零分歧**；表示层仍有
> 6 处改进点（错误名、min/max 重载、constants 区等），已沉淀进
> `docs/spec-template.md` 最佳实践。

### 3.6 路线图

```
Phase 0 ──────→ Phase 1 ──────→ Phase 2 ──────→ Phase 3
[已完成]        [进行中]         [中期]           [远期]
人工参考对齐    AI 替代 1 个     AI 替代 2 个     协议原生
56/56 consensus  verifier         verifier         无需人工翻译
```

- **Phase 0 ✅（已完成）**：三个独立人工实现（Python / Rust / Elixir）对同一份 spec
  逐项一致——spec 对人类无歧义，是后续所有 AI 实验的基准线；
- **Phase 1 🚀（下一步）**：AI 读 spec → 生成实现 → 过 consensus gate（本节的
  sigma-ai-bench.py）；配套整改：spec JSON 机器可解析格式（§5.2）、通用 spec→verifier
  引擎、corpus JSON 化；
- **Phase 2（中期）**：不同模型各自独立读 spec、各自独立生成实现，跨模型互相对齐且
  与人工参考对齐——"AI 之间通过协议达成共识"；
- **Phase 3（远期）**：spec JSON 成为 canonical，任何 AI 系统直接解析 spec 产生执行
  行为，无需人工翻译。

> 完整的整改路线图见 `docs/ROADMAP.md`。

---

## 4. 找茬 Demo / 规约 → 产品的最小可行闭环

### 4.1 定位

找茬产品是**规约 → 产品的最小可行闭环的参考 demo**：证明"业务规则先以 ΣLang 语义
存在并被证明，然后才是任何语言的实现"。它是 demo，不是旗舰——ΣLang 的主角是规约与
共识门禁（第 3 节），找茬是第一个吃螃蟹的落地例子。

### 4.2 功能 ↔ §SK 语义对照

每个业务动作都对应一个被三端共识、z3 可证明的 ΣLang 操作：

| 找茬功能 | §SK 语义（spec_p0_socketkit.md） |
|---------|----------------------------------|
| 注册 / 会话 | `register` / `me`（App 层，用户态隔离） |
| 月度发单额度 | `quota_new` / `quota_use` / `quota_reset` / `quota_advance` |
| 发需求（赏金托管） | `task_create` + `points_hold` |
| 接单 | `accept_task` |
| 提交成果 | `task_submit` |
| 验收确认（受茬人） | `task_accept`（需 caller ≡ 作者） |
| 赏金提现 | `points_release` + `points_withdraw` |
| 契分 / 贡献 / 勋章 | `credit_score` / `contribution_score` / `badge_level` |
| 核验师签发勋章 | `badge_issue`（v ≥ 1000 授权核验师） |
| 督导处理纠纷 | `dispute_review` |
| 受茬团 / 找茬团 | `team_create` / `team_join` / `team_share` |
| 积分来源可追溯 | `points_ledger` |

### 4.3 启动与运行

```sh
python3 impl/python/sigma_app.py --launch
# 启动自检通过 → 前端 http://127.0.0.1:8000 · API http://127.0.0.1:8080（Ctrl+C 停止）
```

| 入口 | 地址 | 说明 |
|------|------|------|
| 前端页面 | `http://127.0.0.1:8000` | 注册/开户/发单/接单/提交/验收/提现/勋章（web/index.html，后端地址可在 localStorage `sigma_base` 配） |
| API | `http://127.0.0.1:8080` | 全部业务端点（见 `docs/api_zhaocha.md`） |
| 运行面板 | `http://127.0.0.1:8080/panel` | 业务摘要 + 门禁摘要 |
| 健康检查 | `http://127.0.0.1:8080/health` | 服务状态 + 配置摘要 |

**完整使用流程（§SK.6）**：注册两个用户（作者 7 / 找茬人 3）→ 作者开户额度（50）→
发单（作者 7，赏金 100）→ 接单（找茬人 3）→ 提交 → 验收（作者 7 确认）→ 提现
（找茬人 100）→ 勋章（契分 105）。

### 4.4 验收与上线

- **运行验收**：`python3 impl/python/sigma_app.py --run-accept` —— 8 项端到端
  （启动自检 / 双服务在线 / 全链路业务流 / /panel 实时数据 / 状态可持久化 / 审计可对账）；
- **协议门禁**：`python3 tools/sigma-accept.py --report acceptance.json` —— 十道门禁
  一键验收（本地与 CI 同一条命令）；
- **上线启动**：

```sh
python3 impl/python/sigma_app.py --launch \
  --port 8080 --web-port 8000 \
  --auth-token SECRET \
  --state data/state.json --audit-log data/audit.json --log-file data/app.log
# 未显式指定 --state/--audit-log/--log-file 时自动落到 data/ 默认路径
```

- **上线验收**：`python3 impl/python/sigma_app.py --deploy-accept`（9 项端到端）→
  `python3 tools/sigma-accept.py --report acceptance.json`（十道门禁 + 运行验收
  runtime 段）；
- **运维要点**：数据在 `data/`（定期备份 state.json）；审计可对账（每个业务动作的
  ΣLang 事件）；`GET /health` 监控服务状态；`GET /panel` 看运行状态与门禁摘要；
  并发安全有 `--concurrency-test` 兜底；
- 详细部署与运维见 `docs/deploy_zhaocha.md`。

### 4.5 上线检查清单（开工前逐项勾选）

| # | 检查项 | 命令 | 期望 |
|---|--------|------|------|
| 1 | 启动自检 | `python3 impl/python/sigma_app.py --serve`（去掉 --skip-startup-check） | 先过 §SK.6 门禁再监听，失败拒绝启动 |
| 2 | 鉴权 | `--serve --auth-token SECRET` | 未带 ?token= 返回 401 |
| 3 | 状态持久化 | `--state state.json` | 重启不丢；原子写崩溃不损坏 |
| 4 | 审计日志 | `--audit-log audit.json` | 每个业务动作的 ΣLang 事件，可对账 |
| 5 | 访问日志 | `--log-file app.log` | 2xx=INFO / 4xx=WARNING 分级 |
| 6 | 健康检查 | `GET /health` | status ok + 门禁摘要 |
| 7 | HTTP 方法 | 前端用 POST 变更、GET 查询 | 变更/查询端点双方法可用 |
| 8 | 业务流剧本 | `--scenario` + `--frontend-scenario` | CLI 与前端视角全绿 |
| 9 | 双端对账 | Python `--smoke` 与 Rust `--app-smoke` | 双端逐项一致 |
| 10 | 一键门禁 | `python3 tools/sigma-accept.py` | 10/10 全绿 |

> 任何一项未过 = 开工放行前必须修复；门禁数字以当前 milestone 为准。

---

## 5. 协议编写指南 / 写你自己的规约

### 5.1 五步法（不用这个仓库的产品，只借它的协议能力）

1. **读规范**：`spec/spec_p0_socketkit.md`（找茬）/ `spec_p0_inventory.md`（供应链）
   ——看业务规则怎么写；模板见 `docs/spec-template.md`；
2. **抄格式写自己的规则**：把业务操作（如"验收"）写成 函数 + 定律 + 测试；
3. **三端验证**：`python3 verify_consensus.py`（Python/Rust/Elixir 三个验证器结论
   必须一致）；
4. **数学证明**：`python3 tools/sigma-prove.py`（z3 证明你的规则不会自相矛盾）；
5. **一键验收**：`python3 tools/sigma-accept.py`（十道门禁全绿才算合格）。

扩展阅读：`docs/TUTORIAL.md`（30 分钟上手）、`docs/USAGE.md`（分角色上手）、
`docs/CONTRIBUTING.md`（贡献者指南）。

### 5.2 spec JSON：机器可解析格式（Phase 1 落地中）

Markdown 是人读格式，AI 解析不稳定。Phase 1 为每份 `spec_p0_*.md` 提供等价的
`spec_p0_*.json`，让 AI 直接从结构化 JSON 提取语义，consensus gate 也直接消费
JSON spec——"翻译出错"这个 bug 源头被消除。顶层结构：

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
      "definition": {"kind": "lambda", "params": ["a", "b"], "body": ["a", "b", 0, 0]},
      "preconditions": [{"expr": "b >= 0", "error": "BountyErr"}],
      "laws": [
        {"forall": ["a", "b"], "predicate": "index(task_create(a, b), 2) == 0",
         "description": "freshly created task is open"}
      ],
      "tests": [
        {"input": [7, 100], "output": [7, 100, 0, 0]},
        {"input": [1, -5], "output": null, "error": "BountyErr"}
      ]
    }
  ]
}
```

- 类型声明（`types`）：`alias` / `list` / `enum` / `option` / `map`，基础类型
  `nat` / `int` / `str` / `bool` / `List<T>` / `Option<T>` / `unit`；
- 操作声明（`operations`）：`fingerprint`（指纹）/ `signature`（签名）/
  `definition`（lambda / table 状态机 / expression 三种定义体）/ `preconditions`
  （前置条件 + 错误码）/ `laws`（定律，forall 谓词）/ `tests`（输入输出对）；
- **完整字段定义与校验规则见 `spec/json-schema.md`（v1.0）**——写 JSON spec 前必读。

### 5.3 架构与数据流

```text
  spec/ 规范（英文为准 + spec/zh 中文参考）
   │  定义操作：指纹 / 签名 / 定律 / 测试（真实函数调用）
   ▼
  corpus/ 语料（56 个模块：ok 期望 PASS，break 期望 FAIL）
   │  三端验证器独立解析 + 求值（eval_expr 真实调用 §SK/§PF/§IN）
   ├──▶ Python verify_consensus.py ─┐
   ├──▶ Rust  impl/verifier        ├──▶ Law XIII 共识门禁（56/56 全绿）
   └──▶ Elixir impl/elixir_rt      ─┘
   │
   ├──▶ tools/sigma-prove.py     z3 义务消解（358 项 PROVED）
   ├──▶ tools/sigma-runtime.py   审计运行时（trace + --domains 96/96）
   ├──▶ impl/python/sigma_app.py 找茬参考后端（自检 + 冒烟 + 持久化/审计）
   └──▶ tools/sigma-accept.py    一键验收（十道门禁）→ GitHub Actions CI
```

**两种验证模式**（互补而非冗余）：

| 工具 | 模式 | 检查内容 |
|------|------|---------|
| `verify_p0.py` | 算法正确性 | 109 tests over §T/§E/§C/§I/§SK 模块算法（Lamport 时钟、Result monad、置信度运算、I/O 效应、SocketKit 行为）——证明 P0 语义可实现。不解析 .md spec。 |
| `verify_consensus.py` | 规范一致性 | 解析 .md spec，应用 Laws I–XVII + E-03/06/07/10 + §S/P-01 检查，要求 56/56 语料模块在 Python / Rust / Elixir 上判定一致（Law XIII 门禁）。 |

**工具链职责**：

| 工具 | 职责 | 结果 |
|------|------|------|
| `verify_consensus.py` | 三端验证器对语料模块独立判定（Python/Rust/Elixir/Expected） | 56/56 一致 |
| `verify_p0.py` | 算法正确性（含 §SK 语义检查） | 109/109 |
| `tools/sigma-prove.py` | 把语料定律编码为 z3 义务并消解 | 358 项 PROVED |
| `tools/sigma-runtime.py` | 审计运行时：逐事件复核定律（trace / --story / --growth / --inventory / --domains） | --domains 96/96 |
| `impl/python/sigma_app.py` | 找茬 MVP 参考后端：业务全委托 §SK，App 只管状态 | 自检 + 冒烟 + 持久化/审计 |
| `tools/sigma-accept.py` | 十道门禁一键验收（本地与 CI 同一条命令） | 10/10 |
| `.github/workflows/ci.yml` | push/PR 自动验收，全绿才算过 | CI 门禁 |

**一条语义的旅程**（以 §SK `task_create` 为例）：

1. `spec/spec_p0_socketkit.md` 定义指纹 `0xF001`、签名、定律与测试；
2. `corpus/socketkit_taskflow_ok.md` 把它写成**真实函数调用**测试；
3. Python / Rust / Elixir 三个独立验证器各自求值，结果必须逐项一致（Law XIII）；
4. `tools/sigma-prove.py` 把定律编码为 z3 义务，证明不可违反（P-01 结构 + 义务 PROVED）；
5. `tools/sigma-runtime.py` 在业务故事线里审计它的行为（input/output/定律复核）；
6. `impl/python/sigma_app.py` 的 `post_task` 直接委托它，并记录审计事件；
7. 任何改动后 `tools/sigma-accept.py` 十道门禁全绿，CI 放行。

> 整条链路的含义：**业务规则先以 ΣLang 语义存在并被证明，然后才是任何语言的实现**
> ——实现只是语义的投影。

### 5.4 设计理念

**三层架构**：

```
L0 — Core (core@1.0)        ← 不可变，始终加载
     ℕ ℤ ℚ ℝ ℂ 𝔹 Sym Prop λ ∀ ∃
     + Iron Laws + Verifier interface

L1 — Standard Library          ← 社区维护，版本化
     math.calculus / math.linear / finance.base
     signal.fourier / stat.prob / opt.gradient

L2 — User Packages            ← 任何人可发布
     emoji.finance / tcm.wuzang / physics.qft
     must pass Verifier Iron Laws / 必须通过验证器铁律
```

**十七条铁律**：

```
Law I    — Fingerprint Uniqueness / 指纹唯一性
Law II   — Encoding to ℕ (everything → number) / 编码到 ℕ
Law III  — Law Declaration (every op has laws) / 定律声明
Law IV   — Test Mandatory (≥1 canonical test per op) / 测试强制
Law V    — No Implementation in Spec / 规范中无实现
Law VI   — Backward Compatibility (published = frozen) / 向后兼容
Law VII  — Explicit Dependencies (no circular deps) / 显式依赖
Law VIII — Temporal Determinism (timing bounds declared) / 时序确定性
Law IX   — Calibration Requirement (confidence matches accuracy) / 校准要求
Law X    — Effect Transparency (all effects declared) / 效应透明
Law XI   — Capability Discipline (FFI needs explicit caps) / 能力纪律
Law XII  — Resource Linearity (open = closed exactly once) / 资源线性
Law XIII — Verifier Consensus / 验证器共识
Law XIV  — Negative Test Mandatory / 负向测试强制
Law XV   — Export Completeness / 导出完整性
Law XVI  — Compatibility Proof / 兼容性证明
Law XVII — Probabilistic Guarantee / 概率保证
```

Laws I–XII 定义于 `spec/spec_p0_foundations.md` §0；Laws XIII–XVII 及 Law VIII 扩展
E-10（评估确定性）定义于 `spec/spec_top_extensions.md`，由全部三个验证器强制执行。

### 5.5 为什么需要 ΣLang

**问题**：把同一份 Markdown 文档交给不同的 AI——GPT-4 一种解读、Claude 另一种、
Gemini 第三种。**同样的输入，不同的输出。这对生产级 AI 系统来说是不可接受的。**

**方案**：ΣLang 用**数学锚定的符号**替换歧义的自然语言：

| 传统 | ΣLang |
|------|-------|
| "把数字加起来" | `a ⊕ b` with associativity law / 带结合律 |
| "如果分数 >= 90" | `grade(s) ≝ if s<60 then 𝗀𝖣 else…` + 边界测试 |
| "大概是真的" | `⊢_0.73 P` with calibration law / 带校准律 |
| "发送消息" | `send(addr, msg)` with causal ordering / 带因果序 |

### 5.6 目录结构

```
sigma-lang/
├── README.md                       # Project entry (this file) / 项目入口（本文件）
├── LICENSE                         # MIT
├── verify_p0.py                    # Algorithmic verification (109 tests) / 算法验证
├── verify_consensus.py             # Three-verifier consensus check / 三验证器共识检查
│
├── spec/                           # English specifications (normative) / 英文规范（规范性）
│   ├── spec_p0_foundations.md      # ⭐ Main P0 specification (整合版核心入口)
│   ├── spec_p0_time.md             # §T Full time & causality spec
│   ├── spec_p0_error.md            # §E Full error algebra spec
│   ├── spec_p0_confidence.md       # §C Full confidence & probability spec
│   ├── spec_p0_io.md               # §I Full I/O & effects spec
│   ├── spec_p0_socketkit.md        # §SK 找茬业务
│   ├── spec_p0_portfolio.md        # §PF 金融（投资组合）
│   ├── spec_p0_inventory.md        # §IN 供应链（库存）
│   ├── spec_top_rules.md           # ⭐ Top-level rules: §S shadowing + §C constants + §G conflict
│   ├── spec_top_extensions.md      # Top-level rules: Law XIII–XVII + E-10 extensions
│   ├── spec_top_proofs.md          # Proof-carrying spec structure (P-01 enforced)
│   ├── json-schema.md              # Spec JSON Schema v1.0（机器可解析格式规范）
│   └── zh/                         # Chinese translations / 中文翻译
│
├── archive/                        # Deprecated / superseded specs / 废弃/已替代的规范
├── corpus/                         # Shared test corpus (56 modules) / 共享测试语料库
├── examples/                       # Usage examples / 使用示例
├── impl/                           # Verifier implementations / 验证器实现
│   ├── verifier/                   # Rust reference Verifier
│   ├── elixir_rt/                  # Elixir/BEAM verifier + runtime
│   └── python/                     # sigma_core.py — minimal reference core
├── tools/                          # Tooling (sigma-prove, sigma-ai-bench…) / 工具
└── .github/workflows/              # CI: consensus gate
```

### 5.7 文档导航

- **入门**：[spec_p0_foundations.md](spec/spec_p0_foundations.md) —— P0 核心规范，
  涵盖 17 条铁律、核心类型、包系统、§T/§E/§C/§I 模块和验证器架构；
- **核心模块**：[spec_p0_time.md](spec/spec_p0_time.md)（§T 17/17）·
  [spec_p0_error.md](spec/spec_p0_error.md)（§E 16/16）·
  [spec_p0_confidence.md](spec/spec_p0_confidence.md)（§C 37/37）·
  [spec_p0_io.md](spec/spec_p0_io.md)（§I 25/25）；
- **业务域**：[spec_p0_socketkit.md](spec/spec_p0_socketkit.md)（§SK 找茬）·
  [spec_p0_portfolio.md](spec/spec_p0_portfolio.md)（§PF 金融）·
  [spec_p0_inventory.md](spec/spec_p0_inventory.md)（§IN 供应链）；
- **顶层治理**：[spec_top_rules.md](spec/spec_top_rules.md)（§S 遮蔽与绑定纪律、§C
  现实常量、§G 冲突裁决、规则索引）· [spec_top_extensions.md](spec/spec_top_extensions.md)
  （Laws XIII–XVII + E-10 评估确定性）· [spec_pki_feasibility.md](spec/spec_pki_feasibility.md)
  （信任与溯源 PKI 可行性研究）· [spec_top_proofs.md](spec/spec_top_proofs.md)
  （P-01 证明携带结构）；
- **中文翻译**：`spec/zh/`（spec_p0_foundations_zh.md 等）。

> **注意**：`spec/` 目录为权威英文原版；`spec/zh/` 为中文参考翻译，如有出入以英文
> 原版为准。

### 5.8 废弃与归档

| 文件 | 原因 |
|------|------|
| `archive/spec.md` | v0.1 初稿 — 已被 `spec/spec_p0_foundations.md` (v0.3.0) 取代。使用旧章节目录结构，缺少 §T/§E/§C/§I 模块化架构、Law XIII–XVII 和三验证器共识。 |
| `archive/spec_p0_shadowing.md` | §S Shadowing v0.2 — 明确标记为 SUPERSEDED，内容已合并到 `spec/spec_top_rules.md` §S（2026-08-01）。 |

---

## 6. 项目状态 / Status

### 6.1 状态总览

| Module / 模块 | Tests / 测试 | Status / 状态 |
|---------------|-------------|---------------|
| §T Time & Causal Order / 时间与因果序 | 17/17 | ✅ |
| §E Error Algebra / 错误代数 | 16/16 | ✅ |
| §C Confidence & Probabilistic Logic / 置信度与概率逻辑 | 37/37 | ✅ |
| §I I/O Boundary & Effects / I/O 边界与效应 | 25/25 | ✅ |
| §SK SocketKit Protocol / SocketKit 协议 | 14/14 | ✅ |
| **Total / 总计** | **109/109** | **✅** |

- **Verifier Consensus / 验证器共识**：**56/56** 语料模块在 Python / Rust / Elixir
  三个验证器上达成一致；
- **z3 义务消解**：**358 项 PROVED**；**一键验收**：**10/10 门禁**；**运行时不变量
  复核**：`--domains` **96/96**；三端 0 warning。

### 6.2 里程碑历史

> README 不再逐条堆叠版本记录（避免变成 changelog），完整逐条记录见仓库提交历史。
> 以下为关键节点：

| 里程碑 | 日期 | 要点 |
|--------|------|------|
| v0.10–v0.13 | 2026-08-02 | 协议雏形：数学符号/基本操作/常量包可用，SocketKit 协议定义，共识门禁 40/40 |
| v0.14–v0.24 | 2026-08-03 | 三端 §SK 执行层 + 找茬 MVP 参考实现，业务故事线三端逐项一致 |
| v0.27–v0.46 | 2026-08-03 | 找茬五大制度（额度/积分/勋章/核验师/督导）+ §PF 金融 / §IN 供应链两域自举（协议泛化性验证） |
| v0.47–v0.70 | 2026-08-04 | 三域概览/验证清单、找茬产品化（鉴权/持久化/审计/健康检查/分级日志）、产品落地指南 |
| v0.71–v0.100 | 2026-08-04 | 服务化十件套、一键开工 `--launch`、运行/上线指南，跨百版本里程碑 |
| v0.101–v0.130 | 2026-08-05 | 部署加固、性能基线、**PyPI 发布**（pip install sigma-lang 全球可用） |
| v0.131–v0.256 | 2026-08-05→06 | 发布链自动化（打 tag 即发布）、跨域联动/错误边界/标准库强化、前端三域面板、审计轨迹视图 |
| v0.257–v0.540 | 2026-08-06→07 | 链式不变量持续补强（INV-* 至 16 组）、批次推进至 41（小阶段 408/496）、PyPI 0.7.5 |

- **当前**：spec **0.7.0** · PyPI **0.7.5** · 里程碑 **v0.540**（批次 41 · 小阶段
  408/496，长期自主运行推进中）；
- **推进规则**：每 10 个小阶段同步仓库，每 100 个发布 PyPI；
- **下一步（Phase 1）**：AI Verifier Benchmark（第 3 节）——让 AI 消费 spec 并自证
  一致。

### 6.3 版本信息

| 项 | 值 |
|----|----|
| Milestone / 里程碑 | v0.540（批次 41） |
| Spec Version / 规范版本 | 0.7.0 |
| PyPI | sigma-lang 0.7.5 |
| License / 许可证 | MIT |
| Date / 日期 | 2026-08-07 |

## Citation / 引用

```
ΣLang: A Specification Protocol for Verifiable AI Consensus
Version 0.7.0
https://github.com/sigma-lang/sigma-lang
```

*（内容由AI生成，仅供参考）*
