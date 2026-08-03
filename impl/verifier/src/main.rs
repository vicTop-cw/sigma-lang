//! ΣLang Verifier — Reference Implementation (Rust)
//!
//! This is the skeleton of the full Verifier. The Python prototype
//! (`verify_p0.py`) proves the algorithms; this is the production version.

use anyhow::{Context, Result};
use clap::{Parser, ValueEnum};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::path::PathBuf;

mod evaluator;
mod sk;
use evaluator::{eval_test, parse_val, TVal};

// ========================================================================
// CLI
// ========================================================================

#[derive(Parser)]
#[command(author, version, about = "ΣLang Verifier")]
struct Cli {
    /// Path to the ΣLang module (.md file)
    file: Option<PathBuf>,

    /// Verbosity level
    #[arg(short, long, default_value = "info")]
    log_level: String,

    /// Output format
    #[arg(short, long, value_enum, default_value = "text")]
    format: OutputFormat,

    /// Run the §SK (SocketKit) reference-implementation self-check and exit
    #[arg(long)]
    sk_self_check: bool,

    /// Run the §SK.6 MVP story (§SK.6, mirrors sigma-runtime --story) and exit
    #[arg(long)]
    sk_story: bool,
}

#[derive(Debug, Clone, ValueEnum)]
enum OutputFormat {
    Text,
    Json,
    Sarif,
}

// ========================================================================
// Core Types
// ========================================================================

/// A fingerprint uniquely identifies a semantic atom.
/// It is the SHA-256 hash of the symbol's definition.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
struct Fingerprint([u8; 32]);

impl Fingerprint {
    fn from_definition(def: &str) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(def.as_bytes());
        Fingerprint(hasher.finalize().into())
    }
}

/// A semantic atom: the smallest unit of meaning in ΣLang.
#[derive(Debug, Clone, Serialize, Deserialize)]
struct Symbol {
    name: String,
    glyph: String,
    fingerprint: Fingerprint,
    semantic_class: String,
    definition: String,
    laws: Vec<Law>,
    tests: Vec<TestCase>,
    has_pre: bool,
    has_post: bool,
}

/// An algebraic law that must hold for a symbol.
#[derive(Debug, Clone, Serialize, Deserialize)]
struct Law {
    name: String,
    statement: String,
    is_universal: bool, // ∀ vs ∃
}

/// A canonical test case.
#[derive(Debug, Clone, Serialize, Deserialize)]
struct TestCase {
    input: String,
    expected: String,
    properties: Vec<String>, // e.g., "boundary", "round-trip"
}

/// A ΣLang module (parsed from MD).
#[derive(Debug, Clone)]
#[allow(dead_code)] // semantic-model fields reserved for the full Verifier
struct Module {
    name: String,
    version: String,
    imports: Vec<Import>,
    exports: Vec<String>,
    compat_tests: Vec<TestCase>,
    proof_declared: bool,
    proof_has_model: bool,
    proof_has_invariant: bool,
    guarantee_declared: bool,
    guarantee_metric: Option<String>,
    guarantee_threshold: Option<String>,
    guarantee_dataset: Option<String>,
    determinism_declared: bool,
    determinism_precision: Option<String>,
    determinism_rounding: Option<String>,
    determinism_sort_stability: Option<String>,
    signature_declared: bool,
    signature_signer: Option<String>,
    signature_pubkey_fp: Option<String>,
    signature_algorithm: Option<String>,
    signature_value: Option<String>,
    shadow_targets: Vec<String>,
    symbols: Vec<Symbol>,
    functions: Vec<Function>,
    timing_contract: Option<TimingContract>,
    capabilities: HashSet<Capability>,
}

#[derive(Debug, Clone)]
#[allow(dead_code)] // semantic-model fields reserved for the full Verifier
struct Import {
    name: String,
    version_constraint: Option<String>,
    kind: ImportKind, // standard / optional / custom
}

#[derive(Debug, Clone)]
enum ImportKind {
    Standard,
    Optional,
    Custom,
}

#[derive(Debug, Clone)]
#[allow(dead_code)] // semantic-model fields reserved for the full Verifier
struct Function {
    name: String,
    signature: String,
    effect_type: EffectType,
    body: String,
    laws: Vec<Law>,
    tests: Vec<TestCase>,
}

#[derive(Debug, Clone)]
#[allow(dead_code)] // effect tags reserved for Law X/§I full checking
enum EffectType {
    Pure,
    IO,
    Comm,
    Net,
    FS,
    Mixed(Vec<EffectType>),
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
#[allow(dead_code)] // capability tags reserved for Law XI full checking
enum Capability {
    ReadFile,
    WriteFile,
    Network,
    CmdExec,
    SpawnAgent,
}

#[derive(Debug, Clone)]
#[allow(dead_code)] // timing contract reserved for Law VIII full checking
struct TimingContract {
    max_latency: u64,
    max_retries: u32,
    timeout_budget: u64,
    deadline_miss_policy: String,
}

// ========================================================================
// Iron Laws (17 laws: I–XVII)
// ========================================================================

#[derive(Debug, Clone, PartialEq)]
enum IronLaw {
    I,   // Fingerprint Uniqueness
    II,  // Encoding to ℕ
    III, // Law Declaration
    IV,  // Test Mandatory
    V,   // No Implementation in Spec
    VI,  // Backward Compatibility
    VII, // Explicit Dependencies
    VIII,// Temporal Determinism
    IX,  // Calibration Requirement
    X,   // Effect Transparency
    XI,  // Capability Discipline
    XII, // Resource Linearity
    XIII,// Verifier Consensus (E-01, promoted 2026-08-01)
    XIV, // Negative Test Mandatory (E-02, promoted 2026-08-01)
    XV,  // Export Completeness (E-04, promoted 2026-08-01)
    XVI, // Compatibility Proof (E-05, promoted 2026-08-01)
    XVII,// Probabilistic Guarantee (E-09, promoted 2026-08-01)
}

// ========================================================================
// Violations
// ========================================================================

#[derive(Debug)]
#[allow(dead_code)] // violation variants reserved for the full Verifier's reporting
enum Violation {
    // Parse errors
    ParseError(String),

    // Iron Law violations
    FingerprintConflict(String, Fingerprint),
    MissingEncoding(String),
    NoLawsDeclared(String),
    NoTestsDefined(String),
    NoNegativeTest(String),
    UnportableAssertion(String, String),
    GhostExport(String),
    HiddenExport(String),
    SignatureMismatch(String, String),
    MissingModel(String),
    MissingInvariant(String),
    IncompleteContract(String),
    MalformedGuarantee(String),
    MalformedDeterminism(String),
    MalformedSignature(String),
    MalformedVersion(String),
    Uncalibrated(String),
    DuplicateSymbol(String),
    ShadowTargetMissing(String),
    OpaqueShadowAttempt(String),
    ImplementationLeak(String),
    CircularDependency(Vec<String>),
    UndeclaredEffect {
        func: String,
        missing: EffectType,
    },
    MissingCapability {
        call: String,
        capability: Capability,
    },
    UnsafeRetry {
        target: String,
    },
    ResourceLeak(String),
    DoubleClose(String),
    UseAfterClose(String),
    NoTimingContract(String),

    // Law violations
    MonadLawFailure {
        law: String,
        counterexample: String,
    },
    ShortCircuitFailure {
        detail: String,
    },
    BayesViolation,
    NotNormalized(f64),
    OutOfBounds(f64),

