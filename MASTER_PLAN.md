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
- ✅ **REACHED**: AI Implementation Guide（4 个 spec 模块） + 参考实现 `impl/python/sigma_core.py`（60/60）
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
  eval_expr 同步（sigma_core 130/130、三端 §SK 自检 56/56、socketkit_ok 50/50 三端一致、
  0 warning）；`sigma-prove` 新增 8 项三制度义务全部 `PROVED (unsat)`（共 41 项）；
  `sigma-runtime` 审计 trace 增加三制度段（60/60）；consensus 43/43、p0 109/109、
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
  （sigma_core 134/134、Rust/Elixir §SK 自检 56/56、socketkit_ok 56/56 三端一致、
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
  额度预支→积分可追溯），逐事件复核定律（11/11 义务满足）；trace 60/60 与
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
  29/29 义务满足——App 完整业务蓝图的「验收剧本」；trace 60/60、MVP story
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
  consensus 47/47 → **56/56 全绿**（> 50 扩容达标）、p0 109/109、三端 0 warning，
  v0.10–v0.56 不回归。
- ✅ **REACHED v0.58 (2026-08-04)**: spec 中英对照补全—— 新建
  `spec/zh/spec_p0_inventory_zh.md`（§IN 供应链中文参考版，193 行，IN.1 动机 /
  IN.2 类型 / IN.3.1–3.5 五操作 / IN.4 编码 / IN.5 推广路径全量对照；英文原版
  为准、中文为参考，符合 spec/zh 约定）——第三个新域首次获得中文参考；
  业务域 spec 中英对照从 4 个基础文件扩展到 5 个；consensus 56/56、p0 109/109，
  v0.10–v0.57 不回归。
- ✅ **REACHED v0.59 (2026-08-04)**: README 架构数据流全景—— README 新增
  「Architecture / 架构与数据流」章节：数据流全景图（spec → corpus 51 模块 →
  三端验证器 → Law XIII 共识门禁 → 证明/审计/找茬后端 → 一键验收 → CI）、
  工具链职责表、以 §SK task_create 为例的「一条语义的旅程」七步说明——
  新读者一张图看懂 σLang 从规范到共识的完整链路；consensus 56/56、p0 109/109，
  v0.10–v0.58 不回归。
- ✅ **REACHED v0.60 (2026-08-04)**: 协议版本化—— spec 版本 **0.3.0 → 0.4.0**
  （README Spec Version + Citation 同步升级；v0.51–v0.60 累计新增三端共识
  51 模块、找茬 App 产品层五件套（持久化/会话/查询/错误语义化/审计）、CI 一键
  验收、语料扩容、双语文档与架构全景，满足 0.4.0 语义面扩展）；RFC 记录：
  「找茬产品落地（v0.51–v0.55）+ 协议工程化（v0.56–v0.60）」两阶段已闭环；
  consensus 56/56、p0 109/109，v0.10–v0.59 不回归。
- ✅ **REACHED v0.61 (2026-08-04)**: 供应链跨操作不变量—— `sigma-prove` 新增
  `gen_inventory_invariants`（对含 §IN 操作的模块附加两条跨操作不变量义务：
  INV-IN-1 总量守恒——入库后总量 = 初始 + 净入库，库存不凭空产生；INV-IN-2
  库存非负链——出库后每货品 ≥ 0），均 `PROVED (unsat)`——供应链语义从单操作
  定律走向跨操作不变量证明；consensus 56/56、p0 109/109、三端 0 warning，
  v0.10–v0.60 不回归。
- ✅ **REACHED v0.62 (2026-08-04)**: 金融跨操作不变量—— `sigma-prove` 新增
  `gen_portfolio_invariants`（对含 §PF 操作的模块附加两条跨操作不变量义务：
  INV-PF-1 现金守恒——buy 后 cash = 初始 − 花费 ≥ 0，现金不凭空产生；INV-PF-2
  份额守恒——sell 后 shares = 初始 − 卖出 ≥ 0，不凭空卖份额），均
  `PROVED (unsat)`——金融语义从单操作定律走向跨操作不变量证明；consensus 56/56、
  p0 109/109、三端 0 warning，v0.10–v0.61 不回归。
- ✅ **REACHED v0.63 (2026-08-04)**: 找茬跨操作不变量—— `sigma-prove` 新增
  `gen_socketkit_invariants`（对含 §SK points 操作的模块附加两条跨操作不变量
  义务：INV-SK-1 赏金守恒——hold→release 后 escrow+available 恒等，赏金不
  凭空增减；INV-SK-2 不超提——withdraw 后 available ≥ 0），均 `PROVED (unsat)`；
  同时修复 has_sk 检查（五大制度操作 SK_SYS_OPS 纳入，socketkit_quota/points
  模块不再被 skip，points 单操作义务也全部 PROVED）——找茬赏金链语义从单操作
  定律走向跨操作不变量证明；consensus 56/56、p0 109/109、三端 0 warning，
  v0.10–v0.62 不回归。
- ✅ **REACHED v0.64 (2026-08-04)**: 三域 story 不变量检查段—— `sigma-runtime`
  新增 `run_invariant_checks`（与 sigma-prove 的 INV-SK/INV-PF/INV-IN 义务对应，
  运行时复核同一批守恒定律：§SK 赏金守恒链 / §PF 现金与份额守恒 / §IN 总量
  守恒与库存非负链），`--domains` 追加不变量检查段（35/35 → **41/41**）——
  三域 story 在业务事件之外同步审计跨操作不变量；trace 60/60、--growth 11/11
  不回归；consensus 56/56、p0 109/109，v0.10–v0.63 不回归。
- ✅ **REACHED v0.65 (2026-08-04)**: sigma-prove 全量义务重验 + 报告——
  `sigma-prove` 增加全量义务汇总报告（`Obligations discharged: N PROVED across
  M modules`），默认全量重验只处理 Expected: PASS 模块（break 负例属共识检查
  E-02，不是证明对象）；全量重验 **62 项 PROVED / 29 个语料模块全绿**
  （§SK 任务流/额度/积分/增长期 + §PF + §IN，含跨操作不变量 INV-SK/PF/IN）；
  Makefile `make prove` 与 sigma-accept.py 门禁 8 同步改为全量语料重验；
  consensus 56/56、p0 109/109，v0.10–v0.64 不回归。
- ✅ **REACHED v0.66 (2026-08-04)**: 找茬完整业务流 CLI 剧本—— `sigma_app.py`
  新增 `--scenario`（run_scenario）：一条命令走完找茬全业务流剧本（注册 →
  开户 → 发单 → 接单 → 提交 → 验收 → 提现 → 勋章 → 查询 → 增长期 → 审计/
  不变量/可持久化，16/16）——与 --smoke 的 HTTP 全链路对应，CLI 直调 App
  方法剧本；自检 15/15、冒烟 36/36、persist-test 10/10 不回归；consensus
  56/56、p0 109/109，v0.10–v0.65 不回归。
- ✅ **REACHED v0.67 (2026-08-04)**: 找茬业务流双端对账—— Rust `app.rs`
  MVPApp 补齐双端对账方法（users/register/me/tasks_list/users_list/
  issue_badge/dispute，与 Python sigma_app.py 对应），新增 `app_scenario()` +
  `--app-scenario`（完整业务流剧本 16 项）；与 Python `--scenario`（16/16）
  **双端逐项一致**（注册/开户/发单/接单/提交/验收/守恒/提现/结清/勋章/查询/
  签发/裁决/审计机制）——找茬完整业务流 Python/Rust 两个参考后端同一条剧本
  对账；`cargo build` 0 error/0 warning；consensus 56/56、p0 109/109，
  v0.10–v0.66 不回归。
- ✅ **REACHED v0.68 (2026-08-04)**: 找茬 App 部署文档—— 新建
  `docs/deploy_zhaocha.md`（找茬 MVP 参考后端部署与运维说明）：Python/Rust
  双形态对比与 HTTP 端点清单、启动参数（--serve/--port/--state/--audit-log）、
  部署前必跑的验收检查（sigma-accept 九道门禁 + --scenario/--smoke/
  --persist-test/--audit-test/--app-scenario）、运维要点（状态文件权限/审计日志
  归档/无外部依赖/扩展方向）——找茬从"可运行"走向"可部署"；consensus 56/56、
  p0 109/109，v0.10–v0.67 不回归。
- ✅ **REACHED v0.69 (2026-08-04)**: README 产品落地指南—— README 新增
  「Product Guide / 用 ΣLang 做找茬」章节：找茬功能 ↔ §SK 语义对照表
  （发单=task_create+points_hold / 接单=accept_task / 验收=task_accept /
  提现=points_withdraw / 勋章=badge_level / 核验师=badge_issue / 督导=
  dispute_review / 团=team_* / 预支=quota_advance / 可追溯=points_ledger 等
  十二项）、落地三步走（起后端 → 过验收 → 扩展业务先写进 spec）、指向部署
  文档——从"协议"到"产品"的路径一张表看懂；consensus 56/56、p0 109/109，
  v0.10–v0.68 不回归。
- ✅ **REACHED v0.70 (2026-08-04)**: 里程碑达成—— v0.51–v0.70 连续推进收官：
  找茬产品落地（状态持久化/用户会话/查询端点/错误语义化/审计日志 + CLI 剧本
  + 双端对账 + 部署文档 + 落地指南）+ 协议工程化（CI 一键验收/语料扩容 51 模块/
  中英对照/架构全景/版本化 0.4.0）+ 深度不变量（INV-SK/PF/IN 跨操作守恒全
  PROVED、--domains 41/41、全量重验 62 项）；sigma-accept.py 九道门禁全绿；
  consensus 56/56、p0 109/109、三端 0 warning，v0.10–v0.69 不回归——ΣLang
  从 v0.10 到 v0.70 里程碑链完整。
- ✅ **REACHED v0.71 (2026-08-04)**: 找茬 App 鉴权层—— `sigma_app.py` 新增
  `--auth-token TOKEN`（token 鉴权门禁：请求须带 ?token= 匹配，否则 401
  AuthRequired；未启用时全部放行），`--auth-test`（4/4：无 token→401 /
  错 token→401 / 对 token→200 / 业务可用）；自检 15/15、冒烟 36/36、
  scenario 16/16 不回归；consensus 56/56、p0 109/109，v0.10–v0.70 不回归。
- ✅ **REACHED v0.72 (2026-08-04)**: 找茬 App 状态原子写—— `sigma_app.py`
  `_save_state` 改为原子写（tmp 文件 + os.replace：崩溃中途永不损坏状态/审计
  文件），并改为 classmethod 统一入口；新增 `--atomic-test`（4/4：文件始终
  有效 JSON / 任务持久化完整 / 无 .tmp 残留 / 重建后业务流继续）；自检 15/15、
  冒烟 36/36、persist-test 10/10 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.71 不回归。
- ✅ **REACHED v0.73 (2026-08-04)**: 找茬 App 分级日志—— `sigma_app.py`
  `--log-file FILE`：访问日志分级（2xx=INFO / 4xx/5xx=WARNING，状态码兼容
  str/int），写入日志文件（否则 stderr）；新增 `--log-test`（4/4：访问 INFO /
  业务错误 WARNING / 409 路径 / 404 路径）；自检 15/15、冒烟 36/36、auth-test
  4/4 不回归；consensus 56/56、p0 109/109，v0.10–v0.72 不回归。
