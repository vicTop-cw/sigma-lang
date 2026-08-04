# ΣLang Master Plan v0.5

> Target audience: **AI agents**.  
> Goal: This document is sufficient for ANY AI to understand, implement, and extend ΣLang.  
> Principle: Spec lives in spec files; this plan tells you what to DO with them.

---

## 状态快照（2026-08-02）

- ✅ **REACHED v0.10**: 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）、基本操作（`index()`/`I₂`、矩阵运算）、
  常量包（§C `0xK0xx`/`0xQ0xx`）三端求值器实现；consensus 35/35 → 38/38、p0 95/95。
- ✅ **REACHED v0.11**: 包管理器 `tools/sigma-cli.py` + 标准库 3 包
  （`std/math.base.md` / `std/data.transform.md` / `std/ai.confidence.md`）+ 三端共识覆盖。
- ✅ **REACHED**: AI Implementation Guide（4 个 spec 模块） + 参考实现 `impl/python/sigma_core.py`（59/59）
  + **AI bootstrapping test**（`tools/sigma-bootstrap.py` 一次干净跑通 spec→impl→verify→pass）。
- ✅ **REACHED**: Verifier format (json output) —— `verify_p0.py --json` 输出结构化 JSON（§1.2：
  spec/pass/modules/fingerprint），`sigma-cli verify --p0` 打通 CLI。
- ✅ **REACHED v0.12 (2026-08-02)**: Novel Spec Test —— `corpus/novel_gene_ok.md`（DNA 对齐语义，
  §5.2）三端验证器一致（consensus 39/39），跑通完整闭环；v0.10/v0.11 不回归。
- ✅ **REACHED v0.13 (2026-08-02)**: SocketKit Protocol —— `spec/spec_p0_socketkit.md`（§SK：
  task_create / review_merge / contribution_score 的 ΣLang 语义）+ `corpus/socketkit_ok.md`
  三端一致（consensus 40/40），走通 RFC → spec → 验证器 → 测试 晋升路径；v0.10–v0.12 不回归。
- ✅ **REACHED v0.14 (2026-08-03)**: SocketKit Runtime（审计闭环）—— §SK 参考实现进入
  `impl/python/sigma_core.py`（自检 75/75）· 审计运行时 `tools/sigma-runtime.py`（业务 trace →
  逐事件 ΣLang obligation 日志，10/10 满足）· `sigma-prove` 新增 §SK 六条定律义务全部
  `PROVED (unsat)` · 负例 `corpus/socketkit_break.md`（E-02，三端一致 FAIL，consensus 41/41）·
  §SK 行为测试进 `verify_p0.py`（109/109）；v0.10–v0.13 不回归。
- ✅ **REACHED v0.15 (2026-08-03)**: 三端 §SK 语义执行层—— §SK 参考实现从 Python 单侧
  同步到 Rust（`impl/verifier/src/sk.rs` + `--sk-self-check`，16/16）与 Elixir
  （`sigma_verify.exs` §SK + `--sk-self-check`，16/16）；三端行为一致（Python 75/75 含 §SK 16 项），
  0 warning；consensus 41/41、p0 109/109 不回退，v0.10–v0.14 全部保持全绿。
- ✅ **REACHED v0.16 (2026-08-03)**: SocketKit 语料执行化—— 三端求值器（verify_consensus.py /
  evaluator.rs / sigma_verify.exs）的 eval_expr 直接支持 §SK 三操作真实调用
  （`task_create(a,b)` / `review_merge([...])` / `contribution_score([...])`，含 ⊥ BountyErr /
  TypeError / ShapeError 错误路径）；`corpus/socketkit_ok.md` 的 Tests 从规范表达式
  （⊕ ∈ ⊘）升级为真实调用，consensus 门禁（Law XIII）直接验证业务语义本身；
  9/9 三端一致（consensus 41/41）、p0 109/109、三端 0 warning，v0.10–v0.15 不回归。
- ✅ **REACHED v0.17 (2026-08-03)**: §SK 对齐真实业务（MVP 语义扩展）—— 依据
  `D:\Desktop\来找茬_需求文档.md` v1.0 校准：Task 扩展为 4 元组 `[author, bounty, status, hunter]`
  并引入 4 态状态机（0=待接单 → 1=进行中 → 2=待验收 → 3=已完成）；新增 `accept_task`（接单）、
  `task_submit`（提交成果）、`task_accept`（受茬人单人验收）、`credit_score`（契分制：基础 100、
  完成 +5/单、违约 ×0.7）；`review_merge` 修正定位为增长期核验师多人评审场景；三端执行层与
  eval_expr 同步（sigma_core 91/91、三端 §SK 自检 32/32、socketkit_ok 24/24 三端一致）、
  sigma-prove 18 项 §SK 义务全部 PROVED (unsat)、sigma-runtime 完整业务 trace 23/23；
  consensus 41/41、p0 109/109、三端 0 warning，v0.10–v0.16 不回归。
- ✅ **REACHED v0.18 (2026-08-03)**: 状态机不变量证明（业务规则固化）—— `task_accept`
  增加作者授权参数（caller ≡ author 方可验收，否则 ⊥ AuthError），spec 新增 §SK.3.8
  不变量章节（INV-1 状态单调 / INV-2 终态不可变 / INV-3 bounty-hunter 守恒 /
  INV-4 作者授权）；三端执行层与 eval_expr 同步授权校验（sigma_core 92/92、三端 §SK
  自检 33/33、socketkit_ok 25/25 三端一致）；`sigma-prove` 新增 6 项不变量义务全部
  `PROVED (unsat)`（共 23 项 §SK 义务）；`sigma-runtime` 审计 trace 增加不变量逐条复核
  （31/31）；consensus 41/41、p0 109/109、三端 0 warning，v0.10–v0.17 不回归。
- ✅ **REACHED v0.19 (2026-08-03)**: 第二个自举新域（金融 portfolio@1.0）——
  `spec/spec_p0_portfolio.md`（§PF：portfolio_new / buy / sell / portfolio_value /
  risk_score，单位价格 1 使守恒可证）+ `corpus/portfolio_ok.md`（19/19 三端一致 PASS）
  与 `corpus/portfolio_break.md`（E-02 三端一致 FAIL）；三端执行层与 eval_expr 同步
  新域真实调用（sigma_core 111/111、Rust/Elixir portfolio 19/19、0 warning）；
  `sigma-prove` 新增 10 项 §PF 义务全部 `PROVED (unsat)`（共 33 项 §SK+§PF 义务）；
  `sigma-runtime` 审计 trace 增加 §PF 段（45/45）；consensus 43/43、p0 109/109、
  三端 0 warning，v0.10–v0.18 不回归。