    // Test failures
    TestFailed {
        name: String,
        input: String,
        expected: String,
        actual: String,
    },
    CompatTestFailed {
        input: String,
        expected: String,
        actual: String,
    },
}

// ========================================================================
// The Verifier
// ========================================================================

struct Verifier {
    symbols: HashMap<Fingerprint, Symbol>,
    #[allow(dead_code)] // package registry reserved for Law VII dependency checking
    packages: HashMap<String, Module>,
    #[allow(dead_code)] // law set reserved for full Iron-Law reporting
    laws: Vec<IronLaw>,
    violations: Vec<Violation>,
}

impl Verifier {
    fn new() -> Self {
        Self {
            symbols: HashMap::new(),
            packages: HashMap::new(),
            laws: vec![
                IronLaw::I, IronLaw::II, IronLaw::III, IronLaw::IV,
                IronLaw::V, IronLaw::VI, IronLaw::VII, IronLaw::VIII,
                IronLaw::IX, IronLaw::X, IronLaw::XI, IronLaw::XII,
                IronLaw::XIII, IronLaw::XIV, IronLaw::XV, IronLaw::XVI,
                IronLaw::XVII,
            ],
            violations: Vec::new(),
        }
    }

    /// Main verification pipeline.
    fn verify(&mut self, module: &Module) -> Result<Certification> {
        // Step 1: Parse (already done by caller)
        // Step 2: Load packages & check Iron Laws
        self.load_packages(&module.imports)?;

        // Step 3: Type check + effect inference
        self.check_effect_transparency(module);

        // Step 4: Fingerprint uniqueness (Law I)
        self.check_fingerprint_uniqueness(module);

        // Step 5: Encoding to ℕ (Law II)
        self.check_n_encoding(module);

        // Step 6: Law declaration (Law III)
        self.check_law_declaration(module);

        // Step 7: Test mandatory (Law IV)
        self.check_tests_mandatory(module);

        // Step 7b: Negative test mandatory (E-02, promoted 2026-08-01)
        self.check_negative_tests(module);

        // Step 7c: Export completeness (E-04, promoted 2026-08-01)
        self.check_export_completeness(module);

        // Step 7d: Test portability (E-03, promoted 2026-08-01)
        self.check_test_portability(module);

        // Step 7e: Proof-carrying spec structure (P-01, spec_top_proofs.md)
        self.check_proof_structure(module);

        // Step 7f: Internal consistency adjudication (E-06, promoted 2026-08-01)
        self.check_internal_consistency(module);

        // Step 7g: Probabilistic guarantee (E-09, promoted 2026-08-01)
        self.check_guarantee(module);

        // Step 7h: Evaluation determinism (E-10, promoted 2026-08-01)
        self.check_eval_determinism(module);

        // Step 7i: Package signature (E-08 S-01 Level 1, 2026-08-01)
        self.check_signature(module);

        // Step 7j: Shadowing & binding discipline (§S, 2026-08-01)
        self.check_shadowing(module);

        // Step 8: No implementation in spec (Law V)
        self.check_no_implementation(module);

        // Step 8b: Backward compatibility (Law VI, basic)
        self.check_backward_compat(module);

        // Step 9: Explicit dependencies (Law VII)
        self.check_dependencies(module);

        // Step 9b: Calibration requirement (Law IX, basic)
        self.check_calibration(module);

        // Step 10: Temporal determinism (Law VIII)
        self.check_timing_contract(module);

        // Step 11: Effect transparency (Law X)
        self.check_capabilities(module);

        // Step 12: Resource linearity (Law XII)
        self.check_resource_linearity(module);

        // Step 13: Run canonical tests
        let (tests_passed, tests_total) = self.run_tests(module);

        // Step 14: Compatibility proof (E-05, promoted 2026-08-01)
        self.check_compat_tests(module);

        // Verdict
        if self.violations.is_empty() {
            Ok(Certification::new(
                module.name.clone(),
                tests_passed,
                tests_total,
            ))
        } else {
            Err(anyhow::anyhow!(
                "Verification failed with {} violation(s)",
                self.violations.len()
            ))
        }
    }

    // --- Iron Law Checks ---

    fn check_fingerprint_uniqueness(&mut self, module: &Module) {
        for sym in &module.symbols {
            if self.symbols.contains_key(&sym.fingerprint) {
                self.violations.push(Violation::FingerprintConflict(
                    sym.name.clone(),
                    sym.fingerprint.clone(),
                ));
            }
        }
    }

    fn check_n_encoding(&mut self, module: &Module) {
        for sym in &module.symbols {
            let type_str = &sym.semantic_class;
            if !is_numeric_type(type_str) && !has_encoding(module, type_str) {
                self.violations.push(Violation::MissingEncoding(sym.name.clone()));
            }
        }
    }

    fn check_law_declaration(&mut self, module: &Module) {
        // Law III applies to operations (fingerprinted symbols) only.
        // Fingerprint-less functions (e.g. encodings) feed the Law II encoding
        // check and are not required to carry their own laws.
        for sym in &module.symbols {
            if sym.laws.is_empty() {
                self.violations.push(Violation::NoLawsDeclared(sym.name.clone()));
            }
        }
    }

    fn check_tests_mandatory(&mut self, module: &Module) {
        // Law IV applies to operations (fingerprinted symbols) only.
        for sym in &module.symbols {
            if sym.tests.is_empty() {
                self.violations.push(Violation::NoTestsDefined(sym.name.clone()));
            }
        }
    }

    /// E-02 (promoted 2026-08-01) — every operation needs ≥1 negative test
    /// (an expected error, i.e. an expected starting with ⊥).
    fn check_negative_tests(&mut self, module: &Module) {
        for sym in &module.symbols {
            let has_negative = sym
                .tests
                .iter()
                .any(|t| t.expected.trim_start().starts_with('⊥'));
            if !has_negative {
                self.violations.push(Violation::NoNegativeTest(sym.name.clone()));
            }
        }
    }

    /// E-04 (promoted 2026-08-01) — export completeness: the `## Exports` list
    /// must match the defined symbols exactly (no ghost, no hidden symbols).
    /// Modules without an `## Exports` block are not checked (declaration
    /// required before the check applies — v0.1 policy).
    fn check_export_completeness(&mut self, module: &Module) {
        if module.exports.is_empty() {
            return;
        }
        // Ghost: declared in Exports but not defined.
        for exp in &module.exports {
            let defined = module.symbols.iter().any(|s| s.name == *exp);
            if !defined {
                self.violations.push(Violation::GhostExport(exp.clone()));
            }
        }
        // Hidden: defined but not declared in Exports.
        for sym in &module.symbols {
            let declared = module.exports.iter().any(|e| e == &sym.name);
            if !declared {
                self.violations.push(Violation::HiddenExport(sym.name.clone()));
            }
        }
    }

    /// E-03 (promoted 2026-08-01) — test portability: every test's expected
    /// output must be semantically structured — either an error (`⊥`-prefixed)
    /// or a parseable literal value — never an implementation-specific format
    /// (e.g. a float string, a Map rendering, or an error message).
    fn check_test_portability(&mut self, module: &Module) {
        for sym in &module.symbols {
            for tc in &sym.tests {
                let exp = tc.expected.trim();
                let portable = exp.starts_with('⊥') || parse_val(exp).is_some();
                if !portable {
                    self.violations.push(Violation::UnportableAssertion(
                        sym.name.clone(),
                        tc.expected.clone(),
                    ));
                }
            }
        }
    }