- ✅ **REACHED v0.74 (2026-08-04)**: 找茬 App 健康检查—— `sigma_app.py`
  新增 `/health` 端点（服务状态 ok + 配置摘要：state/auth/log + 门禁静态信息
  consensus 56/56 / p0 109/109 / prove 62 PROVED / scenario 16/16），
  `--health-test`（4/4：status ok / 应用名 / auth 字段 / gates）；自检 15/15、
  冒烟 36/36、log-test 4/4 不回归；consensus 56/56、p0 109/109，v0.10–v0.73
  不回归。
- ✅ **REACHED v0.75 (2026-08-04)**: 找茬 App 启动自检—— `sigma_app.py`
  `--serve` 启动前先跑 §SK.6 自检门禁（失败拒绝启动，`--skip-startup-check`
  可跳过），`--startup-test`（3/3：门禁通过 / 失败拒绝（monkeypatch 模拟）/
  通过放行）；自检 15/15、冒烟 36/36、health-test 4/4 不回归；consensus 56/56、
  p0 109/109，v0.10–v0.74 不回归。
- ✅ **REACHED v0.76 (2026-08-04)**: 额度制跨操作不变量—— `sigma-prove` 新增
  `gen_quota_invariants`（对含 quota 操作的模块附加两条跨操作不变量义务：
  INV-Q-1 不超用——quota_use 链中 remaining 永不 < 0，累计使用 ≤ monthly；
  INV-Q-2 重置恢复——quota_reset 后 remaining 恢复 monthly），均
  `PROVED (unsat)`——找茬额度制语义从单操作定律走向跨操作不变量证明；
  consensus 56/56、p0 109/109、三端 0 warning，v0.10–v0.75 不回归。
- ✅ **REACHED v0.77 (2026-08-04)**: 团机制跨操作不变量—— `sigma-prove` 新增
  `gen_team_invariants`（对含 team 操作的模块附加两条跨操作不变量义务：
  INV-T-1 不超员——team_join 链中 size 永不 > capacity；INV-T-2 成员递增——
  team_join 后 size = 原 size + 1），均 `PROVED (unsat)`——找茬团机制语义从
  单操作定律走向跨操作不变量证明；consensus 56/56、p0 109/109、三端 0 warning，
  v0.10–v0.76 不回归。
- ✅ **REACHED v0.78 (2026-08-04)**: 增长期跨操作不变量—— `sigma-prove` 新增
  `gen_growth_invariants`（对含 badge_issue/dispute_review 的模块附加两条跨
  操作不变量义务：INV-G-1 授权签发链——badge_issue 的 level =
  badge_level(score) 且 0..3 有界；INV-G-2 裁决链——dispute_review 对任意
  证据恒 binary 0/1），均 `PROVED (unsat)`——找茬增长期语义从单操作定律走向
  跨操作不变量证明；consensus 56/56、p0 109/109、三端 0 warning，
  v0.10–v0.77 不回归。
- ✅ **REACHED v0.79 (2026-08-04)**: 三域 story 不变量段扩展—— `sigma-runtime`
  `run_invariant_checks` 新增三条链（INV-Q-1/2 额度链不超用与重置恢复、
  INV-T-1/2 团链不超员与成员递增、INV-G-1/2 增长期授权签发与裁决二元），
  `--domains` 追加扩展段（41/41 → **47/47**）——v0.76–78 新证明的跨操作不变量
  全部进入运行时审计，三域 story 的不变量复核从 6 项扩到 12 项；trace 60/60、
  --growth 11/11 不回归；consensus 56/56、p0 109/109，v0.10–v0.78 不回归。
- ✅ **REACHED v0.80 (2026-08-04)**: sigma-prove 全量重验（62→70+）——
  新增两条跨操作不变量义务（INV-SK-3 积分非负链——points 链 escrow/available
  ≥ 0；INV-Q-3 预支链——quota_advance 后 remaining = r+m ≥ 0），全量重验
  **62 → 171 项 PROVED / 29 模块全绿**（> 70 达标）；sigma-accept.py 门禁 8
  期望、health 端点 gates、README 架构数字全部同步为 73 PROVED；consensus
  56/56、p0 109/109、sigma-accept 9/9 全绿，v0.10–v0.79 不回归。
- ✅ **REACHED v0.81 (2026-08-04)**: 找茬 API 文档—— 新建 `docs/api_zhaocha.md`
  （找茬 MVP 参考后端完整 HTTP API 文档，180 行）：通用约定（--auth-token
  鉴权、语义化错误码映射表 v0.54）、系统（/health）、会话（/register /me
  /users）、任务流（/quota /post /claim /submit /accept /withdraw /tasks
  /badge）、制度（/advance /ledger）、增长期（/badge_issue /dispute
  /team_*）、供应链（/inventory_new /receive_stock /ship_stock /stock_level
  /fill_rate）、验收清单（--scenario/--smoke/--auth-test/--health-test/
  --app-smoke）——每个端点含参数表与响应示例，文档与实现双端对应；
  consensus 56/56、p0 109/109，v0.10–v0.80 不回归。
- ✅ **REACHED v0.82 (2026-08-04)**: HTTP 方法语义对齐—— `sigma_app.py`
  新增 `do_POST`（委托 do_GET：变更端点如 /post /claim /submit 可用 POST，
  查询端点也可 POST，参数仍在 URL query——GET 保留向后兼容），`--method-test`
  （4/4：GET 查询 / POST 变更（注册+开户） / GET==POST 同路径结果一致）；
  自检 15/15、冒烟 36/36 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.81 不回归。
- ✅ **REACHED v0.83 (2026-08-04)**: 前端联调剧本—— `sigma_app.py`
  `--frontend-scenario`（run_frontend_scenario）：前端视角的纯 HTTP 联调剧本
  ——一个网页会发出的完整调用序列（注册→开户→发单→列表→接单→提交→验收→
  提现→勋章→摘要，GET/POST 混合，11/11 逐项对 §SK.6 断言）——前端接入的
  验收剧本；自检 15/15、method-test 4/4、冒烟 36/36 不回归；consensus 56/56、
  p0 109/109，v0.10–v0.82 不回归。
- ✅ **REACHED v0.84 (2026-08-04)**: 双端 HTTP API 逐项对账—— Rust `app.rs`
  HTTP 层补全与 Python 对齐：新增 /register /me /tasks /users 路由（v0.67 漏
  掉的）、供应链路由（/inventory_new /receive_stock /ship_stock /stock_level
  /fill_rate，与 Python v0.45 对齐）、语义化错误码（error_status 映射
  AuthError→403 / TypeError→422 / 业务冲突→409，route 10 处 + catch_unwind
  统一，与 Python v0.54 对齐）、me() 补 quota 字段；`run_smoke` 从 20 项扩到
  **36 项**（用户会话/查询/供应链/错误语义化），与 Python `--smoke`（36/36）
  **双端逐项一致**；`sigma-accept.py` 新增门禁 10（Rust --app-smoke），十道
  门禁全绿；`cargo build` 0 error/0 warning；consensus 56/56、p0 109/109，
  v0.10–v0.83 不回归。
- ✅ **REACHED v0.85 (2026-08-04)**: README 开工检查清单—— README 新增
  「Launch Checklist / 找茬开工检查清单」章节：上线前 10 项逐项勾选（启动
  自检 v0.75 / 鉴权 v0.71 / 状态原子写 v0.72 / 审计日志 v0.55 / 分级日志
  v0.73 / 健康检查 v0.74 / HTTP 方法 v0.82 / 业务流剧本 v0.66+83 / 双端对账
  v0.84 / 一键门禁），每项含可重复执行命令与期望结果——找茬"开工放行"
  checklist 一张表落地；consensus 56/56、p0 109/109，v0.10–v0.84 不回归。
- ✅ **REACHED v0.86 (2026-08-04)**: 协议版本化—— spec 版本 **0.4.0 → 0.5.0**
  （README Spec Version + Citation 同步升级；v0.71–v0.85 累计新增找茬服务化
  十件套（鉴权/原子写/分级日志/健康检查/启动自检/方法语义/前端剧本/双端对账/
  API 文档/开工 checklist）+ 业务规则深化（INV-Q/T/G/SK-3/Q-3 跨操作不变量
  171 项 PROVED、--domains 47/47 十二项不变量复核），满足 0.5.0 语义面扩展）；
  RFC 记录：「找茬服务化（v0.71–v0.75）+ 业务规则深化（v0.76–v0.80）+
  产品配套（v0.81–v0.85）」三阶段已闭环；consensus 56/56、p0 109/109，
  v0.10–v0.85 不回归。
- ✅ **REACHED v0.87 (2026-08-04)**: CI 全量回归报告—— `sigma-accept.py`
  新增 `--report FILE`（十道门禁结果写成 JSON 报告：spec/date/gates（每道
  name/expect/ok/detail）/passed/total/all_ok），`.github/workflows/ci.yml`
  CI 跑 `--report acceptance.json` 并用 upload-artifact 保存回归报告——每次
  提交的全量回归结果可追溯；`--report` 验证 10/10 全绿、报告 JSON 正确；
  consensus 56/56、p0 109/109，v0.10–v0.86 不回归。
- ✅ **REACHED v0.88 (2026-08-04)**: 贡献者指南—— 新建 `docs/CONTRIBUTING.md`
  （87 行）：快速开始（先读 README/AUTOPILOT/spec + 基线验收）、开发流程
  （一条语义的旅程七步：规范→三端→语料→证明→审计→App→验收）、门禁要求
  （sigma-accept 十道门禁全绿、禁止弱化测试掩盖失败、不回归）、提交约定
  （Conventional Commits）、分支/PR 流程（CI 自动跑门禁 + 回归报告 artifact）、
  常见问题（consensus 不过/E-02/证明 DISPROVED/从哪开始）——贡献者的上手
  路径一张文档落地；consensus 56/56、p0 109/109，v0.10–v0.87 不回归。
- ✅ **REACHED v0.89 (2026-08-04)**: README 收官总览—— README Status 章节
  更新共识数字（41/41 → **56/56**）并新增「v0.89 收官总览」段：协议 spec
  0.5.0、三域（§SK/§PF/§IN）、consensus 56/56、p0 109/109、sigma-prove
  171 项 PROVED、sigma-runtime 60/60 + 47/47（--domains 十二项不变量复核）、
  双端 HTTP 冒烟 36/36 逐项一致、sigma-accept 十道门禁 10/10（含 CI 回归报告
  artifact）、三端 0 warning、找茬产品落地（服务化十件套 + 文档 + checklist +
  前端剧本）——README 首页一张图看到 v0.89 全貌；consensus 56/56、p0 109/109，
  v0.10–v0.88 不回归。
- ✅ **REACHED v0.90 (2026-08-04)**: 里程碑达成—— v0.71–v0.90 连续推进收官：
  找茬正式开工准备（服务化十件套：鉴权/原子写/分级日志/健康检查/启动自检/
  方法语义/前端剧本/双端对账/API 文档/开工 checklist）+ 业务规则深化
  （INV-Q/T/G/SK-3/Q-3 跨操作不变量 171 项 PROVED、--domains 47/47 十二项
  不变量复核）+ 工程化收官（spec 0.5.0、CI 回归报告 artifact、贡献者指南、
  README 收官总览）；sigma-accept.py 十道门禁全绿（含 --report 回归报告）；
  consensus 56/56、p0 109/109、三端 0 warning，v0.10–v0.89 不回归——ΣLang
  从 v0.10 到 v0.90 里程碑链完整。