- ✅ **REACHED v0.20 (2026-08-03)**: 找茬五大制度补齐—— 依据 `D:\Desktop\来找茬_需求文档.md`
  §四 把剩余三制度纳入 §SK：SK.3.9 额度制（`quota_new/quota_use/quota_reset`，月额/
  扣减/月底清零）、SK.3.10 积分制（`points_new/points_hold/points_release/points_withdraw`，
  托管冻结/释放/提现）、SK.3.11 勋章制（`badge_level`，铜银金钻四级）；三端执行层与
  eval_expr 同步（sigma_core 130/130、三端 §SK 自检 52/52、socketkit_ok 50/50 三端一致、
  0 warning）；`sigma-prove` 新增 8 项三制度义务全部 `PROVED (unsat)`（共 41 项）；
  `sigma-runtime` 审计 trace 增加三制度段（59/59）；consensus 43/43、p0 109/109、
  三端 0 warning，v0.10–v0.19 不回归。
- ✅ **REACHED v0.21 (2026-08-03)**: 找茬 MVP 全链路审计剧本—— spec 新增 §SK.6
  MVP 业务剧本（12 步端到端验收场景：开户额度→发布需求→扣减额度→赏金托管→接单→
  提交成果→验收确认→释放赏金→找茬人提现→契分奖励→贡献累计→勋章升级）；`sigma-runtime`
  新增 `--story` 入口（run_mvp_story），一次跑通完整业务故事线并逐事件复核不变量
  （INV-1 状态单调 / INV-3 守恒 / INV-4 作者授权 / 额度扣减 / 积分托管守恒），18/18
  义务满足——作为 App 开工的「验收剧本」；consensus 43/43、p0 109/109、三端 0 warning，
  v0.10–v0.20 不回归。
- ✅ **REACHED v0.22 (2026-08-03)**: 找茬 MVP 参考实现—— `impl/python/sigma_app.py`
  （MVPApp：内存存储 + 业务方法**全部委托** sigma_core §SK，App 层只管状态、不重写
  业务规则；stdlib-only HTTP JSON API：`--serve` 暴露 `/post /claim /submit /accept /
  /withdraw /badge`）；`python3 impl/python/sigma_app.py` 自检跑通 §SK.6 十二步剧本
  （15/15），步骤与 `sigma-runtime --story` 一一对应——证明被审计的验收剧本可直接
  实现为可运行后端；consensus 43/43、p0 109/109、三端 0 warning，v0.10–v0.21 不回归。
- ✅ **REACHED v0.23 (2026-08-03)**: MVP 端到端 HTTP 冒烟测试—— `sigma_app.py` 增加
  `/quota` 端点（开户额度，补全 HTTP 全链路）与 `--smoke` 模式（run_http_smoke：
  起服务→HTTP 七步全链路 `/quota → /post → /claim → /submit → /accept → /withdraw →
  /badge`→逐响应断言→关服务，13/13 通过）——参考实现"作为 HTTP 服务的可用性"
  被可重复执行的冒烟测试固化；自检 15/15 不回归；consensus 43/43、p0 109/109、
  三端 0 warning，v0.10–v0.22 不回归。
- ✅ **REACHED v0.24 (2026-08-03)**: 三端 §SK.6 story 一致性—— §SK.6 MVP 剧本
  从 Python 单侧扩到三端：Rust `sk.rs` 新增 `story()` + CLI `--sk-story`（15/15）、
  Elixir `sigma_verify.exs` 新增 `sk_story()` + `--sk-story`（15/15），与 Python
  `sigma_app.py` 15/15 逐项一致——三把独立的尺子审计**同一条业务故事线**
  （Law XIII 在"产品层"收官）；consensus 43/43、p0 109/109、三端 0 warning，
  v0.10–v0.23 不回归。
- ✅ **REACHED v0.25 (2026-08-03)**: Rust 参考实现（贴近生产部署）——
  `impl/verifier/src/app.rs`（MVPApp 的 Rust 版：内存状态 + 业务方法**全部委托**
  sk.rs §SK，App 层零业务规则重写），CLI 新增 `--app-self-check`；自检跑通
  §SK.6 十二步剧本（15/15），与 Python `sigma_app.py`（15/15）、Rust `--sk-story`
  （15/15）、Elixir `--sk-story`（15/15）**四端逐项一致**——同一业务故事线在
  Python 参考后端与 Rust 生产级实现上算出同一个答案；`cargo build` 0 error/0
  warning；consensus 43/43、p0 109/109，v0.10–v0.24 不回归。
- ✅ **REACHED v0.26 (2026-08-03)**: Rust HTTP 服务 + 冒烟对账—— `app.rs` 增加
  stdlib-only HTTP JSON API（手写 TcpListener + serde_json，端点 `/quota /post
  /claim /submit /accept /withdraw /badge` 与 Python `sigma_app.py --serve`
  一致，业务全部委托 App 层 → §SK），CLI 新增 `--app-serve`；`--app-smoke`
  （run_smoke：起服务→HTTP 七步全链路→逐响应断言→13/13）与 Python
  `sigma_app.py --smoke`（13/13）**双端逐项一致**——HTTP 层也同尺；
  `cargo build` 0 error/0 warning；consensus 43/43、p0 109/109，v0.10–v0.25
  不回归。
- ✅ **REACHED v0.27 (2026-08-03)**: 增长期语义①核验师—— §SK.3.12 `badge_issue`
  （核验师签发勋章，需求文档 §八）：(v, u, s) → [v, u, badge_level(s)]，只有授权
  核验师（v ≥ 1000）可签发否则 ⊥ AuthError；三端执行层 + eval_expr 同步
  （sigma_core 134/134、Rust/Elixir §SK 自检 56/56、socketkit_ok 53/53 三端一致、
  0 warning）；consensus 43/43、p0 109/109，v0.10–v0.26 不回归。
- ✅ **REACHED v0.28 (2026-08-03)**: 增长期语义②督导—— §SK.3.13 `dispute_review`
  （督导处理纠纷，需求文档 §三角色）：加权支持 ≥ 加权驳回 → 1 否则 0，binary +
  order-independent（与 review_merge 同构）；三端执行层 + eval_expr 同步
  （sigma_core 138/138、Rust/Elixir §SK 自检 60/60、socketkit_ok 56/56 三端一致、
  0 warning）；consensus 43/43、p0 109/109，v0.10–v0.27 不回归。
- ✅ **REACHED v0.29 (2026-08-03)**: 增长期语义③团机制—— §SK.3.14
  `team_create/team_join`（受茬团/找茬团，需求文档 §七）：Team =
  [owner, kind, size, capacity]，创始人为成员（size=1）、capacity ≥ 1 否则
  ⊥ TypeError、未满员可加入否则 ⊥ TeamFull；三端执行层 + eval_expr 同步
  （sigma_core 143/143、Rust/Elixir §SK 自检 65/65、socketkit_ok 62/62 三端一致、
  0 warning）；consensus 43/43、p0 109/109，v0.10–v0.28 不回归。