    /// P-01 (spec_top_proofs.md) — proof-carrying spec structure: a module
    /// declaring `## Proof` must have a `### Model` and a `### Invariant`, and
    /// every operation must declare `Pre` and `Post` together (or neither).
    fn check_proof_structure(&mut self, module: &Module) {
        if !module.proof_declared {
            return;
        }
        if !module.proof_has_model {
            self.violations.push(Violation::MissingModel(module.name.clone()));
        }
        if !module.proof_has_invariant {
            self.violations.push(Violation::MissingInvariant(module.name.clone()));
        }
        for sym in &module.symbols {
            if sym.has_pre != sym.has_post {
                self.violations.push(Violation::IncompleteContract(sym.name.clone()));
            }
        }
    }

    /// E-06 (promoted 2026-08-01) — internal consistency adjudication:
    /// an operation's test expected value must match its declared return type
    /// shape (numeric return → numeric expectation, list/container return →
    /// list expectation). Obvious signature/test conflicts are rejected.
    fn check_internal_consistency(&mut self, module: &Module) {
        for sym in &module.symbols {
            let rt = sym.semantic_class.trim();
            let numeric = is_numeric_type(rt);
            let container = rt.contains("List")
                || rt.contains("Tensor")
                || rt.contains("Map")
                || rt.contains("Seq")
                || rt.contains("Fmap");
            if !numeric && !container {
                continue; // unknown shape — cannot judge
            }
            for tc in &sym.tests {
                let e = tc.expected.trim();
                if e.starts_with('⊥') {
                    continue; // error path — no value shape to check
                }
                match parse_val(e) {
                    Some(TVal::Num(_)) | Some(TVal::FNum(_)) => {
                        if container && !numeric {
                            self.violations.push(Violation::SignatureMismatch(
                                sym.name.clone(),
                                tc.expected.clone(),
                            ));
                        }
                    }
                    Some(TVal::List(_)) => {
                        if numeric && !container {
                            self.violations.push(Violation::SignatureMismatch(
                                sym.name.clone(),
                                tc.expected.clone(),
                            ));
                        }
                    }
                    None => {} // unparseable — E-03 portability already flags
                }
            }
        }
    }

    /// E-09 (promoted 2026-08-01) — probabilistic guarantee: a prediction op
    /// must declare a performance floor (`metric`, `threshold`, `dataset`) in
    /// well-formed shape. The Verifier certifies the declaration only —
    /// production conformance is runtime-monitoring's job.
    fn check_guarantee(&mut self, module: &Module) {
        if !module.guarantee_declared {
            return;
        }
        let metric = module.guarantee_metric.as_deref().unwrap_or("");
        let valid_metric = matches!(metric, "accuracy" | "f1" | "brier");
        let threshold_ok = module
            .guarantee_threshold
            .as_deref()
            .and_then(|t| t.parse::<f64>().ok())
            .is_some_and(|v| (0.0..=1.0).contains(&v));
        let dataset_ok = module
            .guarantee_dataset
            .as_deref()
            .is_some_and(|d| !d.is_empty());

        if !valid_metric {
            self.violations.push(Violation::MalformedGuarantee(format!(
                "invalid metric: {:?} (expected accuracy|f1|brier)",
                metric
            )));
        }
        if !threshold_ok {
            self.violations.push(Violation::MalformedGuarantee(format!(
                "invalid threshold: {:?} (expected 0..=1)",
                module.guarantee_threshold.as_deref().unwrap_or("")
            )));
        }
        if !dataset_ok {
            self.violations.push(Violation::MalformedGuarantee(
                "missing dataset".to_string(),
            ));
        }
    }

    /// E-10 (promoted 2026-08-01) — evaluation determinism: a module declaring
    /// `## Determinism` must declare numeric `precision` (positive integer),
    /// `rounding` (round|floor|ceil|trunc), and `sort_stability` (true|false).
    /// Extends Law VIII (temporal determinism) to numeric evaluation.
    fn check_eval_determinism(&mut self, module: &Module) {
        if !module.determinism_declared {
            return;
        }
        let precision_ok = module
            .determinism_precision
            .as_deref()
            .and_then(|p| p.parse::<u32>().ok())
            .is_some_and(|v| v >= 1);
        let rounding_ok = matches!(
            module.determinism_rounding.as_deref(),
            Some("round" | "floor" | "ceil" | "trunc")
        );
        let sort_ok = matches!(
            module.determinism_sort_stability.as_deref(),
            Some("true" | "false")
        );

        if !precision_ok {
            self.violations.push(Violation::MalformedDeterminism(format!(
                "invalid precision: {:?} (expected positive integer)",
                module.determinism_precision.as_deref().unwrap_or("")
            )));
        }
        if !rounding_ok {
            self.violations.push(Violation::MalformedDeterminism(format!(
                "invalid rounding: {:?} (expected round|floor|ceil|trunc)",
                module.determinism_rounding.as_deref().unwrap_or("")
            )));
        }
        if !sort_ok {
            self.violations.push(Violation::MalformedDeterminism(format!(
                "invalid sort_stability: {:?} (expected true|false)",
                module.determinism_sort_stability.as_deref().unwrap_or("")
            )));
        }
    }

    /// E-08 S-01 Level 1 (2026-08-01) — package signature: a module declaring
    /// `## Signature` must provide a well-formed `signer`, `pubkey_fp`
    /// (sha256: prefix), `algorithm` (ed25519), and a non-empty `signature`.
    /// Modules without a signature still verify (backward compatible — Law VI).
    fn check_signature(&mut self, module: &Module) {
        if !module.signature_declared {
            return;
        }
        let signer_ok = module
            .signature_signer
            .as_deref()
            .is_some_and(|s| !s.is_empty());
        let fp_ok = module
            .signature_pubkey_fp
            .as_deref()
            .is_some_and(|fp| fp.starts_with("sha256:") && fp.len() > "sha256:".len());
        let algo_ok = module.signature_algorithm.as_deref() == Some("ed25519");
        let sig_ok = module
            .signature_value
            .as_deref()
            .is_some_and(|s| !s.is_empty());

        if !signer_ok {
            self.violations.push(Violation::MalformedSignature(
                "missing signer".to_string(),
            ));
        }
        if !fp_ok {
            self.violations.push(Violation::MalformedSignature(format!(
                "invalid pubkey_fp: {:?} (expected sha256:…)",
                module.signature_pubkey_fp.as_deref().unwrap_or("")
            )));
        }
        if !algo_ok {
            self.violations.push(Violation::MalformedSignature(format!(
                "invalid algorithm: {:?} (expected ed25519)",
                module.signature_algorithm.as_deref().unwrap_or("")
            )));
        }
        if !sig_ok {
            self.violations.push(Violation::MalformedSignature(
                "missing signature".to_string(),
            ));
        }
    }

    /// Law VI — Backward Compatibility (basic v0.1): the module `version` must
    /// be a well-formed semver (x.y.z). Cross-version semantics are checked by
    /// E-05 (`## Compat Tests`); this is the structural gate.
    fn check_backward_compat(&mut self, module: &Module) {
        let v = module.version.trim();
        let parts: Vec<&str> = v.split('.').collect();
        let well_formed = parts.len() == 3
            && parts
                .iter()
                .all(|p| !p.is_empty() && p.chars().all(|c| c.is_ascii_digit()));
        if !well_formed {
            self.violations
                .push(Violation::MalformedVersion(module.version.clone()));
        }
    }