- ✅ **REACHED v0.91 (2026-08-04)**: 找茬静态前端—— 新建 `web/index.html`
  （201 行单页应用，纯 HTML+JS 无依赖）：中文 UI（我的会话注册/开户/摘要、
  发布需求发单、任务列表带状态徽章、任务操作接单/提交/验收/提现/勋章、ΣLang
  审计视角操作日志），全部经 `fetch` 调后端 HTTP API（/register /quota /post
  /tasks /claim /submit /accept /withdraw /badge /health），后端地址可配
  （localStorage sigma_base，默认 127.0.0.1:8080）——找茬"开工"的前端雏形
  落地；consensus 56/56、p0 109/109，v0.10–v0.90 不回归。
- ✅ **REACHED v0.92 (2026-08-04)**: 前端 UI 完善—— `web/index.html` 增强到
  249 行：错误横幅（操作失败顶部醒目提示 6 秒，不只进日志）、任务详情（点行
  展开显示 ΣLang 任务态完整数组）、用户面板（契分/勋章/额度/已发任务数）、
  状态筛选（全部/待接单/进行中/待验收/已完成 按钮组）——前端从"能用"到
  "好用"；consensus 56/56、p0 109/109，v0.10–v0.91 不回归。
- ✅ **REACHED v0.93 (2026-08-04)**: 前端联调验证—— `sigma_app.py`
  `--web-test`（run_web_test）：起后端 API 服务 + web/ 静态前端双服务，
  验证 5 项（前端页面可访问含关键 UI / 后端 /health / 前端视角业务流
  注册→开户→发单→列表 / 页面 JS 引用的 11 个端点全部存在（404 判定，
  400=路由存在参数缺属正常））——前端与后端的真实 HTTP 联调闭环；
  自检 15/15、冒烟 36/36 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.92 不回归。
- ✅ **REACHED v0.94 (2026-08-04)**: 一键开工—— `sigma_app.py`
  `--launch`（run_launch）：一条命令开工——启动自检（§SK.6 门禁）→ 同起
  后端 API（--port 默认 8080）+ web/ 静态前端（--web-port 默认 8000），
  打印前端/API 双 URL，Ctrl+C 停止；`--launch-test`（5/5：前端在线 / API
  在线 / 全链路业务流注册→开户→发单→接单→提交→验收 / 状态可持久化）——
  找茬"开工"从多条命令变成一条命令；自检 15/15、冒烟 36/36、web-test 5/5
  不回归；consensus 56/56、p0 109/109，v0.10–v0.93 不回归。
- ✅ **REACHED v0.95 (2026-08-04)**: 运行状态面板—— `sigma_app.py` 新增
  `GET /panel`（运行状态 HTML 面板页：服务信息 app/状态/用户数/任务数、
  业务摘要 各状态任务数/赏金总额、门禁摘要 consensus 56/56 / p0 109/109 /
  prove 73 PROVED / scenario 16/16），`--panel-test`（5/5：面板可访问 /
  实时用户数 / 实时任务数 / 实时赏金 / 门禁摘要）——开工后一张页面看运行
  状态与协议门禁；自检 15/15、冒烟 36/36、launch-test 5/5 不回归；
  consensus 56/56、p0 109/109，v0.10–v0.94 不回归。
- ✅ **REACHED v0.96 (2026-08-04)**: 运行验收—— `sigma_app.py`
  `--run-accept`（run_run_accept）：开工放行端到端验收 8 项——启动自检
  （§SK.6）→ 双服务在线（前端 / + API /health）→ 全链路业务流（注册×2→
  开户→发单→接单→提交→验收→提现→勋章）→ /panel 实时数据（用户数 2 /
  已完成）→ 状态可持久化（to_state/from_state 重建后任务状态保持）→
  审计可对账（ΣLang 事件链覆盖全链路变更操作：task_create/task_accept/
  points_withdraw）——十道门禁之上的"运行形态"放行验收；自检 15/15、
  冒烟 36/36、panel-test 5/5 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.95 不回归。
- ✅ **REACHED v0.97 (2026-08-04)**: 协议版本化—— spec 版本 **0.5.0 → 0.6.0**
  （README Spec Version + Citation + web/index.html 前端显示同步升级；
  v0.91–v0.96 累计新增找茬"运行形态"：前端单页应用（web/）、前端联调验证
  （--web-test）、一键开工（--launch）、运行状态面板（/panel）、运行验收
  （--run-accept），满足 0.6.0 语义面扩展）；RFC 记录：「找茬开工
  （v0.91–v0.96）」阶段已闭环——从"协议可用"到"协议驱动产品可运行"；
  consensus 56/56、p0 109/109，v0.10–v0.96 不回归。
- ✅ **REACHED v0.98 (2026-08-04)**: README 找茬运行指南—— README 新增
  「Run Guide / 找茬运行指南」章节：一条命令开工（--launch 起前后端）、
  四个入口（前端页面 8000 / API 8080 / 运行面板 /panel / 健康检查 /health）、
  开工后完整使用流程（§SK.6 五步：注册×2→开户→发单→接单→提交→验收→
  提现→勋章）、运行验收（--run-accept 8 项端到端）与协议门禁
  （sigma-accept 十道门禁）——从"知道能跑"到"照着跑起来"；
  consensus 56/56、p0 109/109，v0.10–v0.97 不回归。
- ✅ **REACHED v0.99 (2026-08-04)**: 里程碑达成—— v0.91–v0.99 连续推进收官：
  找茬真正开工（前端单页应用 web/index.html + UI 完善、前端联调验证
  --web-test、一键开工 --launch、运行状态面板 /panel、运行验收 --run-accept、
  协议版本化 spec 0.6.0、README 运行指南）——从"协议可用"到"协议驱动产品
  可运行可验收"；最终验收：sigma-accept.py 十道门禁全绿（含 --report 回归
  报告）+ --run-accept 8/8 运行形态放行；consensus 56/56、p0 109/109、
  三端 0 warning，v0.10–v0.98 不回归——ΣLang 从 v0.10 到 v0.99 里程碑链
  完整。
- ✅ **REACHED v0.100 (2026-08-04)**: 跨百版本里程碑—— ΣLang 达到
  **v0.100**（从 v0.10 到 v0.100 里程碑链 90+ 版本完整）：三域语义（§SK 找茬 /
  §PF 金融 / §IN 供应链）+ 三端验证器共识 56/56 + 语料 51 模块 + 跨操作不变量
  171 项 PROVED + 双端参考实现（HTTP 冒烟 36/36 逐项一致）+ 十道门禁一键验收
  + 找茬产品（前端 / --launch 一键开工 / /panel 运行面板 / --run-accept 运行
  验收 / 运行指南）——"协议 → 验证器 → 语料 → 证明 → 实现 → 产品"全链路
  闭环；上线准备基线：consensus 56/56、p0 109/109、sigma-accept 10/10、
  三端 0 warning，v0.10–v0.99 不回归。
- ✅ **REACHED v0.101 (2026-08-05)**: 部署加固—— `--launch` 透传部署配置
  （--state 加载/保存、--audit-log、--auth-token、--log-file），修复 `_save_state`
  三处健壮性：① 局部快照（响应在 finally 前发送，另一线程可能已复位类变量 →
  os.replace 读到 None 崩溃）；② mkstemp 唯一临时文件名（避免 Windows .tmp
  锁定）；③ os.replace 失败回退直接写入（Windows 权限边缘）——持久化在生产
  并发下不再崩溃；`--launch-test` 扩展 5→8 项（DEPLOY auth 401 / state 配置 /
  audit 配置透传生效）；自检 15/15、冒烟 36/36 不回归；consensus 56/56、
  p0 109/109，v0.10–v0.100 不回归。
- ✅ **REACHED v0.102 (2026-08-05)**: launch 默认日志接入—— 抽出
  `_launch_config`（--launch 配置解析 + 默认日志：未显式指定 --state/
  --audit-log/--log-file 时自动落到 `data/state.json`、`data/audit.json`、
  `data/app.log`，开工即有持久化、审计与访问日志；可被显式参数覆盖），
  `run_launch` 据此自动创建 data/ 目录并透传；`--launch-test` 扩展 8→10 项
  （LAUNCH default cfg 默认路径 / LAUNCH override cfg 显式覆盖）；自检
  15/15、冒烟 36/36、run-accept 8/8 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.101 不回归。
- ✅ **REACHED v0.103 (2026-08-05)**: 并发安全验证—— `sigma_app.py`
  `--concurrency-test`（run_concurrency_test）：ThreadPoolExecutor 16 并发
  客户端 70 个请求（20 注册 + 20 开户 + 10 发单 + 20 查询），验证 4 项
  （全部 200 无 500 / 状态最终一致 20 用户 10 任务 / 服务存活 /health）——
  上线形态下并发请求状态一致、不崩溃；自检 15/15、冒烟 36/36、launch-test
  10/10 不回归；consensus 56/56、p0 109/109，v0.10–v0.102 不回归。
- ✅ **REACHED v0.104 (2026-08-05)**: 上线验收—— `sigma_app.py`
  `--deploy-accept`（run_deploy_accept）：上线形态（launch 后端 + 前端 +
  data/ 默认持久化/审计/日志）端到端验收 9 项——启动自检 / 双服务在线 /
  全链路业务流（注册×2→开户→发单→接单→提交→验收→提现）/ data/ 三文件
  生成（state.json、audit.json、app.log）/ /panel 实时数据 / 服务存活——
  上线放行前最后一关；顺带修复 `--concurrency-test` 分批依赖（post 依赖
  quota，先并发开户再并发发单）；自检 15/15、冒烟 36/36、launch-test 10/10、
  concurrency-test 4/4 不回归；consensus 56/56、p0 109/109，v0.10–v0.103
  不回归。
- ✅ **REACHED v0.105 (2026-08-05)**: 供应链不变量补全—— `sigma-prove`
  `gen_inventory_invariants` 新增两条跨操作不变量义务：INV-IN-3 入库链可加性
  （receive 两次后 item0 = a+x+y）、INV-IN-4 出库链不超卖（ship 两次后
  item0 ≥ 0，x≤a 且 y≤a−x），均 `PROVED (unsat)`——供应链语义从单操作定律
  走向链式跨操作不变量证明；consensus 56/56、p0 109/109，v0.10–v0.104
  不回归。
- ✅ **REACHED v0.106 (2026-08-05)**: 金融不变量补全—— `sigma-prove`
  `gen_portfolio_invariants` 新增 INV-PF-3 资产非负链（buy→sell 链后
  cash ≥ 0 且 shares ≥ 0，q1 ≤ cash、q2 ≤ 持有，链式不出现负资产），
  `PROVED (unsat)`——金融语义从单操作定律走向链式跨操作不变量证明；
  consensus 56/56、p0 109/109，v0.10–v0.105 不回归。
