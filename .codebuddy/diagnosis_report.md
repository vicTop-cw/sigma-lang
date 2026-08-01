# ΣLang 项目全面诊断报告

> 诊断日期: 2026-08-01 | 项目版本: v0.3.0 (MASTER_PLAN v0.4)
> 分析范围: Rust/Python/Elixir 三端验证器 + spec 规范 + corpus 测试 + tools 工具

---

## 判定等级说明

| 等级 | 含义 |
|:---:|------|
| 🔴 Critical | 功能缺失或逻辑错误，导致验证器行为不正确，影响规范的正确性保障 |
| 🟡 Medium | 设计与文档不一致、实现不完整、边界情况未覆盖 |
| 🟢 Low | 代码质量/维护性问题，不影响当前功能但需逐步改进 |

---

## 🔴 Critical 问题

### C-1. Rust `IronLaw` 枚举缺失 Laws XIII-XVII

**文件**: `impl/verifier/src/main.rs:172-186`

```rust
enum IronLaw {
    I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII,  // 仅 12 条!
}
```

**问题**: 规范 (spec_top_rules.md T.0 索引) 明确定义了 17 条铁律 (I-XVII):
- Law XIII (Verifier Consensus) — spec_top_extensions.md E-01 已 Promote
- Law XIV (Negative Test Mandatory) — E-02 已 Promote  
- Law XV (Export Completeness) — E-04 已 Promote
- Law XVI (Compatibility Proof) — E-05 已 Promote
- Law XVII (Probabilistic Guarantee) — E-09 已 Promote

虽然这些检查方法以独立函数存在 (如 `check_negative_tests`、`check_export_completeness`)，但:
1. `IronLaw` 枚举不含 XIII-XVII 变体
2. `Certification::laws_checked` 硬编码为 `12` (main.rs:783) — 应该是 `17`
3. `Verifier::laws` 向量只有 12 个元素 (main.rs:275-279)

**修复建议**: 向 `IronLaw` 枚举添加 `XIII`、`XIV`、`XV`、`XVI`、`XVII` 变体；更新 `Verifier::new()` 中的 `laws` 向量；将 `laws_checked` 改为 `17`。

---

### C-2. `has_cycle()` 始终返回 `false` — 循环依赖检测完全无效

**文件**: `impl/verifier/src/main.rs:802-806`

```rust
fn has_cycle(_graph: &HashMap<&str, Vec<&str>>) -> bool {
    // Simplified cycle detection
    // Full implementation would use DFS with recursion stack
    false
}
```

**问题**: 函数签名接收依赖图参数但用 `_` 前缀忽略，始终返回 `false`。这意味着 Law VII (Explicit Dependencies — no circular deps) 的循环依赖检查在所有 Rust 验证器运行中都形同虚设。`check_dependencies()` 虽然构造了依赖图 (main.rs:627-638)，但 `has_cycle()` 不会检测到任何环。

**对比**: Python `verify_p0.py:173-197` 的 `has_cycle()` 实现了正确的 DFS + recursion stack 算法。

**修复建议**: 用正确的 DFS + 递归栈实现替换，或直接复用 Python 版算法逻辑。

---

### C-3. `load_packages()` 是空桩 — 导入不验证

**文件**: `impl/verifier/src/main.rs:751-758`

```rust
fn load_packages(&mut self, _imports: &[Import]) -> Result<()> {
    // In the full implementation, this would:
    // 1. Resolve package names to paths
    // 2. Parse package MD files
    // 3. Verify package integrity (fingerprints, laws, tests)
    // 4. Register symbols in the global table
    Ok(())
}
```

**问题**: `Import` 被解析 (main.rs:1111-1131) 但从不验证。`self.packages` HashMap (main.rs:264) 始终保持空。当一个模块 import 了另一个包，import 的符号的 fingerprint 不会被验证，Law VII 的跨包一致性检查不存在。

**影响**: 如果你有一个 `import math.base` 但 `math.base` 不存在或有冲突，Rust 验证器不会报告任何错误。

**修复建议**: 至少实现步骤 1-2（解析 import 目标文件并验证其存在性），逐步推进到 3-4。

---

### C-4. Law VI (Backward Compatibility) 和 Law IX (Calibration) 在枚举中但无检查方法

**文件**: `impl/verifier/src/main.rs:173-186`