- ✅ **REACHED v0.30 (2026-08-03)**: 增长期语义④团收益—— §SK.3.15 `team_share`
  （团内收益按贡献分配，需求文档 §七）：shareᵢ = floor(r·cᵢ/Σc)，Σ shares ≤ r
  不超发、份额非负、零贡献 ⊥ DivByZero；三端执行层 + eval_expr 同步
  （sigma_core 146/146、Rust/Elixir §SK 自检 68/68、socketkit_ok 65/65 三端一致、
  0 warning，语料补 encode_shares 满足 Law II）；consensus 43/43、p0 109/109，
  v0.10–v0.29 不回归。
- ✅ **REACHED v0.31 (2026-08-03)**: 增长期语义⑤额度预支—— §SK.3.16
  `quota_advance`（额度预支，需求文档 §四.1）：[m, r] → [m, r+m]（预支下月额度），
  quota_reset(quota_advance(q)) ≡ quota_reset(q)（月底清零后隔月可再预支）；
  三端执行层 + eval_expr 同步（sigma_core 149/149、Rust/Elixir §SK 自检 71/71、
  socketkit_ok 68/68 三端一致、0 warning）；consensus 43/43、p0 109/109，
  v0.10–v0.30 不回归。
- ✅ **REACHED v0.32 (2026-08-03)**: 增长期语义⑥积分可追溯—— §SK.3.17
  `points_ledger`（积分来源可追溯，需求文档 §四.2）：entries[] →
  [[entry_id, source_id, amount], …]，source_id ≥ 1 可追溯否则 ⊥ NotTraceable、
  amount ≥ 0（ℕ）；三端执行层 + eval_expr 同步（sigma_core 152/152、
  Rust/Elixir §SK 自检 74/74、socketkit_ok 71/71 三端一致、0 warning）；
  consensus 43/43、p0 109/109，v0.10–v0.31 不回归。
- ✅ **REACHED v0.33 (2026-08-03)**: 增长期语料模块化—— 7 个增长期操作
  （badge_issue/dispute_review/team_create/team_join/team_share/quota_advance/
  points_ledger）从 socketkit_ok.md 移入独立模块 `corpus/socketkit_growth_ok.md`
  （21/21 三端一致 PASS）+ `socketkit_growth_break.md`（E-02 三端一致 FAIL）；
  socketkit_ok.md 回归 MVP+五大制度（50/50 三端一致）；consensus 43/43 → 45/45
  全绿、p0 109/109、三端 0 warning，v0.10–v0.32 不回归。
- ✅ **REACHED v0.34 (2026-08-03)**: 增长期义务证明—— `sigma-prove` 新增
  gen_growth_obligation（§SK.3.12–3.17 七个增长期操作的定律义务：badge_issue
  等级有界 / dispute_review binary / team_create 创始人即成员 / team_join 加入 +1 /
  team_share 不超发 / quota_advance 预支加满月额 / points_ledger 积分非负），
  全部 `PROVED (unsat)`——§SK+§PF+增长期共 48 项义务全绿；consensus 45/45、
  p0 109/109、三端 0 warning，v0.10–v0.33 不回归。
- ✅ **REACHED v0.35 (2026-08-03)**: 增长期审计故事线—— `sigma-runtime --growth`
  （run_growth_story）一次跑通增长期业务故事线（核验师签发→督导裁决→团机制→
  额度预支→积分可追溯），逐事件复核定律（11/11 义务满足）；trace 59/59 与
  MVP story 18/18 不回归；consensus 45/45、p0 109/109、三端 0 warning，
  v0.10–v0.34 不回归。
- ✅ **REACHED v0.36 (2026-08-03)**: 三端增长期 story 对账—— §SK.3.12–3.17
  增长期故事线扩到三端：Rust `sk.rs growth_story()` + `--sk-growth`（11/11）、
  Elixir `sk_growth_story()` + `--sk-growth`（11/11），与 Python
  `sigma-runtime --growth`（11/11）**三端逐项一致**——增长期业务故事线三把尺子
  同尺；`cargo build` 0 error/0 warning；consensus 45/45、p0 109/109，
  v0.10–v0.35 不回归。
- ✅ **REACHED v0.37 (2026-08-03)**: Python app 增长期端点—— `sigma_app.py`
  增加增长期方法（全部委托 sigma_core §SK.3.12–3.17）+ HTTP 端点
  （/badge_issue /dispute /team_create /team_join /team_share /advance /ledger，
  新增 _get_str 解析列表参数）；`--smoke` 扩展增长期步骤（13/13 → 20/20）；
  自检 15/15 不回归；consensus 45/45、p0 109/109，v0.10–v0.36 不回归。
- ✅ **REACHED v0.38 (2026-08-03)**: Rust app 增长期端点 + 冒烟对账—— `app.rs`
  增加增长期 HTTP 路由（/badge_issue /dispute /team_create /team_join /team_share
  /advance /ledger，新增 get_str 解析列表参数，纯函数直接调 sk.rs §SK）；
  `--app-smoke` 扩展增长期步骤（13/13 → 20/20），与 Python `--smoke`（20/20）
  **双端逐项一致**；`cargo build` 0 error/0 warning；consensus 45/45、
  p0 109/109，v0.10–v0.37 不回归。
- ✅ **REACHED v0.39 (2026-08-03)**: 完整业务验收剧本—— `sigma-runtime --all`
  一次跑通找茬完整业务故事线（§SK.6 MVP：发单→接单→提交→验收→赏金→契分→贡献
  →勋章 + §SK.3.12–3.17 增长期：核验师签发→督导裁决→团机制→预支→可追溯），
  29/29 义务满足——App 完整业务蓝图的「验收剧本」；trace 59/59、MVP story
  18/18、growth story 11/11 不回归；consensus 45/45、p0 109/109，
  v0.10–v0.38 不回归。
- ✅ **REACHED v0.40 (2026-08-03)**: 第三个自举新域（供应链 inventory@1.0）——
  `spec/spec_p0_inventory.md`（§IN：inventory_new / receive_stock / ship_stock /
  stock_level / fill_rate，库存非负、不超卖 ⊥ InsufficientStock、履约率 0..1
  可证）——协议泛化性第三次验证（生物→业务→金融→供应链）；consensus 45/45、
  p0 109/109、三端 0 warning，v0.10–v0.39 不回归。
- ✅ **REACHED v0.41 (2026-08-03)**: 三端供应链执行层—— §IN 五操作在
  Python `sigma_core.py` / Rust `sk.rs`+`evaluator.rs` / Elixir `sigma_verify.exs`
  全部实现（参考实现 + eval_expr + 自检：sigma_core 167/167、Rust/Elixir §SK 自检
  74/74 + §IN 88/88）；fill_rate 返回 ℚ（fnum）三端一致；`cargo build` 0 error/0
  warning；consensus 45/45、p0 109/109，v0.10–v0.40 不回归。
