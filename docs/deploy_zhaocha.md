# 找茬 MVP 参考后端 — 部署与运维说明（v0.68）

> 本文档说明如何把找茬 MVP 参考后端（`impl/python/sigma_app.py` 与
> `impl/verifier/src/app.rs`）部署为可运行的 HTTP 服务。**业务规则全部委托
> ΣLang 语义（§SK/§IN），App 层只管理状态**——部署时任何"业务行为"都应与
> `tools/sigma-accept.py` 的九道门禁一致。

---

## 1. 两种形态

| 后端 | 命令 | 依赖 | 适用 |
|------|------|------|------|
| Python 参考后端 | `python3 impl/python/sigma_app.py --serve` | Python 3.10+（stdlib only） | 快速原型 / 验收 / 教学 |
| Rust 参考后端 | `cargo run -- --app-serve`（在 `impl/verifier/`） | Rust + serde_json | 生产级单二进制 |

两个后端的 HTTP 端点一致（/quota /register /me /tasks /users /post /claim
/submit /accept /withdraw /badge + 增长期 /badge_issue /dispute /team_* /advance
/ledger + 供应链 /inventory_new /receive_stock /ship_stock /stock_level
/fill_rate），业务流剧本（--scenario / --app-scenario）双端逐项一致。

---

## 2. 启动参数

### 2.1 Python 后端

```sh
# 生产启动（随机端口 0 = 自动；固定端口用 --port）
python3 impl/python/sigma_app.py --serve --port 8080

# 带状态持久化（重启不丢：每次请求后写 JSON）
python3 impl/python/sigma_app.py --serve --port 8080 --state /var/lib/zhaocha/state.json

# 带审计日志导出（每个业务动作的 ΣLang 事件，可对账）
python3 impl/python/sigma_app.py --serve --port 8080 --audit-log /var/log/zhaocha/audit.json
```

> `--state FILE` 与 `--audit-log FILE` 可同时使用；状态文件损坏时服务以空状态
> 启动（并打印告警），审计日志每次请求全量覆盖写入（JSON 数组）。

### 2.2 Rust 后端

```sh
cd impl/verifier
cargo run --release -- --app-serve --port 8080
```

> Rust 端为无状态内存版（单进程内可重启的场景用 --app-scenario 验证业务流
> 一致性；持久化形态以 Python 后端为准，语义相同）。

---

## 3. 验收检查（部署前必跑）

```sh
# 一键九道门禁（共识 / 算法 / 三端自检 / 三端编译 / 审计 / 证明 / 冒烟）
python3 tools/sigma-accept.py

# 找茬 App 专项
python3 impl/python/sigma_app.py --scenario      # CLI 完整业务流剧本 16/16
python3 impl/python/sigma_app.py --smoke         # HTTP 全链路冒烟 36/36
python3 impl/python/sigma_app.py --persist-test  # 状态持久化 10/10
python3 impl/python/sigma_app.py --audit-test    # 审计日志 5/5
cd impl/verifier && cargo run -q -- --app-scenario  # Rust 双端对账 16/16
```

> 任何一项非全绿 = 部署不应放行。门禁数字以当前 milestone 为准
> （consensus 55/55、p0 109/109、sigma-prove 62 项 PROVED）。

---

## 4. 运维要点

1. **状态文件权限**：`--state` 文件只允许运行用户读写（含用户积分/额度，
   属敏感数据）。
2. **审计日志**：`--audit-log` 是 JSON 数组，可与 `tools/sigma-runtime.py`
   的审计事件形状对账（同一批 §SK op）——建议每日归档。
3. **无外部依赖**：Python 后端仅用标准库；Rust 后端仅 serde_json。无数据库、
   无消息队列——状态即 JSON 文件，适合中小规模或作为协议验收基线。
4. **扩展方向**（超出本里程碑）：多实例状态共享需引入外部存储；鉴权（当前
   用户 id 即身份）需接 OAuth/JWT——但这些不改变 §SK 语义，App 层委托不变。