    /// Law IX — Calibration (basic v0.1): a `Conf`-typed operation must declare
    /// at least one boundary anchor (0 or 1) in its laws, grounding the
    /// calibration claim. Full statistical calibration is out of Verifier scope.
    fn check_calibration(&mut self, module: &Module) {
        for sym in &module.symbols {
            if !sym.semantic_class.contains("Conf") {
                continue;
            }
            let laws: String = sym
                .laws
                .iter()
                .map(|l| l.statement.as_str())
                .collect::<Vec<_>>()
                .join(" ");
            if !(laws.contains('0') || laws.contains('1')) {
                self.violations.push(Violation::Uncalibrated(sym.name.clone()));
            }
        }
    }

    /// §S Shadowing & Binding Discipline (v0.1 + R5):
    /// - DuplicateSymbol: a module must not define the same symbol name twice
    ///   (Meta-Rule 2 / No Synonyms, §S R3 determinism).
    /// - ShadowTargetMissing: every `## Shadowing` declaration must reference a
    ///   symbol that actually exists (§S R1 explicit declaration).
    /// - OpaqueShadowAttempt: math-domain symbols (⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈ ℕ ℤ ℚ ℝ ℂ)
    ///   are Opaque-class and must not be shadowed (§S R5).
    fn check_shadowing(&mut self, module: &Module) {
        const OPAQUE_MATH: [&str; 13] =
            ["⊕", "⊗", "⊖", "⊘", "⊙", "≡", "≥", "≤", "∈", "ℕ", "ℤ", "ℚ", "ℝ"];
        // Duplicate symbol names within the module.
        let mut seen: HashSet<&str> = HashSet::new();
        for sym in &module.symbols {
            if !seen.insert(sym.name.as_str()) {
                self.violations
                    .push(Violation::DuplicateSymbol(sym.name.clone()));
            }
        }
        // R5: math-domain symbols cannot be shadowed (Opaque class). §C
        // constant fingerprints (0xK0xx math / 0xQ0xx physics) are Opaque
        // class too (§S.3.1 core-constant).
        for target in &module.shadow_targets {
            if OPAQUE_MATH.contains(&target.as_str())
                || target.starts_with("0xK")
                || target.starts_with("0xQ")
            {
                self.violations
                    .push(Violation::OpaqueShadowAttempt(target.clone()));
            }
        }
        // Every shadow target must resolve to a defined symbol. Qualified
        // names (e.g. finance.base.Δ) reference external-package symbols that
        // v0.1 cannot resolve — only local names are checked.
        let defined: HashSet<&str> = module.symbols.iter().map(|s| s.name.as_str()).collect();
        for target in &module.shadow_targets {
            if target.contains('.') {
                continue;
            }
            if defined.contains(target.as_str()) {
                // R7: declared Free-class shadow — verification passes, but the
                // report flags a warning (spec_top_rules.md §S R7 / S-11).
                eprintln!(
                    "⚠️ R7-warning: free-class shadow of `{}` (declared; verification passes)",
                    target
                );
            } else if !defined.contains(target.as_str()) {
                self.violations
                    .push(Violation::ShadowTargetMissing(target.clone()));
            }
        }
    }

    fn check_no_implementation(&mut self, module: &Module) {
        let forbidden = ["algorithm", "for loop", "while loop", "malloc", "free"];
        for sym in &module.symbols {
            for kw in &forbidden {
                if sym.definition.to_lowercase().contains(kw) {
                    self.violations.push(Violation::ImplementationLeak(
                        sym.name.clone(),
                    ));
                }
            }
        }
    }

    fn check_dependencies(&mut self, module: &Module) {
        // Build dependency graph
        let graph: HashMap<&str, Vec<&str>> = module
            .imports
            .iter()
            .map(|imp| (imp.name.as_str(), vec![]))
            .collect();

        // Check for cycles (simplified)
        if has_cycle(&graph) {
            self.violations.push(Violation::CircularDependency(
                module.imports.iter().map(|i| i.name.clone()).collect(),
            ));
        }
    }

    fn check_timing_contract(&mut self, module: &Module) {
        let has_async = module
            .functions
            .iter()
            .any(|f| matches!(f.effect_type, EffectType::IO | EffectType::Comm));

        if has_async && module.timing_contract.is_none() {
            self.violations.push(Violation::NoTimingContract(module.name.clone()));
        }
    }

    fn check_effect_transparency(&mut self, module: &Module) {
        for func in &module.functions {
            let body_has_io = func.body.contains("print")
                || func.body.contains("read_file")
                || func.body.contains("http_")
                || func.body.contains("send")
                || func.body.contains("recv");

            // `Mixed` is expanded recursively so composite effects
            // (e.g. Mixed([IO, Net])) count as declared IO.
            let declared_io = Self::declared_effect_has_io(&func.effect_type);

            if body_has_io && !declared_io {
                self.violations.push(Violation::UndeclaredEffect {
                    func: func.name.clone(),
                    missing: EffectType::IO,
                });
            }
        }
    }

/// True if an effect type (or any member of a `Mixed` composite) is IO-like
/// (IO / Comm / Net / FS). Used by Law X effect-transparency checking.
fn declared_effect_has_io(effect: &EffectType) -> bool {
    match effect {
        EffectType::IO | EffectType::Comm | EffectType::Net | EffectType::FS => true,
        EffectType::Mixed(inner) => inner.iter().any(Self::declared_effect_has_io),
        EffectType::Pure => false,
    }
}

    fn check_capabilities(&mut self, module: &Module) {
        // Map body markers to the capability they require (Law XI).
        // A function body may require several capabilities; each is checked.
        let markers: [(Capability, &[&str]); 5] = [
            (Capability::ReadFile, &["read_file", "readln"]),
            (Capability::WriteFile, &["write_file", "append_file"]),
            (Capability::Network, &["http_", "connect", "send", "recv"]),
            (Capability::CmdExec, &["exec", "system("]),
            (Capability::SpawnAgent, &["spawn"]),
        ];
        for func in &module.functions {
            for (needed, needles) in &markers {
                let used = needles.iter().any(|n| func.body.contains(n));
                if used && !module.capabilities.contains(needed) {
                    self.violations.push(Violation::MissingCapability {
                        call: func.name.clone(),
                        capability: needed.clone(),
                    });
                }
            }
        }
    }

    fn check_resource_linearity(&mut self, module: &Module) {
        for func in &module.functions {
            // Extract per-resource open/close/use call arguments (Law XII).
            let opens = extract_call_args(&func.body, "open");
            let closes = extract_call_args(&func.body, "close");
            let uses = extract_call_args(&func.body, "use");

            // Per-resource open/close counts.
            let mut open_count: HashMap<&str, usize> = HashMap::new();
            for r in &opens {
                *open_count.entry(r.as_str()).or_insert(0) += 1;
            }
            let mut close_count: HashMap<&str, usize> = HashMap::new();
            for r in &closes {
                *close_count.entry(r.as_str()).or_insert(0) += 1;
            }

            // Leak: opened more than closed for a given resource.
            for (r, oc) in &open_count {
                let cc = close_count.get(r).copied().unwrap_or(0);
                if *oc > cc {
                    self.violations
                        .push(Violation::ResourceLeak(format!("{}:{}", func.name, r)));
                }
            }
            // Double close: closed more than opened for a given resource.
            for (r, cc) in &close_count {
                let oc = open_count.get(r).copied().unwrap_or(0);
                if *cc > oc {
                    self.violations
                        .push(Violation::DoubleClose(format!("{}:{}", func.name, r)));
                }
            }
            // Use-after-close: a `use(r)` occurring after `close(r)` in text.
            for u in &uses {
                let close_pos = find_call_pos(&func.body, "close", u);
                let use_pos = find_call_pos(&func.body, "use", u);
                if let (Some(cp), Some(up)) = (close_pos, use_pos) {
                    if cp < up {
                        self.violations
                            .push(Violation::UseAfterClose(format!("{}:{}", func.name, u)));
                    }
                }
            }
        }
    }