- ✅ **REACHED v0.42 (2026-08-03)**: 供应链语料 + 共识—— `corpus/inventory_ok.md`
  （§IN 五操作真实调用，16/16 三端一致 PASS）+ `inventory_break.md`（E-02 三端
  一致 FAIL）；consensus 45/45 → 47/47 全绿、p0 109/109、三端 0 warning，
  v0.10–v0.41 不回归。
- ✅ **REACHED v0.43 (2026-08-03)**: 供应链证明 + runtime—— `sigma-prove` 新增
  gen_inventory_obligation（§IN 五操作定律义务：库存非负 / 入库可加 / 不超卖 /
  总量守恒 / 履约率有界），全部 `PROVED (unsat)`——§SK+§PF+增长期+§IN 共 53 项
  义务全绿；`sigma-runtime --inventory`（run_inventory_story）审计供应链故事线
  （开仓→入库→出库→水位→履约率），6/6 义务满足；consensus 47/47、p0 109/109，
  v0.10–v0.42 不回归。
- ✅ **REACHED v0.44 (2026-08-03)**: 三端供应链 story 对账—— §IN 供应链故事线
  扩到三端：Rust `sk.rs inventory_story()` + `--sk-inventory`（6/6）、Elixir
  `sk_inventory_story()` + `--sk-inventory`（6/6），与 Python `sigma-runtime
  --inventory`（6/6）**三端逐项一致**——供应链故事线三把尺子同尺；
  `cargo build` 0 error/0 warning；consensus 47/47、p0 109/109，
  v0.10–v0.43 不回归。
- ✅ **REACHED v0.45 (2026-08-03)**: 供应链 app 参考实现—— `sigma_app.py`
  增加供应链方法（open_inventory / receive / ship / level / fill，全部委托
  sigma_core §IN）+ HTTP 端点（/inventory_new /receive_stock /ship_stock
  /stock_level /fill_rate）；`--smoke` 扩展供应链步骤（20/20 → 25/25）；
  自检 15/15 不回归；consensus 47/47、p0 109/109，v0.10–v0.44 不回归。
- ✅ **REACHED v0.46 (2026-08-03)**: 三域协议巩固—— `sigma-runtime --domains`
  一次跑通三域故事线（§SK MVP 18 + §SK 增长期 11 + §IN 供应链 6 = 35/35 义务
  满足），找茬业务 + 供应链两条业务线同一条审计命令验收——协议承载两个独立
  业务域（App 行为 + 供应链）且三端一致；consensus 47/47、p0 109/109、
  sigma-prove 53 项 PROVED，v0.10–v0.45 不回归。
- ✅ **REACHED v0.47 (2026-08-03)**: README 新人上手 + 完整验证—— README 新增
  「新人 30 分钟上手」章节（三域概览：§SK 找茬业务 / §PF 金融 / §IN 供应链；
  快速开始命令；验证清单），新读者一条命令即可跑通共识门禁与三域审计；
  完整验证全绿（consensus 47/47、p0 109/109、sigma_core 167/167、三域 story
  35/35、冒烟 25/25、sigma-prove 全 PROVED）；v0.10–v0.46 不回归。
- ✅ **REACHED v0.48 (2026-08-03)**: 一键收官验收—— 新建 `tools/sigma-accept.py`
  （六道门禁一条命令跑通：三端共识 47/47、p0 109/109、Python 参考 167/167、
  三域审计 35/35、证明消解 PROVED、找茬冒烟 25/25），任何改动后一键全链路验收；
  v0.10–v0.47 不回归。
- ✅ **REACHED v0.49 (2026-08-03)**: 收官验收（续）—— `tools/sigma-accept.py`
  扩展到 9 道门禁（新增 Rust 编译 0 warning、Rust §SK 自检 88/88、Elixir §SK
  自检 88/88），三端编译与自检纳入一键验收；9/9 全部通过——ΣLang 全链路
  （共识→算法→三端→审计→证明→冒烟）一条命令可验收；v0.10–v0.48 不回归。
- ✅ **REACHED v0.50 (2026-08-03)**: 里程碑达成—— v0.27–v0.50 连续推进收官：
  找茬增长期语义（核验师/督导/团机制/预支/可追溯）全部纳入 §SK 并三端一致，
  供应链第三个自举新域走通全流程，三域协议巩固（--domains 35/35），
  sigma-accept.py 9 道门禁一键验收；consensus 47/47、p0 109/109、sigma-prove
  53 项 PROVED、三端 0 warning，v0.10–v0.49 不回归——ΣLang 从 v0.10 到 v0.50
  里程碑链完整。
- ✅ **REACHED v0.51 (2026-08-04)**: 找茬 App 状态持久化—— `sigma_app.py`
  MVPApp 增加 `to_state()/from_state()`（全状态 JSON 序列化，业务规则仍在
  sigma_core §SK），`--state FILE`：HTTP 服务启动加载、每次请求后自动保存
  （重启不丢）；`--persist-test`：半段 §SK.6 story → 序列化 → 重建 → 后半段
  在重建 App 上跑通（10/10，含 INV-1/3 不变量）——找茬从内存版走向可重启版；
  自检 15/15、冒烟 25/25 不回归；consensus 47/47、p0 109/109，v0.10–v0.50
  不回归。
- ✅ **REACHED v0.52 (2026-08-04)**: 找茬 App 用户会话层—— `sigma_app.py`
  MVPApp 增加 `users` 用户表 + `register()/me()`（用户态隔离：每个用户独立的
  配额/积分/贡献/任务上下文），HTTP 端点 `/register`（注册，幂等）与 `/me`
  （会话摘要：档案+配额+积分+发单列表）；users 纳入状态持久化；`--smoke` 增加
  用户会话步骤（25/25 → 29/29，新增 _get_str URL 解码支持中文名）；自检 15/15、
  persist-test 10/10 不回归；consensus 47/47、p0 109/109，v0.10–v0.51 不回归。
- ✅ **REACHED v0.53 (2026-08-04)**: 找茬 App 查询端点—— `sigma_app.py`
  MVPApp 增加 `tasks_list(status)`（任务列表，可按 §SK 状态 0..3 过滤）与
  `users_list()`（用户会话摘要列表），HTTP 端点 `/tasks`（可带 ?status=）与
  `/users`；`--smoke` 增加查询步骤（29/29 → 33/33：任务列表/计数/状态过滤/
  用户列表）；自检 15/15、persist-test 10/10 不回归；consensus 47/47、
  p0 109/109，v0.10–v0.52 不回归。
