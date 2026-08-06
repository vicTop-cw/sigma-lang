# ΣLang 入门教程：从零定义一个业务域（v0.124）

> 30 分钟，只用一个命令就能跑通全流程。学完你会：
> ① 读懂一条 ΣLang 业务规则；② 自己加一条规则；③ 用三端验证 + 数学证明 +
> 一键验收确认它正确；④ 理解"规则 → 验证 → 证明 → 产品"整条链怎么走。
> 本教程用找茬业务域（§SK）演示，**所有命令可直接复制运行**。

---

## 0. 环境准备（1 分钟）

**路径 A：pip 安装（只学协议，最快，v0.137）**

```sh
pip install sigma-lang        # 已在 PyPI 发布（v0.130+）
python3 -c "import sigma_core; print(sigma_core.task_create(7, 100))"
# → [7, 100, 0, 0]
```

**路径 B：clone 仓库（完整版，含三端验证器 / 语料 / 证明工具）**

```sh
git clone https://github.com/vicTop-cw/sigma-lang.git
cd sigma-lang
python3 --version        # 需要 Python 3.8+
python3 verify_consensus.py | tail -1   # 确认基线：56/56
```

> 路径 A 只能调用 sigma_core 纯函数（本教程 §5 之后的产品部分用不到）；
> 教程 §1–§4 的验证/证明需要路径 B。Rust / Elixir 验证器不是必须——但装上
> （`cd impl/verifier && cargo build`、`elixir impl/elixir_rt/sigma_verify.exs
> --sk-self-check`）可以跑三端共识的完整版。

---

## 1. 第一步：读懂一条规则（5 分钟）

找茬的"验收"操作，在规范里长这样——打开 `spec/spec_p0_socketkit.md`：

```markdown
### SK.3.5 task_accept(task, caller)
指纹: "accept_task" 定律: [...]
语义: 任务状态 2（待验收）→ 3（已完成）；
      仅作者（caller == task[0]）可验收，否则 ⊥（AuthError）。
测试: task_accept([7,100,2,3], 7) == [7,100,3,3]
      task_accept([7,100,2,3], 5) ⊥        # 非作者验收 → 必须失败
```

**三件套**：指纹（唯一标识）/ 语义（规则）+ 测试（正例 + ⊥ 负例）。ΣLang 的
"规则"就是"语义 + 测试"成对出现——测试在跑，语义就永远被执行验证。

对应语料在 `corpus/socketkit_taskflow_ok.md`——每条测试是三个验证器都要
判一致的"考题"。

---

## 2. 第二步：自己加一条规则（10 分钟）

规则：**"验收后任务状态必须是 3（已完成）"**——听起来显然，但要让协议
"证明"它。在 `corpus/socketkit_taskflow_ok.md` 末尾加一段：

```markdown
## 验收后状态断言（教程示例）
- test: "accept 后任务已完成"
  expr: index(task_accept([7,100,2,3], 7), 2)
  expect: 3
- test: "未验收任务不能是已完成"
  expr: index(task_create(7, 100), 2)
  expect: 0
```

**先跑三端共识**（这是第一道门禁）：

```sh
python3 verify_consensus.py
# 预期：56/56 —— 新测试在三个验证器上结论一致（全绿）
```

> 如果红了：说明三端实现里有一个算出的 `index(...,2)` 不是 3——找到那个
> 实现，修它（**不许删测试**）。红 = 实现没对齐规则，不是规则错。

**再加一条"故意错的"看门禁怎么抓**（改 `expect: 3` 为 `expect: 0`）再跑：
`verify_consensus.py` 会红——三个验证器都会算出 3 ≠ 0，门禁抓到你手滑了。
改回 `3` 继续。

---

## 3. 第三步：数学证明（10 分钟）

三端验证保证"三个实现一致"，数学证明保证"规则永远不会自相矛盾"：

```sh
python3 tools/sigma-prove.py
# 预期：80 PROVED (unsat) across 29 corpus module(s)，ALL STRUCTURAL CHECKS PASS
```

sigma-prove 把每条定律编码成 z3 数学义务。`PROVED (unsat)` = "反例不存在" =
这条规则在数学上不可能被违反。你刚加的"验收后 state=3"，对应的
`INV-SK-4 state-machine-chain` 也在这里被证明。

---

## 4. 第四步：一键验收（5 分钟）

```sh
python3 tools/sigma-accept.py
# 预期：10/10 项全部通过 — ΣLang 全链路可验收
```

十道门禁一次跑完：三端共识 56/56、算法 109/109、三端自检、三域审计 67/67、
证明 80 PROVED、双端冒烟 36/36。

---

## 5. 第五步：把规则变成产品（5 分钟）

规则验证完了，产品怎么用？——**App 只委托规则，不自己重写**。看
`impl/python/sigma_app.py` 里的验收端点，本质就是一行：

```python
task = core.task_accept(app.tasks[tid], caller)   # 规则在这
```

启动完整产品验证你的规则真的生效：

```sh
python3 impl/python/sigma_app.py --launch-ready   # 环境就绪 7/7
python3 impl/python/sigma_app.py --launch         # 启动前后端
# 浏览器 http://127.0.0.1:8000 发一单→接单→提交→验收→提现
```

---

## 6. 完成检查清单

| 步骤 | 命令 | 预期 |
|------|------|------|
| 基线确认 | `python3 verify_consensus.py` | 56/56 |
| 改规则后共识 | 同上 | 仍全绿（或按 §2 红→修实现） |
| 数学证明 | `python3 tools/sigma-prove.py` | 80 PROVED |
| 一键验收 | `python3 tools/sigma-accept.py` | 10/10 |
| 产品跑起来 | `--launch-ready` + `--launch` | 7/7 + 前端可访问 |

**你现在会了**：读规则（spec + 语料三件套）→ 加规则（语义 + 测试）→
三端验证（一致）→ 数学证明（不矛盾）→ 一键验收（全绿）→ 产品委托（生效）。

---

## 7. 下一步去哪

- 想定**自己的业务域**：照 §2 把找茬换成你的业务（发单→你的操作），
  spec 格式照抄 `spec/spec_p0_socketkit.md`；
- 想了解**协议原理**：读 `README.md` 大白话导读 + `spec/`；
- 想**嵌入系统**：`docs/USAGE.md` §3（import sigma_core / HTTP）；
- 想让**别的 AI 干活**：`docs/USAGE.md` §4 的 prompt 模板直接发。