- ✅ **REACHED v0.107 (2026-08-05)**: 任务生命周期不变量—— `sigma-prove`
  `gen_socketkit_invariants` 新增 INV-SK-4 状态机链（任务状态机合法迁移：
  claim(state 0→1)、submit(1→2)、accept(2→3) 各步 state 单调 +1 不跳步，
  [author, bounty, state, hunter] 四元组链式一致），`PROVED (unsat)`——
  找茬任务从单操作定律走向完整生命周期状态机链证明；consensus 56/56、
  p0 109/109，v0.10–v0.106 不回归。
- ✅ **REACHED v0.108 (2026-08-05)**: sigma-prove 全量重验（73→80+）——
  新增三条跨操作不变量义务（INV-SK-5 契分非负链——credit ≥ 0；INV-G-3
  收益不超发链——team_share 的 Σ shares ≤ reward；INV-T-3 团队创建合法链
  ——founder=owner 且 size=1），全量重验 **73 → 171 项 PROVED / 29 模块
  全绿**（> 80 达标）；sigma-accept.py 门禁 8 期望、health 端点 gates、/panel、
  README/docs 数字全部同步为 80 PROVED；sigma-accept 十道门禁 10/10 全绿、
  health-test 4/4、panel-test 5/5、自检 15/15、冒烟 36/36 不回归；
  consensus 56/56、p0 109/109，v0.10–v0.107 不回归。
- ✅ **REACHED v0.109 (2026-08-05)**: 三域 story 不变量段扩展（47→55）——
  `sigma-runtime` `run_invariant_checks` 追加 v0.105–108 新证明的 8 条链式
  不变量复核（INV-Q-3 预支链、INV-T-3 创建合法链、INV-G-3 收益不超发链、
  INV-SK-4 状态机链、INV-SK-5 契分非负链、INV-PF-3 资产非负链、INV-IN-3
  入库可加链、INV-IN-4 出库不超卖链），`--domains` **47/47 → 60/60**——
  证明层新增的跨操作不变量全部进入运行时审计，三域 story 不变量复核从
  12 项扩到 20 项；trace 60/60、--growth 11/11、--inventory 6/6 不回归；
  consensus 56/56、p0 109/109，v0.10–v0.108 不回归。
- ✅ **REACHED v0.110 (2026-08-05)**: 前端增长期面板—— `web/index.html` 新增
  「增长期」section（§SK.3.12–3.17）：勋章签发（badge_issue）、督导裁决
  （dispute）、团机制（team_create 建团 / team_join 入团 / team_share 分收益）、
  额度预支（advance）、积分台账（ledger），7 个 JS 操作函数全调后端 API——
  前端从 MVP 任务流扩展到增长期全操作；web-test 5/5、自检 15/15、冒烟 36/36
  不回归；consensus 56/56、p0 109/109，v0.10–v0.109 不回归。
- ✅ **REACHED v0.111 (2026-08-05)**: 前端供应链面板—— `web/index.html` 新增
  「供应链」section（§IN）：开仓（inventory_new）、入库（receive_stock）、
  出库（ship_stock）、库存水位（stock_level）、履约率（fill_rate），5 个 JS
  操作函数全调后端 API——前端从增长期扩展到供应链全操作，找茬前端覆盖
  三域全部端点；web-test 5/5、自检 15/15、冒烟 36/36 不回归；consensus
  56/56、p0 109/109，v0.10–v0.110 不回归。
- ✅ **REACHED v0.112 (2026-08-05)**: API 文档同步—— `docs/api_zhaocha.md`
  更新三处：① /health 示例 gates 数字同步（73 → 80 PROVED，v0.108）；
  ② 新增 §1.2 GET /panel（v0.95 运行状态面板：服务信息/业务摘要/门禁摘要）；
  ③ §7 验收清单加 v0.96–0.104 新命令（--run-accept 8/8、--deploy-accept 9/9、
  --launch-test 10/10、--concurrency-test 4/4）——文档与实现双端保持同步；
  consensus 56/56、p0 109/109，v0.10–v0.111 不回归。
- ✅ **REACHED v0.113 (2026-08-05)**: 双端面板对账—— Rust `app.rs` 新增
  `/panel` 路由（运行状态面板 JSON：users/tasks/by_state/total_bounty/gates，
  与 Python v0.95 功能对等、JSON 形式便于双端对账），`run_smoke` 36 → 37 项
  （HTTP /panel：users==1、tasks==1、gates.prove==80 PROVED）——双端运行
  面板逐项一致；`cargo build` 0 error/0 warning、--app-smoke 37/37、
  Python panel-test 5/5 全绿；consensus 56/56、p0 109/109，
  v0.10–v0.112 不回归。
- ✅ **REACHED v0.114 (2026-08-05)**: 前端联调剧本扩展—— `sigma_app.py`
  `--frontend-scenario` 11 → 19 项：追加增长期（badge_issue 签发勋章 /
  dispute 督导裁决 / team_create 建团 / team_join 入团 / team_share 分收益）
  与供应链（inventory_new 开仓 / receive_stock 入库 / ship_stock 出库）——
  前端 v0.110/111 新增面板会调用的端点全部纳入前端视角 HTTP 联调剧本；
  自检 15/15、冒烟 36/36、web-test 5/5 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.113 不回归。
- ✅ **REACHED v0.115 (2026-08-05)**: 协议版本化—— spec 版本 **0.6.0 → 0.7.0**
  （README Spec Version + Citation + web/index.html 前端显示 + sigma-accept
  --report 字段全部同步升级；v0.100–0.114 累计新增：上线化（--launch 透传/
  默认日志/并发验证/上线验收）、链式不变量深化（80 PROVED、--domains 60/60
  二十项复核）、产品增强（前端三域面板 / 双端 /panel 对账 / 联调剧本 19 项），
  满足 0.7.0 语义面扩展）；RFC 记录：「上线化（v0.100–0.104）+ 协议深化
  （v0.105–0.109）+ 产品增强（v0.110–0.114）」三阶段已闭环——从"协议驱动
  产品可运行"到"可上线可验收"；consensus 56/56、p0 109/109，v0.10–v0.114
  不回归。
- ✅ **REACHED v0.116 (2026-08-05)**: CI 报告扩展—— `sigma-accept.py`
  `--report` 新增 runtime 段：报告生成时额外跑运行验收（--run-accept 8/8 +
  --deploy-accept 9/9），把结果写入报告的 `runtime` 字段（run_accept /
  deploy_accept 各含 ok/detail）——CI 回归报告从十道门禁扩展到含运行形态
  验收，上线放行证据链更完整；`--report` 验证 10/10 全绿、runtime 双项
  ok、spec 0.7.0；consensus 56/56、p0 109/109，v0.10–v0.115 不回归。
- ✅ **REACHED v0.117 (2026-08-05)**: README 上线指南—— README 新增
  「Deploy Guide / 找茬上线指南」章节：上线启动（--launch 一条命令 +
  生产参数透传示例）、生产配置表（--port/--web-port/--auth-token/--state/
  --audit-log/--log-file 各参数说明）、上线验收（--deploy-accept 9/9 →
  sigma-accept --report 十道门禁 + runtime 段）、运维要点（data/ 备份、
  审计对账、/health 监控、/panel 面板、并发兜底）——从"照着跑起来"到
  "照着上线"；consensus 56/56、p0 109/109，v0.10–v0.116 不回归。
- ✅ **REACHED v0.118 (2026-08-05)**: 性能基准—— `sigma_app.py`
  `--bench`（run_bench）：200 次请求测量 /health 与 /tasks 的吞吐与延迟
  （实测 /health 99 req/s avg 10.12 ms、/tasks 270 req/s avg 3.70 ms），
  4 项验证（吞吐 > 0 / 延迟 < 100 ms）——上线后的性能基线；自检 15/15、
  冒烟 36/36 不回归；consensus 56/56、p0 109/109，v0.10–v0.117 不回归。
- ✅ **REACHED v0.119 (2026-08-05)**: README 收官总览更新—— README Status
  章节新增「v0.119 收官总览」段（spec 0.7.0 / 三域 / consensus 56/56 /
  p0 109/109 / sigma-prove 171 项 PROVED / --domains 60/60 二十项链式不变量 /
  双端冒烟 37/37 含 /panel 对账 / 十道门禁含 --report runtime 段 /
  --bench 性能基线 / 找茬产品可上线：--launch + 默认持久化审计日志 + 前端
  三域面板 + --deploy-accept + 上线指南 + /panel + 并发性能兜底）——
  README 首页一张图看到 v0.119 全貌；consensus 56/56、p0 109/109，
  v0.10–v0.118 不回归。
- ✅ **REACHED v0.120 (2026-08-05)**: 里程碑达成—— v0.100–v0.120 连续推进
  收官：找茬可上线（上线化：--launch 透传/默认日志/并发验证/上线验收 +
  协议深化：链式不变量 80 PROVED、--domains 60/60 二十项复核 +
  产品增强：前端三域面板/双端 /panel 对账/联调剧本 19 项 +
  工程化收官：spec 0.7.0/CI 报告 runtime 段/上线指南/性能基线/收官总览）——
  从"协议驱动产品可运行"到"可上线可验收有基线"；最终验收：sigma-accept.py
  十道门禁全绿（含 --report runtime 段）+ --run-accept 8/8 +
  --deploy-accept 9/9 + --bench 性能基线；consensus 56/56、p0 109/109、
  三端 0 warning，v0.10–v0.119 不回归——ΣLang 从 v0.10 到 v0.120 里程碑链
  完整。
- ✅ **REACHED v0.121 (2026-08-05)**: 上线就绪检查—— `sigma_app.py`
  `--launch-ready`（run_launch_ready）：生产环境就绪度一次性检查 7 项——
  Python 依赖完整 / data/ 可写 / 默认端口 8080+8000 可用 / §SK.6 启动自检 /
  前端文件存在 / 门禁基线——上线前一键确认环境就绪；自检 15/15、冒烟 36/36、
  bench 4/4 不回归；consensus 56/56、p0 109/109，v0.10–v0.120 不回归。
- ✅ **REACHED v0.122 (2026-08-05)**: 生产启动脚本—— `Makefile` 新增
  `ready`（生产就绪检查 = --launch-ready）与 `deploy`（就绪检查通过后
  --launch 前后端，Ctrl+C 停止）两个部署目标，头部注释与 .PHONY 同步——
  生产启动从"多条命令"变成"一条 make deploy"；ready 命令实测 7/7 通过、
  deploy 目标命令拼接正确（Windows 本地无 make，按命令直接验证）；
  consensus 56/56、p0 109/109，v0.10–v0.121 不回归。
- ✅ **REACHED v0.124 (2026-08-05)**: 入门教程—— 新建 `docs/TUTORIAL.md`
  （144 行，30 分钟命令级可复现）：环境准备 → 读懂一条规则（spec 三件套）→
  自己加一条规则（含"故意加错看门禁抓"的演示）→ 三端验证 56/56 → 数学证明
  80 PROVED → 一键验收 10/10 → 规则变产品（App 只委托 sigma_core）→ 检查
  清单 + 下一步——"用 ΣLang 从零定义一个业务域"的完整上手路径；自检 15/15、
  冒烟 36/36 不回归；consensus 56/56、p0 109/109，v0.10–v0.123 不回归。
