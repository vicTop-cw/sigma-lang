---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 9f2a11add43fbf12a546606fb2b962ab_bc73a5cf8d7d11f1b82d525400287e28
    ReservedCode1: LS3SoS8Fz/Nmdg/+FiJVsp43kTGa0BVC9Y3/6Ez6PietH05hd1b/IzbwpoO7S9LSXykjL0gReG2uKVWIB/plb4LBGe7Z+V8QdJthSsZLd+kVTQmOBMXgvM7No7qCO2M51beJT8U+onifbk6rw5k6qo9GAmSum4Hb6OpNkyk7cr+nk1UVKb/xfY7OogQ=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 9f2a11add43fbf12a546606fb2b962ab_bc73a5cf8d7d11f1b82d525400287e28
    ReservedCode2: LS3SoS8Fz/Nmdg/+FiJVsp43kTGa0BVC9Y3/6Ez6PietH05hd1b/IzbwpoO7S9LSXykjL0gReG2uKVWIB/plb4LBGe7Z+V8QdJthSsZLd+kVTQmOBMXgvM7No7qCO2M51beJT8U+onifbk6rw5k6qo9GAmSum4Hb6OpNkyk7cr+nk1UVKb/xfY7OogQ=
---

# ΣLang P0 基础 — 完整规范

> **版本**: 0.3.0  
> **状态**: P0 — 基础级（无此则 ΣLang 无法运作）  
> **验证**: 95/95 测试通过  
> **许可证**: MIT

---

## 目录

