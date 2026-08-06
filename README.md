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

# ΣLang — AI-Native Semantic Protocol

[![PyPI version](https://img.shields.io/pypi/v/sigma-lang?color=blue&label=PyPI%20version)](https://pypi.org/project/sigma-lang/)
[![PyPI downloads](https://img.shields.io/pypi/dm/sigma-lang?label=PyPI%20downloads)](https://pypi.org/project/sigma-lang/)
[![spec](https://img.shields.io/badge/spec-0.7.0-1a237e)](spec/)

> **Sigma Language** — A deterministic semantic protocol for AI systems.
> One symbol, one meaning, one result — across all models.

> **Sigma Language（ΣLang）** — 面向 AI 系统的确定性语义协议。
> 一个符号，一种含义，一个结果 — 跨所有模型一致。

---

## What is ΣLang? / 什么是 ΣLang？

ΣLang is **not a programming language** in the traditional sense.
It is a **contract between intelligences**.

ΣLang 不是传统意义上的编程语言，而是**智能体之间的合约**。

- ✅ Deterministic semantics / 确定性语义
- ✅ Symbol-anchored meaning / 符号锚定的含义
- ✅ Markdown as source code / Markdown 即源码
- ✅ Ownership-aware dataflow / 所有权感知的数据流
- ✅ Zero syntactic ambiguity / 零语法歧义
- ✅ Verifier-enforced consistency / 验证器强制一致性

---

## 大白话导读：这仓库到底在干嘛？（2026-08-05 更新）

**一句话**：ΣLang 是一套"AI 都能看懂、且大家都认账"的业务规则说明书——
把"找茬平台怎么发单、接单、验收、算钱"这类事，写成任何人都能读、任何 AI
都能执行、而且三个独立验证器结论完全一致的文档。

**打个比方**：想象三个裁判（Python / Rust / Elixir 各一个），同时读同一份
规则书，然后对同一个业务动作下判罚。ΣLang 的要求是：**三个裁判必须给出
一模一样的判罚**，差一个字都不行——这就是"共识门禁"。

**这仓库里有 5 样东西**：

| 东西 | 是啥 | 大白话 |
|------|------|--------|
| `spec/` | 规范 | 规则说明书（业务规则怎么写） |
| `impl/` | 三个验证器 | Python / Rust / Elixir 三个裁判 |
| `corpus/` | 语料 | 考试题（每道题三个裁判都要判一致） |
| `tools/` | 证明工具 | 用数学（z3）证明规则永远不会出错 |
| `web/` + App | 找茬产品 | 一个真的能跑起来的例子：找茬平台 |

**为什么需要它**：现在 AI 各说各话——同一个"验收"动作，不同 AI 可能理解成
不同意思。ΣLang 给业务规则一个**唯一、可验证、可证明**的语义，AI 之间协作
时说的"验收"就是同一个"验收"。

**现在做到哪了**：三块业务语义（找茬 / 金融 / 供应链）已全链路打通——
三端共识 56/56、数学证明 258 项 PROVED、找茬产品一条命令就能启动上线
（`python3 impl/python/sigma_app.py --launch`）。

---

## 怎么用它 / How to use it（2026-08-05）

**用法 1：把找茬产品跑起来（2 分钟，不写代码）**

> 依赖：Python 3.8+（三端验证可选装 Rust/Elixir，使用产品只需 Python）。

```sh
git clone https://github.com/vicTop-cw/sigma-lang.git
cd sigma-lang
make deploy        # 就绪检查通过后自动启动前后端（Windows 无 make，用下面两条）
python3 impl/python/sigma_app.py --launch-ready
python3 impl/python/sigma_app.py --launch
```
浏览器打开 http://127.0.0.1:8000 —— 注册用户、发单、接单、验收、提现、勋章，
全流程可用；API 在 http://127.0.0.1:8080（端点见 `docs/api_zhaocha.md`），
运行面板 http://127.0.0.1:8080/panel。

**用法 2：把 ΣLang 当"业务规则协议"（给 AI 定语义、验证规则）**

不用这个仓库的产品，只借它的协议能力：
1. 读规范：`spec/spec_p0_socketkit.md`（找茬）/ `spec_p0_inventory.md`（供应链）
   —— 看业务规则怎么写；
2. 抄格式写自己的规则：把业务操作（如"验收"）写成 `corpus/*.md` 那样的
   函数 + 定律 + 测试；
3. 三端验证：`python3 verify_consensus.py`（Python/Rust/Elixir 三个验证器
   结论必须一致）；
4. 数学证明：`python3 tools/sigma-prove.py`（z3 证明你的规则不会自相矛盾）；
5. 一键验收：`python3 tools/sigma-accept.py`（十道门禁全绿才算合格）。

**用法 3：把语义嵌入自己的项目（当库用，不碰协议）**

> 安装：`pip install sigma-lang`（**已在 PyPI 发布**：pypi.org/project/sigma-lang）
> ——装完即可 `import sigma_core`，零第三方依赖的纯函数库。

```python
import sigma_core as core
task = core.task_create(7, 100)    # 发单 → [7, 100, 0, 0]
task = core.accept_task(task, 3)   # 接单 → [7, 100, 1, 3]
task = core.task_accept(task, 7)   # 验收 → [7, 100, 3, 3]
```
或走 HTTP：`curl "http://127.0.0.1:8080/post?author=7&bounty=100"`。
你拿到的行为与三端验证器共识一致——就是协议保证的行为。

**用法 4：让别的 AI 智能体用（给 AI 的 prompt 模板）**

把下面这段发给任何 AI（Claude / GPT / 其他 Agent）：

> 你是 ΣLang 协议的开发者。先读 `README.md` 的"大白话导读"和"怎么用它"，
> 再读 `spec/spec_p0_socketkit.md` 掌握业务规则写法。你的任务：
> 1. 用 `impl/python/sigma_core.py` 的纯函数实现业务逻辑（禁止自己重新定义规则）；
> 2. 用 `python3 verify_consensus.py` 确认语义与三个验证器一致；
> 3. 改完必须 `python3 tools/sigma-accept.py` 十道门禁全绿。
> 规则以 spec/ 为准，语料在 corpus/，任何不一致先查 spec 再改实现。

**一句话总结**：想用产品 → 用法 1；想用协议 → 用法 2；想用语义 → 用法 3；
想教 AI 用 → 用法 4。详细分角色上手见 `docs/USAGE.md`。

---

## Quick Start / 新人 30 分钟上手（v0.47）

ΣLang 用一句话介绍：**给 AI 立的"度量衡"协议——同一份规则文档，
Python / Rust / Elixir 三个独立验证器必须给出完全一样的结论。**

### 三域概览（协议已承载三个独立领域）

| 域 | 规范 | 语义 | 语料 |
|----|------|------|------|
| §SK 找茬业务（App 行为） | `spec/spec_p0_socketkit.md` | task_create / accept_task / task_submit / task_accept + 五大制度 + 增长期（核验师/督导/团机制/预支/可追溯） | `corpus/socketkit_ok.md` + `socketkit_growth_ok.md` |
| §PF 金融（投资组合） | `spec/spec_p0_portfolio.md` | portfolio_new / buy / sell / portfolio_value / risk_score | `corpus/portfolio_ok.md` |
| §IN 供应链（库存） | `spec/spec_p0_inventory.md` | inventory_new / receive_stock / ship_stock / stock_level / fill_rate | `corpus/inventory_ok.md` |

### 快速开始命令

```sh
python3 verify_consensus.py                  # 三端共识门禁（47/47 全绿）
python3 verify_p0.py                         # 算法正确性（109/109）
python3 tools/sigma-runtime.py --domains     # 三域审计故事线一次跑通（72/72）
python3 tools/sigma-prove.py corpus/socketkit_ok.md corpus/portfolio_ok.md corpus/inventory_ok.md  # z3 义务消解（258 项 PROVED）
python3 impl/python/sigma_app.py --smoke     # 找茬 MVP 参考后端 HTTP 冒烟（25/25）
```

### 验证清单（任何改动后必须全绿）

```sh
# 1. 三端共识（Law XIII 门禁）
python3 verify_consensus.py                    # 47/47
# 2. 三端 §SK 自检
cd impl/verifier && cargo run -q -- --sk-self-check      # 88/88
cd impl/elixir_rt && elixir sigma_verify.exs --sk-self-check  # 88/88
python3 impl/python/sigma_core.py              # 167/167
# 3. 三端编译
cd impl/verifier && cargo build                # 0 error / 0 warning
# 4. 证明与运行时
python3 tools/sigma-prove.py corpus/socketkit_ok.md corpus/portfolio_ok.md corpus/inventory_ok.md
python3 tools/sigma-runtime.py --domains       # 72/72
```

> 三端一致（Law XIII）是 ΣLang 的核心承诺：**一个符号、一种含义、一个结果——
> 谁来算都一样。**

---

## Architecture / 架构与数据流（v0.59）

ΣLang 的语义如何从规范一路走到共识门禁？全景如下：

```text
  spec/ 规范（英文为准 + spec/zh 中文参考）
   │  定义操作：指纹 / 签名 / 定律 / 测试（真实函数调用）
   ▼
  corpus/ 语料（51 个模块：ok 期望 PASS，break 期望 FAIL）
   │  三端验证器独立解析 + 求值（eval_expr 真实调用 §SK/§PF/§IN）
   ├──▶ Python verify_consensus.py ─┐
   ├──▶ Rust  impl/verifier        ├──▶ Law XIII 共识门禁（56/56 全绿）
   └──▶ Elixir impl/elixir_rt      ─┘
   │
   ├──▶ tools/sigma-prove.py     z3 义务消解（258 项 PROVED）
   ├──▶ tools/sigma-runtime.py   审计运行时（trace 59/59 + --domains 72/72）
   ├──▶ impl/python/sigma_app.py 找茬参考后端（自检 15/15 + 冒烟 36/36 + 持久化/审计）
   └──▶ tools/sigma-accept.py    一键验收（9 道门禁）→ GitHub Actions CI
```

**工具链职责**

| 工具 | 职责 | 结果 |
|------|------|------|
| `verify_consensus.py` | 三端验证器对 51 个语料模块独立判定（Python/Rust/Elixir/Expected） | 56/56 一致 |
| `verify_p0.py` | 算法正确性（含 §SK 语义检查） | 109/109 |
| `tools/sigma-prove.py` | 把语料定律编码为 z3 义务并消解 | 258 项 PROVED |
| `tools/sigma-runtime.py` | 审计运行时：逐事件复核定律（trace / --story / --growth / --inventory / --domains） | 59/59 + 72/72 |
| `impl/python/sigma_app.py` | 找茬 MVP 参考后端：业务全委托 §SK，App 只管状态 | 自检 15/15 + 冒烟 36/36 |
| `tools/sigma-accept.py` | 九道门禁一键验收（本地与 CI 同一条命令） | 9/9 |
| `.github/workflows/ci.yml` | push/PR 自动验收，全绿才算过 | CI 门禁 |

**一条语义的旅程**（以 §SK `task_create` 为例）：

1. `spec/spec_p0_socketkit.md` 定义指纹 `0xF001`、签名、定律与测试；
2. `corpus/socketkit_taskflow_ok.md` 把它写成**真实函数调用**测试；
3. Python / Rust / Elixir 三个独立验证器各自求值，结果必须逐项一致（Law XIII）；
4. `tools/sigma-prove.py` 把定律编码为 z3 义务，证明不可违反（P-01 结构 + 义务 PROVED）；
5. `tools/sigma-runtime.py` 在业务故事线里审计它的行为（input/output/定律复核）；
6. `impl/python/sigma_app.py` 的 `post_task` 直接委托它，并记录审计事件；
7. 任何改动后 `tools/sigma-accept.py` 九道门禁全绿，CI 放行。

> 整条链路的含义：**业务规则先以 ΣLang 语义存在并被证明，然后才是任何语言
> 的实现**——实现只是语义的投影。

---

## Product Guide / 用 ΣLang 做找茬（v0.69）

**找茬功能 ↔ §SK 语义对照**——每个业务动作都对应一个被三端共识、z3 可证明的
ΣLang 操作：

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

**落地三步走**：

1. **起后端**：`python3 impl/python/sigma_app.py --serve --port 8080
   --state state.json --audit-log audit.json`（或 Rust `cargo run -- --app-serve`；
   双端业务流剧本 `--scenario` / `--app-scenario` 16/16 逐项一致）。
2. **过验收**：`python3 tools/sigma-accept.py` 九道门禁全绿 + 找茬专项
   （`--smoke` 36/36 / `--persist-test` 10/10 / `--audit-test` 5/5）——任何
   部署改动放行前必跑。
3. **扩展业务**：新规则**先写进 spec（§SK）→ 三端实现 → 语料进共识门禁 →
   z3 证明 → App 委托**，再进产品——业务逻辑永远先以 ΣLang 语义存在并被证明，
   任何语言的实现都只是它的投影。

> 详细部署与运维见 `docs/deploy_zhaocha.md`（v0.68）。

---

## Launch Checklist / 找茬开工检查清单（v0.85）

上线前逐项勾选——每项都有可重复执行的命令与期望结果（覆盖 v0.71–v0.84
服务化能力）：

| # | 检查项 | 命令 | 期望 |
|---|--------|------|------|
| 1 | 启动自检（v0.75） | `python3 impl/python/sigma_app.py --serve --skip-startup-check` 去掉跳过标志 | 先过 §SK.6 门禁再监听，失败拒绝启动 |
| 2 | 鉴权（v0.71） | `python3 impl/python/sigma_app.py --serve --auth-token SECRET` | 未带 ?token= 返回 401 |
| 3 | 状态持久化（v0.51/72） | `--state state.json` | 重启不丢；原子写崩溃不损坏 |
| 4 | 审计日志（v0.55） | `--audit-log audit.json` | 每个业务动作的 ΣLang 事件，可对账 |
| 5 | 访问日志（v0.73） | `--log-file app.log` | 2xx=INFO / 4xx=WARNING 分级 |
| 6 | 健康检查（v0.74） | `GET /health` | status ok + 门禁摘要（56/56、73 PROVED） |
| 7 | HTTP 方法（v0.82） | 前端用 POST 变更、GET 查询 | 变更/查询端点双方法可用 |
| 8 | 业务流剧本 | `--scenario`（16/16）+ `--frontend-scenario`（11/11） | CLI 与前端视角全绿 |
| 9 | 双端对账（v0.84） | Python `--smoke` 与 Rust `--app-smoke` | 双端 36/36 逐项一致 |
| 10 | 一键门禁 | `python3 tools/sigma-accept.py` | 10/10 全绿 |

> 任何一项未过 = 开工放行前必须修复；门禁数字以当前 milestone 为准。

---

## Run Guide / 找茬运行指南（v0.98）

**一条命令开工（v0.94）**：

```sh
python3 impl/python/sigma_app.py --launch
# 启动自检通过 → 前端 http://127.0.0.1:8000 · API http://127.0.0.1:8080（Ctrl+C 停止）
```

| 入口 | 地址 | 说明 |
|------|------|------|
| 前端页面 | `http://127.0.0.1:8000` | 注册/开户/发单/接单/提交/验收/提现/勋章（web/index.html，后端地址可在 localStorage `sigma_base` 配） |
| API | `http://127.0.0.1:8080` | 全部业务端点（见 `docs/api_zhaocha.md`） |
| 运行面板 | `http://127.0.0.1:8080/panel` | 业务摘要 + 门禁摘要（v0.95） |
| 健康检查 | `http://127.0.0.1:8080/health` | 服务状态 + 配置摘要（v0.74） |

**开工后完整使用流程（§SK.6）**：

1. 「我的会话」注册两个用户（作者 7 / 找茬人 3），作者开户额度（50）；
2. 「发布需求」发单（作者 7，赏金 100）；
3. 「任务列表」看到新单（待接单）→ 「任务操作」接单（找茬人 3）；
4. 提交 → 验收（作者 7 确认）→ 任务变已完成；
5. 提现（找茬人 100）→ 勋章（契分 105）。

**运行验收（v0.96）**：`python3 impl/python/sigma_app.py --run-accept` —— 8 项
端到端（启动自检 / 双服务在线 / 全链路业务流 / /panel 实时数据 / 状态可持久化 /
审计可对账）。**协议门禁**：`python3 tools/sigma-accept.py --report acceptance.json`
十道门禁一键验收（v0.48/56/84/87）。

---

## Deploy Guide / 找茬上线指南（v0.117）

**上线启动（v0.94/101/102）**：

```sh
python3 impl/python/sigma_app.py --launch \
  --port 8080 --web-port 8000 \
  --auth-token SECRET \
  --state data/state.json --audit-log data/audit.json --log-file data/app.log
# 未显式指定 --state/--audit-log/--log-file 时自动落到 data/ 默认路径（v0.102）
```

**生产配置（v0.101 透传）**：

| 参数 | 说明 |
|------|------|
| `--port` / `--web-port` | 后端 API / 前端端口 |
| `--auth-token SECRET` | 启用鉴权（未带 ?token= 返回 401，v0.71） |
| `--state FILE` | 状态持久化（原子写，崩溃不损坏，v0.72/101） |
| `--audit-log FILE` | ΣLang 审计日志（可对账，v0.55） |
| `--log-file FILE` | 访问日志分级（2xx=INFO / 4xx=WARNING，v0.73） |

**上线验收**：`python3 impl/python/sigma_app.py --deploy-accept`（9 项端到端，
v0.104）→ `python3 tools/sigma-accept.py --report acceptance.json`（十道门禁 +
运行验收 runtime 段，v0.116）。

**运维要点**：数据在 `data/`（定期备份 state.json）；审计可对账（每个业务动作
的 ΣLang 事件）；`GET /health` 监控服务状态（v0.74）；`GET /panel` 看运行状态
与门禁摘要（v0.95）；并发安全有 `--concurrency-test` 兜底（v0.103）。

---

## Status / 项目状态

| Module / 模块 | Tests / 测试 | Status / 状态 |
|---------------|-------------|---------------|
| §T Time & Causal Order / 时间与因果序 | 17/17 | ✅ |
| §E Error Algebra / 错误代数 | 16/16 | ✅ |
| §C Confidence & Probabilistic Logic / 置信度与概率逻辑 | 37/37 | ✅ |
| §I I/O Boundary & Effects / I/O 边界与效应 | 25/25 | ✅ |
| §SK SocketKit Protocol / SocketKit 协议 | 14/14 | ✅ |
| **Total / 总计** | **109/109** | **✅** |

Verifier Consensus / 验证器共识: **56/56** corpus modules agree across Python / Rust / Elixir verifiers.
56/56 语料库模块在 Python / Rust / Elixir 三个验证器上达成一致。

**v0.89 收官总览 (2026-08-04)**: 协议 **spec 0.5.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（29 模块）、sigma-runtime **71/71 + 47/47**（--domains 含
12 项跨操作不变量复核）、双端 HTTP 冒烟 **36/36 逐项一致**、sigma-accept
**十道门禁 10/10**（含 CI 回归报告 artifact）、三端 0 warning；找茬产品落地
（服务化十件套 + API 文档 + 部署文档 + 开工 checklist + 前端联调剧本）——
从 v0.10 到 v0.89 里程碑链完整。

**v0.119 收官总览 (2026-08-05)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（29 模块）、sigma-runtime **71/71 + 71/71**（--domains 含
20 项链式不变量复核）、双端 HTTP 冒烟 **37/37 逐项一致**（含 /panel 对账）、
sigma-accept **十道门禁 10/10**（含 --report 运行验收 runtime 段）、
--bench 性能基线（/health 99 req/s、/tasks 270 req/s）、三端 0 warning；
找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端三域面板 +
上线验收 --deploy-accept + 上线指南 + 运行面板 /panel + 并发/性能兜底）——
从 v0.10 到 v0.119 里程碑链完整。

**v0.146 收官总览 (2026-08-05)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（30 模块，含 INV-SK-6 额度-托管联动 / INV-PF-4 交易链可加性）、
sigma-runtime **71/71 + 71/71**（--domains 含 22 项链式不变量复核）、双端 HTTP
冒烟 **38/38 逐项一致**（含 /panel 与 /stats 对账）、前端联调剧本 **19/19**、
sigma-accept **十道门禁 10/10**（含 --report runtime 段）、Elixir 自检 **88/88**、
stats-test **5/5**、三端 0 warning；找茬产品可上线（--launch 一键开工 + 默认
持久化/审计/日志 + 前端三域面板 + 平台统计 /stats + 上线/运行/部署指南 +
性能基线）——从 v0.10 到 v0.146 里程碑链完整（长期自主运行小阶段 13/496 推进
中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.156 收官总览 (2026-08-05)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（31 模块，含 INV-SK-6 额度-托管联动 / INV-PF-4 交易链可加性 /
INV-IN-5 混合货品可加链）、sigma-runtime **71/71 + 71/71**（--domains 含 23 项
链式不变量复核）、双端 HTTP 冒烟 **43/43 逐项一致**（含 /panel、/stats 与
/portfolio_* 对账）、前端联调剧本 **19/19**、sigma-accept **十道门禁 10/10**
（含 --report runtime 段）、Elixir 三域自检（§SK 88/88、§IN 6/6、§PF 8/8）、
stats-test **5/5**、portfolio-test **5/5**、三端 0 warning；找茬产品可上线
（--launch 一键开工 + 默认持久化/审计/日志 + 前端三域面板 + 平台统计 /stats +
金融市场 /portfolio_* + 上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.156
里程碑链完整（长期自主运行小阶段 23/496 推进中，每 10 个同步仓库、每 100 个
发布 PyPI）。

**v0.166 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（32 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动）、sigma-runtime **71/71 +
71/71**（--domains 含 24 项链式不变量复核）、双端 HTTP 冒烟 **44/44 逐项一致**
（含 /panel、/stats、/portfolio_* 与供应链链对账）、前端联调剧本 **19/19**、
sigma-accept **十道门禁 10/10**（含 --report runtime 段）、Elixir 三域自检
（§SK 88/88、§IN 7/7、§PF 8/8）、stats-test **5/5**、portfolio-test **5/5**、
inventory-test **5/5**、三端 0 warning；跨域联动语料（§SK→§PF→§IN 三域链
sigma_cross_domain_ok）进共识 56/56；找茬产品可上线（--launch 一键开工 + 默认
持久化/审计/日志 + 前端三域面板 + 平台统计 /stats + 金融市场 /portfolio_* +
供应链联动演示 + 上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.166 里程碑
链完整（长期自主运行小阶段 33/496 推进中，每 10 个同步仓库、每 100 个发布
PyPI）。

**v0.176 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（33 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒）、
sigma-runtime **71/71 + 71/71**（--domains 含 25 项链式不变量复核）、双端 HTTP
冒烟 **46/46 逐项一致**（含 /panel、/stats、/portfolio_*、供应链链与跨域链对账）、
前端联调剧本 **19/19**、sigma-accept **十道门禁 10/10**（含 --report runtime
段）、Elixir 四域自检（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5）、stats-test
**5/5**、portfolio-test **5/5**、inventory-test **5/5**、cross-domain-test
**5/5**、三端 0 warning；跨域联动语料与三域错误边界语料（§SK→§PF→§IN 链 +
错误路径强化）进共识 56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/
审计/日志 + 前端三域面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/
三域联动演示 + 上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.176 里程碑链
完整（长期自主运行小阶段 43/496 推进中，每 10 个同步仓库、每 100 个发布
PyPI）。

**v0.186 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动）、sigma-runtime **71/71 + 71/71**（--domains 含 26 项
链式不变量复核）、双端 HTTP 冒烟 **48/48 逐项一致**（含 /panel、/stats、
/portfolio_*、供应链链、跨域链与错误边界对账）、前端联调剧本 **19/19**、
sigma-accept **十道门禁 10/10**（含 --report runtime 段）、Elixir 五域自检
（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界 10/10）、stats-test
**5/5**、portfolio-test **5/5**、inventory-test **5/5**、cross-domain-test
**5/5**、errors-test **7/7**、三端 0 warning；跨域联动语料、三域错误边界语料
与标准库边界强化（§SK→§PF→§IN 链 + 错误路径 + std 边界用例 24 项）进共识
56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端三域
面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域联动演示 + 语义化
错误提示 + 上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.186 里程碑链完整
（长期自主运行小阶段 53/496 推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.196 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动）、sigma-runtime **71/71 +
71/71**（--domains 含 27 项链式不变量复核）、双端 HTTP 冒烟 **50/50 逐项一致**
（含 /panel、/stats、/portfolio_*、供应链链、跨域链、错误边界与积分链对账）、
前端联调剧本 **19/19**、sigma-accept **十道门禁 10/10**（含 --report runtime
段）、Elixir 六域自检（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界
10/10、积分链 3/3）、stats-test **5/5**、portfolio-test **5/5**、inventory-test
**5/5**、cross-domain-test **5/5**、points-test **3/3**、errors-test **7/7**、
三端 0 warning；跨域联动语料、三域错误边界语料与标准库双包边界强化
（§SK→§PF→§IN 链 + 错误路径 + std math_base 24 项 + data_transform 18 项）
进共识 56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端
三域面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链联动
演示 + 语义化错误提示 + 上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.196
里程碑链完整（长期自主运行小阶段 63/496 推进中，每 10 个同步仓库、每 100 个
发布 PyPI）。

**v0.206 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性）、
sigma-runtime **71/71 + 71/71**（--domains 含 28 项链式不变量复核）、双端 HTTP
冒烟 **51/51 逐项一致**（含 /panel、/stats、/portfolio_*、供应链链、跨域链、
错误边界、积分链与库存链对账）、前端联调剧本 **19/19**、sigma-accept **十道
门禁 10/10**（含 --report runtime 段）、Elixir 七域自检（§SK 88/88、§IN 7/7、
§PF 8/8、三域链 5/5、错误边界 10/10、积分链 3/3、库存链 5/5）、stats-test
**5/5**、portfolio-test **5/5**、inventory-test **5/5**、cross-domain-test
**5/5**、inventory-chain-test **5/5**、points-test **3/3**、errors-test
**7/7**、三端 0 warning；跨域联动语料、三域错误边界语料与标准库三包边界强化
（§SK→§PF→§IN 链 + 错误路径 + std math_base 24 项 + data_transform 18 项 +
ai_confidence 8 项）进共识 56/56；找茬产品可上线（--launch 一键开工 + 默认
持久化/审计/日志 + 前端三域面板 + 平台统计 /stats + 金融市场 /portfolio_* +
供应链/三域/积分链/库存链联动演示 + 语义化错误提示 + 上线/运行/部署指南 +
性能基线）——从 v0.10 到 v0.206 里程碑链完整（长期自主运行小阶段 73/496
推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.216 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动）、sigma-runtime **71/71 + 71/71**（--domains 含 29 项
链式不变量复核）、双端 HTTP 冒烟 **53/53 逐项一致**（含 /panel、/stats、
/portfolio_*、供应链链、跨域链、错误边界、积分链、库存链与信用链对账）、前端
联调剧本 **19/19**、sigma-accept **十道门禁 10/10**（含 --report runtime 段）、
Elixir 八域自检（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界 10/10、
积分链 3/3、库存链 5/5、信用链 5/5）、stats-test **5/5**、portfolio-test
**5/5**、inventory-test **5/5**、cross-domain-test **5/5**、
inventory-chain-test **5/5**、points-test **3/3**、credit-test **3/3**、
errors-test **7/7**、三端 0 warning；跨域联动语料、三域错误边界语料与标准库
四包边界强化（§SK→§PF→§IN 链 + 错误路径 + std math_base 24 项 +
data_transform 18 项 + ai_confidence 12 项）进共识 56/56；找茬产品可上线
（--launch 一键开工 + 默认持久化/审计/日志 + 前端三域面板 + 平台统计 /stats +
金融市场 /portfolio_* + 供应链/三域/积分链/库存链/信用链联动演示 + 语义化错误
提示 + 上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.216 里程碑链完整
（长期自主运行小阶段 83/496 推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.226 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动）、sigma-runtime **71/71 +
71/71**（--domains 含 30 项链式不变量复核）、双端 HTTP 冒烟 **56/56 逐项一致**
（含 /panel、/stats、/portfolio_*、供应链链、跨域链、错误边界、积分链、库存链、
信用链与全流程对账）、前端联调剧本 **19/19**、sigma-accept **十道门禁 10/10**
（含 --report runtime 段）、Elixir 九域自检（§SK 88/88、§IN 7/7、§PF 8/8、
三域链 5/5、错误边界 10/10、积分链 3/3、库存链 5/5、信用链 5/5、全流程 6/6）、
stats-test **5/5**、portfolio-test **5/5**、inventory-test **5/5**、
cross-domain-test **5/5**、inventory-chain-test **5/5**、full-test **5/5**、
points-test **3/3**、credit-test **3/3**、errors-test **7/7**、三端 0 warning；
跨域联动语料、三域错误边界语料与标准库五包边界强化（§SK→§PF→§IN 链 + 错误
路径 + std math_base 24 项 + data_transform 24 项 + ai_confidence 12 项）进
共识 56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端
三域面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链/库存链/
信用链/全流程联动演示 + 语义化错误提示 + 上线/运行/部署指南 + 性能基线）——
从 v0.10 到 v0.226 里程碑链完整（长期自主运行小阶段 93/496 推进中，每 10 个
同步仓库、每 100 个发布 PyPI）。

**v0.236 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动 / INV-PF-7 资产链完整性）、
sigma-runtime **71/71 + 71/71**（--domains 含 31 项链式不变量复核）、双端 HTTP
冒烟 **58/58 逐项一致**（含 /panel、/stats、/portfolio_*、供应链链、跨域链、
错误边界、积分链、库存链、信用链、全流程与审计对账）、前端联调剧本 **19/19**、
sigma-accept **十道门禁 10/10**（含 --report runtime 段）、Elixir 十域自检
（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界 10/10、积分链 3/3、
库存链 5/5、信用链 5/5、全流程 6/6、审计链 3/3）、stats-test **5/5**、
portfolio-test **5/5**、inventory-test **5/5**、cross-domain-test **5/5**、
inventory-chain-test **5/5**、full-test **5/5**、points-test **3/3**、
credit-test **3/3**、audit-test **6/6**、errors-test **7/7**、三端 0 warning；
跨域联动语料、三域错误边界语料与标准库六包边界强化（§SK→§PF→§IN 链 + 错误
路径 + std math_base 27 项 + data_transform 24 项 + ai_confidence 12 项）进
共识 56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端
三域面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链/库存链/
信用链/全流程联动演示 + 审计轨迹视图 + 语义化错误提示 + 上线/运行/部署指南 +
性能基线）——从 v0.10 到 v0.236 里程碑链完整（长期自主运行小阶段 103/496
推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.246 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动 / INV-PF-7 资产链完整性 /
INV-SK-10 契分-贡献联动）、sigma-runtime **71/71 + 71/71**（--domains 含 32 项
链式不变量复核）、双端 HTTP 冒烟 **60/60 逐项一致**（含 /panel、/stats、
/portfolio_*、供应链链、跨域链、错误边界、积分链、库存链、信用链、全流程、
审计与贡献分对账）、前端联调剧本 **19/19**、sigma-accept **十道门禁 10/10**
（含 --report runtime 段）、Elixir 十一域自检（§SK 88/88、§IN 7/7、§PF 8/8、
三域链 5/5、错误边界 10/10、积分链 3/3、库存链 5/5、信用链 5/5、全流程 6/6、
审计链 3/3、贡献分 3/3）、stats-test **5/5**、portfolio-test **5/5**、
inventory-test **5/5**、cross-domain-test **5/5**、inventory-chain-test
**5/5**、full-test **5/5**、points-test **3/3**、credit-test **3/3**、
audit-test **6/6**、contribution-test **2/2**、errors-test **7/7**、三端
0 warning；跨域联动语料、三域错误边界语料与标准库七包边界强化（§SK→§PF→§IN
链 + 错误路径 + std math_base 27 项 + data_transform 33 项 + ai_confidence
12 项）进共识 56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志
+ 前端三域面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链/
库存链/信用链/全流程联动演示 + 审计轨迹视图 + 贡献分演示 + 语义化错误提示 +
上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.246 里程碑链完整（长期自主
运行小阶段 113/496 推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.256 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动 / INV-PF-7 资产链完整性 /
INV-SK-10 契分-贡献联动 / INV-SK-11 契分-勋章联动）、sigma-runtime **71/71 +
71/71**（--domains 含 33 项链式不变量复核）、双端 HTTP 冒烟 **61/61 逐项一致**
（含 /panel、/stats、/portfolio_*、供应链链、跨域链、错误边界、积分链、库存链、
信用链、全流程、审计、贡献分与额度链对账）、前端联调剧本 **19/19**、
sigma-accept **十道门禁 10/10**（含 --report runtime 段）、Elixir 十二域自检
（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界 10/10、积分链 3/3、
库存链 5/5、信用链 5/5、全流程 6/6、审计链 3/3、贡献分 3/3、额度链 4/4）、
stats-test **5/5**、portfolio-test **5/5**、inventory-test **5/5**、
cross-domain-test **5/5**、inventory-chain-test **5/5**、full-test **5/5**、
points-test **3/3**、credit-test **3/3**、audit-test **6/6**、
contribution-test **2/2**、quota-flow-test **2/2**、errors-test **7/7**、
三端 0 warning；跨域联动语料、三域错误边界语料与标准库八包边界强化（§SK→§PF→
§IN 链 + 错误路径 + std math_base 27 项 + data_transform 33 项 + ai_confidence
16 项）进共识 56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志
+ 前端三域面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链/
库存链/信用链/全流程联动演示 + 审计轨迹视图 + 贡献分演示 + 额度流转演示 +
语义化错误提示 + 上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.256 里程碑链
完整（长期自主运行小阶段 123/496 推进中，每 10 个同步仓库、每 100 个发布
PyPI）。

**v0.266 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动 / INV-PF-7 资产链完整性 /
INV-SK-10 契分-贡献联动 / INV-SK-11 契分-勋章联动 / INV-IN-8 混合出库联动）、
sigma-runtime **71/71 + 71/71**（--domains 含 34 项链式不变量复核）、双端 HTTP
冒烟 **63/63 逐项一致**（含 /panel、/stats、/portfolio_*、供应链链、跨域链、
错误边界、积分链、库存链、信用链、全流程、审计、贡献分、额度链与勋章链对账）、
前端联调剧本 **19/19**、sigma-accept **十道门禁 10/10**（含 --report runtime
段）、Elixir 十三域自检（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界
10/10、积分链 3/3、库存链 5/5、信用链 5/5、全流程 6/6、审计链 3/3、贡献分 3/3、
额度链 4/4、勋章链 4/4）、stats-test **5/5**、portfolio-test **5/5**、
inventory-test **5/5**、cross-domain-test **5/5**、inventory-chain-test
**5/5**、full-test **5/5**、points-test **3/3**、credit-test **3/3**、
audit-test **6/6**、contribution-test **2/2**、quota-flow-test **2/2**、
badge-test **2/2**、errors-test **7/7**、三端 0 warning；跨域联动语料、三域
错误边界语料与标准库九包边界强化（§SK→§PF→§IN 链 + 错误路径 + std math_base
29 项 + data_transform 33 项 + ai_confidence 16 项）进共识 56/56；找茬产品可
上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端三域面板 + 平台统计
/stats + 金融市场 /portfolio_* + 供应链/三域/积分链/库存链/信用链/全流程联动
演示 + 审计轨迹视图 + 贡献分演示 + 额度流转演示 + 勋章链演示 + 语义化错误提示 +
上线/运行/部署指南 + 性能基线）——从 v0.10 到 v0.266 里程碑链完整（长期自主
运行小阶段 133/496 推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.276 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动 / INV-PF-7 资产链完整性 /
INV-SK-10 契分-贡献联动 / INV-SK-11 契分-勋章联动 / INV-IN-8 混合出库联动 /
INV-PF-8 混合资产链完整性）、sigma-runtime **71/71 + 71/71**（--domains 含 35 项
链式不变量复核）、双端 HTTP 冒烟 **65/65 逐项一致**（含 /panel、/stats、
/portfolio_*、供应链链、跨域链、错误边界、积分链、库存链、信用链、全流程、
审计、贡献分、额度链、勋章链与库存流转对账）、前端联调剧本 **19/19**、
sigma-accept **十道门禁 10/10**（含 --report runtime 段）、Elixir 十四域自检
（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界 10/10、积分链 3/3、
库存链 5/5、信用链 5/5、全流程 6/6、审计链 3/3、贡献分 3/3、额度链 4/4、
勋章链 4/4、库存流转 4/4）、stats-test **5/5**、portfolio-test **5/5**、
inventory-test **5/5**、cross-domain-test **5/5**、inventory-chain-test
**5/5**、full-test **5/5**、points-test **3/3**、credit-test **3/3**、
audit-test **6/6**、contribution-test **2/2**、quota-flow-test **2/2**、
badge-test **2/2**、inventory-flow-test **4/4**、errors-test **7/7**、三端
0 warning；跨域联动语料、三域错误边界语料与标准库十包边界强化（§SK→§PF→§IN
链 + 错误路径 + std math_base 29 项 + data_transform 42 项 + ai_confidence
16 项）进共识 56/56；找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志
+ 前端三域面板 + 平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链/
库存链/信用链/全流程联动演示 + 审计轨迹视图 + 贡献分演示 + 额度流转演示 +
勋章链演示 + 库存流转演示 + 语义化错误提示 + 上线/运行/部署指南 + 性能基线）
——从 v0.10 到 v0.276 里程碑链完整（长期自主运行小阶段 143/496 推进中，每 10
个同步仓库、每 100 个发布 PyPI）。

**v0.286 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动 / INV-PF-7 资产链完整性 /
INV-SK-10 契分-贡献联动 / INV-SK-11 契分-勋章联动 / INV-IN-8 混合出库联动 /
INV-PF-8 混合资产链完整性 / INV-SK-12 契分-贡献-勋章三链联动）、sigma-runtime
**71/71 + 71/71**（--domains 含 36 项链式不变量复核）、双端 HTTP 冒烟 **67/67
逐项一致**（含 /panel、/stats、/portfolio_*、供应链链、跨域链、错误边界、积分链、
库存链、信用链、全流程、审计、贡献分、额度链、勋章链、库存流转与组合流转对账）、
前端联调剧本 **19/19**、sigma-accept **十道门禁 10/10**（含 --report runtime
段）、Elixir 十五域自检（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界
10/10、积分链 3/3、库存链 5/5、信用链 5/5、全流程 6/6、审计链 3/3、贡献分 3/3、
额度链 4/4、勋章链 4/4、库存流转 4/4、组合流转 5/5）、stats-test **5/5**、
portfolio-test **5/5**、inventory-test **5/5**、cross-domain-test **5/5**、
inventory-chain-test **5/5**、full-test **5/5**、points-test **3/3**、
credit-test **3/3**、audit-test **6/6**、contribution-test **2/2**、
quota-flow-test **2/2**、badge-test **2/2**、inventory-flow-test **4/4**、
portfolio-flow-test **5/5**、errors-test **7/7**、三端 0 warning；跨域联动语料、
三域错误边界语料与标准库十一包边界强化（§SK→§PF→§IN 链 + 错误路径 + std
math_base 29 项 + data_transform 42 项 + ai_confidence 20 项）进共识 56/56；
找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端三域面板 +
平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链/库存链/信用链/
全流程联动演示 + 审计轨迹视图 + 贡献分演示 + 额度流转演示 + 勋章链演示 +
库存流转演示 + portfolio 流转演示 + 语义化错误提示 + 上线/运行/部署指南 +
性能基线）——从 v0.10 到 v0.286 里程碑链完整（长期自主运行小阶段 153/496
推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.296 收官总览 (2026-08-06)**: 协议 **spec 0.7.0**，三域（§SK 找茬业务 /
§PF 金融 / §IN 供应链）——consensus **56/56**、p0 **109/109**、sigma-prove
**258 项 PROVED**（34 模块，含 INV-SK-6 额度-托管 / INV-PF-4 交易链可加 /
INV-IN-5 混合货品可加 / INV-SK-7 任务-契分联动 / INV-PF-5 买入-卖出链守恒 /
INV-SK-8 赏金-积分联动 / INV-IN-6 入库-出库联动 / INV-PF-6 交易链完整性 /
INV-SK-9 额度-契分联动 / INV-IN-7 混合货品联动 / INV-PF-7 资产链完整性 /
INV-SK-10 契分-贡献联动 / INV-SK-11 契分-勋章联动 / INV-IN-8 混合出库联动 /
INV-PF-8 混合资产链完整性 / INV-SK-12 契分-贡献-勋章三链联动 / INV-SK-13
积分-配额联动链）、sigma-runtime **59/59 + 72/72**（--domains 含 37 项链式
不变量复核）、双端 HTTP 冒烟 **70/70 + 36/36 逐项一致**（含 /panel、/stats、
/portfolio_*、供应链链、跨域链、错误边界、积分链、库存链、信用链、全流程、
审计、贡献分、额度链、勋章链、库存流转、组合流转与三链联动对账）、前端联调
剧本 **19/19**、sigma-accept **十道门禁 10/10**（含 --report runtime 段）、
Elixir 十六域自检（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5、错误边界 10/10、
积分链 3/3、库存链 5/5、信用链 5/5、全流程 6/6、审计链 3/3、贡献分 3/3、
额度链 4/4、勋章链 4/4、库存流转 4/4、组合流转 5/5、三链联动 3/3）、
stats-test **5/5**、portfolio-test **5/5**、inventory-test **5/5**、
cross-domain-test **5/5**、inventory-chain-test **5/5**、full-test **5/5**、
points-test **3/3**、credit-test **3/3**、audit-test **6/6**、
contribution-test **2/2**、quota-flow-test **2/2**、badge-test **2/2**、
inventory-flow-test **4/4**、portfolio-flow-test **5/5**、credit-badge-test
**3/3**、web-test **5/5**、errors-test **7/7**、三端 0 warning；跨域联动语料、
三域错误边界语料与标准库十一包边界强化（§SK→§PF→§IN 链 + 错误路径 + std
math_base 31 项 + data_transform 42 项 + ai_confidence 20 项）进共识 56/56；
找茬产品可上线（--launch 一键开工 + 默认持久化/审计/日志 + 前端三域面板 +
平台统计 /stats + 金融市场 /portfolio_* + 供应链/三域/积分链/库存链/信用链/
全流程/三链联动演示 + 审计轨迹视图 + 贡献分演示 + 额度流转演示 + 勋章链演示 +
库存流转演示 + portfolio 流转演示 + 语义化错误提示 + 上线/运行/部署指南 +
性能基线）——从 v0.10 到 v0.296 里程碑链完整（长期自主运行小阶段 164/496
推进中，每 10 个同步仓库、每 100 个发布 PyPI）。

**v0.10 可用 (2026-08-02)**: 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）、基本操作（`index()`/`I₂`、元素级/矩阵运算）、常量包（§C `0xK0xx`/`0xQ0xx` 按指纹解析，Opaque 类不可遮蔽）已在三个验证器求值器全部实现并有语料覆盖；`sigma-prove` 义务消解 `PROVED (unsat)`，`sigma-moonbit` 生成 `.mbtp`；共识门禁 35/35 全绿。

**v0.11 可用 (2026-08-02)**: 包管理器 `tools/sigma-cli.py`（install/verify/list/search/fingerprint，`~/.sigma/registry.json` 注册表，Iron Law VII 无环依赖解析）+ 标准库 3 包（`std/math.base.md` / `std/data.transform.md` / `std/ai.confidence.md`，各配 `corpus/std_*_ok.md` 验证器测试集）；共识门禁 38/38 全绿、p0 95/95、三端 0 warning，v0.10 不回归。见 `MASTER_PLAN.md` Phase 3–4 与 `AUTOPILOT.md` §6。

**AI Bootstrapping Test (P2, 2026-08-02)**: `tools/sigma-bootstrap.py` — 一键闭环验证 spec→impl→verify→pass：4 个 P0 spec 均携带 `## Implementation Checklist (for AI)`、`impl/python/sigma_core.py` 自检 71/71、`verify_p0.py` 95/95。证明「新鲜 AI 只凭规范+验证器即可从零实现并通过验证」。见 `MASTER_PLAN.md` Phase 5。

**v0.12 Novel Spec Test (2026-08-02)**: `corpus/novel_gene_ok.md`（DNA 对齐语义）三端验证器一致（consensus 39/39），跑通 AI 读 spec → 写实现 → 验证 → 发布的完整闭环。见 `MASTER_PLAN.md` Phase 5.2。

**v0.13 SocketKit Protocol (2026-08-02)**: `spec/spec_p0_socketkit.md`（§SK：task_create / review_merge / contribution_score 的 ΣLang 语义）+ `corpus/socketkit_ok.md` 三端一致（consensus 40/40），走通 RFC → spec → 验证器 → 测试 晋升路径。见 `MASTER_PLAN.md` §6.2。

**v0.14 SocketKit Runtime (2026-08-03)**: §SK 参考实现进入 `impl/python/sigma_core.py`（自检 75/75）· 审计运行时 `tools/sigma-runtime.py`（业务 trace → ΣLang obligation 日志，10/10 满足）· `sigma-prove` 对 §SK 六条定律义务消解全部 `PROVED (unsat)` · 负例 `corpus/socketkit_break.md`（E-02，三端一致 FAIL）· §SK 行为测试进 `verify_p0.py`（109/109）；共识门禁 41/41 全绿、三端 0 warning，v0.10–v0.13 不回归。

**v0.15 三端 §SK 执行层 (2026-08-03)**: §SK 参考实现从 Python 单侧同步到 Rust（`impl/verifier/src/sk.rs` + `--sk-self-check`，16/16）与 Elixir（`sigma_verify.exs` §SK + `--sk-self-check`，16/16）——同一组 §SK 用例三端判定一致（Law XIII 业务语义层），`cargo build` 0 error/0 warning；consensus 41/41、p0 109/109 不回退，v0.10–v0.14 不回归。

**v0.16 SocketKit 语料执行化 (2026-08-03)**: 三端求值器（`verify_consensus.py` / `evaluator.rs` / `sigma_verify.exs`）的 eval_expr 直接支持 §SK 三操作真实调用（`task_create(a,b)` / `review_merge([...])` / `contribution_score([...])`，含 ⊥ BountyErr / TypeError / ShapeError 错误路径）；`corpus/socketkit_ok.md` 的 Tests 从规范表达式（⊕ ∈ ⊘）升级为真实调用——**Law XIII 共识门禁从此直接验证业务语义本身**，9/9 三端一致（consensus 41/41）、0 warning，v0.10–v0.15 不回归。

**v0.17 §SK 对齐真实业务 (2026-08-03)**: 依据找茬需求文档（`D:\Desktop\来找茬_需求文档.md` v1.0）校准 §SK——Task 扩展为 4 元组 `[author, bounty, status, hunter]` + 4 态状态机（待接单→进行中→待验收→已完成）；新增 `accept_task`（接单）/ `task_submit`（提交成果）/ `task_accept`（受茬人单人验收）/ `credit_score`（契分制：基础 100、完成 +5/单、违约 ×0.7）；`review_merge` 修正为增长期核验师场景。三端执行层同步（sigma_core 91/91、三端 §SK 自检 32/32、socketkit_ok 24/24 三端一致），sigma-prove 18 项 §SK 义务全部 PROVED (unsat)，sigma-runtime 完整 MVP 业务 trace 23/23；consensus 41/41、p0 109/109、三端 0 warning，v0.10–v0.16 不回归。

**v0.18 状态机不变量证明 (2026-08-03)**: `task_accept` 增加作者授权参数（只有受茬人本人 caller ≡ author 可验收，否则 ⊥ AuthError），spec 新增 §SK.3.8 不变量章节——**INV-1 状态单调**（状态只前进不后退）、**INV-2 终态不可变**（completed 不可再被任何状态操作改变）、**INV-3 守恒**（bounty 与 hunter 流转中不变）、**INV-4 作者授权**。三端执行层与 eval_expr 同步授权校验（sigma_core 92/92、三端 §SK 自检 33/33、socketkit_ok 25/25 三端一致），sigma-prove 新增 6 项不变量义务全部 `PROVED (unsat)`（§SK 共 23 项），sigma-runtime 审计 trace 增加不变量逐条复核（31/31）；consensus 41/41、p0 109/109、三端 0 warning，v0.10–v0.17 不回归。

**v0.19 第二个自举新域（金融 portfolio@1.0）(2026-08-03)**: 验证 ΣLang 协议泛化性——第二个全新领域（金融投资组合）走通 spec→三端→语料→证明 全流程：`spec/spec_p0_portfolio.md`（§PF：portfolio_new / buy / sell / portfolio_value / risk_score，单位价格 1 使总资产守恒可证）+ `corpus/portfolio_ok.md`（19/19 三端一致 PASS）与 `corpus/portfolio_break.md`（E-02 三端一致 FAIL）；三端 eval_expr 支持新域真实调用（sigma_core 111/111、0 warning）；sigma-prove 新增 10 项 §PF 义务全部 `PROVED (unsat)`（§SK+§PF 共 33 项）；sigma-runtime 审计 trace 增加 §PF 段（45/45）；consensus 43/43、p0 109/109，v0.10–v0.18 不回归。

**v0.20 找茬五大制度补齐 (2026-08-03)**: 依据找茬需求文档（`D:\Desktop\来找茬_需求文档.md` §四）把剩余三制度纳入 §SK——**SK.3.9 额度制**（`quota_new/quota_use/quota_reset`：月额/扣减/月底清零）、**SK.3.10 积分制**（`points_hold/points_release/points_withdraw`：托管冻结/释放/提现，⊥ InsufficientEscrow / InsufficientPoints）、**SK.3.11 勋章制**（`badge_level`：铜银金钻四级）。三端执行层与 eval_expr 同步（sigma_core 130/130、三端 §SK 自检 56/56、socketkit_ok 50/50 三端一致、0 warning），sigma-prove 新增 8 项三制度义务全部 `PROVED (unsat)`（共 41 项），sigma-runtime 审计 trace 增加三制度段（71/71）；consensus 43/43、p0 109/109，v0.10–v0.19 不回归。

**v0.21 找茬 MVP 全链路审计剧本 (2026-08-03)**: spec 新增 **§SK.6 MVP 业务剧本**——12 步端到端验收场景（开户额度→发布需求→扣减额度→赏金托管→接单→提交成果→验收确认→释放赏金→找茬人提现→契分奖励→贡献累计→勋章升级）；`sigma-runtime --story`（run_mvp_story）一次跑通完整业务故事线并逐事件复核不变量（INV-1 状态单调 / INV-3 守恒 / INV-4 作者授权 / 额度扣减 / 积分托管守恒），**18/18 义务满足**——作为 App 开工的「验收剧本」；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.20 不回归。

**v0.22 找茬 MVP 参考实现 (2026-08-03)**: `impl/python/sigma_app.py`（MVPApp）——找茬 MVP 真正"开工"的第一步：业务方法**全部委托** sigma_core §SK 语义（App 层只管状态、零业务规则重写），stdlib-only HTTP JSON API（`--serve` 暴露 `/post /claim /submit /accept /withdraw /badge`）；自检跑通 §SK.6 十二步剧本（**15/15**），步骤与 `sigma-runtime --story`（18/18）一一对应——被审计的验收剧本可直接实现为可运行后端；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.21 不回归。

**v0.23 MVP 端到端 HTTP 冒烟测试 (2026-08-03)**: `sigma_app.py` 增加 `/quota` 端点（开户额度，补全 HTTP 全链路）与 `--smoke` 模式（run_http_smoke：起服务→HTTP 七步全链路 `/quota → /post → /claim → /submit → /accept → /withdraw → /badge` → 逐响应断言 → 关服务，**13/13 通过**）——参考实现"作为 HTTP 服务的可用性"被可重复执行的冒烟测试固化；自检 15/15 不回归；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.22 不回归。

**v0.24 三端 §SK.6 story 一致性 (2026-08-03)**: §SK.6 MVP 业务剧本从 Python 单侧扩到三端——Rust `sk.rs story()` + `--sk-story`（**15/15**）、Elixir `sk_story()` + `--sk-story`（**15/15**），与 Python `sigma_app.py`（**15/15**）逐项一致：三把独立的尺子审计**同一条业务故事线**（开户→发单→扣额度→托管→接单→交成果→验收→释放→提现→加契分→加贡献→升勋章），Law XIII 在"产品层"收官；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.23 不回归。

**v0.25 Rust 参考实现 (2026-08-03)**: `impl/verifier/src/app.rs`（MVPApp 的 Rust 版，贴近生产部署）——业务方法**全部委托** sk.rs §SK 语义（App 层零业务规则重写），CLI 新增 `--app-self-check`（**15/15**）；与 Python `sigma_app.py`（15/15）、Rust `--sk-story`（15/15）、Elixir `--sk-story`（15/15）**四端逐项一致**——同一业务故事线在 Python 参考后端与 Rust 生产级实现上算出同一个答案；`cargo build` 0 error/0 warning；consensus 43/43、p0 109/109，v0.10–v0.24 不回归。

**v0.26 Rust HTTP 服务 + 冒烟对账 (2026-08-03)**: `app.rs` 增加 stdlib-only HTTP JSON API（手写 TcpListener + serde_json，`--app-serve`，端点 `/quota /post /claim /submit /accept /withdraw /badge` 与 Python `sigma_app.py --serve` 一致，业务全部委托 App 层 → §SK）+ `--app-smoke`（run_smoke：HTTP 七步全链路，**13/13**）——与 Python `sigma_app.py --smoke`（**13/13**）**双端逐项一致**，HTTP 层也同尺；`cargo build` 0 error/0 warning；consensus 43/43、p0 109/109，v0.10–v0.25 不回归。

### Two verification modes / 两种验证模式

ΣLang ships **two distinct verification tools** with different purposes:

| Tool / 工具 | Mode / 模式 | What it checks / 检查内容 |
|------------|------------|--------------------------|
| `verify_p0.py` | **Algorithm correctness** / 算法正确性 | 109 tests over §T/§E/§C/§I/§SK module *algorithms* (Lamport clocks, Result monad, confidence ops, I/O effects, SocketKit app behavior) — proves the P0 semantics are implementable. Does NOT parse `.md` specs. |
| `verify_consensus.py` | **Spec conformance** / 规范一致性 | Parses `.md` specs, applies Laws I–XVII + E-03/06/07/10 + §S/P-01 checks, and requires **41/41 corpus modules** to agree across Python / Rust / Elixir (Law XIII gate). |

> These are complementary, not redundant: `verify_p0.py` proves the **semantics** are sound;
> `verify_consensus.py` proves the **specs** conform and that independent implementations agree
> on the same verdict (one symbol, one meaning, one result — across all models).
> 两者互补而非冗余：前者证明语义可靠，后者证明规范合规且跨实现判定一致。

---

## Repository Structure / 目录结构

```
sigma-lang/
├── README.md                       # Project entry (this file) / 项目入口（本文件）
├── LICENSE                         # MIT
├── MASTER_PLAN.md                  # Development roadmap / 开发路线图
├── verify_p0.py                    # Algorithmic verification (109 tests) / 算法验证
├── verify_consensus.py             # Three-verifier consensus check / 三验证器共识检查
│
├── spec/                           # English specifications (normative) / 英文规范（规范性）
│   ├── spec_p0_foundations.md      # ⭐ Main P0 specification (整合版核心入口)
│   ├── spec_p0_time.md             # §T Full time & causality spec
│   ├── spec_p0_error.md            # §E Full error algebra spec
│   ├── spec_p0_confidence.md       # §C Full confidence & probability spec
│   ├── spec_p0_io.md               # §I Full I/O & effects spec
│   ├── spec_top_rules.md           # ⭐ Top-level rules: §S shadowing + §C constants + §G conflict
│   ├── spec_top_extensions.md      # Top-level rules: Law XIII–XVII + E-10 extensions
│   ├── spec_top_proofs.md          # Proof-carrying spec structure (P-01 enforced)
│   └── zh/                         # Chinese translations / 中文翻译
│       ├── spec_p0_foundations_zh.md
│       ├── spec_top_rules_zh.md
│       ├── spec_top_extensions_zh.md
│       └── spec_top_proofs_zh.md
│
├── archive/                        # Deprecated / superseded specs / 废弃/已替代的规范
│   ├── spec.md                     # v0.1 Initial Draft (superseded by spec_p0_foundations.md)
│   └── spec_p0_shadowing.md        # §S v0.2 (merged into spec_top_rules.md §S)
│
├── corpus/                         # Shared test corpus (38 modules) / 共享测试语料库
├── examples/                       # Usage examples / 使用示例
├── impl/                           # Verifier implementations / 验证器实现
│   ├── verifier/                   # Rust reference Verifier
│   ├── elixir_rt/                  # Elixir/BEAM verifier + runtime
│   └── python/                     # sigma_core.py — minimal reference core
├── tools/                          # Tooling (sigma-prove, etc.) / 工具
└── .github/workflows/              # CI: consensus gate
```

---

## Quick Navigation / 快速导航

### Getting Started / 入门

| Document / 文档 | Description / 说明 |
|----------------|-------------------|
| [spec_p0_foundations.md](spec/spec_p0_foundations.md) | **Main P0 specification** — start here. Covers all 17 Iron Laws, core types, package system, §T/§E/§C/§I modules, and Verifier architecture. / **P0 核心规范** — 从这里开始。涵盖全部 17 条铁律、核心类型、包系统、四大模块和验证器架构。 |

### Core Modules / 核心模块

| Document / 文档 | Module / 模块 | Tests / 测试 |
|----------------|---------------|-------------|
| [spec_p0_time.md](spec/spec_p0_time.md) | §T Time & Causal Order / 时间与因果序 | 17/17 |
| [spec_p0_error.md](spec/spec_p0_error.md) | §E Error Algebra / 错误代数 | 16/16 |
| [spec_p0_confidence.md](spec/spec_p0_confidence.md) | §C Confidence & Probabilistic Logic / 置信度与概率逻辑 | 37/37 |
| [spec_p0_io.md](spec/spec_p0_io.md) | §I I/O Boundary & Effects / I/O 边界与效应 | 25/25 |

### Top-Level Governance / 顶层治理

| Document / 文档 | Content / 内容 |
|----------------|---------------|
| [spec_top_rules.md](spec/spec_top_rules.md) | §S Shadowing & Binding Discipline, §C Real-World Constants, §G Conflict Adjudication, Rule Index / §S 遮蔽与绑定纪律、§C 现实常量、§G 冲突裁决、规则索引 |
| [spec_top_extensions.md](spec/spec_top_extensions.md) | Laws XIII–XVII (Verifier Consensus, Negative Tests, Export Completeness, Compatibility Proof, Probabilistic Guarantee) + Law VIII-ext E-10 (Eval Determinism) + E-08 S-01 Level 1 (package signature) + E-08 Strategy Bundle candidate / Law XIII–XVII 扩展 + E-10 评估确定性 + E-08 S-01 Level 1 包签名 + E-08 策略包候选 |
| [spec_pki_feasibility.md](spec/spec_pki_feasibility.md) | E-08 S-01 PKI Feasibility Study (Trust & Provenance: signatures, author identity, anti-poisoning) / 信任与溯源 PKI 可行性研究 |
| [spec_top_proofs.md](spec/spec_top_proofs.md) | Proof-Carrying Spec Structure (P-01 enforced) / 证明携带规范结构（P-01 已强制执行） |

### Chinese Translations / 中文翻译

| Document / 文档 | Original / 原文 |
|----------------|-----------------|
| [spec_p0_foundations_zh.md](spec/zh/spec_p0_foundations_zh.md) | spec_p0_foundations.md |
| [spec_top_rules_zh.md](spec/zh/spec_top_rules_zh.md) | spec_top_rules.md |
| [spec_top_extensions_zh.md](spec/zh/spec_top_extensions_zh.md) | spec_top_extensions.md |
| [spec_top_proofs_zh.md](spec/zh/spec_top_proofs_zh.md) | spec_top_proofs.md |

> **Note**: `spec/` contains the authoritative English originals. `spec/zh/` contains Chinese translations for reference. In case of discrepancy, the English version prevails.
> **注意**: `spec/` 目录为权威英文原版。`spec/zh/` 为中文参考翻译。如有出入，以英文原版为准。

---

## Quick Start / 快速开始

### Run the verifier / 运行验证器

```bash
python3 verify_p0.py
```

Expected output / 预期输出:
```
⏰ MODULE T: 17/17 passed
⚠️  MODULE E: 16/16 passed
🎲 MODULE C: 37/37 passed
🔌 MODULE I: 25/25 passed
📋 MODULE SK: 14/14 passed

  🎯 TOTAL: 109/109 tests passed
  🏆 ALL P0 FOUNDATIONS VERIFIED — ΣLang is sound!
```

### Read the spec / 阅读规范

Start with `spec/spec_p0_foundations.md` — it ties all four P0 modules together.

从 `spec/spec_p0_foundations.md` 开始 — 它聚合了全部四个 P0 模块。

---

## Design Philosophy / 设计理念

### Three-Layer Architecture / 三层架构

```
L0 — Core (core@1.0)        ← immutable, always loaded / 不可变，始终加载
     ℕ ℤ ℚ ℝ ℂ 𝔹 Sym Prop λ ∀ ∃
     + Iron Laws + Verifier interface

L1 — Standard Library          ← community maintained, versioned / 社区维护，版本化
     math.calculus / math.linear / finance.base
     signal.fourier / stat.prob / opt.gradient

L2 — User Packages            ← anyone can publish / 任何人可发布
     emoji.finance / tcm.wuzang / physics.qft
     must pass Verifier Iron Laws / 必须通过验证器铁律
```

### The 17 Iron Laws / 十七条铁律

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

Laws I–XII are defined in `spec/spec_p0_foundations.md` §0. Laws XIII–XVII plus the Law VIII
extension E-10 (Evaluation Determinism) are promoted extensions defined in
`spec/spec_top_extensions.md`, enforced by all three verifiers (Python / Rust / Elixir).

Law I–XII 定义于 `spec/spec_p0_foundations.md` §0。Law XIII–XVII 及 Law VIII 扩展 E-10（评估确定性）为已推广的扩展，定义于 `spec/spec_top_extensions.md`，由全部三个验证器强制执行。

---

## Why ΣLang? / 为什么需要 ΣLang？

### The Problem / 问题

Today, when you give the same Markdown document to different AIs:
- GPT-4 interprets it one way
- Claude interprets it another way
- Gemini interprets it a third way

**Same input, different outputs. This is unacceptable for production AI systems.**

如今，把同一份 Markdown 文档交给不同的 AI：
- GPT-4 按一种方式解读
- Claude 按另一种方式解读
- Gemini 按第三种方式解读

**同样的输入，不同的输出。这对生产级 AI 系统来说是不可接受的。**

### The Solution / 解决方案

ΣLang replaces ambiguous natural language with **mathematically anchored symbols**:

ΣLang 用**数学锚定的符号**替换歧义的自然语言：

| Traditional / 传统 | ΣLang |
|--------------------|--------|
| "add the numbers" / "把数字加起来" | `a ⊕ b` with associativity law / 带结合律 |
| "if score >= 90" / "如果分数 >= 90" | `grade(s) ≝ if s<60 then 𝗀𝖣 else…` + boundary tests / 边界测试 |
| "probably true" / "大概是真的" | `⊢_0.73 P` with calibration law / 带校准律 |
| "send message" / "发送消息" | `send(addr, msg)` with causal ordering / 带因果序 |

---

## Deprecated & Archived / 废弃与归档

The following files have been moved to `archive/` as they are superseded by newer specifications:

以下文件已被移至 `archive/` 目录，因为它们已被更新的规范所取代：

| File / 文件 | Reason / 原因 |
|------------|---------------|
| `archive/spec.md` | v0.1 Initial Draft — superseded by `spec/spec_p0_foundations.md` (v0.3.0). The v0.1 spec uses an older chapter-based structure (chapters 1–17) and lacks the §T/§E/§C/§I modular architecture, promoted Laws XIII–XVII, and three-verifier consensus enforcement. / v0.1 初稿 — 已被 `spec/spec_p0_foundations.md` (v0.3.0) 取代。v0.1 使用旧的章节目录结构（第 1–17 章），缺少 §T/§E/§C/§I 模块化架构、Law XIII–XVII 推广和三验证器共识。 |
| `archive/spec_p0_shadowing.md` | §S Shadowing v0.2 — explicitly marked SUPERSEDED. Content merged into `spec/spec_top_rules.md` §S on 2026-08-01. / §S 遮蔽 v0.2 — 明确标记为 SUPERSEDED。内容已于 2026-08-01 合并到 `spec/spec_top_rules.md` §S。 |

---

## Version / 版本

- **Milestone / 里程碑**: **v0.300 批次 17 阶段收尾 (2026-08-06)** — 小阶段 168/496 · 数字同步 + 全量验收全绿 · **v0.299 Elixir 积分-配额联动自检 (2026-08-06)** — 十七域自检齐 · **v0.298 Rust 积分-配额对账 (2026-08-06)** — 冒烟 72/72 · **v0.297 Python App 积分-配额联动剧本 (2026-08-06)** — --points-quota-test 2/2 · **v0.296 README 收官总览数字同步 (2026-08-06)** — Status v0.296 全貌（INV-SK-13 · --domains 72/72） · **v0.295 运行时不变量复核扩展 (2026-08-06)** — INV-SK-13 复核进审计，--domains 72/72 · **v0.294 标准库语料强化 (2026-08-06)** — math.base ⊖/⊙ 形状边界 31 项 · **v0.293 新增不变量 INV-SK-13 (2026-08-06)** — 积分-配额联动链 PROVED · 全量 258 PROVED · **v0.292 批次 16 收尾 (2026-08-06)** — 小阶段 160/496 · 数字同步 + 全量验收全绿 · **v0.291 Makefile/CI 补三链联动测试 (2026-08-06)** — make cb + CI 对账 · **v0.290 Elixir 三链联动自检 (2026-08-06)** — 十六域自检齐 · **v0.289 Rust 三链联动对账 (2026-08-06)** — 冒烟 70/70 · **v0.288 前端三链联动演示 (2026-08-06)** — web 契分-贡献-勋章三链 · **v0.287 Python App 契分-贡献-勋章三链剧本 (2026-08-06)** — --credit-badge-test 3/3 · **v0.286 README 收官总览数字同步 (2026-08-06)** — Status v0.286 全貌 · **v0.285 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.284 标准库语料强化 (2026-08-06)** — ai.confidence 六元素形状 20 项 · **v0.283 新增不变量 INV-SK-12 (2026-08-06)** — 契分-贡献-勋章三链联动 PROVED · 全量 254 PROVED · **v0.282 批次 15 收尾 (2026-08-06)** — 小阶段 150/496 · 数字同步 + 全量验收全绿 · **v0.281 Makefile/CI 补组合流转测试 (2026-08-06)** — make pfflow + CI 对账 · **v0.280 Elixir 组合流转自检 (2026-08-06)** — 十五域自检齐 · **v0.279 Rust 组合流转对账 (2026-08-06)** — 冒烟 67/67 · **v0.278 前端 portfolio 流转演示 (2026-08-06)** — web 组合生命周期链 · **v0.277 Python App portfolio 流转剧本 (2026-08-06)** — --portfolio-flow-test 5/5 · **v0.276 README 收官总览数字同步 (2026-08-06)** — Status v0.276 全貌 · **v0.275 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.274 标准库语料强化 (2026-08-06)** — data.transform 五元素形状 42 项 · **v0.273 新增不变量 INV-PF-8 (2026-08-06)** — 混合资产链完整性 PROVED · 全量 250 PROVED · **v0.272 批次 14 收尾 (2026-08-06)** — 小阶段 140/496 · 数字同步 + 全量验收全绿 · **v0.271 Makefile/CI 补库存流转测试 (2026-08-06)** — make invflow + CI 对账 · **v0.270 Elixir 库存流转自检 (2026-08-06)** — 十四域自检齐 · **v0.269 Rust 库存流转对账 (2026-08-06)** — 冒烟 65/65 · **v0.268 前端库存流转演示 (2026-08-06)** — web 混合出库链 · **v0.267 Python App 库存流转剧本 (2026-08-06)** — --inventory-flow-test 4/4 · **v0.266 README 收官总览数字同步 (2026-08-06)** — Status v0.266 全貌 · **v0.265 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.264 标准库语料强化 (2026-08-06)** — math.base 长形状 29 项 · **v0.263 新增不变量 INV-IN-8 (2026-08-06)** — 混合出库联动链 PROVED · 全量 246 PROVED · **v0.262 批次 13 收尾 (2026-08-06)** — 小阶段 130/496 · 数字同步 + 全量验收全绿 · **v0.261 Makefile/CI 补勋章链测试 (2026-08-06)** — make badge + CI 对账 · **v0.260 Elixir 勋章链自检 (2026-08-06)** — 十三域自检齐 · **v0.259 Rust 勋章链对账 (2026-08-06)** — 冒烟 63/63 · **v0.258 前端勋章链演示 (2026-08-06)** — web 勋章档位链 · **v0.257 Python App 勋章链剧本 (2026-08-06)** — --badge-test 2/2 · **v0.256 README 收官总览数字同步 (2026-08-06)** — Status v0.256 全貌 · **v0.255 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.254 标准库语料强化 (2026-08-06)** — ai.confidence 长形状 16 项 · **v0.253 新增不变量 INV-SK-11 (2026-08-06)** — 契分-勋章联动链 PROVED · 全量 242 PROVED · **v0.252 批次 12 收尾 (2026-08-06)** — 小阶段 120/496 · 数字同步 + 全量验收全绿 · **v0.251 Makefile/CI 补额度链测试 (2026-08-06)** — make quota + CI 对账 · **v0.250 Elixir 额度链自检 (2026-08-06)** — 十二域自检齐 · **v0.249 Rust 额度链对账 (2026-08-06)** — 冒烟 61/61 · **v0.248 前端额度流转演示 (2026-08-06)** — web 额度链 · **v0.247 Python App 额度流转剧本 (2026-08-06)** — --quota-flow-test 2/2 · **v0.246 README 收官总览数字同步 (2026-08-06)** — Status v0.246 全貌 · **v0.245 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.244 标准库语料强化 (2026-08-06)** — data.transform 长形状 33 项 · **v0.243 新增不变量 INV-SK-10 (2026-08-06)** — 契分-贡献联动链 PROVED · 全量 238 PROVED · **v0.242 批次 11 收尾 (2026-08-06)** — 小阶段 110/496 · 数字同步 + 全量验收全绿 · **v0.241 Makefile/CI 补贡献分测试 (2026-08-06)** — make contribution + CI 对账 · **v0.240 Elixir 贡献分自检 (2026-08-06)** — 十一域自检齐 · **v0.239 Rust 贡献分对账 (2026-08-06)** — 冒烟 60/60 · **v0.238 前端贡献分演示 (2026-08-06)** — web 贡献分链 · **v0.237 Python App 贡献分剧本 (2026-08-06)** — --contribution-test 2/2 · **v0.236 README 收官总览数字同步 (2026-08-06)** — Status v0.236 全貌 · **v0.235 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.234 标准库语料强化 (2026-08-06)** — math.base 算术边界 27 项 · **v0.233 新增不变量 INV-PF-7 (2026-08-06)** — 资产链完整性 PROVED · 全量 234 PROVED · **v0.232 批次 10 收尾 + PyPI 0.7.2 发布 (2026-08-06)** — 小阶段 100/496 · 每 100 阶段发布规则首次兑现 · **v0.231 Makefile/CI 补审计测试 (2026-08-06)** — make audit + CI 对账 · **v0.230 Elixir 审计链自检 (2026-08-06)** — 十域自检齐 · **v0.229 Rust 审计端点 + 对账 (2026-08-06)** — 冒烟 58/58 审计 · **v0.228 前端审计轨迹视图 (2026-08-06)** — web /audit · **v0.227 Python App 审计剧本 (2026-08-06)** — GET /audit + --audit-test 6/6 · **v0.226 README 收官总览数字同步 (2026-08-06)** — Status v0.226 全貌 · **v0.225 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.224 标准库语料强化 (2026-08-06)** — data.transform 反向形状 24 项 · **v0.223 新增不变量 INV-IN-7 (2026-08-06)** — 混合货品联动链 PROVED · 全量 230 PROVED · **v0.222 批次 9 收尾 (2026-08-06)** — 小阶段 90/496 · 数字同步 + 全量验收全绿 · **v0.221 Makefile/CI 补全流程测试 (2026-08-06)** — make full + CI 对账 · **v0.220 Elixir 全流程自检 (2026-08-06)** — 九域自检齐 · **v0.219 Rust 全流程对账 (2026-08-06)** — 冒烟 56/56 · **v0.218 前端全流程演示 (2026-08-06)** — web §SK 端到端链 · **v0.217 Python App 业务剧本 (2026-08-06)** — --full-test 5/5 · **v0.216 README 收官总览数字同步 (2026-08-06)** — Status v0.216 全貌 · **v0.215 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.214 标准库语料强化 (2026-08-06)** — ai.confidence 形状边界 12 项 · **v0.213 新增不变量 INV-SK-9 (2026-08-06)** — 额度-契分联动链 PROVED · 全量 226 PROVED · **v0.212 批次 8 收尾 (2026-08-06)** — 小阶段 80/496 · 数字同步 + 全量验收全绿 · **v0.211 Makefile/CI 补信用链测试 (2026-08-06)** — make credit + CI 对账 · **v0.210 Elixir 信用链自检 (2026-08-06)** — 八域自检齐 · **v0.209 Rust 信用链对账 (2026-08-06)** — 冒烟 53/53 · **v0.208 前端信用链演示 (2026-08-06)** — web 信用流转链 · **v0.207 Python App 信用链剧本 (2026-08-06)** — --credit-test 3/3 · **v0.206 README 收官总览数字同步 (2026-08-06)** — Status v0.206 全貌 · **v0.205 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.204 标准库语料强化 (2026-08-06)** — ai.confidence 边界 8 项 · **v0.203 新增不变量 INV-PF-6 (2026-08-06)** — 交易链完整性 PROVED · 全量 222 PROVED · **v0.202 批次 7 收尾 (2026-08-06)** — 小阶段 70/496 · 数字同步 + 全量验收全绿 · **v0.201 Makefile/CI 补库存链测试 (2026-08-06)** — make invchain + CI 对账 · **v0.200 Elixir 库存链自检 (2026-08-06)** — 七域自检齐 · **v0.199 Rust 库存链对账 (2026-08-06)** — 冒烟 51/51 · **v0.198 前端库存链展示增强 (2026-08-06)** — invChain 各步明细 · **v0.197 Python App 库存链剧本 (2026-08-06)** — --inventory-chain-test 5/5 · **v0.196 README 收官总览数字同步 (2026-08-06)** — Status v0.196 全貌 · **v0.195 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.194 标准库语料强化 (2026-08-06)** — data.transform 形状边界 18 项 · **v0.193 新增不变量 INV-IN-6 (2026-08-06)** — 入库-出库联动链 PROVED · 全量 218 PROVED · **v0.192 批次 6 收尾 (2026-08-06)** — 小阶段 60/496 · 数字同步 + 全量验收全绿 · **v0.191 Makefile/CI 补积分链测试 (2026-08-06)** — make points + CI 对账 · **v0.190 Elixir 积分链自检 (2026-08-06)** — 六域自检齐 · **v0.189 Rust 积分链对账 (2026-08-06)** — 冒烟 50/50 · **v0.188 前端积分链演示 (2026-08-06)** — web 积分流转链 · **v0.187 Python App 积分链剧本 (2026-08-06)** — --points-test 3/3 · **v0.186 README 收官总览数字同步 (2026-08-06)** — Status v0.186 全貌 · **v0.185 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.184 标准库语料强化 (2026-08-06)** — std 边界用例 24 项 · **v0.183 新增不变量 INV-SK-8 (2026-08-06)** — 赏金-积分联动链 PROVED · 全量 214 PROVED · **v0.182 批次 5 收尾 (2026-08-06)** — 小阶段 50/496 · 数字同步 + 全量验收全绿 · **v0.181 Makefile/CI 补错误边界测试 (2026-08-06)** — make errors + CI 对账 · **v0.180 Elixir 错误边界自检 (2026-08-06)** — 五域自检齐 · **v0.179 Rust 错误边界对账 (2026-08-06)** — 冒烟 48/48 · **v0.178 前端错误提示增强 (2026-08-06)** — 语义化错误文案 · **v0.177 Python App 错误边界剧本 (2026-08-06)** — --errors-test 7/7 · **v0.176 README 收官总览数字同步 (2026-08-06)** — Status v0.176 全貌 · **v0.175 运行时不变量复核扩展 (2026-08-06)** — --domains 71/71 · **v0.174 三域错误边界语料 (2026-08-06)** — corpus 错误路径强化 · consensus 56/56 · **v0.173 新增不变量 INV-PF-5 (2026-08-06)** — 买入-卖出链守恒 PROVED · 全量 171 PROVED · **v0.172 批次 4 收尾 (2026-08-06)** — 小阶段 40/496 · 数字同步 + 全量验收全绿 · **v0.171 Makefile/CI 补跨域测试 (2026-08-06)** — make cross-domain + CI 对账 · **v0.170 Elixir 跨域自检 (2026-08-06)** — 四域自检齐 · **v0.169 Rust 跨域链对账 (2026-08-06)** — 冒烟 46/46 跨域链 · **v0.168 前端三域联动演示 (2026-08-06)** — web 三域链展示 · **v0.167 Python App 三域联动剧本 (2026-08-06)** — --cross-domain-test 5/5 · **v0.166 README 收官总览数字同步 (2026-08-06)** — Status v0.166 全貌 · **v0.165 运行时不变量复核扩展 (2026-08-05)** — --domains 71/71 · **v0.164 跨域联动语料 (2026-08-05)** — corpus 三域链 10 操作 · consensus 56/56 · **v0.163 新增不变量 INV-SK-7 (2026-08-05)** — 任务-契分联动链 PROVED · 全量 137 PROVED · **v0.162 批次 3 收尾 (2026-08-05)** — 小阶段 30/496 · 数字同步 + 全量验收全绿 · **v0.161 Makefile/CI 补供应链测试 (2026-08-05)** — make inventory + CI 对账 · **v0.160 Elixir §IN 自检补全 (2026-08-05)** — 三域自检含联动链 · **v0.159 Rust 供应链链式对账 (2026-08-05)** — 冒烟 44/44 链式 · **v0.158 前端供应链联动演示 (2026-08-05)** — web 联动链展示 · **v0.157 Python App 供应链联动测试 (2026-08-05)** — --inventory-test 5/5 · **v0.156 README 收官总览数字同步 (2026-08-05)** — Status v0.156 全貌 · **v0.155 运行时不变量复核扩展 (2026-08-05)** — --domains 71/71 · **v0.154 供应链域联动语料 (2026-08-05)** — corpus 5 操作联动 · consensus 56/56 · **v0.153 新增不变量 INV-IN-5 (2026-08-05)** — 混合货品可加链 PROVED · 全量 125 PROVED · **v0.152 批次 2 收尾 (2026-08-05)** — 小阶段 20/496 · 数字同步 + 全量验收全绿 · **v0.151 Makefile/CI 补金融测试 (2026-08-05)** — make portfolio + CI 对账 · **v0.150 Elixir §IN/§PF 自检补全 (2026-08-05)** — §PF 原生函数 + 三域自检齐 · **v0.149 Rust 金融市场端点 (2026-08-05)** — sk §PF 实现 + 冒烟 43/43 · **v0.148 前端金融市场面板 (2026-08-05)** — web §PF 全操作 · 三域面板齐 · **v0.147 Python App portfolio 市场端点 (2026-08-05)** — §PF 5 端点 · --portfolio-test 5/5 · **v0.146 README 收官总览数字同步 (2026-08-05)** — Status v0.146 全貌 · **v0.145 运行时不变量复核扩展 (2026-08-05)** — --domains 71/71 · **v0.144 金融域联动语料 (2026-08-05)** — corpus 5 操作联动 · consensus 56/56 · **v0.143 新增不变量 INV-PF-4 (2026-08-05)** — 交易链可加性 PROVED · 全量 110 PROVED · **v0.142 批次收尾 (2026-08-05)** — 小阶段 10/496 · 数字同步 + 全量验收全绿 · **v0.141 Makefile/CI 补 stats (2026-08-05)** — make stats + CI 统计对账 · **v0.140 Elixir 自检覆盖确认 (2026-08-05)** — §SK 全操作 88/88 · **v0.139 双端统计对账 (2026-08-05)** — Rust /stats 与 Python 对等 · 冒烟 38/38 · **v0.138 前端统计显示 (2026-08-05)** — web /stats 平台统计 · **v0.137 教程补 pip 安装 (2026-08-05)** — TUTORIAL 双路径 A/B · **v0.136 新增不变量 INV-SK-6 (2026-08-05)** — 额度-托管联动链 PROVED · 全量 109 PROVED · **v0.135 五大制度联动语料 (2026-08-05)** — corpus 13 操作联动 · consensus 56/56 · **v0.134 业务统计端点 (2026-08-05)** — GET /stats JSON 统计 · **v0.133 README PyPI 徽章 (2026-08-05)** — PyPI version/downloads 徽章 · **v0.132 发布链端到端验证成功 (2026-08-05)** — 打 tag 全自动发布 PyPI 0.7.1 · **v0.131 发布链补全 (2026-08-05)** — 打 tag 全自动发布到 PyPI · **v0.130 PyPI 发布成功 (2026-08-05)** — pip install sigma-lang 全球可用 · **v0.129 发布验证成功 (2026-08-05)** — 打 tag 即发布 · GitHub Actions success · **v0.128 发布 workflow (2026-08-05)** — publish.yml tag 触发构建+Release · **v0.127 打包验证 (2026-08-05)** — pip install 即用 import 验证通过 · **v0.126 Python 包化 (2026-08-05)** — pyproject.toml 打包 sigma_core · **v0.124 入门教程 (2026-08-05)** — docs/TUTORIAL.md 30 分钟上手 · **v0.122 生产启动脚本 (2026-08-05)** — make ready/deploy 一条命令上线 · **v0.121 上线就绪检查 (2026-08-05)** — --launch-ready 环境一键确认 · **v0.120 里程碑达成 (2026-08-05)** — v0.100–v0.120 连续推进收官 · **v0.119 README 收官总览更新 (2026-08-05)** — Status v0.119 全貌 · **v0.118 性能基准 (2026-08-05)** — --bench 吞吐/延迟基线 · **v0.117 README 上线指南 (2026-08-05)** — Deploy Guide 上线启动+运维要点 · **v0.116 CI 报告扩展 (2026-08-05)** — --report 含运行验收段 · **v0.115 协议版本化 (2026-08-05)** — spec 0.7.0 + RFC 记录 · **v0.114 前端联调剧本扩展 (2026-08-05)** — --frontend-scenario 19/19 覆盖三域 · **v0.113 双端面板对账 (2026-08-05)** — Rust /panel 与 Python 对等 · **v0.112 API 文档同步 (2026-08-05)** — docs/api_zhaocha.md /panel + 新命令 · **v0.111 前端供应链面板 (2026-08-05)** — web inventory 全操作 · **v0.110 前端增长期面板 (2026-08-05)** — web badge/dispute/team 全操作 · **v0.109 三域 story 不变量段扩展 (2026-08-05)** — --domains 71/71 含 20 项不变量复核 · **v0.108 sigma-prove 全量重验 80+ (2026-08-05)** — 258 项 PROVED / 29 模块全绿 · **v0.107 任务生命周期不变量 (2026-08-05)** — INV-SK 状态机链 PROVED · **v0.106 金融不变量补全 (2026-08-05)** — INV-PF 资产非负链 PROVED · **v0.105 供应链不变量补全 (2026-08-05)** — INV-IN 入库链可加/出库链不超卖 PROVED · **v0.104 上线验收 (2026-08-05)** — --deploy-accept 上线形态 9/9 · **v0.103 并发安全验证 (2026-08-05)** — --concurrency-test 并发 70 请求状态一致 · **v0.102 launch 默认日志接入 (2026-08-05)** — data/ 默认 state/audit/log · **v0.101 部署加固 (2026-08-05)** — --launch 透传部署配置 + 持久化健壮性 · **v0.100 跨百版本里程碑 (2026-08-04)** — v0.10→v0.100 里程碑链完整 · **v0.99 里程碑达成 (2026-08-04)** — v0.91–v0.99 连续推进收官 · **v0.98 README 找茬运行指南 (2026-08-04)** — Run Guide 一条命令开工 · **v0.97 协议版本化 (2026-08-04)** — spec 0.6.0 + RFC 记录 · **v0.96 运行验收 (2026-08-04)** — --run-accept 端到端 8/8 · **v0.95 运行状态面板 (2026-08-04)** — /panel 业务+门禁摘要页 · **v0.94 一键开工 (2026-08-04)** — --launch 前后端一条命令 · **v0.93 前端联调验证 (2026-08-04)** — --web-test 双服务 5/5 · **v0.92 前端 UI 完善 (2026-08-04)** — 错误横幅/任务详情/用户面板/状态筛选 · **v0.91 找茬静态前端 (2026-08-04)** — web/index.html 单页应用 · **v0.90 里程碑达成 (2026-08-04)** — v0.71–v0.90 连续推进收官 · **v0.89 README 收官总览 (2026-08-04)** — Status 56/56 + 收官总览段 · **v0.88 贡献者指南 (2026-08-04)** — docs/CONTRIBUTING.md 上手路径 · **v0.87 CI 全量回归报告 (2026-08-04)** — --report JSON + CI artifact · **v0.86 协议版本化 (2026-08-04)** — spec 0.5.0 + RFC 记录 · **v0.85 README 开工检查清单 (2026-08-04)** — Launch Checklist 10 项上线勾选 · **v0.84 双端 HTTP API 逐项对账 (2026-08-04)** — Rust 冒烟 36/36 与 Python 逐项一致 · **v0.83 前端联调剧本 (2026-08-04)** — `--frontend-scenario` 11/11 · **v0.82 HTTP 方法语义对齐 (2026-08-04)** — POST 变更 + GET 查询 · **v0.81 找茬 API 文档 (2026-08-04)** — docs/api_zhaocha.md 全端点文档 · **v0.80 sigma-prove 全量重验 70+ (2026-08-04)** — 258 项 PROVED / 29 模块全绿 · **v0.79 三域 story 不变量段扩展 (2026-08-04)** — --domains 47/47 含 12 项不变量复核 · **v0.78 增长期跨操作不变量 (2026-08-04)** — INV-G 授权签发/裁决链 PROVED · **v0.77 团机制跨操作不变量 (2026-08-04)** — INV-T 不超员/成员递增 PROVED · **v0.76 额度制跨操作不变量 (2026-08-04)** — INV-Q 不超用/重置恢复 PROVED · **v0.75 找茬 App 启动自检 (2026-08-04)** — --serve 先过 §SK.6 门禁再监听 · **v0.74 找茬 App 健康检查 (2026-08-04)** — `/health` 服务状态 + 门禁摘要 · **v0.73 找茬 App 分级日志 (2026-08-04)** — `--log-file` 访问/错误分级 · **v0.72 找茬 App 状态原子写 (2026-08-04)** — tmp + rename 防崩溃损坏 · **v0.71 找茬 App 鉴权层 (2026-08-04)** — `--auth-token` token 校验 401 门禁 · **v0.70 里程碑达成 (2026-08-04)** — v0.51–v0.70 连续推进收官 · **v0.69 README 产品落地指南 (2026-08-04)** — 找茬功能 ↔ §SK 对照 + 落地三步走 · **v0.68 找茬 App 部署文档 (2026-08-04)** — docs/deploy_zhaocha.md · **v0.67 找茬业务流双端对账 (2026-08-04)** — --scenario 双端 16/16 逐项一致 · **v0.66 找茬完整业务流 CLI 剧本 (2026-08-04)** — `--scenario` 16/16 · **v0.65 sigma-prove 全量义务重验 (2026-08-04)** — 62 项 PROVED / 29 模块全绿 · **v0.64 三域 story 不变量检查段 (2026-08-04)** — --domains 41/41 含不变量复核 · **v0.63 找茬跨操作不变量 (2026-08-04)** — INV-SK 赏金守恒/不超提 PROVED · **v0.62 金融跨操作不变量 (2026-08-04)** — INV-PF 现金/份额守恒 PROVED · **v0.61 供应链跨操作不变量 (2026-08-04)** — INV-IN 总量守恒/非负链 PROVED · **v0.60 协议版本化 (2026-08-04)** — spec 0.4.0 + RFC 记录 · **v0.59 README 架构数据流全景 (2026-08-04)** — 架构数据流全景章节 · **v0.58 spec 中英对照补全 (2026-08-04)** — §IN 供应链中文参考版 · **v0.57 语料扩容 (2026-08-04)** — 语料按主题拆三模块，consensus 56/56 · **v0.56 一键验收接 CI (2026-08-04)** — Makefile + GitHub Actions · **v0.55 找茬 App 审计日志 (2026-08-04)** — `--audit-log` 可对账审计追踪 · **v0.54 找茬 App HTTP 错误码语义化 (2026-08-04)** — §SK/§IN 错误 → 语义化 4xx · **v0.53 找茬 App 查询端点 (2026-08-04)** — /tasks /users 任务与用户列表 · **v0.52 找茬 App 用户会话层 (2026-08-04)** — /register /me 用户态隔离 · **v0.51 找茬 App 状态持久化 (2026-08-04)** — `--state` JSON 重启不丢 · **v0.50 里程碑达成 (2026-08-03)** — v0.27–v0.50 连续推进收官 · **v0.49 收官验收续 (2026-08-03)** — `sigma-accept.py` 9 道门禁一键验收 · **v0.48 一键收官验收 (2026-08-03)** — `sigma-accept.py` 六道门禁一键跑通 · **v0.47 README 新人上手 (2026-08-03)** — 三域概览 + 快速开始 + 验证清单 · **v0.46 三域协议巩固 (2026-08-03)** — `--domains` 35/35 · **v0.45 供应链 app 参考实现 (2026-08-03)** — §IN HTTP 端点 + 冒烟 25/25 · **v0.44 三端供应链 story 对账 (2026-08-03)** — 供应链故事线三端 6/6 逐项一致 · **v0.43 供应链证明 + runtime (2026-08-03)** — §IN 义务 PROVED + --inventory 6/6 · **v0.42 供应链语料 + 共识 (2026-08-03)** — inventory 语料进共识门禁，47/47 · **v0.41 三端供应链执行层 (2026-08-03)** — §IN 五操作三端实现 · **v0.40 第三个自举新域（供应链 inventory@1.0）(2026-08-03)** — §IN 供应链语义，泛化性三验 · **v0.39 完整业务验收剧本 (2026-08-03)** — `sigma-runtime --all` 29/29 · **v0.38 Rust app 增长期端点 + 冒烟对账 (2026-08-03)** — 增长期 HTTP 双端 20/20 逐项一致 · **v0.37 Python app 增长期端点 (2026-08-03)** — 增长期 HTTP 端点 + 冒烟 20/20 · **v0.36 三端增长期 story 对账 (2026-08-03)** — 增长期故事线三端 11/11 逐项一致 · **v0.35 增长期审计故事线 (2026-08-03)** — `sigma-runtime --growth` 11/11 · **v0.34 增长期义务证明 (2026-08-03)** — sigma-prove 增长期 7 项义务 PROVED · **v0.33 增长期语料模块化 (2026-08-03)** — socketkit_growth 独立语料，consensus 45/45 · **v0.32 增长期语义⑥积分可追溯 (2026-08-03)** — `points_ledger` 积分来源可追溯 · **v0.31 增长期语义⑤额度预支 (2026-08-03)** — `quota_advance` 预支下月额度 · **v0.30 增长期语义④团收益 (2026-08-03)** — `team_share` 团内收益按贡献分配 · **v0.29 增长期语义③团机制 (2026-08-03)** — `team_create/team_join` 受茬团/找茬团 · **v0.28 增长期语义②督导 (2026-08-03)** — `dispute_review` 督导处理纠纷 · **v0.27 增长期语义①核验师 (2026-08-03)** — `badge_issue` 核验师签发勋章 · **v0.26 Rust HTTP 服务 + 冒烟对账 (2026-08-03)** — HTTP 层 Python/Rust 双端同尺 · **v0.25 Rust 参考实现 (2026-08-03)** — `app.rs` 生产级后端，四端 story 逐项一致 · **v0.24 三端 §SK.6 story 一致性 (2026-08-03)** — 业务故事线 Python/Rust/Elixir 三端逐项一致 · **v0.23 MVP 端到端 HTTP 冒烟测试 (2026-08-03)** — `sigma_app --smoke` HTTP 七步全链路可重复验收 · **v0.22 找茬 MVP 参考实现 (2026-08-03)** — `sigma_app.py` 可运行后端，业务全委托 §SK 语义 · **v0.21 找茬 MVP 全链路审计剧本 (2026-08-03)** — §SK.6 十二步业务故事线 + `sigma-runtime --story`，App 开工验收剧本 · **v0.20 找茬五大制度补齐 (2026-08-03)** — 额度制/积分制/勋章制进 ΣLang，业务规则链完整可证明 · **v0.19 第二个自举新域（金融 portfolio@1.0）(2026-08-03)** — 协议泛化性再验证，consensus 43/43 · **v0.18 状态机不变量证明 (2026-08-03)** — 作者授权 + 4 项状态机不变量 z3 可证明 · **v0.17 §SK 对齐真实业务 (2026-08-03)** — Task 4 态状态机 + 契分制，MVP 全流程三端一致可执行可证明 · **v0.16 SocketKit 语料执行化 (2026-08-03)** — 业务语义进入 Law XIII 共识门禁 · **v0.15 三端 §SK 执行层 (2026-08-03)** — §SK 业务语义 Python/Rust/Elixir 三端一致可执行 · **v0.14 SocketKit Runtime (2026-08-03)** — §SK 参考实现 + 审计运行时 + z3 证明闭环，共识门禁 41/41 全绿 · **v0.13 SocketKit Protocol (2026-08-02)** — §SK 语义定义，共识门禁 40/40 全绿 · **v0.12 Novel Spec Test (2026-08-02)** — 新域自举闭环 · **v0.11 可用 (2026-08-02)** — 包管理器 `sigma-cli.py` + 标准库 3 包，共识门禁 38/38 全绿 · **v0.10 可用 (2026-08-02)** — 数学符号 / 基本操作 / 常量包可用，证明可消解，共识门禁 35/35 全绿
- **Spec Version / 规范版本**: 0.7.0
- **Date / 日期**: 2026-08-05
- **License / 许可证**: MIT

## Citation / 引用

```
ΣLang: An AI-Native Semantic Protocol
Version 0.7.0
https://github.com/sigma-lang/sigma-lang
```
*（内容由AI生成，仅供参考）*