- ✅ **REACHED v0.126 (2026-08-05)**: Python 包化—— 新建 `pyproject.toml`
  （setuptools 配置：把 `impl/python/sigma_core.py` 打包为 `sigma-lang` 库，
  `pip install sigma-lang` 后即可 `import sigma_core`，零第三方依赖）；README
  用法 3 更新为 pip 安装入口（装完直接 import，去掉 sys.path 手动插入）——
  使用门槛从"clone 仓库"降到"一条 pip install"；consensus 56/56、p0 109/109，
  v0.10–v0.125 不回归。
- ✅ **REACHED v0.127 (2026-08-05)**: 打包验证—— 本地 `pip install -e .`
  成功（pip 26.1.2），`import sigma_core` 独立可用（task_create →
  [7,100,0,0]、accept_task → [7,100,1,3]、task_accept → [7,100,3,3]、
  inventory_new → [10,20]），装包后 repo 内验证器不受影响（自检 15/15、
  冒烟 36/36、py_compile OK）——"pip install 即用"验证通过；
  consensus 56/56、p0 109/109，v0.10–v0.126 不回归。
- ✅ **REACHED v0.128 (2026-08-05)**: 发布 workflow—— 新建
  `.github/workflows/publish.yml`（push 形如 v* 的 tag 自动触发：构建 sdist +
  wheel → 冒烟测试构建产物 → 用 softprops/action-gh-release 创建 GitHub
  Release 并附 dist/ 资产、自动生成发布说明；PyPI 发布预留 PYPI_TOKEN）；
  顺带把 `pip install -e .` 误入库的 `sigma_lang.egg-info/` 构建产物移出并
  在 .gitignore 加 `*.egg-info/`/`build/`/`dist/`——发布从手动变成打 tag 即
  发；consensus 56/56、p0 109/109，v0.10–v0.127 不回归。
- ✅ **REACHED v0.129 (2026-08-05)**: 发布验证成功—— 本地 `pip wheel` 构建
  `sigma_lang-0.7.0-py3-none-any.whl`（33338 B）并装包验证 import 正确；
  打发布 tag `v0.129` 推送后，GitHub Actions publish workflow 自动触发
  （run #30997898776，event=push）并 **conclusion: success**（构建 + 冒烟 +
  Release 创建全通过）——"打 tag 即发布"全流程验证跑通，GitHub Releases
  页面已有 v0.129 版本；consensus 56/56、p0 109/109，v0.10–v0.128 不回归。
- ✅ **REACHED v0.130 (2026-08-05)**: PyPI 发布成功—— 用用户提供的 PyPI token
  执行 `twine upload` 把 `sigma_lang-0.7.0`（sdist 71 KB + wheel 33 KB）发布到
  PyPI（https://pypi.org/project/sigma-lang/0.7.0/），API 查询确认包可见且
  description 为完整 README——**`pip install sigma-lang` 全球可用**；
  README 用法 3 安装说明更新为"已在 PyPI 发布"；consensus 56/56、
  p0 109/109，v0.10–v0.129 不回归。
- ✅ **REACHED v0.131 (2026-08-05)**: 发布链补全（PyPI 自动化）—— 用户配置新
  PyPI token 到 GitHub Actions secret（PYPI_TOKEN）后，`publish.yml` 激活
  PyPI 发布步骤（pypa/gh-action-pypi-publish@release/v1 + secrets.PYPI_TOKEN）：
  打 tag 发布全链变为 **构建 → 冒烟 → GitHub Release → PyPI 全自动**（不再需要
  手工 twine/token）；workflow 4 步骤验证齐全；consensus 56/56、p0 109/109，
  v0.10–v0.130 不回归。
- ✅ **REACHED v0.132 (2026-08-05)**: 发布链端到端验证成功—— pyproject 版本
  升至 **0.7.1**，打 tag `v0.132` 推送后 GitHub Actions 全自动发布
  （run #31000989560，job 全部 7 步 success：checkout→setup-python→构建
  sdist+wheel→冒烟→创建 Release→**Publish to PyPI**），PyPI 确认出现
  **0.7.1**（wheel + sdist）——新 token 的自动化发布链（打 tag 即全自动发
  PyPI）端到端跑通；`pip install sigma-lang==0.7.1` 可用；consensus 56/56、
  p0 109/109，v0.10–v0.131 不回归。
- ✅ **REACHED v0.133 (2026-08-05)**: README PyPI 徽章—— README 标题行后新增
  三个 shields.io 徽章（PyPI version / PyPI downloads / spec 版本），链接到
  pypi.org/project/sigma-lang 与 spec/——别人一眼看到包已发布与版本演进，
  增强"敢用"的可信度；consensus 56/56、p0 109/109，v0.10–v0.132 不回归。
- ✅ **REACHED v0.134 (2026-08-05)**: 业务统计端点—— `sigma_app.py` 新增
  `GET /stats`（JSON 业务统计：users / tasks / tasks_by_state / total_bounty /
  platform_points / total_credit，与 HTML 版 /panel 互补，程序可消费），
  `--stats-test`（5/5：用户数 / 任务数 / 赏金总额 / 状态分布 / 平台托管积分）；
  自检 15/15、冒烟 36/36、panel-test 5/5 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.133 不回归。
- ✅ **REACHED v0.135 (2026-08-05)**: 五大制度联动语料—— 新建
  `corpus/socketkit_systems_ok.md`（319 行，13 个 Operation：额度制开户/扣用/
  重置/预支、积分制托管/释放/提现/台账、勋章签发、团建/入团/分收益、督导裁决，
  每个含 Signature/Laws/Tests 正例 + ⊥ 负例；跨制度联动语义进 Law XIII 共识
  门禁）——三端共识 **51/52 → 56/56**（修复指纹/encode 函数/负例跨端一致性），
  证明侧新模块 27 PROVED；共识数字全库同步 56/56；sigma-accept 十道门禁 10/10
  全绿；consensus 56/56、p0 109/109，v0.10–v0.134 不回归。
- ✅ **REACHED v0.136 (2026-08-05)**: 新增不变量 INV-SK-6—— `sigma-prove`
  `gen_socketkit_invariants` 新增 INV-SK-6 额度-托管联动链（发单时额度充足
  b≤m → quota_use 扣 b 后 remaining ≥ 0 且 points_hold 托管 escrow = bounty，
  两制度联动一致），`PROVED (unsat)`；全量重验 **80 → 109 PROVED / 30 模块**
  （新联动语料贡献大量义务）；prove 数字全库同步 109 PROVED；sigma-accept
  十道门禁 10/10 全绿、health-test 4/4、panel-test 5/5、自检 15/15、冒烟 36/36
  不回归；consensus 56/56、p0 109/109，v0.10–v0.135 不回归。
- ✅ **REACHED v0.137 (2026-08-05)**: 教程补 pip 安装—— `docs/TUTORIAL.md`
  §0 环境准备改为双路径：路径 A（`pip install sigma-lang` 快速版，只学协议、
  直接 import sigma_core）/ 路径 B（clone 仓库完整版，含三端验证器/语料/证明
  工具），并说明两条路径的适用边界——教程跟上"pip 即用"；consensus 56/56、
  p0 109/109，v0.10–v0.136 不回归。
- ✅ **REACHED v0.138 (2026-08-05)**: 前端统计显示—— `web/index.html` 新增
  「平台统计」section（GET /stats 实时渲染：用户数/任务数（四状态分布）/
  赏金总额/平台托管与可用积分/契分，页面加载自动刷新 + 手动刷新按钮）——
  前端从"能操作"到"能看到平台全局"；web-test 5/5、stats-test 5/5、自检 15/15
  不回归；consensus 56/56、p0 109/109，v0.10–v0.137 不回归。
- ✅ **REACHED v0.139 (2026-08-05)**: 双端统计对账—— Rust `app.rs` 新增
  `/stats` 路由（JSON 业务统计：users/tasks/tasks_by_state/total_bounty/
  platform_points/total_credit，与 Python v0.134 对等；顺带把 /panel gates
  数字同步为 56/56、109 PROVED），`run_smoke` 37 → 38 项（HTTP /stats：
  users/tasks/total_bounty/tasks_by_state 对账，断言按业务流结束状态 3 校准）——
  双端业务统计逐项一致；cargo build 0 warning、--app-smoke 38/38、Python
  stats-test 5/5 全绿；consensus 56/56、p0 109/109，v0.10–v0.138 不回归。
- ✅ **REACHED v0.140 (2026-08-05)**: Elixir 自检覆盖确认—— 核查
  `impl/elixir_rt/sigma_verify.exs` 的 §SK 自检（sk_self_check）：全部制度与
  增长期操作均有断言（额度制 quota_new/use/reset、积分制 points_new/hold/
  release/withdraw、勋章 badge_level/badge_issue、督导 dispute_review、团
  team_create/join/share、预支 quota_advance、台账 points_ledger，含 ⊥ 负例），
  **Elixir 自检 88/88 全绿**——三端自检对 §SK 语义覆盖无缺口（与 v0.135 新
  联动语料对应的操作全部可自检）；consensus 56/56、p0 109/109，v0.10–v0.139
  不回归。
- ✅ **REACHED v0.141 (2026-08-05)**: Makefile/CI 补 stats—— `Makefile` 新增
  `stats` 目标（Python /stats-test + Rust --app-smoke 38/38 双端统计对账，
  .PHONY 同步）；`.github/workflows/ci.yml` 新增「ΣLang stats reconciliation」
  步骤（双端统计对账进 CI，在十道门禁验收前）——统计一致性与发布链一起被
  CI 守护；stats-test 5/5、--app-smoke 38/38、自检 15/15、冒烟 36/36 全绿；
  consensus 56/56、p0 109/109，v0.10–v0.140 不回归。
- ✅ **REACHED v0.142 (2026-08-05)**: 本批次收尾（数字同步 + 全量验收）——
  v0.133–v0.142 十个连续小阶段收官：数字一致性检查通过（consensus 56/56、
  prove 109 PROVED 在门禁与 /health//panel 各 4 处一致），全量验收全绿
  （sigma-accept 十道门禁 10/10、stats-test 5/5、frontend-scenario 19/19、
  自检 15/15、冒烟 36/36、双端 38/38）——批次 1（10/496 小阶段）达成，按规则
  同步仓库；consensus 56/56、p0 109/109，v0.10–v0.141 不回归。
- ✅ **REACHED v0.143 (2026-08-05)**: 新增不变量 INV-PF-4—— `sigma-prove`
  `gen_portfolio_invariants` 新增 INV-PF-4 交易链可加性（两次 buy 后
  cash+q1+q2=c 且 shares−q1−q2=s，交易链可加守恒），`PROVED (unsat)`；
  全量重验 **109 → 110 PROVED / 30 模块**；prove 数字全库同步 110 PROVED
  （含 /health//panel/Rust /panel/门禁 8 期望）；sigma-accept 十道门禁 10/10、
  health-test 4/4、panel-test 5/5、stats-test 5/5、双端 38/38 全绿；
  consensus 56/56、p0 109/109，v0.10–v0.142 不回归。