- ✅ **REACHED v0.54 (2026-08-04)**: 找茬 App HTTP 错误码语义化—— `sigma_app.py`
  新增 `ERROR_STATUS` 映射表（§SK/§IN 语义错误码 → 语义化 HTTP 状态码：
  AuthError→403、TypeError/ShapeError→422、业务冲突类→409 等），do_GET 异常
  响应按映射返回语义化 4xx（不再是笼统 400）；`--smoke` 增加错误语义化步骤
  （33/33 → 36/36：InsufficientStock→409 / AuthError→403 / DivByZero→409）；
  自检 15/15、persist-test 10/10 不回归；consensus 47/47、p0 109/109，
  v0.10–v0.53 不回归。
- ✅ **REACHED v0.55 (2026-08-04)**: 找茬 App 审计日志—— `sigma_app.py`
  MVPApp 增加 ΣLang 审计追踪（`_audit`/`audit_trail`：每个业务动作记录
  op/input/output，事件形状与 sigma-runtime 一致——同一批 op 可被运行时审计），
  核心方法（quota_new/task_create/accept_task/task_submit/task_accept/
  points_withdraw）全部记录；audit 纳入状态持久化；`--audit-log FILE`：HTTP
  服务每次请求后导出审计追踪；`--audit-test`：跑完整 story 验证审计日志
  （op 齐全/顺序正确/JSON 可序列化/语义正确，5/5）；自检 15/15、persist-test
  10/10、冒烟 36/36 不回归；consensus 47/47、p0 109/109，v0.10–v0.54 不回归。
- ✅ **REACHED v0.56 (2026-08-04)**: 一键验收接 CI—— 新建 `Makefile`
  （`make accept` = 九道门禁一键验收，另有 check/story/prove/rust/elixir/app
  分目标）与 `.github/workflows/ci.yml`（GitHub Actions：push/PR 时 setup
  Python+Rust+Elixir+z3 后跑 `python3 tools/sigma-accept.py`）——协议工程化：
  σLang 九道门禁进入标准 CI，任何提交全绿才算过；本地与 CI 同一条命令
  （sigma-accept.py 9/9 验证通过）；v0.10–v0.55 不回归。
- ✅ **REACHED v0.57 (2026-08-04)**: 语料扩容—— `corpus/socketkit_ok.md` 按主题
  拆分为三个独立模块（任务流 socketkit_taskflow_ok 25/25、额度制
  socketkit_quota_ok 9/9、积分/勋章制 socketkit_points_ok 16/16，操作分布不重叠
  fingerprint 无冲突），新增两个 E-02 负例（taskflow_break/quota_break）；
  consensus 47/47 → **51/51 全绿**（> 50 扩容达标）、p0 109/109、三端 0 warning，
  v0.10–v0.56 不回归。
- ✅ **REACHED v0.58 (2026-08-04)**: spec 中英对照补全—— 新建
  `spec/zh/spec_p0_inventory_zh.md`（§IN 供应链中文参考版，193 行，IN.1 动机 /
  IN.2 类型 / IN.3.1–3.5 五操作 / IN.4 编码 / IN.5 推广路径全量对照；英文原版
  为准、中文为参考，符合 spec/zh 约定）——第三个新域首次获得中文参考；
  业务域 spec 中英对照从 4 个基础文件扩展到 5 个；consensus 51/51、p0 109/109，
  v0.10–v0.57 不回归。
- ✅ **REACHED v0.59 (2026-08-04)**: README 架构数据流全景—— README 新增
  「Architecture / 架构与数据流」章节：数据流全景图（spec → corpus 51 模块 →
  三端验证器 → Law XIII 共识门禁 → 证明/审计/找茬后端 → 一键验收 → CI）、
  工具链职责表、以 §SK task_create 为例的「一条语义的旅程」七步说明——
  新读者一张图看懂 σLang 从规范到共识的完整链路；consensus 51/51、p0 109/109，
  v0.10–v0.58 不回归。
- ✅ **REACHED v0.60 (2026-08-04)**: 协议版本化—— spec 版本 **0.3.0 → 0.4.0**
  （README Spec Version + Citation 同步升级；v0.51–v0.60 累计新增三端共识
  51 模块、找茬 App 产品层五件套（持久化/会话/查询/错误语义化/审计）、CI 一键
  验收、语料扩容、双语文档与架构全景，满足 0.4.0 语义面扩展）；RFC 记录：
  「找茬产品落地（v0.51–v0.55）+ 协议工程化（v0.56–v0.60）」两阶段已闭环；
  consensus 51/51、p0 109/109，v0.10–v0.59 不回归。
- ✅ **REACHED v0.61 (2026-08-04)**: 供应链跨操作不变量—— `sigma-prove` 新增
  `gen_inventory_invariants`（对含 §IN 操作的模块附加两条跨操作不变量义务：
  INV-IN-1 总量守恒——入库后总量 = 初始 + 净入库，库存不凭空产生；INV-IN-2
  库存非负链——出库后每货品 ≥ 0），均 `PROVED (unsat)`——供应链语义从单操作
  定律走向跨操作不变量证明；consensus 51/51、p0 109/109、三端 0 warning，
  v0.10–v0.60 不回归。
- ✅ **REACHED v0.62 (2026-08-04)**: 金融跨操作不变量—— `sigma-prove` 新增
  `gen_portfolio_invariants`（对含 §PF 操作的模块附加两条跨操作不变量义务：
  INV-PF-1 现金守恒——buy 后 cash = 初始 − 花费 ≥ 0，现金不凭空产生；INV-PF-2
  份额守恒——sell 后 shares = 初始 − 卖出 ≥ 0，不凭空卖份额），均
  `PROVED (unsat)`——金融语义从单操作定律走向跨操作不变量证明；consensus 51/51、
  p0 109/109、三端 0 warning，v0.10–v0.61 不回归。
- ✅ **REACHED v0.63 (2026-08-04)**: 找茬跨操作不变量—— `sigma-prove` 新增
  `gen_socketkit_invariants`（对含 §SK points 操作的模块附加两条跨操作不变量
  义务：INV-SK-1 赏金守恒——hold→release 后 escrow+available 恒等，赏金不
  凭空增减；INV-SK-2 不超提——withdraw 后 available ≥ 0），均 `PROVED (unsat)`；
  同时修复 has_sk 检查（五大制度操作 SK_SYS_OPS 纳入，socketkit_quota/points
  模块不再被 skip，points 单操作义务也全部 PROVED）——找茬赏金链语义从单操作
  定律走向跨操作不变量证明；consensus 51/51、p0 109/109、三端 0 warning，
  v0.10–v0.62 不回归。