`IronLaw` 枚举包含 `VI` (Backward Compatibility) 和 `IX` (Calibration Requirement)，但在 `Verifier::verify()` 的验证管道 (main.rs:285-360) 中，没有对应的 `check_backward_compat()` 或 `check_calibration()` 调用。

- Law VI 要求"已发布的语义不可变" — 这需要跨版本对比，至少应检查 `version` 字段
- Law IX 要求"置信度声明与实际准确率一致" — 这需要对 `Conf` 类型符号的声明做格式校验

**修复建议**: 为 Law VI 和 IX 添加检查方法。Law VI 可以检查 `version` 是否比之前版本更高；Law IX 可以检查 `Conf` 类型符号是否有校准区间声明。

---

### C-5. 效应透明检查遗漏 `EffectType::Mixed` 变体

**文件**: `impl/verifier/src/main.rs:652-671`

```rust
fn check_effect_transparency(&mut self, module: &Module) {
    for func in &module.functions {
        // ... 检测 body_has_io ...
        let declared_io = matches!(
            func.effect_type,
            EffectType::IO | EffectType::Comm | EffectType::Net | EffectType::FS
        );
        // Missing: EffectType::Mixed
    }
}
```

**问题**: `EffectType::Mixed(Vec<EffectType>)` 表示复合效应 (如 IO+Net)，但在透明检查中被完全忽略。如果一个函数声明为 `Mixed(vec![IO, Net])`，即使 body 包含 IO 操作，`declared_io` 也会返回 `false` — 触发误报的 `UndeclaredEffect` 违规。

**修复建议**: 展开 `Mixed` 变体检查其内部效应列表中是否包含匹配的效应类型。

---

### C-6. Capability 检查只覆盖 exec/spawn，遗漏 read_file/write_file/network

**文件**: `impl/verifier/src/main.rs:674-691`

```rust
fn check_capabilities(&mut self, module: &Module) {
    for func in &module.functions {
        if func.body.contains("exec") || func.body.contains("spawn") {
            let needed = if func.body.contains("exec") {
                Capability::CmdExec
            } else {
                Capability::SpawnAgent
            };
            // ...
        }
    }
}
```

**问题**: `Capability` 枚举 (main.rs:151-157) 定义了 5 种能力: `ReadFile, WriteFile, Network, CmdExec, SpawnAgent`，但检查只覆盖了后两种。如果 body 中有 `read_file("/etc/passwd")` 或 `http_get(...)`，这些不安全的操作不会被标记为缺乏能力声明。

**修复建议**: 扩展 `check_capabilities()` 检查所有 5 种能力类型。

---

### C-7. 资源线性检查使用脆弱的字符串匹配

**文件**: `impl/verifier/src/main.rs:693-711`

```rust
fn check_resource_linearity(&mut self, module: &Module) {
    let opens = count_occurrences(&func.body, "open(");
    let closes = count_occurrences(&func.body, "close(");
    // ...
    if func.body.contains("close(r); close(r)") {
    // ...
    if func.body.contains("close(r); use(r") {
```

**问题**: 
1. 变量名硬编码为 `r` — `close(fd)` 不会被检测
2. 精确字符串匹配 `close(r); close(r)` — 即使有空格变化或换行也会漏检
3. 无真正的资源追踪 — 无法区分 `open("a"); close("a")` 和 `open("a"); open("b"); close("b")`（a 被泄露）

**修复建议**: 实现基本的资源追踪（Map<ResourceName, OpenCount>），至少按 resource 标识符追踪 open/close 配对。

---

## 🟡 Medium 问题

### M-1. MASTER_PLAN 与 corpus 文件计数不一致

**文件**: `MASTER_PLAN.md:219`

```
"20 modules × 3 verifiers Python/Rust/Elixir, 20/20 agree"
```

但 `corpus/` 目录实际包含 **21 个文件**，且 `spec_top_extensions.md` E-01 共识结果明确写的是 **"21/21 模块达成共识"**。

**修复建议**: 更新 MASTER_PLAN.md 为 "21/21 agree"。

---

### M-2. §S 遮蔽规则在规范中定义但无任何验证器实现

**文件**: `spec/spec_top_rules.md` §S

规范定义了名称遮蔽/绑定规则来防止两种 AI 代理失败模式：
1. 静默替换 (用户包未声明就重定义符号)
2. 导入顺序依赖 (`import A; import B` vs `import B; import A` 产生不同语义)