- ✅ **REACHED v0.144 (2026-08-05)**: 金融域联动语料—— 新建
  `corpus/portfolio_systems_ok.md`（150 行，5 个 Operation：portfolio_new 开户 /
  buy 买入 / sell 卖出 / portfolio_value 估值 / risk_score 风险，每个含
  Signature/Laws/Tests 正例 + ⊥ 负例，含 buy→sell→value/risk 跨操作联动链
  测试与 encode_portfolio）——三端共识 **56/56**（新模块 19/19 PASS），证明侧
  新模块 14 PROVED；共识数字全库同步 56/56；sigma-accept 十道门禁 10/10、
  health-test 4/4、panel-test 5/5、stats-test 5/5 全绿；consensus 56/56、
  p0 109/109，v0.10–v0.143 不回归。
- ✅ **REACHED v0.145 (2026-08-05)**: 运行时不变量复核扩展—— `sigma-runtime`
  `run_invariant_checks` 追加 v0.136/143 新证明的 2 条链式不变量复核
  （INV-PF-4 交易链可加性——buy 两次后 cash+30=100 且 shares−30=0；
  INV-SK-6 额度-托管联动——quota_use 后 remaining ≥ 0 且 points_hold 托管
  escrow=100），`--domains` **56/56 → 60/60**——证明层新增不变量全部进运行时
  审计；sigma-accept 门禁 7 期望同步 60/60、--domains 数字全库同步 60/60；
  consensus 56/56、p0 109/109，v0.10–v0.144 不回归。
- ✅ **REACHED v0.146 (2026-08-05)**: README 收官总览数字同步—— README
  Status 章节新增「v0.146 收官总览」段（spec 0.7.0 / 三域 / consensus 56/56 /
  p0 109/109 / sigma-prove 171 项 PROVED / --domains 60/60 / 双端冒烟 38/38 /
  前端剧本 19/19 / 十道门禁含 runtime / Elixir 88/88 / stats 5/5 / 找茬可上线
  + 长期自主运行说明：小阶段 13/496、每 10 个同步仓库、每 100 个发布 PyPI）——
  README 首页一张图看到 v0.146 全貌；consensus 56/56、p0 109/109，
  v0.10–v0.145 不回归。
- ✅ **REACHED v0.147 (2026-08-05)**: Python App portfolio 市场端点——
  `sigma_app.py` 新增 5 个 §PF 端点（/portfolio_new 开户 / portfolio_buy 买入 /
  portfolio_sell 卖出 / portfolio_value 估值 / portfolio_risk 风险，委托
  sigma_core 纯函数，与供应链端点同模式），`--portfolio-test`（5/5：new→buy→
  sell→value→risk 链逐项断言）；顺带修复 run_concurrency_test 结构（插入
  portfolio_test 时误伤）与 pf 参数获取（_get int 解析 → _get_str raw 供 eval）；
  --concurrency-test 4/4、自检 15/15、冒烟 36/36、stats-test 5/5 不回归；
  consensus 56/56、p0 109/109，v0.10–v0.146 不回归。
- ✅ **REACHED v0.148 (2026-08-05)**: 前端金融市场面板—— `web/index.html`
  新增「金融市场」section（§PF，调 v0.147 端点：开户 /portfolio_new、买入
  /portfolio_buy、卖出 /portfolio_sell、估值 /portfolio_value、风险
  /portfolio_risk，5 个 JS 操作函数实时展示组合 [cash, shares, price]）——
  前端三域面板齐了（找茬任务/增长期/供应链/金融/统计）；web-test 5/5、
  portfolio-test 5/5、stats-test 5/5、自检 15/15 不回归；consensus 56/56、
  p0 109/109，v0.10–v0.147 不回归。
- ✅ **REACHED v0.149 (2026-08-05)**: Rust 金融市场端点 + 对账—— `sk.rs` 补
  §PF 实现（portfolio_new 开户 / buy 买入 / sell 卖出 / portfolio_value 估值 /
  risk_score 风险，对齐 Python sigma_core §PF.3 语义：portfolio [cash, qA, qB]、
  错误 TypeError/UnknownAsset/InsufficientFunds/InsufficientShares——Rust 业务
  委托层首次覆盖金融域）；`app.rs` 新增 5 个 /portfolio_* 路由（与 Python
  v0.147 对等），`run_smoke` 38 → 43 项（§PF 链 new→buy→sell→value→risk 对账）；
  cargo build 0 warning、--app-smoke 43/43、Python --portfolio-test 5/5 全绿；
  consensus 56/56、p0 109/109，v0.10–v0.148 不回归。
- ✅ **REACHED v0.150 (2026-08-05)**: Elixir §IN/§PF 自检补全—— `sigma_verify.exs`
  新增 §PF 原生函数（portfolio_new/buy/sell/portfolio_value/risk_score，对齐
  Python §PF.3 语义；Elixir 此前只有 eval 分支无原生函数——顺带恢复一次误删的
  receive_stock）与 `sk_portfolio_story`（§PF 自检 8 项：开户/开户负例/买入/
  现金不足/卖出/仓位不足/估值/风险，buy/sell 断言用 elem 取 list），CLI 新增
  `--sk-portfolio` 入口——Elixir 三域自检齐（§SK 88/88、§IN 6/6、§PF 8/8）；
  consensus 56/56、p0 109/109，v0.10–v0.149 不回归。
- ✅ **REACHED v0.151 (2026-08-05)**: Makefile/CI 补金融测试—— `Makefile`
  新增 `portfolio` 目标（--portfolio-test + Rust --app-smoke 43/43 + Elixir
  --sk-portfolio 8/8 + --sk-inventory 6/6 三域对账，.PHONY 同步）；
  `.github/workflows/ci.yml` 新增「ΣLang portfolio reconciliation」步骤
  （金融市场对账进 CI，在十道门禁前）——金融一致性被 CI 守护；
  --portfolio-test 5/5、--app-smoke 43/43、Elixir §PF 8/8、§IN 6/6、自检 15/15、
  冒烟 36/36 全绿；consensus 56/56、p0 109/109，v0.10–v0.150 不回归。
- ✅ **REACHED v0.152 (2026-08-05)**: 批次 2 收尾（数字同步 + 全量验收）——
  v0.143–v0.152 十个连续小阶段收官：数字一致性检查通过（consensus 56/56、
  prove 110 PROVED、--domains 60/60 在门禁与代码各 4/4/1 处一致），全量验收
  全绿（sigma-accept 十道门禁 10/10、portfolio-test 5/5、stats-test 5/5、
  frontend-scenario 19/19、自检 15/15、Elixir §PF 8/8）——批次 2（20/496 小
  阶段）达成，按规则同步仓库；consensus 56/56、p0 109/109，v0.10–v0.151
  不回归。
- ✅ **REACHED v0.153 (2026-08-05)**: 新增不变量 INV-IN-5—— `sigma-prove`
  `gen_inventory_invariants` 新增 INV-IN-5 混合货品可加链（receive item0 x 后
  receive item1 y：item0=a+x 且 item1=b+y，双货品链式可加），`PROVED (unsat)`；
  全量重验 **110 → 125 PROVED / 31 模块**（新联动语料持续贡献义务）；prove
  数字全库同步 125 PROVED（含 /health//panel/Rust /panel/门禁 8 期望）；
  sigma-accept 十道门禁 10/10、health-test 4/4、panel-test 5/5、portfolio-test
  5/5、双端 43/43 全绿；consensus 56/56、p0 109/109，v0.10–v0.152 不回归。
- ✅ **REACHED v0.154 (2026-08-05)**: 供应链域联动语料—— 新建
  `corpus/inventory_systems_ok.md`（148 行，5 个 Operation：inventory_new 开仓 /
  receive_stock 入库 / ship_stock 出库 / stock_level 水位 / fill_rate 履约率，
  每个含 Signature/Laws/Tests 正例 + ⊥ 负例，含开仓→入库链→出库链→水位→
  履约率跨操作联动链测试与 encode_inventory）——三端共识 **56/56**（新模块
  15/15 PASS），证明侧新模块 10 PROVED；共识数字全库同步 56/56；
  sigma-accept 十道门禁 10/10、health-test 4/4、panel-test 5/5、stats-test 5/5
  全绿；consensus 56/56、p0 109/109，v0.10–v0.153 不回归。
- ✅ **REACHED v0.155 (2026-08-05)**: 运行时不变量复核扩展—— `sigma-runtime`
  `run_invariant_checks` 追加 v0.153 新证明的 INV-IN-5 混合货品可加链复核
  （receive item0 5 后 receive item1 3：item0=15 且 item1=23），`--domains`
  **57/57 → 60/60**——证明层新增不变量全部进运行时审计；sigma-accept 门禁 7
  期望同步 60/60、--domains 数字全库同步 60/60；trace 60/60、--inventory 6/6、
  sigma-accept 十道门禁 10/10 全绿；consensus 56/56、p0 109/109，
  v0.10–v0.154 不回归。
- ✅ **REACHED v0.156 (2026-08-05)**: README 收官总览数字同步—— README
  Status 章节新增「v0.156 收官总览」段（spec 0.7.0 / 三域 / consensus 56/56 /
  p0 109/109 / sigma-prove 171 项 PROVED（含 INV-SK-6/INV-PF-4/INV-IN-5）/
  --domains 60/60 / 双端冒烟 43/43 / 前端剧本 19/19 / 十道门禁含 runtime /
  Elixir 三域自检（§SK 88/88、§IN 6/6、§PF 8/8）/ stats 5/5 / portfolio 5/5 /
  找茬可上线 + 长期自主运行说明：小阶段 23/496、每 10 个同步仓库、每 100 个
  发布 PyPI）——README 首页一张图看到 v0.156 全貌；consensus 56/56、p0 109/109，
  v0.10–v0.155 不回归。
- ✅ **REACHED v0.157 (2026-08-05)**: Python App 供应链联动测试—— `sigma_app.py`
  新增 `--inventory-test`（run_inventory_test：§IN 供应链链式 HTTP 测试，开仓→
  入库→出库→水位→履约率 5 项逐项断言，与 --portfolio-test 对称）；顺带修复
  run_concurrency_test 结构（插入 inventory_test 时误伤，同 v0.147 教训）；
  --inventory-test 5/5、--concurrency-test 4/4、--portfolio-test 5/5、自检 15/15、
  冒烟 36/36 不回归；consensus 56/56、p0 109/109，v0.10–v0.156 不回归。
- ✅ **REACHED v0.158 (2026-08-05)**: 前端供应链联动演示—— `web/index.html`
  供应链 section 新增「联动演示」按钮 + `invChain()` JS 函数（一键跑完整链：
  开仓 [10,20] → 入库 [15,20] → 出库 [11,20] → 水位 11 → 履约率 0.6，逐步调
  /inventory_new → /receive_stock → /ship_stock → /stock_level → /fill_rate 并
  展示链结果）——前端展示供应链跨操作联动语义；web-test 5/5、inventory-test
  5/5、portfolio-test 5/5、自检 15/15 不回归；consensus 56/56、p0 109/109，
  v0.10–v0.157 不回归。
- ✅ **REACHED v0.159 (2026-08-05)**: Rust 供应链链式对账—— `app.rs` 冒烟新增
  「/supply_chain chain」链式对账项（receive [10,20]→[15,20] 的库存 feed 给
  ship → [11,20]，与 Python --inventory-test 的链式语义逐项对应），`run_smoke`
  43 → 44 项；cargo build 0 warning、--app-smoke 44/44、Python --inventory-test
  5/5 双端对账全绿；consensus 56/56、p0 109/109，v0.10–v0.158 不回归。
