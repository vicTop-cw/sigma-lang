# ΣLang 使用指南（v0.124）

> 配合 `README.md` 的「大白话导读」与「怎么用它」阅读。本指南按**角色**给出
> 详细上手路径——你是哪种人，就照着哪一节走。

---

## 0. 你属于哪种角色？

| 角色 | 你是谁 | 看哪节 |
|------|--------|--------|
| 产品用户 | 想直接用找茬平台，不写代码 | §1 |
| 业务开发者 | 想把 ΣLang 用在自己的业务上（给 AI 定规则） | §2 |
| 集成工程师 | 想把找茬语义嵌进自己的系统 | §3 |
| AI 使用者 | 想让另一个 AI 智能体用这个仓库 | §4 |

---

## 1. 产品用户：直接跑找茬平台（约 2 分钟）

```sh
git clone https://github.com/vicTop-cw/sigma-lang.git
cd sigma-lang
# 就绪检查（环境没问题才继续）
python3 impl/python/sigma_app.py --launch-ready
# 启动前后端（Ctrl+C 停止）
python3 impl/python/sigma_app.py --launch
```

启动后：

| 入口 | 地址 | 用途 |
|------|------|------|
| 前端页面 | http://127.0.0.1:8000 | 注册/发单/接单/验收/提现/勋章 |
| API | http://127.0.0.1:8080 | 全部业务端点 |
| 运行面板 | http://127.0.0.1:8080/panel | 运行状态 + 门禁摘要 |
| 健康检查 | http://127.0.0.1:8080/health | 服务状态 |

**10 分钟完整体验**：前端注册两个用户（作者 + 找茬人）→ 作者开户额度 →
发一单（赏金 100）→ 任务列表看到待接单 → 找茬人接单 → 提交 → 作者验收 →
任务变已完成 → 找茬人提现 100 → 看勋章。全程中文界面，点按钮即可。

---

## 2. 业务开发者：用 ΣLang 给自己的业务定规则

ΣLang 的工作方式：**先把业务规则写成可验证的文档，再用三端验证器和数学证明
确认规则不会自相矛盾**。任何 AI/系统照着这份文档执行，行为就完全一致。

### 2.1 一次完整的"新规则"流程（以给"验收"加一条校验为例）

1. **读规范学格式**（10 分钟）：`spec/spec_p0_socketkit.md` 看一个操作怎么
   定义（指纹 / 签名 / 定律 / 测试）。

2. **写/改规则**：在语料 `corpus/socketkit_taskflow_ok.md` 里加一条测试：
   ```markdown
   - test: "作者本人才能验收"
     expr: task_accept(task, non_author)
     expect: ⊥  # 非作者验收 → 必须报错
   ```

3. **三端验证**：`python3 verify_consensus.py`
   —— Python / Rust / Elixir 三个验证器对同一份规则必须给出一致结论
   （不一致就是某个实现写错了，修到一致为止）。

4. **数学证明**：`python3 tools/sigma-prove.py`
   —— z3 把每条定律变成数学义务，全部 `PROVED` 才算"规则不会自相矛盾"。

5. **一键验收**：`python3 tools/sigma-accept.py`
   —— 十道门禁全绿，你的规则才合格。

### 2.2 目录对应关系（改哪里）

| 想改什么 | 改哪个文件 |
|----------|-----------|
| 业务规则定义 | `spec/spec_p0_*.md`（英文为准） |
| 规则测试（语料） | `corpus/*_ok.md` |
| 三端执行实现 | `impl/python/sigma_core.py` / `impl/verifier/src/sk.rs` / `impl/elixir_rt/sigma_verify.exs` |
| 证明义务 | `tools/sigma-prove.py` |

---

## 3. 集成工程师：把语义嵌进自己的系统

### 3.1 方式 A：Python 当库用（零依赖，纯函数）

```python
import sys
sys.path.insert(0, "impl/python")
import sigma_core as core

# 找茬任务流（结果与三端验证器共识一致）
task = core.task_create(7, 100)      # [7, 100, 0, 0]
task = core.accept_task(task, 3)     # [7, 100, 1, 3]
task = core.task_submit(task)        # [7, 100, 2, 3]
task = core.task_accept(task, 7)     # [7, 100, 3, 3]

# 供应链
inv = core.inventory_new(10, 20)     # [10, 20]
inv = core.receive_stock(inv, 0, 5)  # [15, 20]
inv = core.ship_stock(inv, 0, 4)     # [11, 20]

# 金融
pf = core.buy(core.portfolio_new(100), 0, 30)
```