- ✅ **REACHED v0.64 (2026-08-04)**: 三域 story 不变量检查段—— `sigma-runtime`
  新增 `run_invariant_checks`（与 sigma-prove 的 INV-SK/INV-PF/INV-IN 义务对应，
  运行时复核同一批守恒定律：§SK 赏金守恒链 / §PF 现金与份额守恒 / §IN 总量
  守恒与库存非负链），`--domains` 追加不变量检查段（35/35 → **41/41**）——
  三域 story 在业务事件之外同步审计跨操作不变量；trace 59/59、--growth 11/11
  不回归；consensus 51/51、p0 109/109，v0.10–v0.63 不回归。
- ✅ **REACHED v0.65 (2026-08-04)**: sigma-prove 全量义务重验 + 报告——
  `sigma-prove` 增加全量义务汇总报告（`Obligations discharged: N PROVED across
  M modules`），默认全量重验只处理 Expected: PASS 模块（break 负例属共识检查
  E-02，不是证明对象）；全量重验 **62 项 PROVED / 29 个语料模块全绿**
  （§SK 任务流/额度/积分/增长期 + §PF + §IN，含跨操作不变量 INV-SK/PF/IN）；
  Makefile `make prove` 与 sigma-accept.py 门禁 8 同步改为全量语料重验；
  consensus 51/51、p0 109/109，v0.10–v0.64 不回归。
- ⏳ **待办队列（avatar_loop 目标来源，一天一个）**:
  1. ⏸️ P3 — Lang-Zone backend integration（§6.1，**DEFERRED**：LZ 尚在原型期，待自举稳定后再融入）。
  2. （无）— v0.65 达成，继续 v0.66–v0.70 开工验收连续推进。

---

## Phase 1 — Verifier as the Single Source of Truth (Week 1)

The verifier is the **only authority** on what ΣLang means. No human text overrides it.

### 1.1 Extend verify_p0.py to validate ALL Iron Laws

> ✅ **DONE 2026-08-02**: Iron Laws automated checks live in `impl/verifier/src/main.rs`
> (`check_*`, 20 项覆盖：fingerprint / n_encoding / law_declaration / tests_mandatory /
> negative_tests / export_completeness / test_portability / proof_structure /
> internal_consistency / guarantee / eval_determinism / signature / backward_compat /
> calibration / shadowing / no_implementation / dependencies / timing_contract /
> effect_transparency / capabilities)，三端（Python/Rust/Elixir）一致。

Current: 109 tests covering Time/Error/Confidence/I/O/SocketKit.  
✅ **DONE 2026-08-02**: `verify_p0.py --json` 输出结构化 JSON（§1.2：spec/pass/modules/total/
fingerprint），`sigma-cli verify --p0` 打通 CLI（P0 队列）。

```
verify_p0.py → validate_spec("your_spec.md")
               ├── §T Time          17/17
               ├── §E Error         16/16
               ├── §C Confidence    37/37
               ├── §I I/O           25/25
               ├── §SK SocketKit    14/14
               └── §L Iron Laws     ✅ done (check_* in impl/verifier)
```

### 1.2 Verifier output format

```json
{
  "spec": "math.calculus@1.0",
  "pass": true,
  "modules": {
    "time": {"pass": 17, "fail": 0},
    "error": {"pass": 16, "fail": 0},
    "confidence": {"pass": 37, "fail": 0},
    "io": {"pass": 25, "fail": 0},
    "iron_laws": {"pass": 0, "fail": 12}
  },
  "fingerprint": "sha256:abc123..."
}
```

This JSON is the **protocol handshake** between AI and spec.

---

## Phase 2 — AI Implementation Guide (Week 1)

### 2.1 For every spec module, add an IMPLEMENTATION section

> ✅ **DONE 2026-08-02**: `## Implementation Checklist (for AI)` added to all 4 spec
> modules (`spec_p0_time.md` §T / `spec_p0_error.md` §E / `spec_p0_confidence.md` §C /
> `spec_p0_io.md` §I) — each lists the exact API to implement and what NOT to implement.

```markdown
## §T: Time & Causal Order

### Implementation Checklist (for AI)

To pass this module, implement exactly these:

1. `tick() -> Time`                           [T-01]
2. `happens_before(a: Time, b: Time) -> bool` [T-02]
3. ...

### What NOT to implement
- Do NOT assume monotonic clock
- Do NOT implement wall-clock synchronization
```

### 2.2 Minimal Reference Implementation

> ✅ **DONE 2026-08-02**: `impl/python/sigma_core.py` (~540 lines incl. self-check,
> stdlib only) implements ALL P0 modules; `python3 impl/python/sigma_core.py` → 59/59.

Place a single-file reference impl in `impl/python/`:

```python
# impl/python/sigma_core.py  (~200 lines)
# Implements ALL P0 modules
# Used by verify_p0.py to prove the spec is implementable
```

No dependencies except stdlib. This is NOT the "official" implementation — it's proof that the protocol is real.

---

## Phase 3 — Package Manager (Week 2)

> ✅ **REACHED 2026-08-02 (v0.11)**: `tools/sigma-cli.py` — `install / verify / list / search /
> fingerprint` 五个命令，`~/.sigma/registry.json` 注册表，Iron Law VII 无环依赖。
> ✅ **REACHED 2026-08-02**: `verify_p0.py --json` 输出结构化 JSON（§1.2）与 CLI 的
> `verify --p0` 子命令打通（P0 队列）。

### 3.1 CLI Design

```bash
sigma install <spec.md>          # Install a ΣLang package
sigma verify <package_name>       # Run its verifier
sigma list                        # List installed packages
sigma search <keyword>            # Search installed specs
sigma fingerprint <package>       # Show hash
```

### 3.2 Package Registry Format

```json
// ~/.sigma/registry.json
{
  "packages": {
    "math.calculus": {
      "version": "1.0.0",
      "path": "/home/user/.sigma/math.calculus/",
      "fingerprint": "sha256:...",
      "modules": ["time", "error", "confidence"],
      "deps": []
    }
  }
}
```

### 3.3 Dependency Resolution (Iron Law VII)

```python
def check_circular(pkg, visited=None):
    """No circular deps allowed. Returns True if clean."""
    visited = visited or set()
    if pkg.fingerprint in visited: return False  # circular!
    visited.add(pkg.fingerprint)
    return all(check_circular(d, visited) for d in pkg.deps)
```

---

## Phase 4 — Standard Library (Week 3)

> ✅ **REACHED 2026-08-02 (v0.11)**: 3 个标准包已落地 —— `std/math.base.md` /
> `std/data.transform.md` / `std/ai.confidence.md`，各配验证器测试集
> `corpus/std_*_ok.md`，三端共识覆盖（consensus 38/38）。

Ship with exactly 3 reference packages that prove the system works:

### 4.1 `math.base@1.0`

```
⊕ ⊖ ⊗ ⊘ — arithmetic with associativity/commutativity laws
√ pow log — transcendental with precision bounds
```

### 4.2 `data.transform@1.0`