    /// Execute canonical tests against the minimal evaluator.
    /// Returns (passed, total). Failures are recorded as violations.
    fn run_tests(&mut self, module: &Module) -> (usize, usize) {
        let mut passed = 0usize;
        let mut total = 0usize;
        for sym in &module.symbols {
            for tc in &sym.tests {
                total += 1;
                match eval_test(&tc.input, &tc.expected) {
                    Ok(()) => passed += 1,
                    Err(detail) => self.violations.push(Violation::TestFailed {
                        name: sym.name.clone(),
                        input: tc.input.clone(),
                        expected: tc.expected.clone(),
                        actual: detail,
                    }),
                }
            }
        }
        (passed, total)
    }

    /// E-05 (promoted 2026-08-01) — compatibility proof: a module declaring
    /// `## Compat Tests` (the previous version's canonical suite) must pass all
    /// of them, or the "backward compatible" claim is rejected.
    fn check_compat_tests(&mut self, module: &Module) {
        for tc in &module.compat_tests {
            if let Err(detail) = eval_test(&tc.input, &tc.expected) {
                self.violations.push(Violation::CompatTestFailed {
                    input: tc.input.clone(),
                    expected: tc.expected.clone(),
                    actual: detail,
                });
            }
        }
    }

    fn load_packages(&mut self, imports: &[Import]) -> Result<()> {
        // Law VII — Explicit Dependencies. v0.1: validate each import's name
        // (non-empty, no whitespace) and register a placeholder package so
        // dependency checks can reference it. Resolving/parsing real package
        // files (steps 2–4) needs the registry backend (`sigma-pkg`).
        for imp in imports {
            let name = imp.name.trim();
            if name.is_empty() {
                return Err(anyhow::anyhow!(
                    "import with empty package name is not allowed"
                ));
            }
            if name.chars().any(char::is_whitespace) {
                return Err(anyhow::anyhow!(
                    "import name must not contain whitespace: {:?}",
                    name
                ));
            }
            self.packages
                .entry(name.to_string())
                .or_insert_with(|| Module {
                    name: name.to_string(),
                    version: "0.0.0".to_string(),
                    imports: vec![],
                    exports: vec![],
                    compat_tests: vec![],
                    proof_declared: false,
                    proof_has_model: false,
                    proof_has_invariant: false,
                    guarantee_declared: false,
                    guarantee_metric: None,
                    guarantee_threshold: None,
                    guarantee_dataset: None,
                    determinism_declared: false,
                    determinism_precision: None,
                    determinism_rounding: None,
                    determinism_sort_stability: None,
                    signature_declared: false,
                    signature_signer: None,
                    signature_pubkey_fp: None,
                    signature_algorithm: None,
                    signature_value: None,
                    shadow_targets: vec![],
                    symbols: vec![],
                    functions: vec![],
                    timing_contract: None,
                    capabilities: HashSet::new(),
                });
        }
        Ok(())
    }
}

// ========================================================================
// Certification
// ========================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Certification {
    module: String,
    fingerprint: Fingerprint,
    timestamp: String,
    tests_passed: usize,
    tests_total: usize,
    laws_checked: usize,
}

impl Certification {
    fn new(module: String, tests_passed: usize, tests_total: usize) -> Self {
        Self {
            module,
            fingerprint: Fingerprint::from_definition("cert"),
            timestamp: chrono_now(),
            tests_passed,
            tests_total,
            laws_checked: 17,
        }
    }
}

// ========================================================================
// Helper Functions
// ========================================================================

fn is_numeric_type(t: &str) -> bool {
    matches!(t, "ℕ" | "ℤ" | "ℚ" | "ℝ" | "ℂ" | "Conf" | "Time")
}

fn has_encoding(module: &Module, type_name: &str) -> bool {
    module.functions.iter().any(|f| {
        f.name.contains("encode") && f.signature.contains(type_name)
    })
}

/// Detect a cycle in the dependency graph using DFS with a recursion stack
/// (Law VII — Explicit Dependencies: no circular deps).
/// Returns true iff the graph contains at least one cycle.
fn has_cycle(graph: &HashMap<&str, Vec<&str>>) -> bool {
    fn dfs<'a>(
        node: &'a str,
        graph: &HashMap<&'a str, Vec<&'a str>>,
        visiting: &mut HashSet<&'a str>,
        visited: &mut HashSet<&'a str>,
    ) -> bool {
        if visiting.contains(node) {
            return true; // back edge → cycle
        }
        if visited.contains(node) {
            return false;
        }
        visiting.insert(node);
        if let Some(neighbors) = graph.get(node) {
            for next in neighbors {
                if dfs(next, graph, visiting, visited) {
                    return true;
                }
            }
        }
        visiting.remove(node);
        visited.insert(node);
        false
    }

    let keys: Vec<&str> = graph.keys().copied().collect();
    let mut visiting = HashSet::new();
    let mut visited = HashSet::new();
    keys.iter()
        .any(|k| dfs(k, graph, &mut visiting, &mut visited))
}

/// Extract the argument of every `name(...)` call in `body`, e.g. `open(fd)`
/// yields `["fd"]`. Used by the Law XII resource-linearity check.
fn extract_call_args(body: &str, name: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut rest = body;
    let needle = format!("{}(", name);
    while let Some(pos) = rest.find(&needle) {
        let after = &rest[pos + needle.len()..];
        match after.find(')') {
            Some(close) => {
                let arg = after[..close].trim().to_string();
                if !arg.is_empty() {
                    out.push(arg);
                }
                rest = &after[close + 1..];
            }
            None => break,
        }
    }
    out
}

/// Byte offset of the first `name(arg)` occurrence in `body`, or None.
fn find_call_pos(body: &str, name: &str, arg: &str) -> Option<usize> {
    let needle = format!("{}({})", name, arg);
    body.find(&needle)
}

fn chrono_now() -> String {
    // Real UTC timestamp without external deps (chrono unavailable offline).
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default();
    let secs = now.as_secs();
    let days = (secs / 86_400) as i64;
    let sod = secs % 86_400;
    let (hour, minute, second) = (sod / 3600, (sod % 3600) / 60, sod % 60);

    // civil_from_days (Howard Hinnant's algorithm) — days since epoch → Y/M/D.
    let z = days + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097; // [0, 146096]
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365; // [0, 399]
    let y0 = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100); // [0, 365]
    let mp = (5 * doy + 2) / 153; // [0, 11]
    let d = doy - (153 * mp + 2) / 5 + 1; // [1, 31]
    let m = if mp < 10 { mp + 3 } else { mp - 9 }; // [1, 12]
    let y = if m <= 2 { y0 + 1 } else { y0 };

    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z", y, m, d, hour, minute, second)
}

/// Build a SARIF 2.1.0 report from the verifier's violations.
/// Successful runs produce an empty `results` array; failed runs carry one
/// result per violation (M-6: no more empty-template output).
fn build_sarif(violations: &[Violation]) -> String {
    let results: Vec<serde_json::Value> = violations
        .iter()
        .map(|v| {
            serde_json::json!({
                "ruleId": "sigma-verifier",
                "level": "error",
                "message": { "text": format!("{:?}", v) }
            })
        })
        .collect();
    serde_json::json!({
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": { "driver": { "name": "sigma-verifier", "semanticVersion": "0.1.0" } },
            "results": results
        }]
    })
    .to_string()
}

// ========================================================================
// Main
// ========================================================================

