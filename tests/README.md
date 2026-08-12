# ΣLang 跨工具评测 · 操作指南

> 目标：让 Qoder / TRAE / WorkBuddy 等工具各自独立实现 ΣLang §SK 协议，
> 验证"同一份规约，不同 AI 是否产出完全一致的实现"。

## 目录结构

```
tests/
├── README.md        # 本文件（操作指南）
├── TASK_SPEC.md     # 任务说明书（发给工具的规范，含全部实现规则）
├── PROMPT.md        # 统一提示词（复制粘贴给每个工具）
└── reports/         # 各工具的报告与实现落这里
    ├── Qoder.md / _impl_Qoder.py
    ├── TRAE.md / _impl_TRAE.py
    ├── WorkBuddy.md / _impl_WorkBuddy.py
    └── （可追加其他工具）
```

## 操作步骤（你只需要做 3 件事）

1. **打开 `PROMPT.md`**，复制"提示词正文"整段
2. **分别粘贴给 Qoder / TRAE / WorkBuddy**（每个工具都用同一段提示词）
   - 工具会自行读取 TASK_SPEC.md 和 spec_p0_socketkit.json
   - 完成后它会生成报告到 `tests/reports/`
   - 如果工具读不到本地路径（如网页版），把 TASK_SPEC.md 内容贴给它
3. **三个工具都完成后告诉我**，我来汇总对比

## 各工具已完成情况（评测历史）

| 实现者 | 来源 | 方式 | 通过率 | 独立复核 |
|--------|------|------|--------|----------|
| DeepSeek（deepseek-v4-flash） | 真实 API | sigma-ai-bench 驱动 | 60/60（3 轮全对） | ✅ |
| zai（本机子代理） | Agent 集群 | 独立 Agent 读 spec JSON | 60/60 | ✅ 复跑确认 |
| Qwen3dot8Max | Qoder | 手动执行 | 60/60 | ✅ 复跑确认 |
| Seed2dot1Turbo | TRAE（字节） | 手动执行 | 60/60 | ✅ 复跑确认 |
| Hy3 | WorkBuddy（腾讯） | 手动执行 | 60/60 | ✅ 复跑确认 |

> 2026-08-12 汇总：5/5 实现者全部 60/60 一致。汇总报告见 `docs/cross_tool_report.html`。

## 一键复核（sigma-impl-verify）

新增复核脚本 `tools/sigma-impl-verify.py`，可一键复跑 `tests/reports/` 下**所有** `_impl_*.py`
（含 Qwen3dot8Max / Seed2dot1Turbo / Hy3 等），并汇总通过率，无需逐个手工运行。

```bash
# 默认: 扫描 tests/reports/ 下所有 _impl_*.py, 按 §SK spec 逐条执行 tests
python tools/sigma-impl-verify.py

# 只复核单个实现文件
python tools/sigma-impl-verify.py --impl tests/reports/_impl_Hy3.py

# 指定规格（默认 spec/spec_p0_socketkit.json）
python tools/sigma-impl-verify.py --spec path/to/spec_xxx.json
```

行为说明：
- 通过 importlib 加载实现文件，不修改任何 `_impl_*.py`；仅依赖标准库
- 判定与实现内部自检一致：`input` 中嵌套 `{"op": ...}` 先递归求值；期望 `output` 的测试比较返回值，
  期望 `error` 的测试比较错误名（ValueError 消息或异常类型名）
- 输出汇总表（实现者 / 通过率 / 失败数 / 状态）+ 每个失败实现者的前 3 条失败详情
- 退出码：所有实现者全过（当前为 60/60）时 `0`；任一实现者不足或加载失败时 `1`（可用于 CI）

## 注意事项

- 提示词已内置"禁止参考已有实现"约束；如果某个工具拒绝遵守（比如主动去读 sigma_core.py），
  在它的报告里如实记录即可，不影响评测（那本身也是信息）
- 报告生成后我可以帮你复核数字（`python tools/sigma-impl-verify.py` 一键复核全部实现者，或 `--impl` 单个复核）
- 如果你的工具无法写文件到指定路径，让它把报告内容直接输出在对话里，你复制保存即可
