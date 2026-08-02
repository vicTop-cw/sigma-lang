---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 9f2a11add43fbf12a546606fb2b962ab_be5c19678d7d11f196d8525400f8a581
    ReservedCode1: eBAEU/QhNTodqcK/qUtXrvU6s2h9FPBd/Epqv3ZB8nEduzHvwUeQSMIl1bJZYESZ35N5PxuGdcv4VJYzBcXAwCLKEQu5DjxfRXeGZq3wEUCiwzfVwC0iJNmSBwWI/emnGxnofp+kkgJNVto+5K/jiJypYWMqov1dbd/Udd7h8eQpbKjmrO7gQ52hbwA=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 9f2a11add43fbf12a546606fb2b962ab_be5c19678d7d11f196d8525400f8a581
    ReservedCode2: eBAEU/QhNTodqcK/qUtXrvU6s2h9FPBd/Epqv3ZB8nEduzHvwUeQSMIl1bJZYESZ35N5PxuGdcv4VJYzBcXAwCLKEQu5DjxfRXeGZq3wEUCiwzfVwC0iJNmSBwWI/emnGxnofp+kkgJNVto+5K/jiJypYWMqov1dbd/Udd7h8eQpbKjmrO7gQ52hbwA=
---

# ΣLang 顶层规则 — 扩展候选

> **状态**: 混合 — Law XIII–XVI 为**规范**（2026-08-01 推广）；其余条目为候选（非规范），
> 需要 RFC + Verifier 支持 + 规范采纳后方可强制执行。
> **来源**: MASTER_PLAN Phase 7 积压（2026-08-01 决定）
> **采纳路径**: RFC → 规范节 → Verifier 检查 → 测试
> **许可证**: MIT

---

## E.0 候选索引

| ID | 规则 | 拟定级别 | Verifier 可检查 | 状态 |
|----|------|---------|-----------------|------|
| E-01 | 验证器共识 | 铁律（XIII） | ✅ | ✅ **已推广** |
| E-02 | 负向测试强制 | 铁律（XIV） | ✅ | ✅ **已推广** |
| E-03 | 测试可移植性 | 元规则 | ✅ | ✅ **已推广** |
| E-04 | 导出完整性 | 铁律（XV） | ✅ | ✅ **已推广** |
| E-05 | 兼容性证明 | 铁律（XVI） | ✅ | ✅ **已推广** |
| E-06 | 内部一致性裁决 | 元规则 | ⚠️ 部分（形状检查 ✅） | ✅ **已推广**（v0.1: 签名/测试一致性） |
| E-07 | 冲突裁决流程 | 元规则 | ❌（治理） | ✅ **已推广**（§G，注册表门控） |
| E-08 | 策略包（信任/溯源、人工升级、评估确定性） | 策略 | ❌ | 候选 |
| E-09 | 概率保证 | 铁律（XVII） | ⚠️ 部分（声明 ✅） | ✅ **已推广**（v0.1: 声明检查） |
| E-10 | 评估确定性 | Law VIII 扩展 | ⚠️ 部分（声明 ✅） | ✅ **已推广**（v0.1: 声明检查） |
| P-01 | 证明携带规范结构 | 元规则（spec_top_proofs.md） | ✅ | ✅ **已强制执行** |

---

## E-01 验证器共识（已推广 — Law XIII）

### 动机

MASTER_PLAN Phase 1 声明"Verifier 是唯一权威"——但没有任何东西约束**Verifier 实现本身**。两个合规验证器（Python + Rust 已存在）可能对同一规范产生分歧，在元层面悄然重新引入跨 AI 不一致。权威必须自洽：权威本身必须与自身一致。

### 拟定规则

```md
Law XIII — Verifier Consensus
同一 spec 在任何合格 Verifier 实现上判定一致（pass/fail 一致、violations 一致）。
同一判定必须可复现：时间无关、机器无关、Verifier 实现无关。
```

### 采纳标准

- [x] 双验证器 CI 任务存在（`verify_consensus.py` — 三个验证器：Python / Rust / Elixir）
- [x] §V Verifier 架构已更新合规条款（§V.4，2026-08-01 推广）

### 验证记录（2026-08-01）

