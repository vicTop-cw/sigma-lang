# ΣLang — 贡献者指南（v0.88）

> 欢迎为 ΣLang 贡献。本项目是 **AI 原生语义协议**：规范（spec/）→ 三端验证器
> （Python / Rust / Elixir）→ 语料（corpus/）→ 证明工具（tools/）→ 参考后端
> （impl/）一体。**任何改动必须让十道门禁全绿**，这是唯一硬性要求。

---

## 1. 快速开始

```sh
# 先读这些（5 分钟）
README.md          # 新人 30 分钟上手 + 架构数据流全景
AUTOPILOT.md       # 自主维护循环与里程碑
spec/spec_p0_socketkit.md  # 找茬业务域规范（§SK）

# 跑一次完整验收（改动前先确认基线全绿）
python3 tools/sigma-accept.py --report acceptance.json   # 期望 10/10
```

---

## 2. 开发流程（一条语义的旅程）

任何新业务语义按此顺序落地（每一步都有门禁）：

1. **写规范**：`spec/spec_p0_*.md` 定义操作（指纹 / 签名 / 定律 / 测试），
   英文为准；中文参考放 `spec/zh/`。
2. **三端实现**：`impl/python/sigma_core.py`、`impl/verifier/src/sk.rs`、
   `impl/elixir_rt/sigma_verify.exs` 同步实现（参考实现 + eval_expr + 自检）。
3. **语料**：`corpus/*_ok.md` 写真实函数调用测试（每操作须含负例 ⊥ 测试），
   `*_break.md` 是 E-02 负例。
4. **证明**：`tools/sigma-prove.py` 生成 z3 义务（定律 / 跨操作不变量），
   必须 PROVED (unsat)。
5. **审计**：`tools/sigma-runtime.py` 把操作纳入审计故事线。
6. **App 委托**：`impl/python/sigma_app.py` / `impl/verifier/src/app.rs`
   的业务方法只委托 sigma_core/sk，不重实现规则。
7. **验收**：`python3 tools/sigma-accept.py` 十道门禁全绿。

> **核心原则：业务规则先以 ΣLang 语义存在并被证明，然后才是任何语言的实现**
> ——实现只是语义的投影。

---

## 3. 门禁要求（必须全绿）

```sh
python3 tools/sigma-accept.py        # 10/10：consensus 52/52 / p0 109/109 /
                                      # 三端自检与编译 / 三域审计 47/47 /
                                      # 证明 73 PROVED / 双端冒烟 36/36
python3 impl/python/sigma_app.py     # App 自检 15/15（改了 App 层才需要）
cd impl/verifier && cargo build      # 0 error / 0 warning（改了 Rust 才需要）
cd impl/elixir_rt && elixir sigma_verify.exs --sk-self-check  # 改了 Elixir 才需要
```

- **禁止**：删除 / 注释 / 弱化测试或检查来让失败消失——修复根因。
- **不回归**：任何改动不得让 v0.10 以来的门禁数字下降。

---

## 4. 提交约定

- 提交信息用 Conventional Commits：
  `feat:` / `fix:` / `docs:` / `refactor:` / `test:` + 简短描述。
- 自然语言部分用英文；代码标识符不变。
- 每次提交独立可验证（改动 + 门禁全绿的证据链）。

---

## 5. 分支 / PR

1. 从 `main` 切分支：`git checkout -b feat/your-change`。
2. 按 §2 流程实现，本地跑 `python3 tools/sigma-accept.py` 全绿。
3. 提交（见 §4），推送分支，开 PR 到 `main`。
4. CI（`.github/workflows/ci.yml`）会自动跑十道门禁 + 上传回归报告
   （acceptance.json artifact）——PR 必须 CI 全绿。

---

## 6. 常见问题

- **改了 spec 但 consensus 不过**：三端 eval_expr 未同步——按 §2 第 2 步
  补三端实现。
- **负例缺失（E-02）**：每操作至少一个 ⊥ 测试。
- **证明 DISPROVED**：定律写错或定义不满足定律——先改规范再改实现。
- **不知道从哪开始**：看 `MASTER_PLAN.md` 待办队列，或直接跑
  `python3 tools/sigma-accept.py` 找第一个红灯。