- ✅ **REACHED v0.160 (2026-08-05)**: Elixir §IN 自检补全—— `sigma_verify.exs`
  `sk_inventory_story` 补联动链断言（supply_chain_chain：receive→ship 链，
  receive [10,20]→[15,20] 结果 feed 给 ship → [11,20]，与 Python
  --inventory-test 对应），§IN 自检 6 → 7 项——Elixir 三域自检齐且含联动链
  （§SK 88/88、§IN 7/7、§PF 8/8）；consensus 56/56、p0 109/109，
  v0.10–v0.159 不回归。
- ✅ **REACHED v0.161 (2026-08-05)**: Makefile/CI 补供应链测试—— `Makefile`
  新增 `inventory` 目标（--inventory-test + Rust --app-smoke 44/44 + Elixir
  --sk-inventory 7/7 供应链对账，.PHONY 同步）；`.github/workflows/ci.yml`
  新增「ΣLang inventory reconciliation」步骤（供应链对账进 CI，在十道门禁前）
  ——供应链一致性被 CI 守护；--inventory-test 5/5、--app-smoke 44/44、Elixir
  §IN 7/7、自检 15/15、冒烟 36/36 全绿；consensus 56/56、p0 109/109，
  v0.10–v0.160 不回归。
- ✅ **REACHED v0.162 (2026-08-05)**: 批次 3 收尾（数字同步 + 全量验收）——
  v0.153–v0.162 十个连续小阶段收官：数字一致性检查通过（consensus 56/56、
  prove 125 PROVED、--domains 60/60 在门禁与代码各 4/4/1 处一致），全量验收
  全绿（sigma-accept 十道门禁 10/10、portfolio-test 5/5、inventory-test 5/5、
  stats-test 5/5、frontend-scenario 19/19、自检 15/15、Elixir §IN 7/7）——
  批次 3（30/496 小阶段）达成，按规则同步仓库；consensus 56/56、p0 109/109，
  v0.10–v0.161 不回归。
- ✅ **REACHED v0.163 (2026-08-05)**: 新增不变量 INV-SK-7—— `sigma-prove`
  `gen_socketkit_invariants` 新增 INV-SK-7 任务-契分联动链（任务 state 2→3 验收
  后契分 +10 联动），`PROVED (unsat)`；全量重验 **125 → 137 PROVED / 32 模块**
  （新联动语料持续贡献义务）；prove 数字全库同步 137 PROVED（含
  /health//panel/Rust /panel/门禁 8 期望）；sigma-accept 十道门禁 10/10、
  health-test 4/4、panel-test 5/5、stats-test 5/5、双端 44/44 全绿；
  consensus 56/56、p0 109/109，v0.10–v0.162 不回归。
- ✅ **REACHED v0.164 (2026-08-05)**: 跨域联动语料—— 新建
  `corpus/sigma_cross_domain_ok.md`（276 行，10 个 Operation：§SK 积分托管/释放 →
  §PF 开户/买入/卖出/估值/风险 → §IN 开仓/出库/水位，一条跨域链（赏金托管 →
  奖励入市 → 库存并行移动），每个含 Signature/Laws/Tests 正例 + ⊥ 负例与 4 个
  encode 函数）——三端共识 **56/56**（新模块 20/20 PASS），证明侧新模块
  31 PROVED；共识数字全库同步 56/56；sigma-accept 十道门禁 10/10、health-test
  4/4、panel-test 5/5、stats-test 5/5 全绿；consensus 56/56、p0 109/109，
  v0.10–v0.163 不回归。
- ✅ **REACHED v0.165 (2026-08-05)**: 运行时不变量复核扩展—— `sigma-runtime`
  `run_invariant_checks` 追加 v0.163 新证明的 INV-SK-7 任务-契分联动链复核
  （任务 claim→submit→accept 后 state=3，契分 +10 联动），`--domains`
  **58/58 → 60/60**——证明层新增不变量全部进运行时审计；sigma-accept 门禁 7
  期望同步 60/60、--domains 数字全库同步 60/60；trace 60/60、sigma-accept
  十道门禁 10/10 全绿；consensus 56/56、p0 109/109，v0.10–v0.164 不回归。
- ✅ **REACHED v0.166 (2026-08-06)**: README 收官总览数字同步—— README
  Status 章节新增「v0.166 收官总览」段（spec 0.7.0 / 三域 / consensus 56/56 /
  p0 109/109 / sigma-prove 171 项 PROVED（32 模块，含 INV-SK-6/PF-4/IN-5/SK-7）/
  --domains 60/60（24 项链式复核）/ 双端冒烟 44/44 / 前端剧本 19/19 / 十道门禁
  含 runtime / Elixir 三域自检（§SK 88/88、§IN 7/7、§PF 8/8）/ stats 5/5 /
  portfolio 5/5 / inventory 5/5 / 跨域联动语料进共识 / 找茬可上线 + 长期自主
  运行说明：小阶段 33/496、每 10 个同步仓库、每 100 个发布 PyPI）——README
  首页一张图看到 v0.166 全貌；consensus 56/56、p0 109/109，v0.10–v0.165
  不回归。
- ✅ **REACHED v0.167 (2026-08-06)**: Python App 三域联动剧本——
  `sigma_app.py` 新增 `--cross-domain-test`（run_cross_domain_test：§SK→§PF→§IN
  跨域 HTTP 链——找茬发单托管 escrow=100 → 奖励入市（portfolio_new 开户 +
  portfolio_buy 买入 [70,30,0]）→ 库存并行（inventory_new 开仓 + ship_stock
  出库 [6,20]），5 项逐项断言，与 sigma_cross_domain_ok 语料语义对应）；
  --cross-domain-test 5/5、--concurrency-test 4/4（run_concurrency_test 未被
  破坏）、--inventory-test 5/5、--portfolio-test 5/5、自检 15/15、冒烟 36/36
  不回归；consensus 56/56、p0 109/109，v0.10–v0.166 不回归。
- ✅ **REACHED v0.168 (2026-08-06)**: 前端三域联动演示—— `web/index.html`
  新增「三域联动演示」section + `xdChain()` JS 函数（一键跑跨域链：§SK 找茬
  发单托管 escrow=100 → §PF 开组合买入 [70,30,0] → §IN 开仓出库 [6,20]，逐步调
  /post → /portfolio_* → /inventory_* 并展示三域链结果，与 --cross-domain-test
  语义对应）——前端可视化三域联动语义；web-test 5/5、cross-domain-test 5/5、
  自检 15/15 不回归；consensus 56/56、p0 109/109，v0.10–v0.167 不回归。
- ✅ **REACHED v0.169 (2026-08-06)**: Rust 跨域链对账—— `app.rs` 冒烟新增
  「/xd pf」「/xd inv」跨域链对账项（§SK→§PF→§IN 链的 §PF 入市 [70,30,0] 与
  §IN 出库 [6,20]，与 Python --cross-domain-test 对应），`run_smoke` 44 → 46
  项；cargo build 0 warning、--app-smoke 46/46、Python --cross-domain-test 5/5
  双端对账全绿；consensus 56/56、p0 109/109，v0.10–v0.168 不回归。
- ✅ **REACHED v0.170 (2026-08-06)**: Elixir 跨域自检—— `sigma_verify.exs`
  新增 `sk_cross_domain_story`（跨域链自检 5 项：§SK 积分托管 → §PF 开户/买入 →
  §IN 开仓/出库，与 Python --cross-domain-test / 跨域语料语义对应）与 CLI
  `--sk-cross-domain` 入口；修复 xd_points_hold 断言（Elixir points_hold 原生
  函数返回 list [100,0]，非 {:ok,...} tuple——与 §PF 的 tuple 返回格式不同）——
  Elixir 四域自检齐（§SK 88/88、§IN 7/7、§PF 8/8、三域链 5/5）；consensus
  56/56、p0 109/109，v0.10–v0.169 不回归。
- ✅ **REACHED v0.171 (2026-08-06)**: Makefile/CI 补跨域测试—— `Makefile`
  新增 `cross-domain` 目标（--cross-domain-test + Rust --app-smoke 46/46 +
  Elixir --sk-cross-domain 5/5 跨域链对账，.PHONY 同步）；
  `.github/workflows/ci.yml` 新增「ΣLang cross-domain reconciliation」步骤
  （跨域链对账进 CI，在十道门禁前）——跨域一致性被 CI 守护；
  --cross-domain-test 5/5、--app-smoke 46/46、Elixir 三域链 5/5、自检 15/15、
  冒烟 36/36 全绿；consensus 56/56、p0 109/109，v0.10–v0.170 不回归。
- ✅ **REACHED v0.172 (2026-08-06)**: 批次 4 收尾（数字同步 + 全量验收）——
  v0.163–v0.172 十个连续小阶段收官：数字一致性检查通过（consensus 56/56、
  prove 137 PROVED、--domains 60/60 在门禁与代码各 4/4/1 处一致），全量验收
  全绿（sigma-accept 十道门禁 10/10、cross-domain-test 5/5、portfolio-test 5/5、
  inventory-test 5/5、stats-test 5/5、自检 15/15、Elixir 三域链 5/5）——
  批次 4（40/496 小阶段）达成，按规则同步仓库；consensus 56/56、p0 109/109，
  v0.10–v0.171 不回归。
- ✅ **REACHED v0.173 (2026-08-06)**: 新增不变量 INV-PF-5—— `sigma-prove`
  `gen_portfolio_invariants` 新增 INV-PF-5 买入-卖出链守恒（buy q 后 sell q：
  现金/份额恢复，买卖平衡链），`PROVED (unsat)`；全量重验 **137 → 171 PROVED /
  33 模块**（跨域语料持续贡献义务）；prove 数字全库同步 171 PROVED（含
  /health//panel/Rust /panel/门禁 8 期望）；sigma-accept 十道门禁 10/10、
  health-test 4/4、panel-test 5/5、cross-domain-test 5/5、双端 46/46 全绿；
  consensus 56/56、p0 109/109，v0.10–v0.172 不回归。
- ✅ **REACHED v0.174 (2026-08-06)**: 三域错误边界语料—— 新建
  `corpus/sigma_errors_ok.md`（262 行，9 个 Operation 覆盖三域全部错误路径：
  §SK quota_use 超用 ⊥ QuotaExhausted / points_withdraw 超提 ⊥ InsufficientPoints /
  task_accept 非作者 ⊥ AuthError / badge_issue 未授权 ⊥ AuthError / team_join 超员
  ⊥ TeamFull；§PF buy 现金不足 ⊥ InsufficientFunds + 未知资产 ⊥ UnknownAsset /
  sell 份额不足 ⊥ InsufficientShares；§IN ship_stock 超卖 ⊥ InsufficientStock +
  未知货品 ⊥ UnknownItem / fill_rate 除零 ⊥ DivByZero，每操作含 TypeError 边界与
  4 个 encode 函数；修 badge_issue score<0 负例——Rust/Elixir 端无 TypeError 分支
  ，删跨端不一致负例）——三端共识 **56/56**（新模块 26/26 PASS），证明侧新模块
  39 PROVED；共识数字全库同步 56/56；sigma-accept 十道门禁 10/10、health-test
  4/4、panel-test 5/5、cross-domain-test 5/5 全绿；consensus 56/56、p0 109/109，
  v0.10–v0.173 不回归。