三验证器在共享语料库（18 个模块，PASS/FAIL × 3 个验证器）上达成共识：

**`🏆 E-01 验证器共识在共享语料库上确立 — 18/18 模块一致（Python == Rust == Elixir == Expected）`**

---

## E-02 负向测试强制（已推广 — Law XIV）

### 拟定规则

```md
Law — Negative Test Mandatory
每个操作至少 1 个成功用例 且 至少 1 个失败/边界用例（错误路径）。
失败用例必须断言错误值（Error 代数，§E），不得仅断言 "不崩溃"。
```

### 推广记录（2026-08-01）

E-02 现由全部三个验证器强制执行。语料库 8 个模块，三验证器一致。

---

## E-03 测试可移植性（已推广 — 元规则）

### 拟定规则

```md
Meta-rule — Test Portability
测试只依据 spec 定义的语义判定（值、错误代数、效应），
不得依赖任何实现的输出格式、内部表示或错误消息文本。
```

### 推广记录（2026-08-01）

E-03 现由全部三个验证器强制执行。13/13 模块一致。

---

## E-04 导出完整性（已推广 — Law XV）

### 拟定规则

```md
Law — Export Completeness
包的 Exports 列表与实际定义符号一一对应：
无幽灵符号（声明未定义）、无隐藏符号（定义未声明）。
```

### 推广记录（2026-08-01）

E-04 现由全部三个验证器强制执行。10/10 模块一致。

---

## E-05 兼容性证明（已推广 — Law XVI，Law VI 执行）

### 拟定规则

```md
Law — Compatibility Proof
任何声明 "向后兼容" 的新版本，必须通过旧版本的完整 canonical 测试集，
并以 Verifier 报告为证据（无新增 violation）。
```

### 推广记录（2026-08-01）

E-05 现由全部三个验证器强制执行。`## Compat Tests` 块是 `--against pkg@old` 的内联形式。35/35 模块一致。

---

## E-06 内部一致性裁决（已推广 — 元规则）

### 拟定规则

```md
Meta-rule — Internal Consistency
类型签名、定律、测试、自然语言四者冲突时：
优先级 测试 ≥ 定律 ≥ 类型签名 > 自然语言。
Verifier 应检测明显冲突（如测试输入类型与签名不符）并告警。
```

### 推广记录（2026-08-01）

已编入 `spec_p0_foundations.md` §0.1 元规则 11。16/16 模块一致。

---

## E-07 冲突裁决流程（已推广 — 元规则）

### 拟定规则

```md
Meta-rule — Conflict Adjudication
指纹冲突或语义争议的处置路径：
1. RFC 提交（冲突描述 + 双方证据）
2. 仲裁委员会评审（人工 + 双 Verifier 互证）
3. 裁决结果写入 registry（winner 保留指纹，loser 重分配）
4. 争议期旧版本保持可加载（Law VI 不因争议失效）
```

### 推广记录（2026-08-01）

现为 `spec_top_rules.md` §G 中的规范治理。

---

## E-08 策略包（候选策略）

长期稳健性需要三个非语义保证。推迟——需要外部生态系统（PKI、监控），而不仅仅是规范变更。

| ID | 策略 | 内容 | 阻塞因素 |
|----|------|------|---------|
| S-01 | 信任与溯源 | 包签名、作者身份、供应链防投毒 | **Level 1 可行**（见研究）；L2 注册表，L3 Sigstore |
| S-02 | 人工升级 | 高风险语义操作必须声明人工确认点 | 应用层策略 |
| S-03 | 评估确定性 | **→ 已推广为 E-10（2026-08-01）**：数值精度/舍入/排序稳定性声明 | — |

> S-03 已拆分并单独推广为 **E-10 — 评估确定性**（见下），因为它是该包中唯一可机检的条目。S-02 保持推迟（应用层策略）。
>
> **S-01 可行性研究已发布（2026-08-01）**：`spec/spec_pki_feasibility.md` 结论为 Level 1（作者签名，Ed25519）完全可行，纯软件实现；Level 2（注册表信任，TUF-lite）在 `sigma-pkg` 注册表后端就绪后可行；Level 3（透明日志）保持路线图。S-01 在 Level 1 **不再被 PKI 生态系统阻塞**。

### 采纳标准

