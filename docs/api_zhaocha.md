# 找茬 MVP 参考后端 — HTTP API 文档（v0.81）

> 适用后端：`impl/python/sigma_app.py --serve` 与 `impl/verifier/src/app.rs
> --app-serve`（端点一致；业务结果双端逐项对账）。所有端点均为 GET + 查询参数，
> 返回 JSON；业务规则全部委托 ΣLang 语义（§SK/§IN），App 层只管理状态。

---

## 0. 通用约定

- **鉴权**（可选）：启动加 `--auth-token TOKEN` 后，每个请求须带
  `?token=TOKEN`，否则 `401 {"error":"AuthRequired"}`。
- **错误响应**：统一 `{"error":"<语义错误码>"}`，HTTP 状态码语义化
  （v0.54）：

| 语义错误码 | HTTP | 含义 |
|-----------|------|------|
| AuthError | 403 | 未授权 |
| TypeError / ShapeError | 422 | 参数类型/形状不符 |
| BountyErr / StateError / QuotaExhausted / InsufficientEscrow / InsufficientPoints / InsufficientStock / TeamFull / UnknownItem / DivByZero / NotTraceable | 409 | 业务状态冲突 |
| （其他 ValueError/KeyError） | 400 | 通用参数错误 |
| 未知路径 | 404 | Not Found |

- **请求/响应格式**：`GET /path?k=v&…` → `200 {"…": …}`；列表类参数（如
  `evidence=[[1,1,3],[2,1,2]]`）需 URL 编码。

---

## 1. 系统

### 1.1 GET /health — 健康检查（v0.74）

服务状态 + 配置摘要 + 门禁静态信息。

```json
{"status":"ok","app":"找茬 MVP 参考实现 (sigma_app)",
 "state":null,"auth":"disabled","log":null,
 "gates":{"consensus":"52/52","p0":"109/109","prove":"80 PROVED","scenario":"16/16"}}
```

### 1.2 GET /panel — 运行状态面板（v0.95）

运行状态 HTML 面板页：服务信息（用户数/任务数）、业务摘要（各状态任务数/
赏金总额）、门禁摘要（consensus 52/52 / p0 109/109 / prove 80 PROVED /
scenario 16/16）。
```

---

## 2. 会话（v0.52）

### 2.1 GET /register?user=&name= — 注册（幂等）

| 参数 | 说明 |
|------|------|
| user | 用户 id（即身份） |
| name | 昵称（中文需 URL 编码） |

```json
{"profile":{"name":"找茬主","joined":true}}
```

### 2.2 GET /me?user= — 会话摘要

```json
{"user":7,"profile":{"name":"找茬主","joined":true},"credit":105,"posted_tasks":[0]}
```

### 2.3 GET /users — 用户列表（v0.53）

```json
{"users":[{"user":3,"profile":{...},"credit":105,"posted_tasks":[]}, ...]}
```

---

## 3. 任务流（§SK.6 MVP）

### 3.1 GET /quota?user=&monthly= — 开户额度

```json
{"quota":[50,50]}
```

### 3.2 GET /post?author=&bounty= — 发需求（发单+扣额度+赏金托管）

```json
{"task_id":0,"task":[7,100,0,0],"quota":[50,49],"points":[100,0]}
```

### 3.3 GET /claim?task=&hunter= — 接单

```json
{"task":[7,100,1,3]}
```

### 3.4 GET /submit?task= — 提交成果

```json
{"task":[7,100,2,3]}
```

### 3.5 GET /accept?task=&caller= — 验收确认（须 caller = 作者）

```json
{"task":[7,100,3,3],"points":[0,100],"credit":105,"contribution":10}
```

### 3.6 GET /withdraw?user=&amount= — 提现

```json
{"points":[0,0]}
```

### 3.7 GET /tasks?status= — 任务列表（可状态过滤 0..3，v0.53）

```json
{"tasks":[{"task_id":0,"task":[7,100,0,0]}]}
```

### 3.8 GET /badge?user= — 契分与勋章

```json
{"credit":105,"badge":1}
```

---

## 4. 制度（§SK.3.9–3.11）

### 4.1 GET /advance?quota=[m,r] — 额度预支（v0.31）

```json
{"quota":[50,100]}
```

### 4.2 GET /ledger?entries=[[k,a,s],…] — 积分来源可追溯（v0.32）

```json
{"ledger":[[1,1,100]]}
```

---

## 5. 增长期（§SK.3.12–3.17，v0.37）

| 端点 | 参数 | 说明 |
|------|------|------|
| GET /badge_issue | verifier, user, score | 核验师签发勋章（v ≥ 1000 授权） |
| GET /dispute | evidence=[[rid,side,w],…] | 督导裁决（0/1） |
| GET /team_create | owner, kind, capacity | 受茬团(0)/找茬团(1) |
| GET /team_join | team=[o,k,s,c], member | 加入团队 |
| GET /team_share | contribs=[[m,c],…], reward | 收益按贡献分配 |

示例：`GET /badge_issue?verifier=1001&user=3&score=105` →
`{"badge":[1001,3,1]}`；`GET /dispute?evidence=[[1,1,3],[2,1,2]]` →
`{"decision":1}`。

---

## 6. 供应链（§IN，v0.45）

| 端点 | 参数 | 说明 |
|------|------|------|
| GET /inventory_new | qty_a, qty_b | 开仓 |
| GET /receive_stock | inv=[a,b], item, qty | 入库 |
| GET /ship_stock | inv=[a,b], item, qty | 出库（不超卖） |
| GET /stock_level | inv=[a,b], item | 库存水位 |
| GET /fill_rate | shipped, demanded | 履约率 |

示例：`GET /ship_stock?inv=[15,20]&item=0&qty=99` →
`409 {"error":"InsufficientStock"}`。

---

## 7. 验收清单（文档对应实现）

```sh
python3 impl/python/sigma_app.py --scenario      # CLI 业务流剧本 16/16
python3 impl/python/sigma_app.py --smoke         # HTTP 全链路 36/36（覆盖上述端点）
python3 impl/python/sigma_app.py --auth-test     # 鉴权 4/4
python3 impl/python/sigma_app.py --health-test   # /health 4/4
python3 impl/python/sigma_app.py --run-accept        # 运行验收 8/8（v0.96）
python3 impl/python/sigma_app.py --deploy-accept     # 上线验收 9/9（v0.104）
python3 impl/python/sigma_app.py --launch-test       # launch 形态 10/10（v0.94/101/102）
python3 impl/python/sigma_app.py --concurrency-test  # 并发安全 4/4（v0.103）
cd impl/verifier && cargo run -q -- --app-smoke  # Rust HTTP 冒烟对账
```

> 若某端点行为与本文档不符 → 文档或实现必有一处待修正；以
> `tools/sigma-accept.py` 九道门禁全绿为准。