### 3.2 方式 B：HTTP 调参考后端

```sh
# 启动后端（或 make deploy 前后端一起）
python3 impl/python/sigma_app.py --launch
# 业务调用（GET + query 参数）
curl "http://127.0.0.1:8080/post?author=7&bounty=100"
curl "http://127.0.0.1:8080/claim?task=0&hunter=3"
curl "http://127.0.0.1:8080/accept?task=0&caller=7"
```
完整端点与错误码见 `docs/api_zhaocha.md`。生产建议：`--auth-token SECRET`
启用鉴权、`--state/--audit-log/--log-file` 落 `data/`（默认已开）。

---

## 4. AI 使用者：让别的 AI 智能体用这个仓库

### 4.1 现成 prompt 模板（发给任何 AI）

> 你是 ΣLang 协议的开发者。先读 `README.md` 的"大白话导读"和"怎么用它"，
> 再读 `spec/spec_p0_socketkit.md` 掌握业务规则写法。你的任务：
> 1. 用 `impl/python/sigma_core.py` 的纯函数实现业务逻辑（禁止自己重新定义规则）；
> 2. 用 `python3 verify_consensus.py` 确认语义与三个验证器一致；
> 3. 改完必须 `python3 tools/sigma-accept.py` 十道门禁全绿。
> 规则以 spec/ 为准，语料在 corpus/，任何不一致先查 spec 再改实现。

### 4.2 常见 AI 协作模式

| 场景 | 给 AI 的指令示例 |
|------|-----------------|
| 让 AI 实现一个业务动作 | "用 sigma_core 实现'督导裁决'：先读 spec 里 dispute_review 的定义，再写代码，跑 verify_consensus 确认" |
| 让 AI 审查规则是否一致 | "检查 corpus/socketkit_ok.md 里的规则和三端实现是否一致，不一致指出 spec 为准" |
| 让 AI 写新业务域 | "按 spec_p0_inventory.md 的格式，把'库存管理'写成一个新域：规范 + 语料 + 三端实现，最后 sigma-accept 全绿" |
| 让 AI 解释行为 | "任务从发单到验收的状态怎么流转？读 spec 和 sigma_core 后解释" |

---

## 5. 常用命令速查

```sh
python3 impl/python/sigma_app.py --launch          # 启动前后端（生产）
python3 impl/python/sigma_app.py --launch-ready    # 生产就绪检查
python3 impl/python/sigma_app.py --deploy-accept   # 上线验收 9/9
python3 impl/python/sigma_app.py --bench           # 性能基线
python3 verify_consensus.py                        # 三端共识 56/56
python3 verify_p0.py                               # 算法正确性 109/109
python3 tools/sigma-prove.py                       # z3 证明 290 项 PROVED
python3 tools/sigma-runtime.py --domains           # 三域审计 80/80
python3 tools/sigma-accept.py                      # 十道门禁一键验收
make deploy                                       # = ready + launch
```

---

## 6. 常见问题（FAQ）

**Q: 这不是编程语言，那我能用它写程序吗？**
A: 不能直接写程序，但能：① 定义业务规则（给 AI 定语义）；② 调用它的参考
实现（Python import / HTTP）；③ 用它保证你的规则可验证、可证明、多端一致。

**Q: 三个验证器是干嘛的？为什么必须三个？**
A: 同一份规则，三个独立实现（Python/Rust/Elixir）结论一致，说明规则语义
唯一，不是某个实现的 bug 或解读偏差——这就是"共识门禁"的意义。

**Q: 我改了 corpus 里的测试，verify_consensus 红了怎么办？**
A: 红 = 三端结论不一致。先看哪个实现错了，修实现（不是删测试）——规则以
spec/ 为准，实现要对齐 spec。

**Q: 我只想用找茬产品，需要会 Rust / Elixir 吗？**
A: 不需要。产品是 Python 后端 + 静态前端，`python3` 就能跑；Rust/Elixir
只用于协议验证，不是使用前提。

**Q: AI 拿到这个仓库第一步该干嘛？**
A: 把 §4.1 的 prompt 发给它。它会先读导读 → 读 spec → 用 sigma_core →
跑门禁，按协议方式工作，而不是自己瞎定义规则。