- [ ] `## Signature` 块语法 RFC（spec_pki_feasibility.md F.3 Level 1）— 语法在实践中已稳定
- [x] 三个验证器实现 `check_signature`（缺失时跳过）— 23/23 一致
- [ ] 注册表 `provenance` 字段（Level 2）
- [x] PKI 可行性研究 — `spec/spec_pki_feasibility.md`（F.6）

### S-01 Level 1 实现记录（2026-08-01）

PKI 可行性研究的 Level 1（作者签名，Ed25519）现由全部三个验证器作为声明检查强制执行：`## Signature` 块必须格式良好（`signer` 非空、`pubkey_fp` 带 `sha256:` 前缀、`algorithm: ed25519`、`signature` 非空）。违规报告 `MalformedSignature(detail)`。无签名的模块仍可验证（Law VI）。

语料更新：`signature_ok.md`（PASS — 格式良好的签名）和 `signature_break.md`（FAIL — 缺 signer、错误 pubkey_fp、错误算法、空签名）。

**`🏆 共识：23/23 模块一致（Python == Rust == Elixir == Expected）`**

注意：签名值的真实密码学验证（Level 1+ 加密检查）仍是未来工作——此处仅为声明级检查，与 E-09/E-10 一致。

---

## E-09 概率保证（已推广 — Law XVII）

### 拟定规则

```md
Law XVII — Probabilistic Guarantee
预测类操作必须声明最低性能下限（指标 + 阈值 + 评测数据集）。
Verifier 仅认证：(a) 声明存在且格式良好；(b) 在声明数据集上测量结果可复现。
生产环境达标属于运行时监控职责，不由 Verifier 保证。
防作弊：数据集须为 held-out/第三方提供；指标可选 accuracy / F1 / Brier，
默认 Brier/校准误差（普通 accuracy 在失衡数据上失真）。
```

### 推广记录（2026-08-01）

全部三个验证器在**声明**级别强制执行。语料库 18/18 模块一致。

---

## E-10 评估确定性（已推广 — Law VIII 扩展）

### 动机

Law VIII（时间确定性）约束*何时*发生；数值评估还需要约束*如何*产生值。两个实现使用不同的浮点精度、舍入模式或不稳定排序，会对同一规范产生不同输出——跨实现一致性漏洞（Law XIII 领域）。

### 拟定规则

```md
Law VIII 扩展 — Evaluation Determinism
模块若执行数值/排序计算，必须声明：
- precision: 数值精度（正整数，十进制位数）
- rounding: 舍入模式（round | floor | ceil | trunc）
- sort_stability: 排序稳定性（true | false）
Verifier 仅认证声明格式良好；实际精度由实现保证并接受交叉验证（Law XIII）。
```

### 采纳标准

- [x] 三个验证器强制执行声明检查
- [x] 跨实现数值一致性运行（Law XIII 浮点输出门禁）— `float_ok.md`，21/21 一致

### 推广记录（2026-08-01）— 已推广（Law VIII 扩展）

E-10 现由全部三个验证器在**声明**级别强制执行：声明 `## Determinism` 的模块必须提供格式良好的 `precision`（正整数）、`rounding`（round|floor|ceil|trunc）和 `sort_stability`（true|false）。违规报告 `MalformedDeterminism(detail)`。

语料更新：`eval_ok.md`（PASS — precision 6 / round / true）和 `eval_break.md`（FAIL — precision 0 / banker / maybe）。

跟进（同日）：**浮点字面量已加入全部三个求值器**（`TVal::FNum` / `fnum`），`float_ok.md`（IEEE 精确小数 `0.5⊕0.25=0.75`、`0.125⊕0.875=1.0`）行使跨实现数值一致性运行（采纳标准 2）。三个验证器在这些值上逐位一致。

**`🏆 共识：21/21 模块一致（Python == Rust == Elixir == Expected）`**

副作用说明：由于 `0.333333` 现在是一等浮点字面量，E-03 可移植性语料案例已从浮点字符串改为原始 Map 渲染（`Map{scode → [p₁,p₂]}`，不可解析）以继续行使 UnportableAssertion。

---

*ΣLang 顶层规则 — 扩展候选（积压）结束*
*（内容由AI生成，仅供参考）*