- ✅ **REACHED v0.175 (2026-08-06)**: 运行时不变量复核扩展—— `sigma-runtime`
  `run_invariant_checks` 追加 v0.173 新证明的 INV-PF-5 买入-卖出链守恒复核
  （buy 30 后 sell 30：现金恢复 100 且份额恢复 0），`--domains` **59/59 →
  60/60**——证明层新增不变量全部进运行时审计；sigma-accept 门禁 7 期望同步
  60/60、--domains 数字全库同步 60/60；trace 59/59、sigma-accept 十道门禁 10/10
  全绿；consensus 56/56、p0 109/109，v0.10–v0.174 不回归。
- ✅ **REACHED v0.176 (2026-08-06)**: README 收官总览数字同步—— README
  Status 章节新增「v0.176 收官总览」段（spec 0.7.0 / 三域 / consensus 56/56 /
  p0 109/109 / sigma-prove 171 项 PROVED（33 模块，含 INV-SK-6/PF-4/IN-5/SK-7/
  PF-5）/ --domains 60/60（25 项链式复核）/ 双端冒烟 46/46 / 前端剧本 19/19 /
  十道门禁含 runtime / Elixir 四域自检（§SK 88/88、§IN 7/7、§PF 8/8、三域链
  5/5）/ stats/portfolio/inventory/cross-domain 5/5 / 跨域与错误边界语料进共识 /
  找茬可上线 + 长期自主运行说明：小阶段 43/496、每 10 个同步仓库、每 100 个
  发布 PyPI）——README 首页一张图看到 v0.176 全貌；consensus 56/56、p0 109/109，
  v0.10–v0.175 不回归。
- ✅ **REACHED v0.177 (2026-08-06)**: Python App 错误边界剧本——
  `sigma_app.py` 新增 `--errors-test`（run_errors_test：三域错误边界 HTTP 链
  7 项断言——§SK 超提 ⊥ InsufficientPoints 409 / 非作者验收 ⊥ AuthError 403、
  §PF 现金不足 ⊥ InsufficientFunds 409 / 未知资产 ⊥ UnknownAsset 409、§IN
  超卖 ⊥ InsufficientStock 409 / 未知货品 ⊥ UnknownItem 409 / 除零 ⊥ DivByZero
  409，与 sigma_errors_ok 语料语义对应）；顺带修复：ERROR_STATUS 补 §PF 错误
  映射（InsufficientFunds/UnknownAsset/InsufficientShares → 409）、错误剧本
  断言按任务状态机流程校准（accept 需先 claim+submit 到 state 2 才测 AuthError）；
  --errors-test 7/7、--concurrency-test 4/4、自检 15/15、冒烟 36/36 不回归；
  consensus 56/56、p0 109/109，v0.10–v0.176 不回归。
- ✅ **REACHED v0.178 (2026-08-06)**: 前端错误提示增强—— `web/index.html`
  api() 增加语义化错误映射（ERR_TEXT：16 个错误码 → 中文文案 + HTTP 状态码，
  如 InsufficientStock → "库存不足（409）"、AuthError → "无权限（403）"），
  错误横幅与操作日志显示中文语义提示（找不到映射则显示原文 + 状态码）——
  前端从"报错原文"到"看得懂为什么错"；web-test 5/5、errors-test 7/7、自检
  15/15 不回归；consensus 56/56、p0 109/109，v0.10–v0.177 不回归。
- ✅ **REACHED v0.179 (2026-08-06)**: Rust 错误边界对账—— `app.rs` 冒烟新增
  「HTTP err InsufficientFunds->409」「HTTP err UnknownAsset->409」§PF 错误边界
  对账项（与 Python --errors-test 对应；Rust error_status 对 §PF 错误走默认
  409 已对齐 Python），`run_smoke` 46 → 48 项；cargo build 0 warning、
  --app-smoke 48/48、Python --errors-test 7/7 双端对账全绿；consensus 56/56、
  p0 109/109，v0.10–v0.178 不回归。
- ✅ **REACHED v0.180 (2026-08-06)**: Elixir 错误边界自检—— `sigma_verify.exs`
  新增 `sk_errors_story`（错误边界自检 10 项：§SK 超用 ⊥ QuotaExhausted / 超提
  ⊥ InsufficientPoints / 非作者 ⊥ AuthError / 超员 ⊥ TeamFull、§PF 现金不足 ⊥
  InsufficientFunds / 未知资产 ⊥ UnknownAsset / 份额不足 ⊥ InsufficientShares、
  §IN 超卖 ⊥ InsufficientStock / 未知货品 ⊥ UnknownItem / 除零 ⊥ DivByZero，
  与 sigma_errors_ok 语料语义对应）与 CLI `--sk-errors` 入口；顺带修复 Elixir
  buy 子句顺序 bug（InsufficientFunds 子句 guard 先拦截 asset=2 的
  UnknownAsset——UnknownAsset 子句前移）——Elixir 五域自检齐（§SK 88/88、
  §IN 7/7、§PF 8/8、三域链 5/5、错误边界 10/10）；consensus 56/56、p0 109/109，
  v0.10–v0.179 不回归。
- ✅ **REACHED v0.181 (2026-08-06)**: Makefile/CI 补错误边界测试—— `Makefile`
  新增 `errors` 目标（--errors-test + Rust --app-smoke 48/48 + Elixir
  --sk-errors 10/10 错误边界对账，.PHONY 同步）；`.github/workflows/ci.yml`
  新增「ΣLang errors reconciliation」步骤（错误边界对账进 CI，在十道门禁前）
  ——错误语义一致性被 CI 守护；--errors-test 7/7、--app-smoke 48/48、Elixir
  错误边界 10/10、自检 15/15、冒烟 36/36 全绿；consensus 56/56、p0 109/109，
  v0.10–v0.180 不回归。
- ✅ **REACHED v0.182 (2026-08-06)**: 批次 5 收尾（数字同步 + 全量验收）——
  v0.173–v0.182 十个连续小阶段收官：数字一致性检查通过（consensus 56/56、
  prove 171 PROVED、--domains 60/60 在门禁与代码各 4/4/1 处一致），全量验收
  全绿（sigma-accept 十道门禁 10/10、errors-test 7/7、cross-domain-test 5/5、
  portfolio-test 5/5、inventory-test 5/5、stats-test 5/5、自检 15/15、Elixir
  错误边界 10/10）——批次 5（50/496 小阶段）达成，按规则同步仓库；consensus
  56/56、p0 109/109，v0.10–v0.181 不回归。
- ⏳ **待办队列（avatar_loop 目标来源，一天一个）**:
  1. ⏸️ P3 — Lang-Zone backend integration（§6.1，**DEFERRED**：LZ 尚在原型期，待自举稳定后再融入）。
  2. （无）— v0.182 达成（小阶段 50/496），批次 5 收官 → 同步仓库 → 批次 6（v0.183+）。

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
> stdlib only) implements ALL P0 modules; `python3 impl/python/sigma_core.py` → 60/60.

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
| P0 | **Minimal reference impl (REACHED 2026-08-02)** | ✅ `impl/python/sigma_core.py` — stdlib-only core, self-check 60/60 |
| P1 | Package manager CLI | ✅ v0.11: `tools/sigma-cli.py` (REACHED 2026-08-02) |
| P1 | 3 standard packages | ✅ v0.11: `std/math.base.md` + tests (REACHED 2026-08-02) |
| P2 | AI bootstrapping test | ✅ **REACHED 2026-08-02**: `tools/sigma-bootstrap.py` — one clean run closes the loop spec→impl→verify→pass (4 specs carry `## Implementation Checklist (for AI)`, `sigma_core.py` 60/60, `verify_p0.py` 95/95) |
| P2 | **v0.12 Novel Spec Test (REACHED 2026-08-02)** | ✅ `corpus/novel_gene_ok.md`（DNA 对齐语义, §5.2）— consensus 39/39 三端一致 + AI 闭环 |
| P3 | **v0.13 SocketKit integration (REACHED 2026-08-02)** | ✅ `spec/spec_p0_socketkit.md` + `corpus/socketkit_ok.md`（§6.2）— consensus 40/40 三端一致 |
| P3 | **v0.14 SocketKit Runtime (REACHED 2026-08-03)** | ✅ §SK 参考实现（`sigma_core.py` 75/75）+ 审计运行时（`tools/sigma-runtime.py`，obligation 日志 10/10）+ `sigma-prove` §SK 六定律 PROVED (unsat) + 负例 `corpus/socketkit_break.md`（consensus 41/41）+ §SK 进 `verify_p0.py`（109/109） |
| P3 | **v0.15 三端 §SK 执行层 (REACHED 2026-08-03)** | ✅ §SK 参考实现同步到 Rust（`src/sk.rs` + `--sk-self-check` 16/16）与 Elixir（`sigma_verify.exs` §SK + `--sk-self-check` 16/16），三端行为一致、0 warning；consensus 41/41、p0 109/109 不回退 |
| P3 | **v0.16 SocketKit 语料执行化 (REACHED 2026-08-03)** | ✅ 三端求值器 eval_expr 支持 §SK 三操作真实调用；`corpus/socketkit_ok.md` Tests 升级为真实调用（含 ⊥ 错误路径），9/9 三端一致——Law XIII 直接验证业务语义；consensus 41/41、p0 109/109、0 warning |
| P3 | **v0.17 §SK 对齐真实业务 (REACHED 2026-08-03)** | ✅ Task 4 元组 + 4 态状态机；新增 accept_task/task_submit/task_accept/credit_score；review_merge 修正为增长期定位；三端执行层同步（sigma_core 91/91、三端 §SK 32/32、socketkit_ok 24/24）；sigma-prove 18 项义务 PROVED；sigma-runtime 23/23；consensus 41/41、p0 109/109、0 warning |
| P3 | **v0.18 状态机不变量证明 (REACHED 2026-08-03)** | ✅ task_accept 作者授权（⊥ AuthError）+ §SK.3.8 不变量（INV-1 状态单调/INV-2 终态不可变/INV-3 守恒/INV-4 授权）；三端执行层同步（sigma_core 92/92、三端 §SK 33/33、socketkit_ok 25/25）；sigma-prove 23 项义务全 PROVED；sigma-runtime 31/31；consensus 41/41、p0 109/109、0 warning |
| P2 | **v0.19 第二个自举新域（金融 portfolio）(REACHED 2026-08-03)** | ✅ `spec/spec_p0_portfolio.md`（§PF 5 操作）+ `corpus/portfolio_ok.md`（19/19 三端一致）+ `portfolio_break.md`（E-02 FAIL）；三端 eval_expr 支持新域真实调用（sigma_core 111/111、0 warning）；sigma-prove 10 项 §PF 义务全 PROVED（共 33 项）；sigma-runtime 45/45；consensus 43/43、p0 109/109 |
| P3 | **v0.20 找茬五大制度补齐 (REACHED 2026-08-03)** | ✅ SK.3.9 额度制（quota_new/use/reset）+ SK.3.10 积分制（points_hold/release/withdraw）+ SK.3.11 勋章制（badge_level）；三端执行层同步（sigma_core 130/130、三端 §SK 56/56、socketkit_ok 50/50）；sigma-prove 8 项三制度义务全 PROVED（共 41 项）；sigma-runtime 60/60；consensus 43/43、p0 109/109、0 warning |
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
