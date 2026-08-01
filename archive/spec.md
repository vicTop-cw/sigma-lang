# ΣLang — AI-Native Semantic Protocol

> **Version**: 0.1 (Initial Draft)
> **Status**: Experimental
> **License**: MIT
> **Tagline**: One symbol, one meaning, one result — across all models.

---

## Table of Contents

1. [Meta-Semantics](#1-meta-semantics)
2. [Core Philosophy](#2-core-philosophy)
3. [Type System](#3-type-system)
4. [Semantic Atoms (Symbol Registry)](#4-semantic-atoms-symbol-registry)
5. [Mathematical Symbols (Inherited)](#5-mathematical-symbols-inherited)
6. [Borrowed Symbols (From Existing Languages)](#6-borrowed-symbols-from-existing-languages)
7. [Algebraic Laws & Contracts](#7-algebraic-laws--contracts)
8. [Ownership & Dataflow Semantics](#8-ownership--dataflow-semantics)
9. [Encoding Principle (Everything → ℕ)](#9-encoding-principle-everything--ℕ)
10. [Function & Control Semantics](#10-function--control-semantics)
11. [Verification Rules](#11-verification-rules)
12. [Surface Syntax (Markdown as AST)](#12-surface-syntax-markdown-as-ast)
13. [Canonical Test Suite](#13-canonical-test-suite)
14. [Backend Interface (Rust / Elixir / Julia)](#14-backend-interface)
15. [Non-Goals & Explicit Rejections](#15-non-goals--explicit-rejections)
16. [Versioning & Evolution](#16-versioning--evolution)
17. [Glossary](#17-glossary)

---

## 1. Meta-Semantics

The following rules are **absolute** and **non-negotiable**. They constitute the "constitution" of ΣLang. Every other rule in this document is subordinate to these.

| # | Rule | Description |
|---|------|-------------|
| M1 | **Symbol Primacy** | Every symbol is a semantic atom. It cannot be split, redefined, or overloaded outside its registered meaning. |
| M2 | **No Synonyms** | One semantic concept ⇒ one symbol. One symbol ⇒ one semantic concept. Bidirectional uniqueness. |
| M3 | **Definition = Constraint** | A definition is not an explanation. It is a set of constraints that all implementations must satisfy. |
| M4 | **Equality by Test** | Two implementations are semantically equivalent **iff** they produce identical outputs for all canonical tests. |
| M5 | **No Implementation in Spec** | The specification MUST NOT contain algorithms, performance hints, memory layouts, or execution strategies. |
| M6 | **Human Text is Non-Normative** | All natural-language prose in this document is advisory. Only formal definitions, laws, and tests are normative. |
| M7 | **Determinism Mandatory** | Non-determinism, randomness, and undefined behavior are **forbidden** in the core language. |
| M8 | **Open Encoding** | Any external concept (strings, dates, names) MAY be used **only after** a deterministic mapping to ℕ is defined. |
| M9 | **Verifier Supremacy** | The Verifier is the sole authority for semantic correctness. No AI, compiler, or runtime may override it. |
| M10 | **Backward Compatibility of Atoms** | Once a semantic atom is registered, its meaning is **immutable** for the lifetime of the language. Deprecation ≠ redefinition. |

---

## 2. Core Philosophy

ΣLang is not designed for humans to write comfortably. It is designed for AI systems to communicate with **zero ambiguity** and **provable consistency**.

### 2.1 Design Priorities (Ordered)

1. **Semantic Precision** — Every construct has exactly one meaning.
2. **Verifiability** — Every claim can be checked by a mechanical process.
3. **Mathematical Foundation** — All semantics reduce to mathematical objects.
4. **Implementation Freedom** — How a result is computed is irrelevant; only the result matters.
5. **AI Readability** — Symbols are chosen for unambiguous parsing by language models.
6. **Human Readability** — Secondary concern; achieved through clear mapping tables and MD structure.

### 2.2 What ΣLang Is

- A **semantic contract** between AI systems
- A **deterministic protocol** for computation
- A **mathematical specification language** with built-in verification
- A **Markdown-native** format where the document IS the source code

### 2.3 What ΣLang Is Not

- Not a systems programming language
- Not a scripting language
- Not a replacement for Python, Rust, or Julia
- Not designed for interactive human use
- Not a general-purpose computing platform

---

## 3. Type System

### 3.1 Primitive Types

| Type | Symbol | Description | Examples |
|------|--------|-------------|---------|
| Natural numbers | `ℕ` | Non-negative integers (mathematical, infinite precision) | 0, 1, 2, … |
| Integers | `ℤ` | All integers (mathematical, infinite precision) | …, −2, −1, 0, 1, … |
| Rational numbers | `ℚ` | Ratios of integers (exact arithmetic) | 1/2, −3/4, 22/7 |
| Real numbers | `ℝ` | Abstract real numbers (idealized, no precision specified) | π, e, √2 |
| Booleans | `𝔹` | Two-valued logic | `⊤` (true), `⊥` (false) |
| Symbols | `Sym` | Opaque, atomic identifiers | `msg₁`, `err_timeout` |
| Propositions | `Prop` | Truth values in logic | `P`, `Q`, `x > 0` |

### 3.2 Type Constructors

| Constructor | Symbol | Meaning | Example |
|-------------|--------|---------|---------|
| Product | `A × B` | Pair of A and B | `ℝ × ℝ` (a 2D point) |
| Sum | `A + B` | Either A or B | `T + Unit` (Option) |
| Function | `A → B` | Pure function from A to B | `ℕ → ℕ` |
| Effectful function | `A ↝ B` | Function with side effects | `Query ↝ Result` |
| Parametric | `T⟨P⟩` | Type parameterized by P | `List⟨ℕ⟩` |
| Dependent | `(x:A) → B(x)` | Function where return type depends on input value | — |
| Unit | `Unit` | Single-inhabitant type | `()` |
| Bottom | `∅` | Uninhabited type (never returns) | — |

### 3.3 Type Judgements

```
x : T        # x is of type T
T : Type     # T is a type
⊢ P          # P is provable
Γ ⊢ e : T    # Under context Γ, expression e has type T
```

### 3.4 Type Equivalence

Two types are equivalent (`A ≡ B`) iff:
- They are the same primitive type, OR
- They are constructed from equivalent types using the same constructor, OR
- A definitional equality has been established (see §7)

---

## 4. Semantic Atoms (Symbol Registry)

This is the **immutable core** of ΣLang. Each entry, once registered, is permanent.

### 4.1 Logic & Truth

| Glyph | Name | Semantic Class | Fingerprint | Notes |
|-------|------|---------------|-------------|-------|
| `⊤` | Top / True | Boolean value | `0xA001` | Always true proposition |
| `⊥` | Bottom / False | Boolean value | `0xA002` | Always false; also failure |
| `¬` | Negation | Unary logical | `0xA003` | `¬⊤ ≡ ⊥` |
| `∧` | Conjunction | Binary logical | `0xA004` | AND, associative, commutative |
| `∨` | Disjunction | Binary logical | `0xA005` | OR, associative, commutative |
| `⊃` | Implication | Binary logical | `0xA006` | `P ⊃ Q` ≡ `¬P ∨ Q` |
| `≡` | Equivalence | Equality | `0xA007` | Definitional equality |
| `≠` | Inequality | Equality | `0xA008` | `a ≠ b` ≡ `¬(a ≡ b)` |
| `∀` | Universal quantifier | Quantifier | `0xA009` | For all |
| `∃` | Existential quantifier | Quantifier | `0xA00A` | There exists |
| `⊢` | Provability | Meta-logical | `0xA00B` | Turnstile |
| `⊨` | Entailment | Meta-logical | `0xA00C` | Semantic entailment |
| `∴` | Therefore | Meta-logical | `0xA00D` | Conclusion marker |

### 4.2 Arithmetic & Algebra

| Glyph | Name | Semantic Class | Fingerprint | Laws |
|-------|------|---------------|-------------|------|
| `+` | Addition | Binary ℕ×ℕ→ℕ | `0xB001` | Associative, commutative, has identity 0 |
| `−` | Subtraction | Binary ℤ×ℤ→ℤ | `0xB002` | Partial on ℕ; total on ℤ |
| `×` or `·` | Multiplication | Binary ℕ×ℕ→ℕ | `0xB003` | Associative, commutative, distributes over `+` |
| `÷` | Division | Binary ℚ×ℚ→ℚ | `0xB004` | Partial (no division by 0); total on ℚ |
| `^` | Exponentiation | Binary ℝ×ℝ→ℝ | `0xB005` | `a^0 ≡ 1`, `a^(b+c) ≡ a^b × a^c` |
| `√` | Square root | Unary ℝ→ℝ | `0xB006` | `√(a×a) ≡ a` for a ≥ 0 |
| `|a|` | Absolute value | Unary ℝ→ℝ | `0xB007` | `|a| ≥ 0` |
| `sgn` | Sign | Unary ℝ→ℤ | `0xB008` | −1, 0, or 1 |

### 4.3 Order & Comparison

| Glyph | Name | Semantic Class | Fingerprint | Notes |
|-------|ower|---------------|-------------|-------|
| `<` | Less than | Binary ℕ×ℕ→𝔹 | `0xC001` | Strict partial order |
| `>` | Greater than | Binary ℕ×ℕ→𝔹 | `0xC002` | `a > b` ≡ `b < a` |
| `≤` | Less or equal | Binary ℕ×ℕ→𝔹 | `0xC003` | `a ≤ b` ≡ `a < b ∨ a ≡ b` |
| `≥` | Greater or equal | Binary ℕ×ℕ→𝔹 | `0xC004` | `a ≥ b` ≡ `b ≤ a` |
| `min` | Minimum | Binary ℕ×ℕ→ℕ | `0xC005` | Returns lesser of two |
| `max` | Maximum | Binary ℕ×ℕ→ℕ | `0xC006` | Returns greater of two |

### 4.4 Algebraic Operations (Semantic Slots)

These are **not** tied to specific types. They define algebraic contracts.

| Glyph | Name | Contract | Fingerprint | Required Laws |
|-------|------|----------|-------------|---------------|
| `⊕` | Sum / Join | Associative binary | `0xD001` | Associativity; optionally commutative |
| `⊗` | Product / Meet | Associative binary | `0xD002` | Associativity; distributes over `⊕` |
| `⊛` | Monoidal combine | Associative + identity | `0xD003` | Associativity + identity element |
| `⊜` | Structural equivalence | Equality with structure | `0xD004` | Reflexive, symmetric, transitive |
| `∘` | Composition | Function composition | `0xD005` | `(f ∘ g)(x) ≡ f(g(x))` |

### 4.5 Set & Collection

| Glyph | Name | Semantic Class | Fingerprint | Notes |
|-------|------|---------------|-------------|-------|
| `∈` | Element of | Membership | `0xE001` | `x ∈ S` |
| `∉` | Not element of | Membership | `0xE002` | `x ∉ S` ≡ `¬(x ∈ S)` |
| `∪` | Union | Binary set op | `0xE003` | `A ∪ B` |
| `∩` | Intersection | Binary set op | `0xE004` | `A ∩ B` |
| `∖` | Set difference | Binary set op | `0xE005` | `A ∖ B` |
| `⊆` | Subset | Binary relation | `0xE006` | `A ⊆ B` |
| `|S|` or `#S` | Cardinality | Unary | `0xE007` | Number of elements |

### 4.6 Lambda Calculus & Functions

| Glyph | Name | Semantic Class | Fingerprint | Notes |
|-------|------|---------------|-------------|-------|
| `λ` | Lambda abstraction | Function creation | `0xF001` | `λx. body` |
| `→` | Function type | Type constructor | `0xF002` | `A → B` |
| `↝` | Effectful function | Type constructor | `0xF003` | `A ↝ B` |
| `π₁` | First projection | Product elim | `0xF004` | `π₁(a,b) ≡ a` |
| `π₂` | Second projection | Product elim | `0xF005` | `π₂(a,b) ≡ b` |
| `inject₁` | Left injection | Sum intro | `0xF006` | Into `A + B` |
| `inject₂` | Right injection | Sum intro | `0xF007` | Into `A + B` |
| `case` | Case analysis | Sum elim | `0xF008` | Pattern match on sum |
| `∘` | Composition | Function op | `0xF009` | See §4.4 |

### 4.7 Control Flow & Computation

| Glyph | Name | Semantic Class | Fingerprint | Notes |
|-------|------|---------------|-------------|-------|
| `⏳` | Async / Suspend | Effect marker | `0xG001` | Marks suspension point |
| `∥` | Parallel | Composition | `0xG002` | Parallel evaluation |
| `;` | Sequential | Composition | `0xG003` | Sequential evaluation |
| `if_then_else` | Conditional | Control | `0xG004` | `if P then A else B` |
| `fold` | Fold / Reduce | Recursion | `0xG005` | `fold(⊕, z, [a,b,c]) ≡ a⊕b⊕c` |
| `map` | Map | Transformation | `0xG006` | `map(f, [a,b]) ≡ [f(a), f(b)]` |
| `filter` | Filter | Selection | `0xG007` | Keep elements satisfying predicate |
| `Σ` | Summation | Aggregation | `0xG008` | `Σ_{i∈S} f(i)` |
| `Π` | Product (Π) | Aggregation | `0xG009` | `Π_{i∈S} f(i)` |

### 4.8 Ownership & Memory (Borrowed from Rust)

| Glyph | Name | Semantic Class | Fingerprint | Meaning |
|-------|------|---------------|-------------|---------|
| `↦` | Move | Ownership | `0xH001` | Value moves from source to target; source invalidated |
| `↶` | Borrow (imm) | Ownership | `0xH002` | Immutable borrow; original inaccessible for mutation |
| `↷` | Borrow (mut) | Ownership | `0xH003` | Mutable borrow; original inaccessible until returned |
| `&` | Reference | Pointer | `0xH004` | Immutable reference |
| `&̅` | Mutable ref | Pointer | `0xH005` | Mutable reference |
| `x̅` | Mutable binding | Binding | `0xH006` | `x` is mutable |
| `x̸` | Consumed | State marker | `0xH007` | `x` has been moved/consumed |
| `drop` | Explicit drop | Effect | `0xH008` | Immediately deallocate |

### 4.9 Effects & IO

| Glyph | Name | Semantic Class | Fingerprint | Meaning |
|-------|------|---------------|-------------|---------|
| `IO` | IO effect | Effect type | `0xI001` | Marks input/output capability |
| `State` | State effect | Effect type | `0xI002` | Marks mutable state access |
| `Except` | Exception | Effect type | `0xI003` | Marks partiality / errors |
| `Async` | Async effect | Effect type | `0xI004` | Marks asynchronous computation |
| `pure` | Purity marker | Effect | `0xI005` | Function has no effects |
| `catch` | Exception handler | Control | `0xI006` | Recover from `Except` |
| `throw` | Raise exception | Effect | `0xI007` | Introduce `Except` |

### 4.10 Encoding & Mapping

| Glyph | Name | Semantic Class | Fingerprint | Meaning |
|-------|------|---------------|-------------|---------|
| `encode` | Encode to ℕ | Mapping | `0xJ001` | `encode : Sym → ℕ` |
| `decode` | Decode from ℕ | Mapping | `0xJ002` | Inverse of encode (when bijective) |
| `hash` | Cryptographic hash | Mapping | `0xJ003` | `hash : Any → ℕ` (deterministic) |
| `fingerprint` | Type fingerprint | Mapping | `0xJ004` | Unique ID for type definition |

---

## 5. Mathematical Symbols (Inherited)

ΣLang **inherits the standard mathematical meaning** of all symbols defined in this section. No new semantics are introduced; existing mathematical consensus is adopted wholesale.

### 5.1 Set Theory

| Symbol | Standard Meaning | Adopted As-Is |
|--------|-----------------|--------------|
| `∅` | Empty set | ✅ |
| `ℕ` | Natural numbers | ✅ |
| `ℤ` | Integers | ✅ |
| `ℚ` | Rational numbers | ✅ |
| `ℝ` | Real numbers | ✅ |
| `ℂ` | Complex numbers | ✅ (optional extension) |
| `𝔹` | Boolean algebra | ✅ |
| `∈` | Membership | ✅ |
| `⊆` | Subset | ✅ |
| `⊂` | Proper subset | ✅ |
| `∪` | Union | ✅ |
| `∩` | Intersection | ✅ |
| `∖` | Set difference | ✅ |
| `×` | Cartesian product | ✅ (also multiplication) |
| `|S|` | Cardinality | ✅ |

### 5.2 Calculus & Analysis

| Symbol | Standard Meaning | Adopted As-Is |
|--------|-----------------|--------------|
| `∫` | Integral | ✅ |
| `∂` | Partial derivative | ✅ |
| `∇` | Gradient | ✅ |
| `Δ` | Finite difference / Laplacian | ✅ |
| `lim` | Limit | ✅ |
| `→` (under limit) | Approaches | ✅ |
| `∞` | Infinity | ✅ |

### 5.3 Logic

| Symbol | Standard Meaning | Adopted As-Is |
|--------|-----------------|--------------|
| `∀` | For all | ✅ |
| `∃` | There exists | ✅ |
| `¬` | Not | ✅ |
| `∧` | And | ✅ |
| `∨` | Or | ✅ |
| `⊃` or `⇒` | Implies | ✅ |
| `⇔` | If and only if | ✅ |
| `⊢` | Provable | ✅ |
| `⊨` | Models / entails | ✅ |

### 5.4 Greek Alphabet (as Variables)

All Greek letters are valid identifiers with no predefined meaning unless explicitly defined in this spec.

| Letter | Can Represent |
|--------|--------------|
| `α, β, γ` | Generic type parameters |
| `λ` | Lambda abstraction |
| `σ, τ` | Types |
| `π` | Product type / projection |
| `μ` | Fixed point / recursion |
| `ρ` | Relations |
| `φ, ψ` | Predicates / propositions |
| `ω` | Ordinals / limits |
| `ε` | Small quantity / epsilon |
| `δ` | Delta / change |
| `θ, φ` | Angles |
| `Σ, Π` | Summation / product |

---

## 6. Borrowed Symbols (From Existing Languages)

ΣLang adopts useful symbolic conventions from established languages. Each borrowing is explicitly documented with attribution.

### 6.1 From Julia

| Symbol | Julia Usage | ΣLang Adoption |
|--------|------------|----------------|
| `⊕` | User-defined operator | Semantic slot: associative addition |
| `⊗` | User-defined operator | Semantic slot: associative multiplication |
| `⋅` | Dot product | Scalar product in vector spaces |
| `∇` | Gradient | Differential operator |
| `∂` | Partial derivative | Partial differentiation |
| `∈` | Set membership (in) | Same |
| `∪` `∩` | Set operations | Same |
| `≠` `≤` `≥` | Comparisons | Same |
| `→` | Function arrow (->) | Function type |
| `↦` | Mapping (->) | Move semantics |

### 6.2 From Haskell / ML

| Symbol | Source Usage | ΣLang Adoption |
|--------|-------------|----------------|
| `λ` | Lambda abstraction | Same |
| `→` | Function type | Same |
| `⇒` | Type constraint | `C ⇒ T` means T under constraint C |
| `∀` | Universal quantification | Same |
| `∷` | Type annotation | `x ∷ T` means x has type T |
| `<>` | Monoidal append | Alias for `⊛` |
| `<<<` `>>>` | Compositions | Arrow compositions |
| `fmap` | Functor map | `map : (A→B) → F(A) → F(B)` |
| `pure` | Applicative pure | Lift value into context |
| `bind` (>>=) | Monadic bind | `A ↝ B` sequencing |

### 6.3 From Rust

| Symbol/Concept | Rust Usage | ΣLang Adoption |
|---------------|-----------|----------------|
| Ownership | Move semantics | `↦` move operator |
| Borrowing | `&T`, `&mut T` | `↶` immut borrow, `↷` mut borrow |
| Lifetimes | `'a` | Implicit (handled by verifier) |
| `drop` | RAII cleanup | Explicit `drop` effect |
| `Result<T,E>` | Error handling | `T + E` sum type |
| `Option<T>` | Nullable | `T + Unit` sum type |
| Trait bounds | `T: Clone` | `T ⇒ Clone` constraint |
| `!` (Never) | Never type | `∅` bottom type |

### 6.4 From APL / J

| Symbol | APL Usage | ΣLang Adoption |
|--------|----------|----------------|
| `⌊` | Floor | `⌊x⌋` floor function |
| `⌈` | Ceiling | `⌈x⌉` ceiling function |
| `⍳` | Index generator | `⍳n` ≡ `[0,1,…,n-1]` |
| `⊂` | Enclose / box | `⊂` proper subset |
| `↓` `↑` | Take / drop | List operations |
| `⍴` | Shape / reshape | Tensor shape |
| `∘.` | Outer product | `∘` composition + `.` extension |

### 6.5 From Python (Magic Methods as Symbols)

| Python Dunder | ΣLang Symbol | Semantic Contract |
|--------------|-------------|-------------------|
| `__add__` | `⊕` | `a ⊕ b` ≡ `a.__add__(b)` |
| `__mul__` | `⊗` | `a ⊗ b` ≡ `a.__mul__(b)` |
| `__eq__` | `≡` | `a ≡ b` ≡ `a.__eq__(b)` |
| `__lt__` | `<` | `a < b` ≡ `a.__lt__(b)` |
| `__iter__` | `iter` | Iterable protocol |
| `__call__` | `apply` | Callable protocol |
| `__enter__`/`__exit__` | `with` | Scoped resource |
| `__hash__` | `hash` | Hashable protocol |
| `__repr__` | `repr` | Canonical representation |
| `__bool__` | `truthy` | Truthiness test |

### 6.6 From Coq / Lean / Agda (Proof Assistants)

| Symbol | Proof Assistant Usage | ΣLang Adoption |
|--------|----------------------|----------------|
| `≡` | Definitional equality | Same |
| `≢` | Not definitionally equal | `a ≢ b` |
| `↦` | Rewrite rule | Move / rewrite |
| `induction` | Proof by induction | `ind : (P(0) → (∀n.P(n)→P(n+1)) → ∀n.P(n))` |
| `match` | Pattern matching | Same |
| `where` | Local definition | `where` clause |
| `let` | Binding | `let x ≝ v in body` |

### 6.7 From Elixir / Erlang

| Symbol/Concept | Source Usage | ΣLang Adoption |
|---------------|-------------|----------------|
| `|>` | Pipe operator | `x |> f` ≡ `f(x)` |
| `<>` | String concat | Monoidal append (when on Strings) |
| Pattern match | `= ` (match) | `x ≝ v` (definition/pattern) |
| `spawn` | Process creation | `spawn : (Unit → A) ↝ Pid` |
| `send` / `receive` | Message passing | `send : Pid → Msg ↝ Unit` |
| `supervisor` | Fault tolerance | `supervise : Tree → Tree` |

### 6.8 From Prolog / Logic Programming

| Symbol | Source Usage | ΣLang Adoption |
|--------|-------------|----------------|
| `:-` | Rule definition | `head :- body` |
| `,` | Conjunction (in rules) | Same as `∧` |
| `;` | Disjunction (in rules) | Same as `∨` |
| `=` | Unification | `x = y` (unify) |
| `is` | Evaluation | `Result is Expression` |

---

## 7. Algebraic Laws & Contracts

Every semantic operation in ΣLang is governed by algebraic laws. These laws are **not suggestions**; they are **part of the definition**.

### 7.1 Laws for `⊕` (Associative Addition)

```
Associativity:  ∀a,b,c. (a ⊕ b) ⊕ c ≡ a ⊕ (b ⊕ c)
Optionally:     Commutativity: ∀a,b. a ⊕ b ≡ b ⊕ a
Identity (opt): ∃e. ∀a. a ⊕ e ≡ a
```

### 7.2 Laws for `⊗` (Associative Multiplication)

```
Associativity:  ∀a,b,c. (a ⊗ b) ⊗ c ≡ a ⊗ (b ⊗ c)
Distributivity: ∀a,b,c. a ⊗ (b ⊕ c) ≡ (a ⊗ b) ⊕ (a ⊗ c)
Identity (opt): ∃1. ∀a. a ⊗ 1 ≡ a
```

### 7.3 Laws for Function Composition `∘`

```
Associativity:  ∀f,g,h. (f ∘ g) ∘ h ≡ f ∘ (g ∘ h)
Identity:       ∃id. ∀f. f ∘ id ≡ f ≡ id ∘ f
```

### 7.4 Laws for `↦` (Move)

```
Move Invalidates Source:
  x ↦ y  ⊨  x̸

Move Transfers Uniqueness:
  x ↦ y  ⊨  y : T  where  x : T

No Double Move:
  (x ↦ y); (x ↦ z)  ⊨  ⊥
```

### 7.5 Laws for `↶` (Immutable Borrow)

```
Borrow Does Not Invalidate:
  x ↶ y  ⊨  x : T  (x still valid)

No Mutable Access During Borrow:
  (x ↶ y); (x̅ := v)  ⊨  ⊥

Multiple Immutable Borrows Allowed:
  (x ↶ y); (x ↶ z)  ⊨  valid
```

### 7.6 Laws for `↷` (Mutable Borrow)

```
Exclusive Borrow:
  (x ↷ y); (x ↶ z)  ⊨  ⊥

Borrow Returns:
  After x ↷ y, y is returned  ⊨  x is accessible again
```

### 7.7 Laws for `fold`

```
fold(⊕, z, []) ≡ z
fold(⊕, z, [a]) ≡ a
fold(⊕, z, [a,b,c]) ≡ a ⊕ b ⊕ c
fold(⊕, z, xs ∥ ys) ≡ fold(⊕, z, xs) ⊕ fold(⊕, z, ys)
```

### 7.8 Laws for `map`

```
map(f, []) ≡ []
map(f, [a]) ≡ [f(a)]
map(f ∘ g, xs) ≡ map(f, map(g, xs))
map(id, xs) ≡ xs
```

### 7.9 Laws for `filter`

```
filter(P, []) ≡ []
filter(P, [x|xs]) ≡ if P(x) then [x|filter(P,xs)] else filter(P,xs)
filter(∀⊤, xs) ≡ xs
filter(∀⊥, xs) ≡ []
```

### 7.10 Laws for `Σ` (Summation)

```
Σ_{i∈∅} f(i) ≡ 0
Σ_{i∈{a}} f(i) ≡ f(a)
Σ_{i∈A∪B} f(i) ≡ Σ_{i∈A} f(i) ⊕ Σ_{i∈B} f(i)  (when A∩B=∅)
```

---

## 8. Ownership & Dataflow Semantics

### 8.1 Core Concepts

| Concept | Symbol | Description |
|---------|--------|-------------|
| Ownership | — | Every value has exactly one owner at any time |
| Move | `↦` | Transfer ownership; source becomes invalid |
| Borrow (immutable) | `↶` | Temporary read-only access; owner frozen |
| Borrow (mutable) | `↷` | Temporary read-write access; owner locked |
| Lifetime | implicit | Scope during which a reference is valid |
| Drop | `drop` | Explicit deallocation at end of ownership |

### 8.2 Ownership Rules (Formal)

```
Rule O1: Single Owner
  ∀v. ∃!x. x owns v

Rule O2: Move Invalidates
  x ↦ y  ⊨  x̸

Rule O3: Borrow Prevents Move
  x ↶ y  ⊨  ¬(x ↦ z) until y returned

Rule O4: Mutable Exclusive
  x ↷ y  ⊨  ¬(x ↶ z) ∧ ¬(x̅ := v) until y returned

Rule O5: No Aliasing with Mutation
  ¬∃x,y,z. (x̅ := v) ∧ (x ↶ y) ∧ (x̅ is live)

Rule O6: Drop at Scope End
  At end of owner's scope: drop(x) is implicit unless moved
```

### 8.3 Dataflow Notation

```
# Move: x's value transfers to y
y ← x ↦ y

# Immutable borrow: y can read x
y ← x ↶ y

# Mutable borrow: y can modify x
y ← x ↷ y

# Explicit drop
drop(x)
```

### 8.4 Example: Ownership Trace

```
f(x):
  y ← x ↦ y      # x̸, y owns value
  z ← y ↶ z      # y frozen, z reads
  w ← y ↷ w      # z must be returned first
  w := w ⊕ 1     # mutate through w
  return y       # y still valid, w returned
```

Verifier checks:
- ✅ No use of `x` after move
- ✅ `z` returned before `w` borrowed
- ✅ `y` returned exactly once

---

## 9. Encoding Principle (Everything → ℕ)

### 9.1 The Fundamental Rule

> **Every non-numeric concept in ΣLang MUST have a deterministic, bijective (or injective) encoding to ℕ.**

This is non-negotiable. If you cannot encode it to ℕ, you cannot use it in ΣLang core.

### 9.2 Encoding Functions

| External Concept | Encoding Function | Inverse | Example |
|-----------------|-------------------|---------|---------|
| Strings (opaque) | `encode_str : Str → ℕ` | N/A (opaque) | `encode_str("hello") ≝ 0xH3A8F` |
| Symbols | `encode_sym : Sym → ℕ` | `decode_sym` | `encode_sym("张") ≝ 101` |
| Dates | `encode_date : Y×M×D → ℕ` | `decode_date` | `encode_date(1990,5,12) ≝ 19900512` |
| Booleans | `encode_bool : 𝔹 → ℕ` | `decode_bool` | `⊤ ↦ 1, ⊥ ↦ 0` |
| Pairs | `encode_pair : A×B → ℕ` | `decode_pair` | Cantor pairing |
| Lists | `encode_list : [A] → ℕ` | `decode_list` | Gödel numbering |

### 9.3 Cantor Pairing (for Products)

```
pair(a, b) ≝ ½(a + b)(a + b + 1) + b
unpair(z) ≝ let w = ⌊(√(8z+1)−1)/2⌋ in
             let t = (w²+w)/2 in
             (z−t, w−(z−t))
```

### 9.4 Gödel Numbering (for Lists)

```
encode_list([]) ≝ 1
encode_list([a|as]) ≝ 2^encode(a) × 3^encode_list(as)
```

### 9.5 Example: Surname Statistics

```md
# Surname encoding
encode_surname : Sym → ℕ
encode_surname("张") ≝ 101
encode_surname("李") ≝ 102
encode_surname("王") ≝ 103

# Date encoding
encode_birth : Y × M × D → ℕ
encode_birth(y,m,d) ≝ y×10000 + m×100 + d

# Age from birth
age_of : ℕ → ℕ
age_of(birth_enc) ≝ CURRENT_YEAR − (birth_enc ÷ 10000)

# Group by surname, compute average age
avg_age_by_surname : [PersonId] → Map(ℕ, ℚ)
avg_age_by_surname(ps) ≝
  let groups ≝ group_by(ps, λp. encode_surname(surname_of(p))) in
  map (λ(k,vs). (k, avg_age(vs))) groups

avg_age : [PersonId] → ℚ
avg_age(ps) ≝ (Σ_{p∈ps} age_of(encode_birth_of(p))) / |ps|
```

### 9.6 What This Buys Us

- ✅ **No string comparison** → only ℕ comparison
- ✅ **No date parsing** → only ℕ arithmetic
- ✅ **No struct field access** → only projection functions
- ✅ **No ambiguity** → every concept is a number
- ✅ **Verifiable** → all operations reduce to ℕ arithmetic

---

## 10. Function & Control Semantics

### 10.1 Function Definition

```
# Lambda (anonymous)
f ≝ λx:T. body

# Named definition
f : A → B
f(x) ≝ body

# Effectful
f : A ↝ B
f(x) ≝ effectful_body
```

### 10.2 Function Application

```
# Pure application
f(a) : B  where f : A → B

# Effectful application
f(a) ⏳ : B  where f : A ↝ B
```

### 10.3 Higher-Order Functions

```
# Map
map : (A → B) → List⟨A⟩ → List⟨B⟩

# Filter
filter : (A → 𝔹) → List⟨A⟩ → List⟨A⟩

# Fold left
foldl : (B → A → B) → B → List⟨A⟩ → B

# Fold right
foldr : (A → B → B) → B → List⟨A⟩ → B

# Compose
compose : (B → C) → (A → B) → (A → C)
compose(g, f) ≝ g ∘ f
```

### 10.4 Recursion

```
# Explicit recursion
fact : ℕ → ℕ
fact(n) ≝ if n ≤ 1 then 1 else n × fact(n−1)

# Fold-based (preferred)
fact(n) ≝ fold(×, 1, range(1, n+1))

# Fixed point
fix : ((A → B) → A → B) → A → B
fix(F) ≝ F(fix(F))
```

### 10.5 Conditionals

```
if P then A else B

Laws:
  if ⊤ then A else B ≡ A
  if ⊥ then A else B ≡ B
```

### 10.6 Parallel Evaluation

```
# Parallel map
par_map : (A → B) → [A] → [B]
par_map(f, xs) ≝ map(f, xs) ∥

# Concurrent composition
a ∥ b  # both evaluated in parallel
```

### 10.7 Pattern Matching

```
match x with
| Some(a) → f(a)
| None    → z
```

Laws:
- Exhaustiveness required (all cases covered)
- Non-overlapping (no ambiguity)

---

## 11. Verification Rules

### 11.1 The Verifier

The Verifier is the **sole authority** for determining semantic correctness in ΣLang. It is not a compiler, not an interpreter, not a runtime. It is a **judge**.

### 11.2 What the Verifier Checks

| Check | Description |
|-------|-------------|
| **Type correctness** | All expressions have valid types per §3 |
| **Law satisfaction** | All algebraic laws hold for all inputs |
| **Test compliance** | All canonical tests pass with exact expected outputs |
| **Ownership correctness** | No use-after-move, no aliasing violations |
| **Determinism** | No randomness, no undefined behavior |
| **Encoding validity** | All non-numeric values have valid ℕ encodings |
| **Effect tracking** | All effects are declared and accounted for |

### 11.3 Verification Algorithm (Pseudo-Rust)

```rust
fn verify(impl: AIModel, spec: SigmaSpec) -> Result<(), Violation> {
    // 1. Check type correctness
    for expr in spec.expressions {
        if !impl.type_check(expr) {
            return Err(Violation::Type(expr));
        }
    }

    // 2. Check algebraic laws
    for law in spec.laws {
        if !impl.satisfies(law) {
            return Err(Violation::Law(law));
        }
    }

    // 3. Run canonical tests
    for test in spec.tests {
        let output = impl.run(test.input);
        if output != test.expected {
            return Err(Violation::Test(test, output));
        }
    }

    // 4. Check ownership
    for trace in spec.ownership_traces {
        if !impl.valid_ownership(trace) {
            return Err(Violation::Ownership(trace));
        }
    }

    Ok(())
}
```

### 11.4 What the Verifier Is NOT

- ❌ Not an interpreter (does not execute business logic)
- ❌ Not a compiler (does not generate machine code)
- ❌ Not a type checker (types are necessary but not sufficient)
- ❌ Not an AI model (has no intelligence, only rules)
- ❌ Not a runtime (does not manage memory or threads)

### 11.5 Canonical Test Format

```md
## Tests for ⊕

| # | Input | Expected | Law Checked |
|---|-------|----------|-------------|
| 1 | 1 ⊕ 2 | 3 | — |
| 2 | (1⊕2)⊕3 | 6 | Associativity |
| 3 | 1⊕2 | 2⊕1 | Commutativity |
| 4 | a⊕(b⊕c) | (a⊕b)⊕c | Associativity |
| 5 | 0 ⊕ x | x | Identity |
```

### 11.6 Soundness & Completeness

```
Soundness:  If Verifier accepts I, then I is correct.
Completeness: If I is correct, Verifier may or may not accept
              (decidability limits apply).
```

We prioritize **soundness over completeness**. False positives are unacceptable; false negatives are tolerable.

---

## 12. Surface Syntax (Markdown as AST)

### 12.1 Design Principle

> **The Markdown document IS the source code. There is no separate parser input format.**

### 12.2 Document Structure → AST Mapping

| Markdown Element | AST Node |
|-----------------|----------|
| `# Title` | `Module(name)` |
| `## Section` | `Section(name)` |
| `### Subsection` | `Definition(name)` |
| `| table |` | `TestSuite` or `TypeDef` |
| ` ``` ` code block | `Expression` or `Implementation` |
| `- bullet` | `Constraint` or `Law` |
| `> quote` | `Non-normative note` |

### 12.3 Example: Full Module in MD

```md
# Module: numeric_basics

## Type: ℕ
Primitive type. Non-negative integers.

## Operation: ⊕
### Signature
⊕ : ℕ × ℕ → ℕ

### Laws
- Associativity: (a⊕b)⊕c ≡ a⊕(b⊕c)
- Commutativity: a⊕b ≡ b⊕a

### Tests
| Input | Output |
|-----|-------|
| 1⊕2 | 3 |
| 0⊕x | x |

## Operation: ⊗
### Signature
⊗ : ℕ × ℕ → ℕ

### Laws
- Associativity: (a⊗b)⊗c ≡ a⊗(b⊗c)
- Distributivity: a⊗(b⊕c) ≡ (a⊗b)⊕(a⊗c)

### Tests
| Input | Output |
|-----|-------|
| 2⊗3 | 6 |
| 0⊗x | 0 |
```

### 12.4 Parser Rules (for implementers)

```
1. Parse MD into AST (using commonmark or similar)
2. Extract headings → module/section hierarchy
3. Extract tables → test suites / type definitions
4. Extract code blocks → expressions
5. Extract bullet lists under "Laws" → constraints
6. Validate all symbols against §4 registry
7. Build internal representation: Module { types, ops, laws, tests }
8. Pass to Verifier
```

### 12.5 What is NOT in the Surface Syntax

- ❌ No `if/else` keywords (use `if_then_else` as function)
- ❌ No `for/while` loops (use `fold` / `map` / recursion)
- ❌ No `class/struct` (use product types `A × B`)
- ❌ No `try/catch` (use sum types `A + E`)
- ❌ No `import/include` (modules are self-contained)
- ❌ No comments (MD prose is non-normative by default)

---

## 13. Canonical Test Suite

### 13.1 Test for `⊕` (Addition)

| # | Input | Expected | Category |
|---|-------|----------|----------|
| 1 | `2 ⊕ 3` | `5` | Basic |
| 2 | `0 ⊕ 7` | `7` | Identity |
| 3 | `(-3) ⊕ 5` | `2` | ℤ extension |
| 4 | `(1⊕2)⊕3` | `6` | Associativity |
| 5 | `1⊕(2⊕3)` | `6` | Associativity |
| 6 | `4⊕(-4)` | `0` | Inverse |

### 13.2 Test for `⊗` (Multiplication)

| # | Input | Expected | Category |
|---|-------|----------|----------|
| 1 | `3 ⊗ 4` | `12` | Basic |
| 2 | `0 ⊗ 5` | `0` | Annihilation |
| 3 | `1 ⊗ x` | `x` | Identity |
| 4 | `(2⊗3)⊗4` | `24` | Associativity |
| 5 | `2⊗(3⊕4)` | `14` | Distributivity |

### 13.3 Test for `fold`

| # | Input | Expected | Category |
|---|-------|----------|----------|
| 1 | `fold(⊕,0,[])` | `0` | Empty |
| 2 | `fold(⊕,0,[1,2,3])` | `6` | Basic |
| 3 | `fold(⊗,1,[2,3,4])` | `24` | Product |
| 4 | `fold(⊕,0,[a,b])` | `a⊕b` | Symbolic |

### 13.4 Test for `map`

| # | Input | Expected | Category |
|---|-------|----------|----------|
| 1 | `map(f,[])` | `[]` | Empty |
| 2 | `map(λx.x⊕1, [1,2,3])` | `[2,3,4]` | Basic |
| 3 | `map(id, xs)` | `xs` | Identity law |

### 13.5 Test for Ownership

| # | Code | Expected | Category |
|---|------|----------|----------|
| 1 | `x↦y; y` | ✅ valid | Move |
| 2 | `x↦y; x` | ❌ use-after-move | Move |
| 3 | `x↶y; x↶z` | ✅ valid | Borrow |
| 4 | `x↷y; x↶z` | ❌ exclusive borrow | Borrow |
| 5 | `x↷y; y:=v; x` | ✅ after return | Borrow return |

### 13.6 Test for Encoding

| # | Input | Expected | Category |
|---|-------|----------|----------|
| 1 | `encode("张")` | `101` | Surjective encoding |
| 2 | `encode(1990,5,12)` | `19900512` | Date encoding |
| 3 | `pair(3,5)` | `41` | Cantor pairing |
| 4 | `unpair(41)` | `(3,5)` | Cantor inverse |

---

## 14. Backend Interface

### 14.1 Backend Responsibilities

The backend is responsible for **executing** ΣLang specifications after they pass verification. The backend is **not part of the language specification**; it is an implementation choice.

### 14.2 Required Backend Capabilities

| Capability | Description |
|------------|-------------|
| ℕ arithmetic | Arbitrary-precision integer arithmetic |
| ℚ arithmetic | Exact rational arithmetic |
| Function evaluation | Lambda application, closure |
| List processing | map, fold, filter |
| Parallel execution | For `∥` operator |
| Async handling | For `⏳` operator |
| Memory management | For ownership semantics |

### 14.3 Recommended Backend: Rust Core + Elixir Runtime

#### Rust Layer (Core Engine)
- Implements ℕ, ℚ arithmetic
- Implements ownership tracking
- Implements Verifier
- Provides FFI boundary

#### Elixir Layer (Agent Runtime)
- Manages AI agent processes (Actor model)
- Handles async/await via BEAM
- Provides hot-code swapping
- Supervises long-running AI tasks

### 14.4 Backend Interface Contract

```rust
// Pseudo-interface for backend implementers

trait SigmaBackend {
    // Core arithmetic
    fn add(&self, a: BigInt, b: BigInt) -> BigInt;
    fn mul(&self, a: BigInt, b: BigInt) -> BigInt;
    fn div(&self, a: BigRational, b: BigRational) -> Result<BigRational, Err>;

    // Function application
    fn apply(&self, f: Closure, args: Vec<Value>) -> Result<Value, Err>;

    // List operations
    fn map(&self, f: Closure, list: List) -> List;
    fn fold(&self, f: Closure, init: Value, list: List) -> Value;
    fn filter(&self, pred: Closure, list: List) -> List;

    // Parallel
    fn par_eval(&self, exprs: Vec<Expr>) -> Vec<Result<Value, Err>>;

    // Ownership
    fn track_move(&self, src: VarId, dst: VarId) -> Result<(), OwnershipErr>;
    fn track_borrow(&self, var: VarId, mutable: bool) -> Result<BorrowId, OwnershipErr>;
    fn end_borrow(&self, borrow: BorrowId) -> Result<(), OwnershipErr>;
}
```

### 14.5 Backend Freedom

Backends MAY:
- ✅ Use any internal representation
- ✅ Optimize aggressively (as long as results match)
- ✅ Use JIT, AOT, interpretation, or table lookup
- ✅ Use SIMD, GPU, distributed computing
- ✅ Cache results

Backends MUST NOT:
- ❌ Introduce non-determinism
- ❌ Change numeric results
- ❌ Skip ownership checks
- ❌ Bypass the Verifier

---

## 15. Non-Goals & Explicit Rejections

The following features are **deliberately excluded** from ΣLang. Any proposal to add them must overcome the meta-rules in §1.

| Feature | Status | Reason |
|---------|--------|--------|
| **Floating-point (`Float32/64`)** | ❌ Rejected | Non-deterministic across platforms; use `ℚ` instead |
| **String manipulation** | ❌ Rejected in core | Strings must be encoded to ℕ first |
| **Null / Nil** | ❌ Rejected | Use `Option⟨T⟩ ≝ T + Unit` |
| **Inheritance / OOP** | ❌ Rejected | Not compositional; use sum types |
| **Exceptions (unchecked)** | ❌ Rejected | Use `Result ≝ T + E` |
| **Global mutable state** | ❌ Rejected | Violates purity; use explicit State effect |
| **Implicit conversions** | ❌ Rejected | All conversions explicit |
| **Operator overloading** | ❌ Restricted | Only via semantic slot registration |
| **Macros / metaprogramming** | ❌ Deferred | Out of scope for v0.1 |
| **Concurrency primitives** | ❌ In backend | Not in core language |
| **File I/O** | ❌ Effect only | `read : Path → IO String` (opaque) |
| **Network I/O** | ❌ Effect only | `send : Addr → Msg → IO Unit` |
| **Garbage collection** | ❌ Backend choice | Ownership system handles memory |
| **Reflection** | ❌ Rejected | Defeats determinism |
| **Type inference** | ⚠️ Optional | Allowed in surface syntax, not required |
| **Generics / Parametric polymorphism** | ✅ Allowed | `T⟨P⟩` syntax |
| **Dependent types** | ⚠️ Future | Deferred past v0.1 |

---

## 16. Versioning & Evolution

### 16.1 Versioning Scheme

ΣLang uses **semantic versioning** with one critical constraint:

> **Semantic atoms (§4) are immutable. New versions MAY add atoms but NEVER change their meaning.**

### 16.2 Version Format

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes to verification rules or core semantics
MINOR: New semantic atoms added, new laws, new test cases
PATCH: Clarifications, corrections to non-normative text
```

### 16.3 Evolution Rules

| Change Type | Allowed? | Process |
|------------|----------|---------|
| Add new atom | ✅ MINOR | Assign new fingerprint, document, add tests |
| Change atom meaning | ❌ NEVER | Would break all existing implementations |
| Deprecate atom | ✅ MAJOR | Mark deprecated, keep working for 2 majors |
| Add new law | ✅ MINOR | All implementations must comply |
| Remove test | ⚠️ MAJOR | Only if law changed |
| Change test expected value | ❌ NEVER | Tests are canonical |

### 16.4 Backward Compatibility Pledge

```
ΣLang 1.0 atoms will mean the same thing in ΣLang 99.0.
```

This is the language's **most important guarantee**.

---

## 17. Glossary

| Term | Definition |
|------|------------|
| **Semantic Atom** | A symbol with immutable, globally unique meaning |
| **Fingerprint** | A hash-based identifier for a semantic atom |
| **Verifier** | The mechanical judge that determines semantic correctness |
| **Backend** | The execution engine that runs verified ΣLang code |
| **Encoding** | A deterministic mapping from non-numeric concept to ℕ |
| **Effect** | A declared side-effect type (IO, State, Except, Async) |
| **Pure function** | A function with no effects (`A → B`) |
| **Effectful function** | A function with declared effects (`A ↝ B`) |
| **Sum type** | `A + B` — a value is either A or B |
| **Product type** | `A × B` — a value contains both A and B |
| **Canonical test** | A normative test that all implementations must pass |
| **Law** | An algebraic constraint that operations must satisfy |
| **Move** | Transfer of ownership; source becomes invalid |
| **Borrow** | Temporary access to a value without ownership transfer |
| **Surface syntax** | The Markdown format in which ΣLang is written |
| **AST** | Abstract Syntax Tree, derived from Markdown structure |
| **Backend freedom** | The principle that implementation details are not specified |
| **Determinism** | The property that same input always produces same output |
| **Non-normative** | Text that explains but does not define semantics |

---

## Appendix A: Complete Symbol Index

> This appendix lists every symbol in ΣLang v0.1 with its fingerprint and section reference.

### A.1 Logic
`⊤` `⊥` `¬` `∧` `∨` `⊃` `≡` `≠` `∀` `∃` `⊢` `⊨` `∴`

### A.2 Arithmetic
`+` `−` `×` `÷` `^` `√` `|a|` `sgn`

### A.3 Order
`<` `>` `≤` `≥` `min` `max`

### A.4 Algebra
`⊕` `⊗` `⊛` `⊜` `∘`

### A.5 Sets
`∈` `∉` `∪` `∩` `∖` `⊆` `|S|`

### A.6 Functions
`λ` `→` `↝` `π₁` `π₂` `inject₁` `inject₂` `case`

### A.7 Control
`⏳` `∥` `;` `if_then_else` `fold` `map` `filter` `Σ` `Π`

### A.8 Ownership
`↦` `↶` `↷` `&` `&̅` `x̅` `x̸` `drop`

### A.9 Effects
`IO` `State` `Except` `Async` `pure` `catch` `throw`

### A.10 Encoding
`encode` `decode` `hash` `fingerprint`

### A.11 Types
`ℕ` `ℤ` `ℚ` `ℝ` `𝔹` `Sym` `Prop` `Unit` `∅` `Type`

---

## Appendix B: Quick Reference — "Hello World" Equivalent

Since ΣLang does not have strings or I/O in the core, the equivalent of "Hello World" is **defining and verifying a simple function**:

```md
# Module: hello

## Operation: greet
### Signature
greet : ℕ → ℕ

### Definition
greet(x) ≝ x ⊕ 1

### Tests
| Input | Output |
|-----|-------|
| greet(0) | 1 |
| greet(41) | 42 |

### Laws
∀x. greet(x) > x
```

When the Verifier accepts this module, ΣLang has successfully "said hello."

---

## Appendix C: Design Rationale Summary

| Decision | Rationale |
|----------|-----------|
| Markdown as source | AI-native; structured; human-readable; version-controllable |
| No string ops in core | Strings are non-deterministic; encode to ℕ instead |
| No floating-point | Platform-dependent; use ℚ for exact arithmetic |
| Immutable atoms | Cross-AI consistency requires frozen semantics |
| Verifier supremacy | No AI or compiler can override semantic truth |
| Ownership in spec | Memory safety is a semantic property, not an implementation detail |
| Effect types | Side effects must be declared for verifiability |
| No reflection | Breaks determinism; defeats verification |
| Backend freedom | Innovation should not be constrained by specification |
| Math symbols inherited | Leverage centuries of mathematical consensus |

---

**End of Specification v0.1**