fn main() -> Result<()> {
    let cli = Cli::parse();

    // §SK (SocketKit) reference-implementation self-check — mirrors
    // `python3 impl/python/sigma_core.py` §SK block (73/73 total there).
    if cli.sk_self_check {
        let (passed, total) = sk::self_check();
        println!("sigma_core self-check (§SK): {passed}/{total} passed");
        std::process::exit(if passed == total { 0 } else { 1 });
    }

    // §SK.6 MVP story — mirrors `python3 tools/sigma-runtime.py --story` so the
    // three implementations audit the same story line (Law XIII).
    if cli.sk_story {
        let (passed, total) = sk::story();
        println!("sigma_core story (§SK.6): {passed}/{total} passed");
        std::process::exit(if passed == total { 0 } else { 1 });
    }

    // Initialize logging
    let filter = format!("sigma_verifier={}", cli.log_level);
    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .init();

    // Parse the ΣLang module from MD
    let file = cli.file.context("a module .md file is required")?;
    let module = parse_sigma_module(&file)?;

    // Run the Verifier
    let mut verifier = Verifier::new();
    match verifier.verify(&module) {
        Ok(cert) => {
            match cli.format {
                OutputFormat::Json => {
                    println!("{}", serde_json::to_string_pretty(&cert)?);
                }
                OutputFormat::Sarif => {
                    println!("{}", build_sarif(&[]));
                }
                OutputFormat::Text => {
                    println!("🏆 CERTIFIED: {} tests passed", cert.tests_passed);
                    println!("   Fingerprint: {:?}", cert.fingerprint);
                }
            }
            Ok(())
        }
        Err(e) => {
            // SARIF consumers need machine-readable output even on failure.
            if matches!(cli.format, OutputFormat::Sarif) {
                println!("{}", build_sarif(&verifier.violations));
                std::process::exit(1);
            }
            eprintln!("❌ VERIFICATION FAILED");
            eprintln!("   {}", e);
            eprintln!("   {} violation(s) found", verifier.violations.len());
            for v in &verifier.violations {
                eprintln!("   - {:?}", v);
            }
            std::process::exit(1);
        }
    }
}