**但三端验证器 (Rust/Python/Elixir) 均未实现这些规则**。`spec_top_rules.md` 标记 §S 为"始终具有约束力"，但缺少执行机制。

**修复建议**: 在验证器中添加 §S 检查（至少检测重复符号定义和导入顺序无关性）。

---

### M-3. `verify_consensus.py` 仅比较 pass/fail 一致性，不比较 violations 内容

**文件**: `verify_consensus.py:709-712`

```python
agree = (len(verdicts) == 3
         and len(set(verdicts)) == 1
         and (exp_pass is None or verdicts[0] == exp_pass))
```

**问题**: 三个验证器可能都返回 `PASS` 或都返回 `FAIL`，但各自报告的 violations 内容可能不同（比如 Python 报告 `MissingEncoding` 而 Rust 报告 `NoLawsDeclared`）。当前的"共识"判断只看二进制的 pass/fail，不检查 violations 是否一致。

**修复建议**: 添加 violations 类型的交叉比较，至少对 FAIL 模块验证三个验证器报告了相同类别的 violations。

---

### M-4. `parse_val()` Unicode 减号替换的防御性不足

**文件**: `impl/verifier/src/main.rs:1524`

```rust
let s = s.trim().replace('−', "-");
```

Unicode 减号 `−` (U+2212) 被替换为 ASCII `-`，但这只是众多可能的 Unicode 数字变体之一。Unicode 减号 `﹣` (U+FE63) 或全角数字不会被处理。`-?` 的负号假设也会在非标准负号前失败。

**修复建议**: 使用 Unicode 规范化 (NFKD) 或将数值解析统一委托给一个成熟的数字库。

---

### M-5. Rust 验证器 `chrono_now()` 硬编码时间戳

**文件**: `impl/verifier/src/main.rs:812-815`

```rust
fn chrono_now() -> String {
    "2025-01-01T00:00:00Z".to_string()
}
```

**问题**: `Certification` 的 `timestamp` 字段始终是 "2025-01-01T00:00:00Z"，所有证书都有相同的时间戳。这使认证时间失去意义，也无法追踪验证历史。

**修复建议**: 引入 `chrono` crate 获取实际 UTC 时间。

---

### M-6. Rust SARIF 输出是空模板

**文件**: `impl/verifier/src/main.rs:842`

```rust
OutputFormat::Sarif => {
    println!("{{ \"version\": \"2.1.0\", \"runs\": [] }}");
}
```

**问题**: SARIF (Static Analysis Results Interchange Format) 输出仅打印一个空模板。`runs` 数组中不包含任何实际结果。如果被 IDE 集成（如在计划中），这会表现为"无问题"的误导结果。

**修复建议**: 填入实际的 violations 到 SARIF result 中，或标记该输出格式为 "WIP, not yet implemented"。

---

### M-7. `Capability` HashSet 始终为空 — 能力声明不被解析

**文件**: `impl/verifier/src/main.rs:1298`

```rust
Ok(Module {
    // ...
    capabilities: HashSet::new(),  // 从未被填充!
})
```

**问题**: MD 解析器从不从 `## Capabilities` 块（如果存在）中读取能力声明。因此 `check_capabilities()` 永远找不到任何已授权的能力，任何需要 CmdExec/SpawnAgent 的函数都会被错误标记为违规。

**修复建议**: 在 MD 解析器中添加 `## Capabilities` 块的解析逻辑。

---

### M-8. `verify_p0.py` 测试的是算法而非规范文件解析

**文件**: `verify_p0.py`

**问题**: 95 个测试覆盖 Time/Error/Confidence/I/O 四个模块的算法逻辑（Lamport 时钟、Result Monad、置信度运算……），但：
1. 这些测试不解析 `.md` 规范文件
2. 不检查规范中的声明与实际实现是否一致
3. 不是 "spec conformance" 而是 "algorithm correctness"

这意味着 `verify_p0.py` 和 `verify_consensus.py` 的职责有根本性差异 — 前者验证算法本身，后者验证规范一致性。

**修复建议**: 这不是 bug 而是设计差异，但需要在文档和 MASTER_PLAN 中明确区分这两种验证模式。

---

### M-9. Module 结构体 `timing_contract` 和 `capabilities` 永不从 MD 解析