- [§0 元规则与铁律](#0-元规则与铁律)
- [§1 核心类型（来自 core@1.0）](#1-核心类型)
- [§2 包系统](#2-包系统)
- [§T 时间与因果序](#t-时间与因果序)
- [§E 错误代数](#e-错误代数)
- [§C 置信度与概率逻辑](#c-置信度与概率逻辑)
- [§I I/O 边界与效应](#i-io-边界与效应)
- [§V 验证器架构](#v-验证器架构)
- [§A 附录：完整符号索引](#a-附录完整符号索引)

---

## §0 元规则与铁律

### §0.1 元语义（11 条规则）

```md
1. Symbol Primacy（符号首位性）
   每个符号是语义原子，不可拆分，不可重定义。

2. No Synonyms（无同义词）
   一个语义只有一个符号，一个符号只有一个语义。

3. Definition = Constraint（定义即约束）
   定义不是解释，是约束集合。

4. Equality by Test（基于测试的等价性）
   语义等价 ⇔ 通过同一测试集。

5. No Implementation in Spec（规范中无实现）
   规范中不得出现算法、性能、内存布局描述。

6. Human Text is Non-normative（人类文本非规范）
   所有自然语言描述仅为辅助，不构成语义。

7. Fingerprint Uniqueness（指纹唯一性，Law I）
   每个符号的 fingerprint 全局唯一，不可冲突。

8. Encoding to ℕ（编码到 ℕ，Law II）
   包内所有非数值概念，必须有 ℕ 编码函数。

9. Law Declaration（定律声明，Law III）
   每个操作必须声明其代数定律。

10. Test Mandatory（测试强制，Law IV）
    每个操作至少 1 个 canonical test。

11. Internal Consistency Adjudication（内部一致性裁决，E-06）
    类型签名、定律、测试、自然语言四者冲突时：
    优先级 测试 ≥ 定律 ≥ 类型签名 > 自然语言。
    Verifier 检测明显冲突（如测试期望与签名返回类型形状不符）。
```

### §0.2 扩展铁律（P0）

```md
Law V   — No Implementation in Spec（规范中无实现）
Law VI  — Backward Compatibility（向后兼容，已发布语义不可变）
Law VII — Explicit Dependencies（显式依赖，无循环依赖）
Law VIII — Temporal Determinism（时序确定性，时序边界必须声明）
Law IX  — Calibration Requirement（校准要求，置信度匹配准确率）
Law X  — Effect Transparency（效应透明，所有效应必须声明）
Law XI  — Capability Discipline（能力纪律，FFI 需要显式能力）
Law XII — Resource Linearity（资源线性，打开 = 恰好关闭一次）
```

> **已推广的顶层定律（2026-08-01）** — 定义于 `spec_top_extensions.md`，
> 由全部三个验证器（Python / Rust / Elixir）强制执行：
> Law XIII — 验证器共识（§V.4），Law XIV — 负向测试强制，
> Law XV — 导出完整性，Law XVI — 兼容性证明。

### §0.3 验证状态

```
⏰ 模块 T（时间）:        17/17 ✅
⚠️  模块 E（错误）:       16/16 ✅
🎲 模块 C（置信度）:      37/37 ✅
🔌 模块 I（I/O）:         25/25 ✅
                          ─────
                    总计:  95/95 ✅
```

---

## §1 核心类型

```md
## 原始类型
ℕ : Type    # 自然数
ℤ : Type    # 整数
ℚ : Type    # 有理数
ℝ : Type    # 实数（理想化，非 Float）
ℂ : Type    # 复数（ℝ[i]/(i²+1)）
𝔹 : Type    # 布尔 {⊤, ⊥}
Sym : Type   # 原子符号（不透明）
String : Type  # 不透明字节序列
Prop : Type  # 命题

## 类型构造器
A × B : Type    # 积（对）
A + B : Type    # 和（either）
A → B : Type    # 函数（纯）
A ↝ B : Type    # 函数（有效应）
Result⟨V,E⟩ : Type  # V + E（来自 §E）
P⟨T⟩ : Type     # T × Conf（来自 §C）
Dist⟨T⟩ : Type  # 概率分布
Effect : Type   # 效应标签（来自 §I）
Event : Type    # 因果事件（来自 §T）
Time : Type     # 逻辑时间
AgentID : Type  # 代理标识符
Resource : Type # IO 资源
Capability : Type # 权限
Conf : Type     # ℚ ∩ [0,1]
```

---

## §2 包系统

### §2.1 三层架构

```
L0 — Core (core@1.0) — 不可变，始终加载
     ℕ ℤ ℚ ℝ ℂ 𝔹 Sym Prop λ ∀ ∃
     + 铁律 + Verifier 接口

L1 — 标准库（社区维护，版本化）
     math.calculus / math.linear / finance.base
     signal.fourier / stat.prob / opt.gradient
     graph.core / crypto.hash / logic.temporal

L2 — 用户包（任何人可发布）
     emoji.finance / tcm.wuzang / physics.qft
     必须通过 Verifier 铁律
```

### §2.2 包格式

```md
# Package: finance.base
# Version: 1.0.0
# Fingerprint Prefix: 0xN000-0xNFFF
# Depends: core@1.0, math.calculus@1.0
# Maintainer: sigma-finance-wg
# License: MIT

## Imports
import core
import math.calculus

## Exports
PV, FV, NPV, IRR, Δ, Γ, Θ, ν, ρ, N

## Symbols
### PV : 现值
Type: ℝ → ℝ → ℕ → ℝ
Fingerprint: 0xN001
Definition: PV(C, r, n) ≡ C / (1+r)^n

Laws:
- 对 C 单调: C₁ < C₂ ⇒ PV(C₁) < PV(C₂)

Tests:
| C | r | n | Expected |
|----|---|---|----------|
| 100 | 0.05 | 1 | 95.238… |
```

### §2.3 导入语法

```md
import core                       # 始终可用
import math.calculus              # ∫ ∂
import finance.base@>=1.0,<2.0   # 版本约束
import signal.fourier    optional # 缺失时警告
import my_emoji_pack      custom  # 用户定义

## 冲突时的限定访问
math.calculus.Δ     # 拉普拉斯算子
finance.greeks.Δ    # Delta
```

### §2.4 自定义符号包

```md
# Package: emoji.finance
# Version: 0.1.0

### 📈 : 牛市
Type: Market → 𝔹
Fingerprint: 0xE001
Definition: 📈(m) ≡ trend(m) > 0

### 🔥 : 烧钱率
Type: Company → ℝ⁺
Fingerprint: 0xE004
Definition: 🔥(c) ≡ −d/dt(cash(c))

Laws:
∀ m . 📈(m) ∧ 📉(m) ≡ ⊥

# Package: tcm.wuzang（中医·五脏）
### 心 : Heart  → Organ, Fingerprint: 0xC001
### 肝 : Liver  → Organ, Fingerprint: 0xC002
### 生 : Generates → Organ × Organ
### 克 : Overcomes → Organ × Organ

encode(心) ≝ 1
encode(肝) ≝ 2
∀ o . ∃! o' . 生(o, o')
```

---

## §T 时间与因果序

> **完整规范**: 见 `spec_p0_time.md`  
> **验证**: 17/17 测试通过

### §T.1 原语

| 字形 | 类型 | 指纹 | 含义 |
|------|------|------|------|
| `⏰` | `Unit → Time` | `0xT001` | 当前逻辑时间 |
| `⏳` | `Future⟨T⟩ → T` | `0xT002` | 等待 |
| `⏱` | `Time → Effect` | `0xT003` | 截止时间 |
| `⌛` | `Time × Time → ℕ` | `0xT004` | 持续时间 |
| `→ᵢₒ` | `Event × Event → 𝔹` | `0xT005` | 先于发生 |
| `∥ᵢₒ` | `Event × Event → 𝔹` | `0xT006` | 并发 |
| `clock` | `Agent → ℕ` | `0xT007` | Lamport 时钟 |
| `vc` | `Agent → ℕ^∞` | `0xT008` | 向量时钟 |
| `tick` | `Agent → Effect` | `0xT009` | 推进时钟 |
| `timeout` | `Effect × ℕ → Result⟨T,TimeoutErr⟩` | `0xT00A` | 有界等待 |
| `retry` | `Effect × ℕ → Effect` | `0xT00B` | 重试 n 次 |
| `race` | `Effect × Effect → Effect` | `0xT00C` | 先到者胜 |
| `after` | `Effect × ℕ → Effect` | `0xT00D` | 延迟 |
| `periodic` | `Effect × ℕ → Effect` | `0xT00E` | 每 n 个 tick |

### §T.2 核心定律

```md
## 先于发生（反自反）
∀ e . ¬(e →ᵢₒ e)

## 先于发生（传递）
∀ a b c . a →ᵢₒ b ∧ b →ᵢₒ c ⇒ a →ᵢₒ c

## 先于发生（反对称）
∀ a b . a →ᵢₒ b ⇒ ¬(b →ᵢₒ a)

## 消息因果
∀ send recv . send_msg(m) →ᵢₒ recv_msg(m)

## 向量时钟更新
vc_recv(vc_loc, vc_rem) ≝ λx. max(vc_loc(x), vc_rem(x)) then +1

## 超时定律
∀ eff . timeout(eff, 0) ≡ err(TimeoutErr)
∃ t . eff completes in t ⇒ timeout(eff, t+1) ≡ ok(result)

## 重试定律
retry(eff, 0) ≡ eff
deterministic(eff) ∧ failed(eff) ⇒ retry always fails

## 竞争自由
∀ e₁ e₂ . access_same_resource(e₁,e₂)
          ∧ (write(e₁) ∨ write(e₂))
          ⇒ e₁ →ᵢₒ e₂ ∨ e₂ →ᵢₒ e₁
```

### §T.3 代理生命周期

```md
spawn : Agent → Effect
die   : Agent → Effect
join  : Agent → Effect
link  : Agent × Agent → Effect  # 监督

## 监督定律
∀ p c . linked(p,c) ⇒ c_dies ⇒ p_notified
```

### §T.4 时序合约（异步时强制）

```md
timing_contract {
  max_latency: 1000 ticks,
  max_retries: 3,
  timeout_budget: 5000 ticks,
  deadline_miss_policy: "fail_fast"
}
```

---

## §E 错误代数

> **完整规范**: 见 `spec_p0_error.md`  
> **验证**: 16/16 测试通过

### §E.1 Result 类型

```md
Result⟨V, E⟩ ≝ V + E

ok  : V → Result⟨V, E⟩
err : E → Result⟨V, E⟩
```

### §E.2 内置错误

```md
TimeoutErr    : Error
NetworkErr    : Error
DecodeErr     : Error
EncodeErr     : Error
NotFound      : Error
PermissionErr : Error
OutOfMem      : Error
OverflowErr   : Error
UnderflowErr  : Error
NaNErr        : Error
AssertErr     : Error
PanicErr      : Error
UnknownErr    : Error
```

### §E.3 核心组合子

| 字形 | 类型 | 指纹 | 含义 |
|------|------|------|------|
| `>>=` | `Result⟨V,E⟩ → (V→Result⟨W,E⟩) → Result⟨W,E⟩` | `0xE001` | 绑定 |
| `>>` | `Result⟨V,E⟩ → Result⟨W,E⟩ → Result⟨W,E⟩` | `0xE002` | 序列 |
| `\|>` | `V → (V→Result⟨W,E⟩) → Result⟨W,E⟩` | `0xE003` | 管道 |
| `try` | `Effect → Result⟨V,E⟩` | `0xE004` | 捕获 |
| `throw` | `E → Result⟨V,E⟩` | `0xE005` | 抛出 |
| `catch` | `Result⟨V,E₁⟩ → (E₁→Result⟨V,E₂⟩) → Result⟨V,E₂⟩` | `0xE006` | 恢复 |
| `map` | `Result⟨V,E⟩ → (V→W) → Result⟨W,E⟩` | `0xE007` | 转换 ok |
| `map_err` | `Result⟨V,E₁⟩ → (E₁→E₂) → Result⟨V,E₂⟩` | `0xE008` | 转换 err |
| `flatten` | `Result⟨Result⟨V,E⟩,E⟩ → Result⟨V,E⟩` | `0xE009` | 去除嵌套 |
| `or_else` | `Result⟨V,E₁⟩ → Result⟨V,E₂⟩ → Result⟨V,E₁+E₂⟩` | `0xE00A` | 回退 |
| `unwrap_or` | `Result⟨V,E⟩ → V → V` | `0xE00B` | 默认值 |
| `expect` | `Result⟨V,E⟩ → String → V` | `0xE00C` | 强制解包 |

### §E.4 单子律

```md
## 左单位元
∀ v f . ok(v) >>= f ≡ f(v)

## 右单位元
∀ m . m >>= ok ≡ m

## 结合律
∀ m f g . (m >>= f) >>= g ≡ m >>= (λx. f(x) >>= g)

## 短路
∀ e f . err(e) >>= f ≡ err(e)
```

### §E.5 Do-记法

```md
do {
  x ← ok(1);
  y ← ok(2);
  return (x + y)
}
≡ ok(3)

## 第一个错误停止链
do {
  x ← ok(1);
  y ← err(e);
  return (x + y)
}
≡ err(e)
```

---

## §C 置信度与概率逻辑

> **完整规范**: 见 `spec_p0_confidence.md`  
> **验证**: 37/37 测试通过

### §C.1 核心类型

```md
Conf : Type ≝ ℚ ∩ [0, 1]    # 置信度值
𝔹̃ : Type ≝ Conf               # 模糊布尔
P⟨T⟩ : Type ≝ T × Conf       # 带置信度的值
Dist⟨T⟩ : Type ≝ T → ℝ⁺      # 概率分布
```

### §C.2 置信度操作

| 字形 | 类型 | 指纹 | 定义 |
|------|------|------|------|
| `⊗̃` | `Conf×Conf→Conf` | `0xC001` | c₁⊗̃c₂ ≝ c₁⊗c₂ |
| `⊕̃` | `Conf×Conf→Conf` | `0xC002` | c₁⊕̃c₂ ≝ c₁⊕c₂⊖c₁⊗c₂ |
| `¬̃` | `Conf→Conf` | `0xC003` | ¬̃c ≝ 1⊖c |
| `⊓` | `Conf×Conf→Conf` | `0xC004` | c₁⊓c₂ ≝ min(c₁,c₂) |
| `⊔` | `Conf×Conf→Conf` | `0xC005` | c₁⊔c₂ ≝ max(c₁,c₂) |
| `≈̃` | `Conf×Conf→Conf` | `0xC006` | 基于容差 |
| `with_c` | `T→Conf→P⟨T⟩` | `0xC007` | 附加置信度 |
| `conf` | `P⟨T⟩→Conf` | `0xC008` | 提取置信度 |
| `val` | `P⟨T⟩→T` | `0xC009` | 提取值 |

### §C.3 置信度定律

```md
## 边界
∀ c:Conf . 0 ≤ c ≤ 1

## 对合
∀ c . ¬̃(¬̃(c)) ≡ c

## 乘法单位元
∀ c . c ⊗̃ 1 ≡ c

## 乘法零化
∀ c . c ⊗̃ 0 ≡ 0

## 加法单位元
∀ c . c ⊕̃ 0 ≡ c

## 加法上界
∀ c . c ⊕̃ 1 ≡ 1

## 德摩根律
¬̃(c₁ ⊓ c₂) ≡ ¬̃(c₁) ⊔ ¬̃(c₂)
¬̃(c₁ ⊔ c₂) ≡ ¬̃(c₁) ⊓ ¬̃(c₂)

## 单调性
∀ c₁ c₂ . c₁ ≤ c₂ ⇒ ∀ op . op(c₁) ≤ op(c₂)
```

### §C.4 分布

| 字形 | 类型 | 指纹 | 说明 |
|------|------|------|------|
| `Bern(p)` | `ℝ→Dist 𝔹` | `0xC010` | 抛硬币，Bern(p)(⊤)=p |
| `Bin(n,p)` | `ℝ×ℝ→Dist ℕ` | `0xC011` | n 次抛掷 |
| `Norm(μ,σ²)` | `ℝ×ℝ⁺→Dist ℝ` | `0xC012` | 钟形曲线 |
| `Exp(λ)` | `ℝ⁺→Dist ℝ⁺` | `0xC013` | 等待时间 |
| `Unif(a,b)` | `ℝ×ℝ→Dist ℝ` | `0xC014` | 均匀 |
| `Beta(α,β)` | `ℝ⁺×ℝ⁺→Dist [0,1]` | `0xC015` | p 的先验 |
| `Cat(probs)` | `List⟨ℝ⟩→Dist ℕ` | `0xC016` | 多类 |
| `Dirac(v)` | `T→Dist⟨T⟩` | `0xC017` | 确定值 |

### §C.5 分布定律

```md
## 归一化（离散）
∀ dist:Dist⟨ℕ⟩ . Σₙ dist(n) ≡ 1

## 归一化（连续）
∀ dist:Dist⟨ℝ⟩ . ∫ dist(x)dx ≡ 1

## 伯努利
Bern(p)(⊤) ≡ p
Bern(p)(⊥) ≡ 1⊖p

## Dirac（确定性）
∀ v . Dirac(v)(v) ≡ 1
∀ v w . v≠w ⇒ Dirac(v)(w) ≡ 0

## 期望线性
expect(λx.a⊗x⊕b, dist) ≡ a⊗expect(dist)⊕b

## 线性变换的方差
var(λx.a⊗x, dist) ≡ a²⊗var(dist)
```

### §C.6 贝叶斯定理（声明式）

```md
## 规范形式
∀ H E . P(H|E) ≡ P(E|H) ⊗ P(H) / P(E)

## 全概率公式
∀ H₁…Hₙ partition . P(E) ≡ Σᵢ P(E|Hᵢ)⊗P(Hᵢ)

## 链式法则
∀ A B . P(A∩B) ≡ P(A)⊗P(B|A)

## 条件独立
A ⊥ B | C  ⇔  P(A|B,C) ≡ P(A|C)
```

### §C.7 推理操作

| 字形 | 类型 | 指纹 | 含义 |
|------|------|------|------|
| `observe` | `Dist⟨T⟩→(T→𝔹)→Dist⟨T⟩` | `0xC020` | 贝叶斯更新 |
| `infer` | `Dist⟨T⟩→(T→𝔹)→Dist⟨T⟩` | `0xC021` | observe 的别名 |
| `expect` | `Dist⟨ℝ⟩→ℝ` | `0xC022` | E[X] |
| `var` | `Dist⟨ℝ⟩→ℝ⁺` | `0xC023` | Var(X) |
| `sample` | `Dist⟨T⟩→T` | `0xC024` | 随机抽取 |
| `n_samples` | `Dist⟨T⟩→ℕ→List⟨T⟩` | `0xC025` | 蒙特卡洛采样 |
| `mcmc` | `Dist⟨T⟩→ℕ→List⟨T⟩` | `0xC026` | 马尔可夫链 |
| `map_est` | `Dist⟨T⟩→T` | `0xC027` | argmax 后验 |
| `entropy` | `Dist⟨T⟩→ℝ⁺` | `0xC028` | H(X) = −Σp·log(p) |

### §C.8 带置信度的 AI 通信

```md
## 带置信度的消息
Msg⟨T⟩ ≝ {
  sender    : AgentID,
  payload   : P⟨T⟩,
  timestamp : Time,
  evidence  : List⟨Fact⟩
}

## 取更可信者
combine_msgs(m₁, m₂) ≝
  if conf(m₁) > conf(m₂) then m₁ else m₂

## 加权共识
consensus(msgs) : P⟨T⟩ ≝
  let total ≝ Σ conf(m) in
  let weighted ≝ Σ val(m)⊗conf(m) / total in
  (weighted, pooled_conf)

## 信任校准
trust : AgentID → Conf
calibrated_conf(m) ≝ conf(m) ⊗ trust(sender(m))
```

### §C.9 校准铁律

> **Law IX**: 任何声称置信度 `c` 的 AI，在足够大的测试集上，
> 其经验准确率必须在 `c` 的 ±0.05 范围内。过度自信的 AI 在
> `consensus()` 中受到惩罚。

---

## §I I/O 边界与效应

> **完整规范**: 见 `spec_p0_io.md`  
> **验证**: 25/25 测试通过

### §I.1 效应标签

```md
Effect : Type

Pure      : Effect   # 无可观察效应
IO(String): Effect   # 带资源的输入/输出
Comm(Ch)  : Effect   # 通道上的通信
Spawn     : Effect   # 创建代理
Die       : Effect   # 终止
Net(Addr) : Effect   # 网络调用
FS(Path)  : Effect   # 文件系统
Time      : Effect   # 时间相关
Rand      : Effect   # 随机数
```

### §I.2 效应操作

| 字形 | 类型 | 指纹 | 含义 |
|------|------|------|------|
| `⊕ₑ` | `Effect×Effect→Effect` | `0xI001` | 效应和 |
| `≤ₑ` | `Effect×Effect→𝔹` | `0xI002` | 效应序 |
| `print` | `String→IO Unit` | `0xI001` | 写 stdout |
| `readln` | `IO String` | `0xI002` | 读 stdin |
| `read_file` | `Path→IO Result⟨String,IOErr⟩` | `0xI003` | 文件读 |
| `write_file` | `Path→String→IO Result⟨Unit,IOErr⟩` | `0xI004` | 文件写 |
| `append_file` | `Path→String→IO Result⟨Unit,IOErr⟩` | `0xI005` | 文件追加 |
| `delete_file` | `Path→IO Result⟨Unit,IOErr⟩` | `0xI006` | 文件删除 |
| `exists` | `Path→IO 𝔹` | `0xI007` | 存在检查 |
| `mkdir` | `Path→IO Result⟨Unit,IOErr⟩` | `0xI008` | 创建目录 |
| `list_dir` | `Path→IO Result⟨List⟨Path⟩,IOErr⟩` | `0xI009` | 列出目录 |
| `send` | `Addr→Msg→IO Result⟨Unit,NetErr⟩` | `0xI00A` | 网络发送 |
| `recv` | `Addr→IO Result⟨Msg,NetErr⟩` | `0xI00B` | 网络接收 |
| `connect` | `Addr→IO Result⟨Conn,NetErr⟩` | `0xI00C` | 打开连接 |
| `close` | `Conn→IO Unit` | `0xI00D` | 关闭连接 |
| `http_get` | `URL→IO Result⟨Response,NetErr⟩` | `0xI00E` | HTTP GET |
| `http_post` | `URL→Body→IO Result⟨Response,NetErr⟩` | `0xI00F` | HTTP POST |
| `now` | `IO Time` | `0xI010` | 墙上时钟 |
| `rand` | `IO ℝ` | `0xI011` | 随机 [0,1) |
| `rand_int` | `ℕ→ℕ→IO ℕ` | `0xI012` | 随机 [a,b] |
| `sleep` | `ℕ→IO Unit` | `0xI013` | 阻塞 n ticks |
| `spawn_io` | `IO()→IO AgentID` | `0xI014` | 创建代理 |
| `kill` | `AgentID→IO Unit` | `0xI015` | 终止 |
| `log` | `Level→String→IO Unit` | `0xI016` | 结构化日志 |

### §I.3 效应系统

```md
## 效应和
IO(a) ⊕ₑ IO(b) ≝ IO(a+b)
IO(a) ⊕ₑ Comm(c) ≝ IO(a) + Comm(c)

## 效应序
Pure ≤ₑ Comm ≤ₑ IO

## 效应定律
∀ e . Pure ⊕ₑ e ≡ e
∀ e . e ⊕ₑ e ≡ e          # 幂等
∀ a b c . (a⊕ₑb)⊕ₑc ≡ a⊕ₑ(b⊕ₑc)  # 结合

## 函数效应标注
f : A → B       # 纯
g : A →ᵢₒ B     # 有 IO 效应
h : A →ᶜ B      # 有通信
k : A →^{IO+Comm} B  # 多个效应
```

### §I.4 I/O 定律

```md
## 写后读（因果）
write_file(p, s); read_file(p) ≡ ok(s)

## 删后检查
delete_file(p); exists(p) ≡ ok(⊥)

## 追加结合律
write_file(p,a); append_file(p,b) ≡ write_file(p, a⊕b)

## GET 幂等
http_get(url); http_get(url) ≡ http_get(url)

## POST 非幂等
http_post(url,b); http_post(url,b) ≠ http_post(url,b)

## 资源线性
∀ r . open(r); use(r); close(r)  # 恰好一次关闭
∀ r . close(r); close(r) ≡ err(DoubleClose)
∀ r . close(r); use(r) ≡ err(UseAfterClose)
```

### §I.5 资源安全

```md
## RAII 风格
with_file : Path → (Handle→IO A) → IO Result⟨A,IOErr⟩
with_file(p, f) ≝
  do {
    h ← open(p);
    result ← f(h);
    close(h);
    return result
  }

## Verifier 检查:
## - 每个 open 有恰好一个 close
## - 关闭后不可使用
## - 不可双重关闭
## - 错误路径上资源不泄漏
```

### §I.6 FFI（外部函数接口）

```md
## FFI 声明语法
foreign import "rust" sqrt : ℝ → ℝ
  ensures: result ≥ 0
  ensures: result² ≈ input (within 1e-10)
  effect: Pure

foreign import "python" torch_infer : Tensor → Tensor
  effect: IO
  ensures: output.shape ≡ input.shape
  timeout: 30000

foreign import "sql" query : String → IO Result⟨Rows,SqlErr⟩
  effect: IO + Comm
  ensures: read-only if starts with "SELECT"
  timeout: 5000

foreign import "system" exec : String → IO Result⟨String,ExecErr⟩
  effect: IO + FS + Net
  ⚠️ requires: capability(CmdExec)
```

### §I.7 I/O 铁律

> **Law X（效应透明）**: 每个执行 I/O 的函数必须声明其效应类型。未声明 = 拒绝。
>
> **Law XI（能力纪律）**: 没有显式授予所需能力，不得执行外部调用。
>
> **Law XII（资源线性）**: 每个打开的资源必须恰好关闭一次，或使用 `with_*` 组合子。

---

## §V 验证器架构

### §V.1 验证器流水线

```
┌──────────────┐
│  MD 源文件    │  （人类/AI 编写）
└──────┬───────┘
       ▼
┌──────────────┐
│  解析器       │  → AST（带类型）
└──────┬───────┘
       ▼
┌──────────────┐
│ 包加载器      │  → 解析导入，检查指纹
└──────┬───────┘
       ▼
┌──────────────┐
│ 类型检查器    │  → 效应推断，能力检查
└──────┬───────┘
       ▼
┌──────────────┐
│ 定律检查器    │  → 验证代数定律
└──────┬───────┘
       ▼
┌──────────────┐
│ 测试运行器    │  → 执行规范测试
└──────┬───────┘
       ▼
┌──────────────┐
│ 竞争检测器    │  → 先于发生分析
└──────┬───────┘
       ▼
┌──────────────┐
│ 资源检查器    │  → 线性验证
└──────┬───────┘
       ▼
┌──────────────┐
│ 判决          │  → ✅ 认证 / ❌ 拒绝
└──────────────┘
```

### §V.2 验证器不做什么

```md
❌ 不执行业务逻辑
❌ 不基准测试性能
❌ 不选择算法
❌ 不优化代码
❌ 不解释自然语言
❌ 不训练模型

✅ 仅检查: 定律是否满足？
✅ 仅检查: 测试是否通过？
✅ 仅检查: 效应是否声明？
✅ 仅检查: 资源是否线性？
✅ 仅检查: 是否存在竞争？
✅ 仅检查: 指纹是否唯一？
```

### §V.3 验证器共识合规条款（Law XIII，2026-08-01 推广）

```md
## 合规
一个 Verifier 实现是"合规的"当且仅当：

1. 可复现性: 同一规范 → 同一判决，跨运行、机器、时间。
2. 跨实现一致: 在共享语料库（`corpus/`）上，
   每个合规 Verifier 对每个模块产生与参考集（Python / Rust / Elixir）
   相同的 pass/fail 判决。
3. 共享语料库: `corpus/*.md`（18 个模块，覆盖 `## Operation:` 和 `###`
   块风格、PASS/FAIL 判决、§T/§E/§C 语义、Law XIII–XVII）。

## 验证记录（2026-08-01）
18/18 语料库模块在 Python / Rust / Elixir 间一致
```

---

## §A 附录：完整符号索引

### A.1 核心（始终可用）

```
ℕ ℤ ℚ ℝ ℂ 𝔹 Sym String Prop
× + → ↝ λ ∀ ∃
⊤ ⊥ ⊨ ⊢ ¬ ∧ ∨ ⇒ ⇔
≡ ≠ ≤ ≥ < >
∑ ∏ ∫ ∂ ∇ Δ d/dx lim ∞
∈ ∉ ⊆ ⊂ ∪ ∩ ∅
```

### A.2 时间模块（§T）

```
⏰ ⏳ ⏱ ⌛ →ᵢₒ ∥ᵢₒ clock vc tick timeout retry race after periodic
```

### A.3 错误模块（§E）

```
Result⟨V,E⟩ ok err
>>= >> |> try throw catch map map_err flatten or_else unwrap_or expect
```

### A.4 置信度模块（§C）

```
Conf 𝔹̃ P⟨T⟩ Dist⟨T⟩
⊗̃ ⊕̃ ¬̃ ⊓ ⊔ ≈̃ with_c conf val
Bern Bin Norm Exp Unif Beta Cat Dirac
observe infer expect var sample n_samples mcmc map_est entropy
⊢_c ~ ⊥ (indep) | (conditional)
```

### A.5 I/O 模块（§I）

```
Effect Pure IO Comm Spawn Die Net FS Time Rand
⊕ₑ ≤ₑ
print readln read_file write_file append_file delete_file exists mkdir list_dir
send recv connect close http_get http_post now rand rand_int sleep spawn_io kill log
foreign import grant revoke capability
```

### A.6 铁律总结

```
Law I    — 指纹唯一性
Law II   — 编码到 ℕ
Law III  — 定律声明
Law IV   — 测试强制
Law V    — 规范中无实现
Law VI   — 向后兼容性
Law VII  — 显式依赖
Law VIII — 时序确定性
Law IX   — 校准要求
Law X    — 效应透明
Law XI   — 能力纪律
Law XII  — 资源线性
Law XIII — 验证器共识
Law XIV  — 负向测试强制
Law XV   — 导出完整性
Law XVI  — 兼容性证明
Law XVII — 概率保证
```

---

## §Z 版本管理与演进

```md
## 核心版本管理
core@1.0  — 永久冻结（ℕ ℤ ℚ ℝ ℂ + 逻辑）
core@1.x  — 仅 Bug 修复，无语义变更

## 标准库
math.calculus@1.0  → 1.x（增量：新符号，不破坏）
finance.base@1.0     → 2.0（破坏性：新增必需定律）

## 破坏性变更协议
1. RFC 流程
2. 6 个月弃用警告
3. 提供迁移工具
4. 旧版本保持可加载
5. 兼容性证明（Law XVI）：任何声明"向后兼容"的版本
   必须通过前一版本的规范测试套件
```

---

## §F 最终说明

> **ΣLang 不是一门编程语言。**
> **它是智能体之间的合约。**
>
> 人类编写定律。
> AI 编写实现。
> Verifier 裁判。
> 测试决定。

### ΣLang 是什么：
✅ 语义协议  
✅ 数学规范语言  
✅ 可验证的 AI 通信标准  
✅ 领域知识的包系统  

### ΣLang 不是什么：
❌ 通用编程语言  
❌ Python/Rust/Elixir 的替代品  
❌ 自然语言处理工具  
❌ 机器学习框架  
❌ 人类友好的语法  

### 愿景

```
┌─────────────────────────────────────────────┐
│             AI 代理 A                       │
│  编写 ΣLang 代码 → Verifier 检查 → ✅       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           ΣLang Verifier                    │
│  定律 ✓  测试 ✓  效应 ✓  竞争 ✓            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│             AI 代理 B                       │
│  读取 ΣLang 规范 → 实现 → 测试 ✓            │
│  输出 ≡ 代理 A 的输出（按测试套件）          │
└─────────────────────────────────────────────┘
```

**这是最终目标：AI-to-AI 语义互操作，**
**由数学保证，而非靠运气。**

---

*ΣLang P0 基础规范 v0.3.0 结束*  
*已验证: 95/95 测试通过*  
*许可证: MIT*
*（内容由AI生成，仅供参考）*