```
map ∥ filter ∥ reduce — with lazy/eager semantics
sort group — with ordering laws
```

### 4.3 `ai.confidence@1.0`

```
calibrate(confidence, actual) -> calibrated_confidence
combine(opinions: List[Message]) -> consensus
```

Each package = 1 `.md` spec + 1 verifier test set.

---

## Phase 5 — AI Self-Bootstrapping (Week 4)

The ultimate test: **give ΣLang to a fresh AI session and see if it can implement a new spec without human help.**

### 5.1 Bootstrapping Protocol

```
1. Human: "Here is ΣLang spec and verifier"
2. AI reads spec/spec_p0_foundations.md
3. AI runs verify_p0.py → 0/95 passed (no implementation yet)
4. AI reads Implementation Guide for each module
5. AI writes impl/python/sigma_core.py
6. AI runs verify_p0.py → 95/95 passed
7. AI now "understands" ΣLang
```

### 5.2 Novel Spec Test

> ✅ **DONE 2026-08-02（v0.12）** — 验收标准已全部满足：
> 1. 新建 `corpus/novel_gene_ok.md`（DNA 对齐语义，ΣLang 格式）；
> 2. 三端验证器（Python/Rust/Elixir）判定一致，`verify_consensus.py` 计入 39/39；
> 3. 跑通完整流程：AI 读 spec → 写实现 → `verify_p0.py` 全绿 → 发布。

```
8. Human gives AI a new domain: "biomedical.gene@1.0 — DNA alignment semantics"
9. AI writes the spec in ΣLang format
10. AI writes the verifier tests
11. Human reviews, publishes
```

---

## Phase 6 — Backend Integration (Week 5+)

### 6.1 Lang-Zone as ΣLang Compiler（⏸️ DEFERRED）

> ⏸️ **搁置（P3）**：Lang-Zone（`E:/IDEProjects/AI/lang-zone`）是 LZ 语言编译器
> （`lzc`→Rust / `lzcyc`→Cython），CLI 无 `--target sigma` 参数，且 README 明示仍处
> IR 路线迁移中（原型期）。**待 LZ 自举且稳定后再考虑融入**，届时验收标准：
> 1. 用 `lzc`/`lzcyc` 将 ΣLang 语义实现（.lz）编译为原生产物（Cython `.pyd` 或 Rust `.so`）；
> 2. 产物可被 Python/Rust 加载并跑通验证器；
> 3. 三端共识不回退（consensus 保持 N/N）。

```
ΣLang spec → Lang-Zone → Cython → .pyd
                          OR
                          → Rust → .so
```

The spec defines WHAT; LZ compiles it to HOW.

### 6.2 SocketKit Protocol

> ✅ **DONE 2026-08-02（v0.13）** — 验收标准已全部满足：
> 1. 在 spec 中定义 `task_create / review_merge / contribution_score` 的 ΣLang 语义；
> 2. 每个行为配 1 个语料模块 + 验证器测试，三端判定一致；
> 3. 走通 RFC → spec 章节 → 验证器检查 → 测试 的晋升路径（参考 Phase 7）。

```
来找茬 App behavior defined in ΣLang:
  - Task submission: task_create(author, bounty) 
  - Review resolution: review_merge(opinions[]) → decision
  - Contribution calculation: contribution_score(actions[]) → points
```

This makes your App's business logic **mathematically auditable**.

---

## Phase 7 — Top-Level Rule Candidates (decided 2026-08-01)

> **Moved to `spec/spec_top_extensions.md`** — full candidate drafts (E-01 … E-09).
> Foundational top-level rules now live in **`spec/spec_top_rules.md`** (§S Shadowing Discipline).
> Candidates become normative via: RFC → spec section → Verifier check → tests.

---

## Priority Order