/// Parse a ΣLang module from a Markdown file.
///
/// Real line-based parser supporting two block styles:
/// - `## Operation: glyph (desc)` + `### Signature/Laws/Tests` (tensor_ops style)
/// - `### Name` blocks with a fenced `Name : T → T` signature, `Fingerprint:`,
///   and in-fence `## Laws` / `## Tests` markers (demographics style)
/// - `import pkg` under `## Imports`; `# Module:` / `# Version:` headers.
///
/// Blocks that declare a `Fingerprint:` become [`Symbol`]s (operations);
/// fingerprint-less blocks with a signature become [`Function`]s (e.g. encodings),
/// which feed the Law II encoding check.
fn parse_sigma_module(path: &PathBuf) -> Result<Module> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read {}", path.display()))?;

    let mut name = "parsed_module".to_string();
    let mut version = "0.1.0".to_string();
    let mut imports: Vec<Import> = Vec::new();
    let mut exports: Vec<String> = Vec::new();
    let mut compat_tests: Vec<TestCase> = Vec::new();
    let mut symbols: Vec<Symbol> = Vec::new();
    let mut functions: Vec<Function> = Vec::new();

    let mut in_imports = false;
    let mut in_exports = false;
    let mut in_compat_tests = false;
    let mut in_fence = false;

    // `## Proof` block state (spec_top_proofs.md P.3).
    let mut in_proof = false;
    let mut proof_declared = false;
    let mut proof_has_model = false;
    let mut proof_has_invariant = false;

    // `## Guarantee` block state (E-09).
    let mut in_guarantee = false;
    let mut guarantee_declared = false;
    let mut guarantee_metric: Option<String> = None;
    let mut guarantee_threshold: Option<String> = None;
    let mut guarantee_dataset: Option<String> = None;

    // `## Determinism` block state (E-10).
    let mut in_determinism = false;
    let mut determinism_declared = false;
    let mut determinism_precision: Option<String> = None;
    let mut determinism_rounding: Option<String> = None;
    let mut determinism_sort_stability: Option<String> = None;

    // `## Signature` block state (E-08 S-01 Level 1).
    let mut in_signature = false;
    let mut signature_declared = false;
    let mut signature_signer: Option<String> = None;
    let mut signature_pubkey_fp: Option<String> = None;
    let mut signature_algorithm: Option<String> = None;
    let mut signature_value: Option<String> = None;

    // `## Capabilities` block state (Law XI).
    let mut in_capabilities = false;
    let mut capabilities: HashSet<Capability> = HashSet::new();

    // `## Timing` block state (Law VIII).
    let mut in_timing = false;
    let mut timing_max_latency: Option<u64> = None;
    let mut timing_max_retries: Option<u32> = None;
    let mut timing_timeout_budget: Option<u64> = None;
    let mut timing_deadline_policy: Option<String> = None;

    // `## Shadowing` block state (§S).
    let mut in_shadowing = false;
    let mut shadow_targets: Vec<String> = Vec::new();

    // Pending-block state (flushed at the next block boundary or EOF).
    let mut blk_name: Option<String> = None;
    let mut blk_sig = String::new();
    let mut blk_fp: Option<String> = None;
    let mut blk_laws: Vec<Law> = Vec::new();
    let mut blk_tests: Vec<TestCase> = Vec::new();
    let mut blk_in_laws = false;
    let mut blk_in_tests = false;
    let mut blk_has_pre = false;
    let mut blk_has_post = false;

    let reset_block = |blk_name: &mut Option<String>,
                       blk_sig: &mut String,
                           blk_fp: &mut Option<String>,
                           blk_laws: &mut Vec<Law>,
                           blk_tests: &mut Vec<TestCase>,
                           blk_in_laws: &mut bool,
                           blk_in_tests: &mut bool,
                           blk_has_pre: &mut bool,
                           blk_has_post: &mut bool,
                           heading: &str| {
        *blk_name = Some(heading.to_string());
        blk_sig.clear();
        *blk_fp = None;
        blk_laws.clear();
        blk_tests.clear();
        *blk_in_laws = false;
        *blk_in_tests = false;
        *blk_has_pre = false;
        *blk_has_post = false;
    };

    for raw in content.lines() {
        let line = raw.trim();
        if line.is_empty() {
            continue;
        }

        if let Some(rest) = line.strip_prefix("# Module:") {
            name = rest.trim().to_string();
            continue;
        }
        if let Some(rest) = line.strip_prefix("# Version:") {
            version = rest.trim().to_string();
            continue;
        }
        if line == "## Imports" {
            in_imports = true;
            continue;
        }
        if line == "## Exports" {
            in_exports = true;
            in_imports = false;
            continue;
        }
        if line == "## Compat Tests" {
            in_compat_tests = true;
            in_imports = false;
            in_exports = false;
            continue;
        }
        if line == "## Proof" {
            in_proof = true;
            proof_declared = true;
            in_imports = false;
            in_exports = false;
            in_compat_tests = false;
            continue;
        }
        if line == "## Guarantee" {
            in_guarantee = true;
            guarantee_declared = true;
            in_imports = false;
            in_exports = false;
            in_compat_tests = false;
            in_proof = false;
            continue;
        }
        if line == "## Determinism" {
            in_determinism = true;
            determinism_declared = true;
            in_imports = false;
            in_exports = false;
            in_compat_tests = false;
            in_proof = false;
            in_guarantee = false;
            continue;
        }
        if line == "## Signature" {
            in_signature = true;
            signature_declared = true;
            in_imports = false;
            in_exports = false;
            in_compat_tests = false;
            in_proof = false;
            in_guarantee = false;
            in_determinism = false;
            in_shadowing = false;
            continue;
        }
        if line == "## Capabilities" {
            in_capabilities = true;
            in_imports = false;
            in_exports = false;
            in_compat_tests = false;
            in_proof = false;
            in_guarantee = false;
            in_determinism = false;
            in_signature = false;
            in_shadowing = false;
            in_timing = false;
            continue;
        }
        if line == "## Timing" {
            in_timing = true;
            in_imports = false;
            in_exports = false;
            in_compat_tests = false;
            in_proof = false;
            in_guarantee = false;
            in_determinism = false;
            in_signature = false;
            in_capabilities = false;
            in_shadowing = false;
            continue;
        }
        if line == "## Shadowing" {
            in_shadowing = true;
            in_imports = false;
            in_exports = false;
            in_compat_tests = false;
            in_proof = false;
            in_guarantee = false;
            in_determinism = false;
            in_signature = false;
            in_capabilities = false;
            in_timing = false;
            continue;
        }
        if line.starts_with("```") {
            in_fence = !in_fence;
            continue;
        }

        // `## Shadowing` block: collect `shadow <target>` declarations (§S R1).
        if in_shadowing {
            if line.starts_with("## ") || line.starts_with("### ") {
                in_shadowing = false; // next heading ends the block; fall through
            } else if let Some(rest) = line.strip_prefix("shadow ") {
                let target = rest
                    .split('→')
                    .next()
                    .unwrap_or(rest)
                    .trim()
                    .to_string();
                if !target.is_empty() {
                    shadow_targets.push(target);
                }
                continue;
            } else {
                continue; // other content inside the block is ignored
            }
        }

        // `## Timing` block: collect max_latency / max_retries /
        // timeout_budget / deadline_miss_policy (Law VIII).
        if in_timing {
            if line.starts_with("## ") || line.starts_with("### ") {
                in_timing = false; // next heading ends the block; fall through
            } else if let Some(v) = line.strip_prefix("max_latency:") {
                timing_max_latency = v.trim().parse().ok();
                continue;
            } else if let Some(v) = line.strip_prefix("max_retries:") {
                timing_max_retries = v.trim().parse().ok();
                continue;
            } else if let Some(v) = line.strip_prefix("timeout_budget:") {
                timing_timeout_budget = v.trim().parse().ok();
                continue;
            } else if let Some(v) = line.strip_prefix("deadline_miss_policy:") {
                timing_deadline_policy = Some(v.trim().to_string());
                continue;
            } else {
                continue; // other content inside the block is ignored
            }
        }

        // `## Capabilities` block: collect comma/whitespace-separated
        // capability names (Law XI).
        if in_capabilities {
            if line.starts_with("## ") || line.starts_with("### ") {
                in_capabilities = false; // next heading ends the block; fall through
            } else {
                for token in line.split(|c: char| c == ',' || c.is_whitespace()) {
                    let t = token.trim();
                    if t.is_empty() || t == "```" {
                        continue;
                    }
                    let cap = match t {
                        "read_file" => Capability::ReadFile,
                        "write_file" => Capability::WriteFile,
                        "network" => Capability::Network,
                        "cmd_exec" => Capability::CmdExec,
                        "spawn_agent" => Capability::SpawnAgent,
                        _ => continue, // unknown capability name ignored
                    };
                    capabilities.insert(cap);
                }
                continue;
            }
        }

        if in_compat_tests {
            if !in_fence && (line.starts_with("## ") || line.starts_with("### ")) {
                // A new heading ends the compat-tests section; fall through.
                in_compat_tests = false;
            } else if line.starts_with('|') {
                if !line.starts_with("|-")
                    && !line.contains("Input")
                    && !line.contains("Output")
                    && !line.contains("Expected")
                {
                    let cells: Vec<&str> = line
                        .trim_matches('|')
                        .split('|')
                        .map(|c| c.trim())
                        .collect();
                    if cells.len() >= 2 {
                        compat_tests.push(TestCase {
                            input: cells[0].to_string(),
                            expected: cells[1].to_string(),
                            properties: vec![],
                        });
                    }
                }
                continue;
            } else {
                continue;
            }
        }

        if in_exports {
            if !line.starts_with("## ") && !line.starts_with("### ") {
                // Collect comma/whitespace-separated exported names.
                for token in line.split(|c: char| c == ',' || c.is_whitespace()) {
                    let t = token.trim();
                    if !t.is_empty() && t != "```" {
                        exports.push(t.to_string());
                    }
                }
                continue;
            }
            // A new heading ends the exports section; fall through.
            in_exports = false;
        }

        // `## Signature` block: collect `signer:` / `pubkey_fp:` /
        // `algorithm:` / `signature:` lines (E-08 S-01 Level 1).
        if in_signature {
            if line.starts_with("## ") || line.starts_with("### ") {
                in_signature = false; // next heading ends the block; fall through
            } else if let Some(v) = line.strip_prefix("signer:") {
                signature_signer = Some(v.trim().to_string());
                continue;
            } else if let Some(v) = line.strip_prefix("pubkey_fp:") {
                signature_pubkey_fp = Some(v.trim().to_string());
                continue;
            } else if let Some(v) = line.strip_prefix("algorithm:") {
                signature_algorithm = Some(v.trim().to_string());
                continue;
            } else if let Some(v) = line.strip_prefix("signature:") {
                signature_value = Some(v.trim().to_string());
                continue;
            } else {
                continue; // other content inside the block is ignored
            }
        }

        // `## Determinism` block: collect `precision:` / `rounding:` /
        // `sort_stability:` lines.
        if in_determinism {
            if line.starts_with("## ") || line.starts_with("### ") {
                in_determinism = false; // next heading ends the block; fall through
            } else if let Some(v) = line.strip_prefix("precision:") {
                determinism_precision = Some(v.trim().to_string());
                continue;
            } else if let Some(v) = line.strip_prefix("rounding:") {
                determinism_rounding = Some(v.trim().to_string());
                continue;
            } else if let Some(v) = line.strip_prefix("sort_stability:") {
                determinism_sort_stability = Some(v.trim().to_string());
                continue;
            } else {
                continue; // other content inside the block is ignored
            }
        }

        // `## Guarantee` block: collect `metric:` / `threshold:` / `dataset:` lines.
        if in_guarantee {
            if line.starts_with("## ") || line.starts_with("### ") {
                in_guarantee = false; // next heading ends the block; fall through
            } else if let Some(v) = line.strip_prefix("metric:") {
                guarantee_metric = Some(v.trim().to_string());
                continue;
            } else if let Some(v) = line.strip_prefix("threshold:") {
                guarantee_threshold = Some(v.trim().to_string());
                continue;
            } else if let Some(v) = line.strip_prefix("dataset:") {
                guarantee_dataset = Some(v.trim().to_string());
                continue;
            } else {
                continue; // other content inside the block is ignored
            }
        }

        // `## Proof` block: collect Model / Invariant / Trusted sub-blocks;
        // any other heading exits proof mode and is handled below.
        if in_proof {
            if line.starts_with("## ") || line.starts_with("### ") {
                match line {
                    "### Model" => {
                        proof_has_model = true;
                        continue;
                    }
                    "### Invariant" => {
                        proof_has_invariant = true;
                        continue;
                    }
                    "### Trusted" => {
                        continue;
                    }
                    _ => {
                        in_proof = false; // fall through to heading handling
                    }
                }
            } else {
                continue; // proof content lines are not parsed
            }
        }

        if in_imports {
            if let Some(rest) = line.strip_prefix("import") {
                let pkg = rest.trim();
                let kind = if pkg.contains("optional") {
                    ImportKind::Optional
                } else if pkg.contains("custom") {
                    ImportKind::Custom
                } else {
                    ImportKind::Standard
                };
                let clean = pkg
                    .split_whitespace()
                    .next()
                    .unwrap_or(pkg)
                    .trim_end_matches(',')
                    .to_string();
                imports.push(Import {
                    name: clean,
                    version_constraint: None,
                    kind,
                });
                continue;
            }
            // Non-import line: the imports section ends here; reprocess this
            // line below (it is usually a heading that starts a new block).
            in_imports = false;
        }

        // Markdown headings outside code fences are block boundaries.
        if !in_fence && (line.starts_with("## ") || line.starts_with("### ")) {
            match line {
                "### Signature" => {
                    blk_in_laws = false;
                    blk_in_tests = false;
                    continue;
                }
                "### Laws" | "## Laws" => {
                    blk_in_laws = true;
                    blk_in_tests = false;
                    continue;
                }
                "### Tests" | "## Tests" => {
                    blk_in_laws = false;
                    blk_in_tests = true;
                    continue;
                }
                _ => {}
            }
            // Flush the pending block, then start a new one.
            flush_block(
                &mut symbols,
                &mut functions,
                blk_name.take(),
                std::mem::take(&mut blk_sig),
                blk_fp.take(),
                std::mem::take(&mut blk_laws),
                std::mem::take(&mut blk_tests),
                blk_has_pre,
                blk_has_post,
            );
            let heading = line
                .trim_start_matches('#')
                .trim()
                .trim_start_matches("Operation:")
                .trim()
                .to_string();
            reset_block(
                &mut blk_name,
                &mut blk_sig,
                &mut blk_fp,
                &mut blk_laws,
                &mut blk_tests,
                &mut blk_in_laws,
                &mut blk_in_tests,
                &mut blk_has_pre,
                &mut blk_has_post,
                &heading,
            );
            continue;
        }

        // In-fence `## Laws` / `## Tests` markers (demographics style).
        if in_fence {
            match line {
                "## Laws" => {
                    blk_in_laws = true;
                    blk_in_tests = false;
                    continue;
                }
                "## Tests" => {
                    blk_in_laws = false;
                    blk_in_tests = true;
                    continue;
                }
                _ => {}
            }
        }

        // Content lines: fingerprint / tests / laws / signature / pre / post.
        if let Some(fp) = line.strip_prefix("Fingerprint:") {
            blk_fp = Some(fp.trim().to_string());
            continue;
        }
        if line.starts_with("# Pre:") {
            blk_has_pre = true;
            continue;
        }
        if line.starts_with("# Post:") {
            blk_has_post = true;
            continue;
        }
        if blk_in_tests && line.starts_with('|') {
            if !line.starts_with("|-")
                && !line.contains("Input")
                && !line.contains("Output")
                && !line.contains("Expected")
            {
                let cells: Vec<&str> = line
                    .trim_matches('|')
                    .split('|')
                    .map(|c| c.trim())
                    .collect();
                if cells.len() >= 2 {
                    blk_tests.push(TestCase {
                        input: cells[0].to_string(),
                        expected: cells[1].to_string(),
                        properties: vec![],
                    });
                }
            }
            continue;
        }
        // Signature detection must run BEFORE the `≡`-in-line law heuristic:
        // an operator whose glyph is `≡` (e.g. `≡ : ℕ × ℕ → ℕ`) would otherwise
        // be swallowed as a law line and lose its signature/name.
        if blk_sig.is_empty() && looks_like_signature(line) {
            blk_sig = line.to_string();
            if let Some(left) = line.split(':').next() {
                let nm = left.trim();
                if !nm.is_empty() && !nm.contains(' ') {
                    blk_name = Some(nm.to_string());
                }
            }
            continue;
        }
        if blk_in_laws || line.starts_with('∀') || line.starts_with('∃') || line.contains('≡') {
            if !line.contains('|') {
                let is_universal = line.starts_with('∀');
                blk_laws.push(Law {
                    name: format!("law-{}", blk_laws.len() + 1),
                    statement: line.to_string(),
                    is_universal,
                });
            }
            continue;
        }
    }

    // Flush the final block, if any.
    flush_block(
        &mut symbols,
        &mut functions,
        blk_name.take(),
        std::mem::take(&mut blk_sig),
        blk_fp.take(),
        std::mem::take(&mut blk_laws),
        std::mem::take(&mut blk_tests),
        blk_has_pre,
        blk_has_post,
    );

    // Assemble the timing contract from collected `## Timing` fields (Law VIII).
    let timing_contract = match (
        timing_max_latency,
        timing_max_retries,
        timing_timeout_budget,
        timing_deadline_policy,
    ) {
        (Some(max_latency), Some(max_retries), Some(timeout_budget), Some(deadline_miss_policy)) => {
            Some(TimingContract {
                max_latency,
                max_retries,
                timeout_budget,
                deadline_miss_policy,
            })
        }
        _ => None,
    };

    Ok(Module {
        name,
        version,
        imports,
        exports,
        compat_tests,
        proof_declared,
        proof_has_model,
        proof_has_invariant,
        guarantee_declared,
        guarantee_metric,
        guarantee_threshold,
        guarantee_dataset,
        determinism_declared,
        determinism_precision,
        determinism_rounding,
        determinism_sort_stability,
        signature_declared,
        signature_signer,
        signature_pubkey_fp,
        signature_algorithm,
        signature_value,
        shadow_targets,
        symbols,
        functions,
        timing_contract,
        capabilities,
    })
}

