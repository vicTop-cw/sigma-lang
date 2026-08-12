# ΣLang §SK 统一实现提示词

> 用法：把下面"提示词正文"整段复制，粘贴给每个工具（Qoder / TRAE / WorkBuddy / 其他 AI）。
> 所有工具使用**完全相同**的提示词，保证评测公平。
> 每个工具生成的报告保存为 `E:\IDEProjects\AI\sigma-lang\tests\reports\<工具名>.md`。

---

## 提示词正文（从这里开始复制）

你是 ΣLang 协议的独立实现者。请完成以下任务，这是一个跨工具一致性评测，你的实现将与
其他 AI 工具的独立实现逐项对比。

**任务步骤：**

1. 通读任务说明书：`E:\IDEProjects\AI\sigma-lang\tests\TASK_SPEC.md`
   （包含背景、实现规则、内置函数语义、业务规则速查、报告模板）
2. 通读业务规格：`E:\IDEProjects\AI\sigma-lang\spec\spec_p0_socketkit.json`
   （22 个操作的完整定义：fingerprint / signature / definition / preconditions / tests）
3. 用 Python 独立实现全部 22 个操作，保存为 `E:\IDEProjects\AI\sigma-lang\tests\reports\_impl_<工具名>.py`
4. 实现后逐条执行规格中的 60 条测试，统计通过率
5. 按 TASK_SPEC.md 第六节的报告模板，把报告写入 `E:\IDEProjects\AI\sigma-lang\tests\reports\<工具名>.md`

**硬性约束：**

- 只读 TASK_SPEC.md 和 spec_p0_socketkit.json 两个文件
- 禁止查看或参考仓库内任何已有实现（`impl/python/sigma_core.py`、`sigma_engine.py`、
  `corpus/`、`impl/verifier/`、`impl/elixir_rt/` 等）
- 错误一律用 `raise ValueError("错误名")`，错误名与规格 tests 中 `error` 字段完全一致
- 不要修改规格文件

**完成后回复我：** 你的工具名、通过率（N/60）、失败项数量（如有列出前 5 条）。

（复制结束）

---

## 替换说明

| 占位 | 替换为 |
|------|--------|
| `<工具名>` | Qoder / TRAE / WorkBuddy（或你实际使用的工具名） |
| `_impl_<工具名>.py` | 如 `_impl_Qoder.py` |