| Priority | Milestone | Deliverable |
|:---:|------|------|
| P0 | Verifier format (json output) | ✅ **REACHED 2026-08-02**: `verify_p0.py --json` (spec/pass/modules/total/fingerprint) + `sigma-cli verify --p0` |
| P0 | Iron Laws automated check | ✅ `check_*` in `impl/verifier` (I–IV, XIII–XVII, E-03/E-06/E-10); 3 verifiers |
| P0 | **Law XIII — Verifier Consensus** | ✅ **PROMOTED 2026-08-01**: `verify_consensus.py` + `corpus/` (38 modules × 3 verifiers Python/Rust/Elixir, 38/38 agree) |
| P0 | **Law XIV — Negative Test Mandatory** | ✅ **PROMOTED 2026-08-01**: `NoNegativeTest` in all 3 verifiers |
| P0 | **Law XV — Export Completeness** | ✅ **PROMOTED 2026-08-01**: ghost/hidden checks in all 3 verifiers |
| P0 | **Law XVI — Compatibility Proof** | ✅ **PROMOTED 2026-08-01**: `## Compat Tests` in all 3 verifiers |
| P0 | **v0.10 可用 (REACHED 2026-08-02)** | 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）、基本操作（`index()`/`I₂`、矩阵运算）、常量包（§C `0xK0xx`/`0xQ0xx`，Opaque 不可遮蔽）三端求值器全部实现；`sigma-prove` PROVED (unsat)、`sigma-moonbit` 生成 `.mbtp`；consensus 35/35、p0 95/95、0 warning |
| P0 | **v0.11 可用 (REACHED 2026-08-02)** | 包管理器 `tools/sigma-cli.py`（install/verify/list/search/fingerprint + `~/.sigma/registry.json` + Iron Law VII 无环依赖）；标准库 3 包 `std/math.base.md` / `std/data.transform.md` / `std/ai.confidence.md`（各 1 规范 + 1 验证器测试集 `corpus/std_*_ok.md`，三端共识覆盖）；v0.10 不回归；consensus 38/38、p0 95/95、0 warning |
| P0 | **AI Implementation Guide (REACHED 2026-08-02)** | ✅ `## Implementation Checklist (for AI)` in all 4 spec modules (§T/§E/§C/§I) |
| P0 | **Minimal reference impl (REACHED 2026-08-02)** | ✅ `impl/python/sigma_core.py` — stdlib-only core, self-check 59/59 |
| P1 | Package manager CLI | ✅ v0.11: `tools/sigma-cli.py` (REACHED 2026-08-02) |
| P1 | 3 standard packages | ✅ v0.11: `std/math.base.md` + tests (REACHED 2026-08-02) |
| P2 | AI bootstrapping test | ✅ **REACHED 2026-08-02**: `tools/sigma-bootstrap.py` — one clean run closes the loop spec→impl→verify→pass (4 specs carry `## Implementation Checklist (for AI)`, `sigma_core.py` 59/59, `verify_p0.py` 95/95) |
| P2 | **v0.12 Novel Spec Test (REACHED 2026-08-02)** | ✅ `corpus/novel_gene_ok.md`（DNA 对齐语义, §5.2）— consensus 39/39 三端一致 + AI 闭环 |
| P3 | **v0.13 SocketKit integration (REACHED 2026-08-02)** | ✅ `spec/spec_p0_socketkit.md` + `corpus/socketkit_ok.md`（§6.2）— consensus 40/40 三端一致 |
| P3 | **v0.14 SocketKit Runtime (REACHED 2026-08-03)** | ✅ §SK 参考实现（`sigma_core.py` 75/75）+ 审计运行时（`tools/sigma-runtime.py`，obligation 日志 10/10）+ `sigma-prove` §SK 六定律 PROVED (unsat) + 负例 `corpus/socketkit_break.md`（consensus 41/41）+ §SK 进 `verify_p0.py`（109/109） |
| P3 | **v0.15 三端 §SK 执行层 (REACHED 2026-08-03)** | ✅ §SK 参考实现同步到 Rust（`src/sk.rs` + `--sk-self-check` 16/16）与 Elixir（`sigma_verify.exs` §SK + `--sk-self-check` 16/16），三端行为一致、0 warning；consensus 41/41、p0 109/109 不回退 |
| P3 | **v0.16 SocketKit 语料执行化 (REACHED 2026-08-03)** | ✅ 三端求值器 eval_expr 支持 §SK 三操作真实调用；`corpus/socketkit_ok.md` Tests 升级为真实调用（含 ⊥ 错误路径），9/9 三端一致——Law XIII 直接验证业务语义；consensus 41/41、p0 109/109、0 warning |
| P3 | **v0.17 §SK 对齐真实业务 (REACHED 2026-08-03)** | ✅ Task 4 元组 + 4 态状态机；新增 accept_task/task_submit/task_accept/credit_score；review_merge 修正为增长期定位；三端执行层同步（sigma_core 91/91、三端 §SK 32/32、socketkit_ok 24/24）；sigma-prove 18 项义务 PROVED；sigma-runtime 23/23；consensus 41/41、p0 109/109、0 warning |
| P3 | **v0.18 状态机不变量证明 (REACHED 2026-08-03)** | ✅ task_accept 作者授权（⊥ AuthError）+ §SK.3.8 不变量（INV-1 状态单调/INV-2 终态不可变/INV-3 守恒/INV-4 授权）；三端执行层同步（sigma_core 92/92、三端 §SK 33/33、socketkit_ok 25/25）；sigma-prove 23 项义务全 PROVED；sigma-runtime 31/31；consensus 41/41、p0 109/109、0 warning |
| P2 | **v0.19 第二个自举新域（金融 portfolio）(REACHED 2026-08-03)** | ✅ `spec/spec_p0_portfolio.md`（§PF 5 操作）+ `corpus/portfolio_ok.md`（19/19 三端一致）+ `portfolio_break.md`（E-02 FAIL）；三端 eval_expr 支持新域真实调用（sigma_core 111/111、0 warning）；sigma-prove 10 项 §PF 义务全 PROVED（共 33 项）；sigma-runtime 45/45；consensus 43/43、p0 109/109 |
| P3 | **v0.20 找茬五大制度补齐 (REACHED 2026-08-03)** | ✅ SK.3.9 额度制（quota_new/use/reset）+ SK.3.10 积分制（points_hold/release/withdraw）+ SK.3.11 勋章制（badge_level）；三端执行层同步（sigma_core 130/130、三端 §SK 52/52、socketkit_ok 50/50）；sigma-prove 8 项三制度义务全 PROVED（共 41 项）；sigma-runtime 59/59；consensus 43/43、p0 109/109、0 warning |
| P3 | **v0.21 找茬 MVP 全链路审计剧本 (REACHED 2026-08-03)** | ✅ spec §SK.6 MVP 业务剧本（12 步端到端场景）+ `sigma-runtime --story`（run_mvp_story 一次跑通完整业务故事线，18/18 义务满足）——App 开工「验收剧本」；consensus 43/43、p0 109/109、三端 0 warning、v0.10–v0.20 不回归 |
| P3 | **v0.22 找茬 MVP 参考实现 (REACHED 2026-08-03)** | ✅ `impl/python/sigma_app.py`（MVPApp 业务方法全部委托 sigma_core §SK + stdlib HTTP `--serve` API）；自检跑通 §SK.6 剧本 15/15，与 `sigma-runtime --story` 步骤一一对应；consensus 43/43、p0 109/109、三端 0 warning、v0.10–v0.21 不回归 |
| P3 | **v0.23 MVP 端到端 HTTP 冒烟测试 (REACHED 2026-08-03)** | ✅ `sigma_app.py` 增 `/quota` 端点 + `--smoke`（HTTP 七步全链路 /quota→/post→/claim→/submit→/accept→/withdraw→/badge，13/13 通过）——参考实现 HTTP 服务可用性被可重复冒烟固化；consensus 43/43、p0 109/109、三端 0 warning、v0.10–v0.22 不回归 |
| P3 | **v0.24 三端 §SK.6 story 一致性 (REACHED 2026-08-03)** | ✅ §SK.6 剧本扩到三端：Rust `sk.rs story()` + `--sk-story`（15/15）、Elixir `sk_story()` + `--sk-story`（15/15），与 Python `sigma_app.py` 15/15 逐项一致——三把尺子审计同一故事线；consensus 43/43、p0 109/109、三端 0 warning、v0.10–v0.23 不回归 |
| P3 | **v0.25 Rust 参考实现 (REACHED 2026-08-03)** | ✅ `impl/verifier/src/app.rs`（MVPApp Rust 版，业务全部委托 sk.rs §SK）+ `--app-self-check`（15/15）；与 Python `sigma_app.py` / Rust `--sk-story` / Elixir `--sk-story` 四端逐项一致；`cargo build` 0 error/0 warning；consensus 43/43、p0 109/109、v0.10–v0.24 不回归 |
| P3 | **v0.26 Rust HTTP 服务 + 冒烟对账 (REACHED 2026-08-03)** | ✅ `app.rs` stdlib HTTP JSON API（`--app-serve`，端点与 Python `--serve` 一致）+ `--app-smoke`（HTTP 七步全链路 13/13）与 Python `sigma_app.py --smoke` 13/13 双端逐项一致——HTTP 层同尺；`cargo build` 0 error/0 warning；consensus 43/43、p0 109/109、v0.10–v0.25 不回归 |
| P3 | Lang-Zone backend integration | ⏸️ **DEFERRED**：LZ 原型期，待自举稳定后融入（§6.1） |

---

## What you (Victor) should NOT do

- ❌ Don't implement every ΣLang package personally
- ❌ Don't optimize performance yet
- ❌ Don't build a GUI

You design the **protocol grammar** (the Iron Laws + verifier). AI fills in the implementations.