**文件**: `impl/verifier/src/main.rs:1297-1298`

```rust
timing_contract: None,     // 永不设置
capabilities: HashSet::new(), // 永不设置
```

**问题**: `Module` 结构体定义了 `timing_contract` (Law VIII 所需) 和 `capabilities` (Law XI 所需)，但 MD 解析器 `parse_sigma_module()` 从不填充它们。Law VIII 检查 (`check_timing_contract`) 和 Law XI 检查 (`check_capabilities`) 实质上无法工作。

**修复建议**: 在解析器中将 `## Timing` 和 `## Capabilities` 块的处理逻辑补充完整。

---

## 🟢 Low 问题

### L-1. `erl_crash.dump` 残留文件

**文件**: `erl_crash.dump` (项目根目录)

Erlang/Elixir 运行时崩溃转储文件。应该被 `.gitignore` 排除或直接删除。

**修复建议**: 添加到 `.gitignore` 并删除。

---

### L-2. Rust 代码大量使用 `#[allow(dead_code)]`

**文件**: `impl/verifier/src/main.rs:88, 113, 128, 139, 150, 160, 193, 263, 265`

7 处 `#[allow(dead_code)]` 标注表明大量结构体字段和枚举变体未被实际使用。虽然注释说明它们"保留给完整验证器"，但这使编译警告被压制，导致无法发现真正的未使用代码。

**修复建议**: 去掉 `#[allow(dead_code)]`，对确实"保留供将来使用"的字段使用 `_` 前缀命名约定。

---

### L-3. Elixir `sigma_verify.exs` `:fnum` 类型支持已完整实现

**验证结果**: 在诊断过程中确认，Elixir 验证器 (sigma_verify.exs:619-621) 已经通过 `{:fnum, x}` 模式匹配支持浮点数类型，与 Python 和 Rust 保持一致。之前怀疑的 Elixir `:fnum` 缺失问题 **不存在**。

---

### L-4. 文件命名不统一

- `verify_p0.py` — 单一下划线
- `verify_consensus.py` — 单一下划线
- `sigma_verify.exs` — 单一下划线

所有验证文件使用一致的命名约定。此条标记为 Low 仅供参考，实际可以保持现状。

---

### L-5. `impl/verifier/src/main.rs` 单文件 1587 行

所有解析、验证、评估逻辑挤在一个文件中。虽然没有功能性问题，但随着 Law XIII-XVII 的枚举化和更多规范的添加，建议拆分为 `parser.rs`、`verifier.rs`、`evaluator.rs` 等模块。

---

## 总结统计

| 等级 | 数量 | 影响 |
|:---:|:---:|------|
| 🔴 Critical | 7 | 核心铁律检查缺失/无效/不完整 |
| 🟡 Medium | 9 | 文档不一致、边界未覆盖、实现不完整 |
| 🟢 Low | 5 | 代码质量、维护性、残留文件 |

**关键结论**: 
1. Iron Law 枚举与规范的最严重脱节 — 规范有 17 条铁律，Rust 只枚举了 12 条
2. 三个核心检查完全无效: `has_cycle()`、`load_packages()`、`Capability` 解析
3. Law VI 和 Law IX 在枚举中有定义但无对应检查方法
4. 项目整体架构合理，三验证器共识框架工作良好 (21/21)，但 Rust 生产级验证器仍处骨架阶段

---

## 修复优先级建议

| 优先级 | 修复项 | 预计工时 |
|:---:|------|:---:|
| P0 | C-1: IronLaw 枚举补全 XIII-XVII | 0.5h |
| P0 | C-2: `has_cycle()` 正确实现 | 1h |
| P0 | C-5: `Mixed` 效应处理 | 0.5h |
| P1 | C-3: `load_packages()` 基础实现 | 3h |
| P1 | C-6: 全能力检查 | 1h |
| P1 | M-7+M-9: Capability/Timing 解析 | 2h |
| P1 | C-4: Law VI/IX 检查方法 | 2h |
| P2 | M-1: 文档计数修正 | 0.1h |
| P2 | M-3: violations 内容一致性检查 | 1h |
| P2 | M-2: §S 遮蔽规则实现 | 4h |
| P3 | L-1: erl_crash.dump 清理 | 0.1h |
| P3 | L-2: 移除 dead_code 标注 | 1h |