/// True if `line` looks like a signature: `Name : Type → Type`.
fn looks_like_signature(line: &str) -> bool {
    !line.starts_with('|')
        && !line.starts_with('#')
        && line.contains(':')
        && line.contains('→')
}

/// Flush a pending block: with a fingerprint it becomes a [`Symbol`] (operation);
/// without one, a signature becomes a [`Function`] (e.g. an encoding).
fn flush_block(
    symbols: &mut Vec<Symbol>,
    functions: &mut Vec<Function>,
    name: Option<String>,
    sig: String,
    fp: Option<String>,
    laws: Vec<Law>,
    tests: Vec<TestCase>,
    has_pre: bool,
    has_post: bool,
) {
    let Some(fp) = fp else {
        // No fingerprint → not an operation. Keep a signed block as a declared
        // function so Law II (encoding to ℕ) can detect encoders.
        if !sig.is_empty() {
            functions.push(Function {
                name: name.unwrap_or_else(|| "fn".to_string()),
                signature: sig,
                effect_type: EffectType::Pure,
                body: String::new(),
                laws,
                tests,
            });
        }
        return;
    };
    let fingerprint = Fingerprint::from_definition(&fp);
    let semantic_class = if sig.is_empty() {
        "Any".to_string()
    } else {
        sig.split('→').last().unwrap_or(&sig).trim().to_string()
    };
    let name = name.unwrap_or_else(|| "op".to_string());
    let glyph = name.clone();
    symbols.push(Symbol {
        name: name.clone(),
        glyph,
        fingerprint,
        semantic_class,
        definition: sig,
        laws,
        tests,
        has_pre,
        has_post,
    });
}

// ========================================================================
// Minimal canonical-test evaluator — moved to `evaluator.rs` (L-5 split).
// See `mod evaluator;` at the top of this file.
// ========================================================================
