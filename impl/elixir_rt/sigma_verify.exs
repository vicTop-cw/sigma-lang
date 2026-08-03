#!/usr/bin/env elixir
# sigma_verify.exs — Elixir-side ΣLang MD verifier (E-01 third implementation)
#
# Usage:  elixir sigma_verify.exs <module.md>
# Exit:   0 = PASS, 1 = FAIL (mirrors the Rust verifier's contract)
#
# Implements the same contract as the Rust and Python verifiers:
#   - MD parsing (both `## Operation:` and `### Name` block styles)
#   - Iron Laws I/II/III/IV (fingerprint uniqueness, encoding to ℕ,
#     law declaration, test mandatory)
#   - canonical test execution (minimal evaluator: ⊕, ⊗, index, ⊥, I₂)

defmodule SigmaVerify do
  @numeric_types ["ℕ", "ℤ", "ℚ", "ℝ", "ℂ", "Conf", "Time"]

  # §C Real-World Constants (spec_top_rules.md §C) — resolvable by fingerprint.
  # Reference values (non-normative precision) held as IEEE-754 doubles so the
  # Python/Rust evaluators agree on float handling.
  @constants %{
    # C.1 Mathematical (0xK0xx)
    "0xK001" => {:fnum, 3.141592653589793},  # π
    "0xK002" => {:fnum, 2.718281828459045},  # e
    "0xK003" => {:fnum, 1.618033988749895},  # φ
    "0xK004" => {:fnum, 0.5772156649015329},  # γ
    "0xK005" => {:fnum, 1.4142135623730951},  # √2
    "0xK006" => {:fnum, 0.6931471805599453},  # ln2
    "0xK007" => {:fnum, 0.915965594177219},  # G_𝒦
    "0xK008" => {:fnum, 1.2020569031595942},  # ζ3
    "0xK009" => {:fnum, 4.66920160910299},  # δ_ℱ
    # C.2 Physics (0xQ0xx)
    "0xQ001" => {:num, 299_792_458},  # c (exact SI integer)
    "0xQ002" => {:fnum, 6.62607015e-34},  # h
    "0xQ003" => {:fnum, 1.054571817e-34},  # ℏ
    "0xQ004" => {:fnum, 6.67430e-11},  # G_𝔫
    "0xQ005" => {:fnum, 8.8541878128e-12},  # ε₀
    "0xQ006" => {:fnum, 1.25663706212e-6},  # μ₀
    "0xQ007" => {:fnum, 1.602176634e-19},  # e
    "0xQ008" => {:fnum, 1.380649e-23},  # k_B
    "0xQ009" => {:fnum, 6.02214076e23},  # N_A
    "0xQ00A" => {:fnum, 8.314462618},  # R
    "0xQ00B" => {:fnum, 9.1093837015e-31},  # mₑ
    "0xQ00C" => {:fnum, 1.67262192369e-27},  # mₚ
    "0xQ00D" => {:fnum, 7.2973525693e-3},  # α (fine-structure constant)
    "0xQ00E" => {:fnum, 5.670374419e-8},  # σ (Stefan–Boltzmann)
    "0xQ00F" => {:fnum, 9.80665},  # g₀ (standard gravity, exact SI)
    "0xQ010" => {:fnum, 10973731.568160}  # R_∞ (Rydberg constant)
  }

  # ============================================================
  # Parser (mirrors impl/verifier/src/main.rs parse_sigma_module)
  # ============================================================

  def parse(path) do
    content = File.read!(path)
    initial = %{
      name: "parsed_module",
      version: "0.1.0",
      imports: [],
      exports: [],
      compat_tests: [],
      symbols: [],
      functions: [],
      proof_declared: false,
      proof_has_model: false,
      proof_has_invariant: false,
      guarantee_declared: false,
      guarantee_metric: nil,
      guarantee_threshold: nil,
      guarantee_dataset: nil,
      determinism_declared: false,
      determinism_precision: nil,
      determinism_rounding: nil,
      determinism_sort_stability: nil,
      signature_declared: false,
      signature_signer: nil,
      signature_pubkey_fp: nil,
      signature_algorithm: nil,
      signature_value: nil,
      shadow_targets: [],
      timing_contract: nil,
      capabilities: [],
      in_imports: false,
      in_exports: false,
      in_compat_tests: false,
      in_proof: false,
      in_guarantee: false,
      in_determinism: false,
      in_signature: false,
      in_shadowing: false,
      in_timing: false,
      in_capabilities: false,
      in_fence: false,
      blk: nil
    }
    lines = String.split(content, "\n")
    state = walk(lines, initial)
    flush(state)
  end

  # Recursive walk; step/2 may replay a line (imports-section exit).
  defp walk([], state), do: state
  defp walk([line | rest], state) do
    case step(line, state) do
      {:cont, new_state} -> walk(rest, new_state)
      {:replay, new_state} -> walk([line | rest], new_state)
    end
  end

  defp step(line, state) do
    t = String.trim(line)

    cond do
      t == "" ->
        {:cont, state}

      String.starts_with?(t, "# Module:") ->
        {:cont, %{state | name: String.trim(String.replace_prefix(t, "# Module:", ""))}}

      String.starts_with?(t, "# Version:") ->
        {:cont, %{state | version: String.trim(String.replace_prefix(t, "# Version:", ""))}}

      t == "## Imports" ->
        {:cont, %{state | in_imports: true}}

      t == "## Exports" ->
        {:cont, %{state | in_exports: true, in_imports: false}}

      t == "## Compat Tests" ->
        {:cont, %{state | in_compat_tests: true, in_imports: false, in_exports: false}}

      t == "## Proof" ->
        {:cont, %{state | proof_declared: true, in_proof: true,
                          in_imports: false, in_exports: false, in_compat_tests: false}}

      t == "## Guarantee" ->
        {:cont, %{state | guarantee_declared: true, in_guarantee: true,
                          in_imports: false, in_exports: false, in_compat_tests: false,
                          in_proof: false}}

      t == "## Determinism" ->
        {:cont, %{state | determinism_declared: true, in_determinism: true,
                          in_imports: false, in_exports: false, in_compat_tests: false,
                          in_proof: false, in_guarantee: false}}

      t == "## Signature" ->
        {:cont, %{state | signature_declared: true, in_signature: true,
                          in_imports: false, in_exports: false, in_compat_tests: false,
                          in_proof: false, in_guarantee: false, in_determinism: false,
                          in_shadowing: false}}

      t == "## Shadowing" ->
        {:cont, %{state | in_shadowing: true,
                          in_imports: false, in_exports: false, in_compat_tests: false,
                          in_proof: false, in_guarantee: false, in_determinism: false,
                          in_signature: false}}

      t == "## Timing" ->
        {:cont, %{state | in_timing: true,
                          in_imports: false, in_exports: false, in_compat_tests: false,
                          in_proof: false, in_guarantee: false, in_determinism: false,
                          in_signature: false, in_shadowing: false}}

      t == "## Capabilities" ->
        {:cont, %{state | in_capabilities: true,
                          in_imports: false, in_exports: false, in_compat_tests: false,
                          in_proof: false, in_guarantee: false, in_determinism: false,
                          in_signature: false, in_shadowing: false, in_timing: false}}

      String.starts_with?(t, "```") ->
        {:cont, %{state | in_fence: not state.in_fence}}

      state.in_timing ->
        cond do
          String.starts_with?(t, "## ") or String.starts_with?(t, "### ") ->
            # A heading ends the timing block; replay it below.
            {:replay, %{state | in_timing: false}}

          true ->
            {key, val} =
              cond do
                String.starts_with?(t, "max_latency:") ->
                  {"max_latency", t |> String.replace_prefix("max_latency:", "") |> String.trim()}
                String.starts_with?(t, "max_retries:") ->
                  {"max_retries", t |> String.replace_prefix("max_retries:", "") |> String.trim()}
                String.starts_with?(t, "timeout_budget:") ->
                  {"timeout_budget", t |> String.replace_prefix("timeout_budget:", "") |> String.trim()}
                String.starts_with?(t, "deadline_miss_policy:") ->
                  {"deadline_miss_policy", t |> String.replace_prefix("deadline_miss_policy:", "") |> String.trim()}
                true ->
                  {nil, nil}
              end
            case key do
              nil ->
                {:cont, state}
              _ ->
                cur = state.timing_contract || %{}
                {:cont, %{state | timing_contract: Map.put(cur, key, val)}}
            end
        end

      state.in_capabilities ->
        cond do
          String.starts_with?(t, "## ") or String.starts_with?(t, "### ") ->
            # A heading ends the capabilities block; replay it below.
            {:replay, %{state | in_capabilities: false}}

          true ->
            caps =
              t
              |> String.split(",")
              |> Enum.map(&String.trim/1)
              |> Enum.reject(&(&1 == "" or &1 == "```"))
            {:cont, %{state | capabilities: Enum.uniq(state.capabilities ++ caps)}}
        end

      state.in_shadowing ->
        cond do
          String.starts_with?(t, "## ") or String.starts_with?(t, "### ") ->
            # A heading ends the shadowing block; replay it below.
            {:replay, %{state | in_shadowing: false}}

          true ->
            case Regex.run(~r/^shadow\s+(\S+)/, t) do
              [_, target_raw] ->
                target = target_raw |> String.split("→") |> List.first() |> String.trim()
                if target == "" do
                  {:cont, state}
                else
                  {:cont, %{state | shadow_targets: state.shadow_targets ++ [target]}}
                end
              _ ->
                {:cont, state}
            end
        end

      state.in_signature ->
        cond do
          String.starts_with?(t, "## ") or String.starts_with?(t, "### ") ->
            # A heading ends the signature block; replay it below.
            {:replay, %{state | in_signature: false}}

          true ->
            {key, val} =
              cond do
                String.starts_with?(t, "signer:") ->
                  {"signer", t |> String.replace_prefix("signer:", "") |> String.trim()}
                String.starts_with?(t, "pubkey_fp:") ->
                  {"pubkey_fp", t |> String.replace_prefix("pubkey_fp:", "") |> String.trim()}
                String.starts_with?(t, "algorithm:") ->
                  {"algorithm", t |> String.replace_prefix("algorithm:", "") |> String.trim()}
                String.starts_with?(t, "signature:") ->
                  {"signature", t |> String.replace_prefix("signature:", "") |> String.trim()}
                true ->
                  {nil, nil}
              end
            case key do
              nil -> {:cont, state}
              "signer" -> {:cont, %{state | signature_signer: val}}
              "pubkey_fp" -> {:cont, %{state | signature_pubkey_fp: val}}
              "algorithm" -> {:cont, %{state | signature_algorithm: val}}
              "signature" -> {:cont, %{state | signature_value: val}}
            end
        end

      state.in_determinism ->
        cond do
          String.starts_with?(t, "## ") or String.starts_with?(t, "### ") ->
            # A heading ends the determinism block; replay it below.
            {:replay, %{state | in_determinism: false}}

          true ->
            {key, val} =
              cond do
                String.starts_with?(t, "precision:") ->
                  {"precision", t |> String.replace_prefix("precision:", "") |> String.trim()}
                String.starts_with?(t, "rounding:") ->
                  {"rounding", t |> String.replace_prefix("rounding:", "") |> String.trim()}
                String.starts_with?(t, "sort_stability:") ->
                  {"sort_stability", t |> String.replace_prefix("sort_stability:", "") |> String.trim()}
                true ->
                  {nil, nil}
              end
            case key do
              nil -> {:cont, state}
              "precision" -> {:cont, %{state | determinism_precision: val}}
              "rounding" -> {:cont, %{state | determinism_rounding: val}}
              "sort_stability" -> {:cont, %{state | determinism_sort_stability: val}}
            end
        end

      state.in_guarantee ->
        cond do
          String.starts_with?(t, "## ") or String.starts_with?(t, "### ") ->
            # A heading ends the guarantee block; replay it below.
            {:replay, %{state | in_guarantee: false}}

          true ->
            {key, val} =
              cond do
                String.starts_with?(t, "metric:") ->
                  {"metric", t |> String.replace_prefix("metric:", "") |> String.trim()}
                String.starts_with?(t, "threshold:") ->
                  {"threshold", t |> String.replace_prefix("threshold:", "") |> String.trim()}
                String.starts_with?(t, "dataset:") ->
                  {"dataset", t |> String.replace_prefix("dataset:", "") |> String.trim()}
                true ->
                  {nil, nil}
              end
            case key do
              nil -> {:cont, state}
              "metric" -> {:cont, %{state | guarantee_metric: val}}
              "threshold" -> {:cont, %{state | guarantee_threshold: val}}
              "dataset" -> {:cont, %{state | guarantee_dataset: val}}
            end
        end

      state.in_proof ->
        cond do
          String.starts_with?(t, "## ") or String.starts_with?(t, "### ") ->
            case t do
              "### Model" -> {:cont, %{state | proof_has_model: true}}
              "### Invariant" -> {:cont, %{state | proof_has_invariant: true}}
              "### Trusted" -> {:cont, state}
              # Any other heading exits proof mode; replay it below.
              _ -> {:replay, %{state | in_proof: false}}
            end

          true ->
            {:cont, state}  # proof content lines are not parsed
        end

      state.in_compat_tests ->
        cond do
          not state.in_fence and (String.starts_with?(t, "## ") or String.starts_with?(t, "### ")) ->
            # A heading ends the compat-tests section; replay it (block boundary).
            {:replay, %{state | in_compat_tests: false}}

          String.starts_with?(t, "|") ->
            cond do
              String.starts_with?(t, "|-") or String.contains?(t, "Input") or
                String.contains?(t, "Output") or String.contains?(t, "Expected") ->
                {:cont, state}

              true ->
                cells = t |> String.trim_leading("|") |> String.trim_trailing("|")
                         |> String.split("|") |> Enum.map(&String.trim/1)
                case cells do
                  [input, expected | _] ->
                    test = {input, expected}
                    {:cont, %{state | compat_tests: state.compat_tests ++ [test]}}
                  _ ->
                    {:cont, state}
                end
            end

          true ->
            {:cont, state}
        end

      state.in_exports ->
        cond do
          not (String.starts_with?(t, "## ") or String.starts_with?(t, "### ")) ->
            # Collect comma/whitespace-separated exported names.
            toks = Regex.split(~r/[,\s]+/, t) |> Enum.map(&String.trim/1)
                    |> Enum.reject(fn x -> x == "" or x == "```" end)
            {:cont, %{state | exports: state.exports ++ toks}}

          true ->
            # A heading ends the exports section; replay it (block boundary).
            {:replay, %{state | in_exports: false}}
        end

      state.in_imports ->
        cond do
          String.starts_with?(t, "import") ->
            pkg = String.trim(String.replace_prefix(t, "import", ""))
            kind = cond do
              String.contains?(pkg, "optional") -> :optional
              String.contains?(pkg, "custom") -> :custom
              true -> :standard
            end
            clean = pkg |> String.split(~r/\s+/) |> List.first() |> String.trim_trailing(",")
            {:cont, %{state | imports: state.imports ++ [{clean, kind}]}}

          true ->
            # Non-import line: leave imports mode and replay this line.
            {:replay, %{state | in_imports: false}}
        end

      not state.in_fence and (String.starts_with?(t, "## ") or String.starts_with?(t, "### ")) ->
        handle_heading(t, state)

      state.in_fence and (t == "## Laws" or t == "## Tests") ->
        mode = if t == "## Laws", do: :laws, else: :tests
        {:cont, set_mode(state, mode)}

      state.blk != nil and String.starts_with?(t, "Fingerprint:") ->
        fp = String.trim(String.replace_prefix(t, "Fingerprint:", ""))
        {:cont, %{state | blk: %{state.blk | fp: fp}}}

      state.blk != nil and String.starts_with?(t, "# Pre:") ->
        {:cont, %{state | blk: %{state.blk | has_pre: true}}}

      state.blk != nil and String.starts_with?(t, "# Post:") ->
        {:cont, %{state | blk: %{state.blk | has_post: true}}}

      state.blk != nil and state.blk.mode == :tests and String.starts_with?(t, "|") ->
        cond do
          String.starts_with?(t, "|-") or String.contains?(t, "Input") or
            String.contains?(t, "Output") or String.contains?(t, "Expected") ->
            {:cont, state}

          true ->
            cells = t |> String.trim_leading("|") |> String.trim_trailing("|")
                     |> String.split("|") |> Enum.map(&String.trim/1)
            case cells do
              [input, expected | _] ->
                test = {input, expected}
                {:cont, %{state | blk: %{state.blk | tests: state.blk.tests ++ [test]}}}
              _ ->
                {:cont, state}
            end
        end

      # Signature detection must run BEFORE the `≡`-in-line law heuristic:
      # an operator whose glyph is `≡` (e.g. `≡ : ℕ × ℕ → ℕ`) would otherwise
      # be swallowed as a law line and lose its signature/name.
      state.blk != nil and state.blk.sig == "" and looks_like_signature(t) ->
        name = t |> String.split(":", parts: 2) |> List.first() |> String.trim()
        name = if name == "" or String.contains?(name, " "), do: state.blk.name, else: name
        {:cont, %{state | blk: %{state.blk | sig: t, name: name}}}

      state.blk != nil and (state.blk.mode == :laws or String.starts_with?(t, "∀") or
                            String.starts_with?(t, "∃") or String.contains?(t, "≡")) ->
        if String.contains?(t, "|") do
          {:cont, state}
        else
          {:cont, %{state | blk: %{state.blk | laws: state.blk.laws ++ [t]}}}
        end

      true ->
        {:cont, state}
    end
  end

  defp handle_heading(t, state) do
    case t do
      "### Signature" -> {:cont, set_mode(state, :sig)}
      "### Laws" -> {:cont, set_mode(state, :laws)}
      "## Laws" -> {:cont, set_mode(state, :laws)}
      "### Tests" -> {:cont, set_mode(state, :tests)}
      "## Tests" -> {:cont, set_mode(state, :tests)}
      _ ->
        state = flush(state)
        heading = t |> String.trim_leading("#") |> String.trim()
                   |> String.replace_prefix("Operation:", "") |> String.trim()
        {:cont, %{state | blk: new_blk(heading)}}
    end
  end

  defp set_mode(state, mode) do
    case state.blk do
      nil -> state
      blk -> %{state | blk: %{blk | mode: mode}}
    end
  end

  defp new_blk(heading) do
    %{name: heading, glyph: heading, sig: "", fp: nil, laws: [], tests: [], mode: :sig,
      has_pre: false, has_post: false}
  end

  # Mirror Rust flush_block: fp -> symbol; signed no-fp -> function; else discard.
  defp flush(state) do
    case state.blk do
      nil -> state
      %{fp: fp} = blk when fp != nil ->
        semantic = if blk.sig == "", do: "Any", else: blk.sig |> String.split("→") |> List.last() |> String.trim()
        sym = %{name: blk.name, glyph: blk.glyph, fingerprint: fp,
                semantic_class: semantic, definition: blk.sig,
                laws: blk.laws, tests: blk.tests,
                has_pre: blk.has_pre, has_post: blk.has_post}
        %{state | blk: nil, symbols: state.symbols ++ [sym]}
      %{sig: sig} = blk when sig != "" ->
        fn_ = %{name: blk.name, signature: blk.sig, effect: :pure,
                body: "", laws: blk.laws, tests: blk.tests}
        %{state | blk: nil, functions: state.functions ++ [fn_]}
      _ ->
        %{state | blk: nil}
    end
  end

  defp looks_like_signature(t) do
    not String.starts_with?(t, "|") and not String.starts_with?(t, "#") and
      String.contains?(t, ":") and String.contains?(t, "→")
  end

  # ============================================================
  # Iron Law checks (Law I / II / III / IV)
  # ============================================================

  def check(state) do
    violations = []

    # Law I — fingerprint uniqueness (within module).
    {violations, _seen} =
      Enum.reduce(state.symbols, {violations, MapSet.new()}, fn sym, {v, seen} ->
        if sym.fingerprint == nil do
          {v ++ ["MissingFingerprint(#{sym.name})"], seen}
        else
          if MapSet.member?(seen, sym.fingerprint) do
            {v ++ ["FingerprintConflict(#{sym.name}, #{sym.fingerprint})"], seen}
          else
            {v, MapSet.put(seen, sym.fingerprint)}
          end
        end
      end)

    # Law II — encoding to ℕ for non-numeric return types.
    encoders = Enum.map(state.functions, fn f -> "#{f.name} #{f.signature}" end)
    violations =
      Enum.reduce(state.symbols, violations, fn sym, v ->
        rt = sym.semantic_class
        if rt in @numeric_types do
          v
        else
          has_enc = Enum.any?(encoders, fn e ->
            String.contains?(String.downcase(e), "encode") and String.contains?(e, rt)
          end)
          if has_enc, do: v, else: v ++ ["MissingEncoding(#{sym.name})"]
        end
      end)

    # Law III — law declaration.
    violations =
      Enum.reduce(state.symbols, violations, fn sym, v ->
        if sym.laws == [], do: v ++ ["NoLawsDeclared(#{sym.name})"], else: v
      end)

    # Law IV — test mandatory.
    violations =
      Enum.reduce(state.symbols, violations, fn sym, v ->
        if sym.tests == [], do: v ++ ["NoTestsDefined(#{sym.name})"], else: v
      end)

    # E-02 (promoted 2026-08-01) — negative test mandatory:
    # every op needs ≥1 test whose expected output starts with ⊥.
    violations =
      Enum.reduce(state.symbols, violations, fn sym, v ->
        has_neg = Enum.any?(sym.tests, fn {_input, exp} ->
          String.starts_with?(String.trim(exp), "⊥")
        end)
        if has_neg, do: v, else: v ++ ["NoNegativeTest(#{sym.name})"]
      end)

    # E-03 (promoted 2026-08-01) — test portability:
    # every test's expected output must be semantically structured —
    # an error (⊥-prefixed) or a parseable literal — never an
    # implementation-specific format (float string, Map rendering, …).
    violations =
      Enum.reduce(state.symbols, violations, fn sym, v ->
        Enum.reduce(sym.tests, v, fn {_input, exp}, acc ->
          e = String.trim(exp)
          portable = String.starts_with?(e, "⊥") or match?({:ok, _}, parse_val(e))
          if portable, do: acc, else: acc ++ ["UnportableAssertion(#{sym.name}, #{exp})"]
        end)
      end)

    # E-04 (promoted 2026-08-01) — export completeness:
    # `## Exports` must match defined symbols (no ghost, no hidden).
    # Modules without an Exports block are not checked (v0.1 policy).
    violations =
      if state.exports == [] do
        violations
      else
        defined = MapSet.new(Enum.map(state.symbols, & &1.name))
        violations =
          Enum.reduce(state.exports, violations, fn exp, v ->
            if MapSet.member?(defined, exp),
              do: v,
              else: v ++ ["GhostExport(#{exp})"]
          end)
        Enum.reduce(state.symbols, violations, fn sym, v ->
          if sym.name in state.exports,
            do: v,
            else: v ++ ["HiddenExport(#{sym.name})"]
        end)
      end

    # E-05 (promoted 2026-08-01) — compatibility proof:
    # `## Compat Tests` (the previous version's canonical suite) must all pass,
    # otherwise the "backward compatible" claim is rejected.
    violations =
      Enum.reduce(state.compat_tests, violations, fn {input, expected}, v ->
        case eval_test(input, expected) do
          :ok -> v
          {:error, detail} -> v ++ ["CompatTestFailed(#{input}): #{detail}"]
        end
      end)

    # P-01 (spec_top_proofs.md) — proof-carrying spec structure:
    # a module declaring `## Proof` must have a `### Model` and a `### Invariant`,
    # and every operation must declare Pre and Post together (or neither).
    violations =
      if state.proof_declared do
        violations =
          if state.proof_has_model,
            do: violations,
            else: violations ++ ["MissingModel(#{state.name})"]
        violations =
          if state.proof_has_invariant,
            do: violations,
            else: violations ++ ["MissingInvariant(#{state.name})"]
        Enum.reduce(state.symbols, violations, fn sym, v ->
          if sym.has_pre == sym.has_post,
            do: v,
            else: v ++ ["IncompleteContract(#{sym.name})"]
        end)
      else
        violations
      end

    # E-06 (promoted 2026-08-01) — internal consistency adjudication:
    # test expected value must match the operation's declared return-type shape
    # (numeric return → numeric expectation, container return → list expectation).
    violations =
      Enum.reduce(state.symbols, violations, fn sym, v ->
        rt = sym.semantic_class |> String.trim()
        numeric = rt in @numeric_types
        container = Enum.any?(["List", "Tensor", "Map", "Seq", "Fmap"], fn k ->
          String.contains?(rt, k)
        end)
        if not numeric and not container do
          v  # unknown shape — cannot judge
        else
          Enum.reduce(sym.tests, v, fn {_input, exp}, acc ->
            e = String.trim(exp)
            if String.starts_with?(e, "⊥") do
              acc  # error path — no value shape to check
            else
              case parse_val(e) do
                {:ok, {:num, _}} ->
                  if container and not numeric,
                    do: acc ++ ["SignatureMismatch(#{sym.name}, #{exp})"],
                    else: acc
                {:ok, {:fnum, _}} ->
                  if container and not numeric,
                    do: acc ++ ["SignatureMismatch(#{sym.name}, #{exp})"],
                    else: acc
                {:ok, {:list, _}} ->
                  if numeric and not container,
                    do: acc ++ ["SignatureMismatch(#{sym.name}, #{exp})"],
                    else: acc
                :error ->
                  acc  # unparseable — E-03 portability already flags
              end
            end
          end)
        end
      end)

    # E-09 (promoted 2026-08-01) — probabilistic guarantee: a prediction op must
    # declare a performance floor (metric, threshold, dataset) well-formed. The
    # Verifier certifies the declaration only; production conformance is runtime
    # monitoring's job.
    violations =
      if not state.guarantee_declared do
        violations
      else
        metric = state.guarantee_metric || ""
        violations =
          if metric in ["accuracy", "f1", "brier"],
            do: violations,
            else: violations ++ ["MalformedGuarantee(invalid metric: #{inspect(metric)})"]
        violations =
          case Float.parse(state.guarantee_threshold || "") do
            {v, _} when v >= 0.0 and v <= 1.0 -> violations
            _ -> violations ++ ["MalformedGuarantee(invalid threshold: #{inspect(state.guarantee_threshold)} (expected 0..=1))"]
          end
        violations =
          if String.trim(state.guarantee_dataset || "") == "",
            do: violations ++ ["MalformedGuarantee(missing dataset)"],
            else: violations
        violations
      end

    # E-10 (promoted 2026-08-01) — evaluation determinism: a module declaring
    # `## Determinism` must declare numeric precision (positive integer),
    # rounding (round|floor|ceil|trunc), and sort_stability (true|false).
    # Extends Law VIII (temporal determinism) to numeric evaluation.
    violations =
      if not state.determinism_declared do
        violations
      else
        precision = state.determinism_precision || ""
        violations =
          case Integer.parse(precision) do
            {v, _} when v >= 1 -> violations
            _ -> violations ++ ["MalformedDeterminism(invalid precision: #{inspect(precision)} (expected positive integer))"]
          end
        rounding = state.determinism_rounding || ""
        violations =
          if rounding in ["round", "floor", "ceil", "trunc"],
            do: violations,
            else: violations ++ ["MalformedDeterminism(invalid rounding: #{inspect(rounding)} (expected round|floor|ceil|trunc))"]
        sort_stab = state.determinism_sort_stability || ""
        violations =
          if sort_stab in ["true", "false"],
            do: violations,
            else: violations ++ ["MalformedDeterminism(invalid sort_stability: #{inspect(sort_stab)} (expected true|false))"]
        violations
      end

    # E-08 S-01 Level 1 (2026-08-01) — package signature: a module declaring
    # `## Signature` must provide a well-formed signer, pubkey_fp (sha256:),
    # algorithm (ed25519), and a non-empty signature. Modules without a
    # signature still verify (backward compatible — Law VI).
    violations =
      if not state.signature_declared do
        violations
      else
        violations =
          if String.trim(state.signature_signer || "") == "",
            do: violations ++ ["MalformedSignature(missing signer)"],
            else: violations
        fp = state.signature_pubkey_fp || ""
        violations =
          if String.starts_with?(fp, "sha256:") and byte_size(fp) > 7,
            do: violations,
            else: violations ++ ["MalformedSignature(invalid pubkey_fp: #{inspect(fp)} (expected sha256:…))"]
        algo = state.signature_algorithm || ""
        violations =
          if algo == "ed25519",
            do: violations,
            else: violations ++ ["MalformedSignature(invalid algorithm: #{inspect(algo)} (expected ed25519))"]
        violations =
          if String.trim(state.signature_value || "") == "",
            do: violations ++ ["MalformedSignature(missing signature)"],
            else: violations
        violations
      end

    # §S Shadowing & Binding Discipline (2026-08-01):
    # - DuplicateSymbol: a module must not define the same symbol name twice
    #   (Meta-Rule 2 / No Synonyms, §S R3 determinism).
    # - ShadowTargetMissing: every `## Shadowing` declaration must reference a
    #   symbol that actually exists (§S R1 explicit declaration).
    # - OpaqueShadowAttempt: math-domain symbols are Opaque-class and must not
    #   be shadowed (§S R5).
    opaque_math = ["⊕", "⊗", "⊖", "⊘", "⊙", "≡", "≥", "≤", "∈", "ℕ", "ℤ", "ℚ", "ℝ"]
    violations =
      Enum.reduce(state.shadow_targets, violations, fn target, v ->
        # §C constant fingerprints (0xK0xx math / 0xQ0xx physics) are Opaque
        # class too (§S.3.1 core-constant) — shadow attempts are violations.
        if target in opaque_math or String.starts_with?(target, ["0xK", "0xQ"]),
          do: v ++ ["OpaqueShadowAttempt(#{target})"],
          else: v
      end)
    violations =
      Enum.reduce(state.symbols, violations, fn sym, v ->
        if sym.name in Enum.map(state.symbols, & &1.name) do
          v
        else
          v
        end
      end)
    # Duplicate symbol detection via set.
    seen = MapSet.new()
    {violations, _seen} =
      Enum.reduce(state.symbols, {violations, seen}, fn sym, {v, seen} ->
        if MapSet.member?(seen, sym.name) do
          {v ++ ["DuplicateSymbol(#{sym.name})"], seen}
        else
          {v, MapSet.put(seen, sym.name)}
        end
      end)
    # Shadow targets must resolve to defined symbols. Qualified names
    # (e.g. finance.base.Δ) reference external-package symbols that v0.1
    # cannot resolve — only local names are checked.
    defined = MapSet.new(Enum.map(state.symbols, & &1.name))
    violations =
      Enum.reduce(state.shadow_targets, violations, fn target, v ->
        cond do
          String.contains?(target, ".") ->
            v
          MapSet.member?(defined, target) ->
            # R7: declared Free-class shadow — verification passes, but the
            # report flags a warning (spec_top_rules.md §S R7 / S-11).
            IO.puts("⚠️ R7-warning: free-class shadow of #{target} (declared; verification passes)")
            v
          true ->
            v ++ ["ShadowTargetMissing(#{target})"]
        end
      end)

    {violations == [], violations}
  end

  # ============================================================
  # Minimal canonical-test evaluator (tensor ops subset)
  # ============================================================

  # Values: {:num, int} | {:list, [value]}

  def run_tests(state) do
    {passed, total, failures} =
      Enum.reduce(state.symbols, {0, 0, []}, fn sym, {p, t, f} ->
        Enum.reduce(sym.tests, {p, t, f}, fn {input, expected}, {p, t, f} ->
          t = t + 1
          case eval_test(input, expected) do
            :ok -> {p + 1, t, f}
            {:error, detail} -> {p, t, f ++ ["TestFailed(#{sym.name}, #{input}): #{detail}"]}
          end
        end)
      end)
    {passed, total, failures}
  end

  defp eval_test(input, expected) do
    expect_err = String.starts_with?(String.trim(expected), "⊥")
    case eval_expr(input) do
      {:ok, v} ->
        if expect_err do
          {:error, "expected error, got #{fmt(v)}"}
        else
          case parse_val(expected) do
            {:ok, exp} when exp == v -> :ok
            {:ok, exp} -> {:error, "expected #{fmt(exp)}, got #{fmt(v)}"}
            :error -> {:error, "unparseable expectation: #{expected}"}
          end
        end
      {:error, e} ->
        if expect_err, do: :ok, else: {:error, "evaluation failed: #{e}"}
    end
  end

  defp eval_expr(s) do
    t = String.trim(s)
    cond do
      String.contains?(t, "where shape mismatch") -> {:error, "ShapeError"}
      String.contains?(t, "⊕") ->
        [a, b] = String.split(t, "⊕", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: elemwise_add(va, vb)
      String.contains?(t, "⊗") ->
        [a, b] = String.split(t, "⊗", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: mat_mul(va, vb)
      String.contains?(t, "⊖") ->
        [a, b] = String.split(t, "⊖", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: elemwise_sub(va, vb)
      String.contains?(t, "⊘") ->
        [a, b] = String.split(t, "⊘", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: elemwise_div(va, vb)
      String.contains?(t, "⊙") ->
        [a, b] = String.split(t, "⊙", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: elemwise_mul(va, vb)
      String.contains?(t, "≡") ->
        [a, b] = String.split(t, "≡", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: value_eq(va, vb)
      String.contains?(t, "≥") ->
        [a, b] = String.split(t, "≥", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: value_cmp(va, vb, :ge)
      String.contains?(t, "≤") ->
        [a, b] = String.split(t, "≤", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: value_cmp(va, vb, :le)
      String.contains?(t, "∈") ->
        [a, b] = String.split(t, "∈", parts: 2)
        with {:ok, va} <- eval_expr(a), {:ok, vb} <- eval_expr(b),
             do: value_in(va, vb)
      String.starts_with?(t, "index(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 6..-2//1)
        case split_top_level(inner, ?,) do
          {target, idx} ->
            with {:ok, tv} <- eval_expr(target), {:ok, iv} <- parse_val(idx),
                 do: index_into(tv, iv)
          nil -> {:error, "bad index args: #{inner}"}
        end
      # §SK — SocketKit Protocol operations (spec_p0_socketkit.md §SK.3).
      # Real function calls, not spec-expression aliases: mirrors
      # verify_consensus.py so the corpus consensus gate verifies app behavior.
      String.starts_with?(t, "task_create(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case split_top_level(inner, ?,) do
          {a, b} ->
            with {:ok, {:num, author}} <- eval_expr(a),
                 {:ok, {:num, bounty}} <- eval_expr(b) do
              if bounty < 0 do
                {:error, "BountyErr"}
              else
                {:ok, {:list, [{:num, author}, {:num, bounty}, {:num, 0}, {:num, 0}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad task_create args: #{inner}"}
        end
      String.starts_with?(t, "accept_task(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case split_top_level(inner, ?,) do
          {task_s, hunter_s} ->
            with {:ok, {:list, task}} <- eval_expr(task_s),
                 {:ok, {:num, hunter}} <- eval_expr(hunter_s) do
              if length(task) != 4 do
                {:error, "TypeError"}
              else
                case task do
                  [a, b, {:num, 0}, {:num, 0}] ->
                    {:ok, {:list, [a, b, {:num, 1}, {:num, hunter}]}}
                  _ -> {:error, "StateError"}
                end
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad accept_task args: #{inner}"}
        end
      String.starts_with?(t, "task_submit(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        with {:ok, {:list, task}} <- eval_expr(inner) do
          if length(task) != 4 do
            {:error, "TypeError"}
          else
            case task do
              [a, b, {:num, 1}, h] -> {:ok, {:list, [a, b, {:num, 2}, h]}}
              _ -> {:error, "StateError"}
            end
          end
        else
          _ -> {:error, "TypeError"}
        end
      String.starts_with?(t, "task_accept(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case split_top_level(inner, ?,) do
          {task_s, caller_s} ->
            with {:ok, {:list, task}} <- eval_expr(task_s),
                 {:ok, {:num, caller}} <- eval_expr(caller_s) do
              if length(task) != 4 do
                {:error, "TypeError"}
              else
                case task do
                  [a, b, {:num, 2}, h] ->
                    if caller == elem(a, 1) do
                      {:ok, {:list, [a, b, {:num, 3}, h]}}
                    else
                      {:error, "AuthError"}
                    end
                  _ -> {:error, "StateError"}
                end
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad task_accept args: #{inner}"}
        end
      String.starts_with?(t, "review_merge(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 13..-2//1)
        case eval_expr(inner) do
          {:ok, {:list, opinions}} ->
            result =
              Enum.reduce_while(opinions, {0, 0}, fn o, {wa, wr} ->
                case o do
                  {:list, [{:num, _rid}, {:num, vote}, {:num, weight}]} ->
                    cond do
                      vote == 1 -> {:cont, {wa + weight, wr}}
                      vote == 0 -> {:cont, {wa, wr + weight}}
                      true -> {:halt, :type_error}
                    end
                  _ -> {:halt, :shape_error}
                end
              end)
            case result do
              {wa, wr} -> {:ok, {:num, if(wa >= wr, do: 1, else: 0)}}
              :type_error -> {:error, "TypeError"}
              :shape_error -> {:error, "ShapeError"}
            end
          _ -> {:error, "TypeError"}
        end
      String.starts_with?(t, "contribution_score(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 19..-2//1)
        case eval_expr(inner) do
          {:ok, {:list, actions}} ->
            result =
              Enum.reduce_while(actions, 0, fn a, acc ->
                case a do
                  {:list, [{:num, _aid}, {:num, _kind}, {:num, delta}]} ->
                    {:cont, acc + delta}
                  _ -> {:halt, :shape_error}
                end
              end)
            case result do
              total when is_integer(total) -> {:ok, {:num, max(total, 0)}}
              :shape_error -> {:error, "ShapeError"}
            end
          _ -> {:error, "TypeError"}
        end
      String.starts_with?(t, "credit_score(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 13..-2//1)
        case eval_expr(inner) do
          {:ok, {:list, events}} ->
            result =
              Enum.reduce_while(events, 100, fn e, acc ->
                case e do
                  {:list, [{:num, kind}, {:num, count}]} ->
                    cond do
                      kind == 0 -> {:cont, acc + 5 * count}
                      kind == 1 -> {:cont, Enum.reduce(1..count//1, acc, fn _, c -> div(c * 7, 10) end)}
                      true -> {:halt, :type_error}
                    end
                  _ -> {:halt, :shape_error}
                end
              end)
            case result do
              credit when is_integer(credit) -> {:ok, {:num, max(credit, 0)}}
              :type_error -> {:error, "TypeError"}
              :shape_error -> {:error, "ShapeError"}
            end
          _ -> {:error, "TypeError"}
        end
      # §PF — Portfolio Protocol operations (spec_p0_portfolio.md §PF.3).
      # Second novel domain: finance. Real function calls, mirrors
      # verify_consensus.py so the consensus gate verifies investment semantics.
      String.starts_with?(t, "portfolio_new(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 14..-2//1)
        case eval_expr(inner) do
          {:ok, {:num, cash}} ->
            if cash < 0 do
              {:error, "TypeError"}
            else
              {:ok, {:list, [{:num, cash}, {:num, 0}, {:num, 0}]}}
            end
          _ -> {:error, "TypeError"}
        end
      String.starts_with?(t, "buy(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 4..-2//1)
        case split_all_top_level(inner, ?,) do
          [p_s, a_s, q_s] ->
            with {:ok, {:list, [{:num, cash}, {:num, q_a}, {:num, q_b}]}} <- eval_expr(p_s),
                 {:ok, {:num, asset}} <- eval_expr(a_s),
                 {:ok, {:num, qty}} <- eval_expr(q_s) do
              cond do
                asset not in [0, 1] ->
                  {:error, "UnknownAsset"}
                cash < qty ->
                  {:error, "InsufficientFunds"}
                asset == 0 ->
                  {:ok, {:list, [{:num, cash - qty}, {:num, q_a + qty}, {:num, q_b}]}}
                true ->
                  {:ok, {:list, [{:num, cash - qty}, {:num, q_a}, {:num, q_b + qty}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          _ -> {:error, "bad buy args: #{inner}"}
        end
      String.starts_with?(t, "sell(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 5..-2//1)
        case split_all_top_level(inner, ?,) do
          [p_s, a_s, q_s] ->
            with {:ok, {:list, [{:num, cash}, {:num, q_a}, {:num, q_b}]}} <- eval_expr(p_s),
                 {:ok, {:num, asset}} <- eval_expr(a_s),
                 {:ok, {:num, qty}} <- eval_expr(q_s) do
              held = if asset == 0, do: q_a, else: q_b
              cond do
                asset not in [0, 1] ->
                  {:error, "UnknownAsset"}
                qty > held ->
                  {:error, "InsufficientShares"}
                asset == 0 ->
                  {:ok, {:list, [{:num, cash + qty}, {:num, q_a - qty}, {:num, q_b}]}}
                true ->
                  {:ok, {:list, [{:num, cash + qty}, {:num, q_a}, {:num, q_b - qty}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          _ -> {:error, "bad sell args: #{inner}"}
        end
      String.starts_with?(t, "portfolio_value(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 16..-2//1)
        case eval_expr(inner) do
          {:ok, {:list, [{:num, cash}, {:num, q_a}, {:num, q_b}]}} ->
            {:ok, {:num, cash + q_a + q_b}}
          _ -> {:error, "TypeError"}
        end
      String.starts_with?(t, "risk_score(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 11..-2//1)
        case eval_expr(inner) do
          {:ok, {:list, [_cash, {:num, q_a}, {:num, q_b}]}} ->
            {:ok, {:num, q_a + q_b}}
          _ -> {:error, "TypeError"}
        end
      # §SK.3.9 额度制 quota — 每月额度 / 扣减 / 月底清零.
      String.starts_with?(t, "quota_new(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 10..-2//1)
        case eval_expr(inner) do
          {:ok, {:num, monthly}} ->
            if monthly < 0 do
              {:error, "TypeError"}
            else
              {:ok, {:list, [{:num, monthly}, {:num, monthly}]}}
            end
          _ -> {:error, "TypeError"}
        end
      String.starts_with?(t, "quota_use(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 10..-2//1)
        case split_top_level(inner, ?,) do
          {q_s, a_s} ->
            with {:ok, {:list, [{:num, monthly}, {:num, remaining}]}} <- eval_expr(q_s),
                 {:ok, {:num, amount}} <- eval_expr(a_s) do
              if amount > remaining do
                {:error, "QuotaExhausted"}
              else
                {:ok, {:list, [{:num, monthly}, {:num, remaining - amount}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad quota_use args: #{inner}"}
        end
      String.starts_with?(t, "quota_reset(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case eval_expr(inner) do
          {:ok, {:list, [{:num, monthly}, _remaining]}} ->
            {:ok, {:list, [{:num, monthly}, {:num, monthly}]}}
          _ -> {:error, "TypeError"}
        end
      # §SK.3.10 积分制 points — 托管 / 释放 / 提现.
      t == "points_new()" ->
        {:ok, {:list, [{:num, 0}, {:num, 0}]}}
      String.starts_with?(t, "points_hold(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case split_top_level(inner, ?,) do
          {p_s, x_s} ->
            with {:ok, {:list, [{:num, escrow}, {:num, available}]}} <- eval_expr(p_s),
                 {:ok, {:num, amount}} <- eval_expr(x_s) do
              {:ok, {:list, [{:num, escrow + amount}, {:num, available}]}}
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad points_hold args: #{inner}"}
        end
      String.starts_with?(t, "points_release(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 15..-2//1)
        case split_top_level(inner, ?,) do
          {p_s, x_s} ->
            with {:ok, {:list, [{:num, escrow}, {:num, available}]}} <- eval_expr(p_s),
                 {:ok, {:num, amount}} <- eval_expr(x_s) do
              if amount > escrow do
                {:error, "InsufficientEscrow"}
              else
                {:ok, {:list, [{:num, escrow - amount}, {:num, available + amount}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad points_release args: #{inner}"}
        end
      String.starts_with?(t, "points_withdraw(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 16..-2//1)
        case split_top_level(inner, ?,) do
          {p_s, x_s} ->
            with {:ok, {:list, [{:num, escrow}, {:num, available}]}} <- eval_expr(p_s),
                 {:ok, {:num, amount}} <- eval_expr(x_s) do
              if amount > available do
                {:error, "InsufficientPoints"}
              else
                {:ok, {:list, [{:num, escrow}, {:num, available - amount}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad points_withdraw args: #{inner}"}
        end
      # §SK.3.11 勋章制 badge_level — 0=铜 1=银 2=金 3=钻石.
      String.starts_with?(t, "badge_level(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case eval_expr(inner) do
          {:ok, {:num, score}} ->
            cond do
              score < 100 -> {:ok, {:num, 0}}
              score < 300 -> {:ok, {:num, 1}}
              score < 600 -> {:ok, {:num, 2}}
              true -> {:ok, {:num, 3}}
            end
          _ -> {:error, "TypeError"}
        end
      # §SK.3.12 核验师签发勋章 badge_issue — v ≥ 1000 授权核验师.
      String.starts_with?(t, "badge_issue(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case split_all_top_level(inner, ?,) do
          [v_s, u_s, s_s] ->
            with {:ok, {:num, verifier}} <- eval_expr(v_s),
                 {:ok, {:num, user}} <- eval_expr(u_s),
                 {:ok, {:num, score}} <- eval_expr(s_s) do
              if verifier < 1000 do
                {:error, "AuthError"}
              else
                level =
                  cond do
                    score < 100 -> 0
                    score < 300 -> 1
                    score < 600 -> 2
                    true -> 3
                  end
                {:ok, {:list, [{:num, verifier}, {:num, user}, {:num, level}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          _ -> {:error, "bad badge_issue args: #{inner}"}
        end
      # §SK.3.13 督导处理纠纷 dispute_review — 加权支持 ≥ 加权驳回.
      String.starts_with?(t, "dispute_review(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 15..-2//1)
        case eval_expr(inner) do
          {:ok, {:list, evidence}} ->
            result =
              Enum.reduce_while(evidence, {0, 0}, fn e, {ws, wr} ->
                case e do
                  {:list, [{:num, _rid}, {:num, side}, {:num, weight}]} ->
                    cond do
                      side == 1 -> {:cont, {ws + weight, wr}}
                      side == 0 -> {:cont, {ws, wr + weight}}
                      true -> {:halt, :type_error}
                    end
                  _ -> {:halt, :shape_error}
                end
              end)
            case result do
              {ws, wr} -> {:ok, {:num, if(ws >= wr, do: 1, else: 0)}}
              :type_error -> {:error, "TypeError"}
              :shape_error -> {:error, "ShapeError"}
            end
          _ -> {:error, "TypeError"}
        end
      # §SK.3.14 团机制 team_create / team_join — Team = [owner, kind, size, capacity].
      String.starts_with?(t, "team_create(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 12..-2//1)
        case split_all_top_level(inner, ?,) do
          [o_s, k_s, c_s] ->
            with {:ok, {:num, owner}} <- eval_expr(o_s),
                 {:ok, {:num, kind}} <- eval_expr(k_s),
                 {:ok, {:num, capacity}} <- eval_expr(c_s) do
              if capacity < 1 do
                {:error, "TypeError"}
              else
                {:ok, {:list, [{:num, owner}, {:num, kind}, {:num, 1}, {:num, capacity}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          _ -> {:error, "bad team_create args: #{inner}"}
        end
      String.starts_with?(t, "team_join(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 10..-2//1)
        case split_top_level(inner, ?,) do
          {t_s, m_s} ->
            with {:ok, {:list, [{:num, owner}, {:num, kind}, {:num, size}, {:num, capacity}]}} <- eval_expr(t_s),
                 {:ok, {:num, _member}} <- eval_expr(m_s) do
              if size >= capacity do
                {:error, "TeamFull"}
              else
                {:ok, {:list, [{:num, owner}, {:num, kind}, {:num, size + 1}, {:num, capacity}]}}
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad team_join args: #{inner}"}
        end
      # §SK.3.15 团内收益按贡献分配 team_share — shareᵢ = floor(r·cᵢ/Σc).
      String.starts_with?(t, "team_share(") and String.ends_with?(t, ")") ->
        inner = String.slice(t, 11..-2//1)
        case split_top_level(inner, ?,) do
          {c_s, r_s} ->
            with {:ok, {:list, contribs}} <- eval_expr(c_s),
                 {:ok, {:num, reward}} <- eval_expr(r_s) do
              parsed = Enum.map(contribs, fn
                {:list, [{:num, m}, {:num, c}]} -> {m, c}
                _ -> :bad
              end)
              if Enum.any?(parsed, &(&1 == :bad)) do
                {:error, "ShapeError"}
              else
                total = Enum.sum(Enum.map(parsed, fn {_, c} -> c end))
                if total == 0 do
                  {:error, "DivByZero"}
                else
                  {:ok, {:list, Enum.map(parsed, fn {m, c} ->
                    {:list, [{:num, m}, {:num, div(reward * c, total)}]}
                  end)}}
                end
              end
            else
              _ -> {:error, "TypeError"}
            end
          nil -> {:error, "bad team_share args: #{inner}"}
        end
      t == "I₂" ->
        {:ok, {:list, [{:list, [{:num, 1}, {:num, 0}]},
                       {:list, [{:num, 0}, {:num, 1}]}]}}
      Map.has_key?(@constants, t) ->
        {:ok, Map.fetch!(@constants, t)}
      true ->
        # Unparseable literal (e.g. "+5", "1e3") must surface as a proper
        # {:error, _} tuple — a bare :error atom would crash eval_test's
        # case (CaseClauseError). Mirrors Rust's Err("unparseable: …").
        case parse_val(t) do
          {:ok, v} -> {:ok, v}
          :error -> {:error, "unparseable: #{t}"}
        end
    end
  end

  defp elemwise_add({:num, x}, {:num, y}), do: {:ok, {:num, x + y}}
  defp elemwise_add({:fnum, x}, {:fnum, y}), do: {:ok, {:fnum, x + y}}
  defp elemwise_add({:num, x}, {:fnum, y}), do: {:ok, {:fnum, x * 1.0 + y}}
  defp elemwise_add({:fnum, x}, {:num, y}), do: {:ok, {:fnum, x + y * 1.0}}
  defp elemwise_add({:list, xs}, {:list, ys}) do
    if length(xs) != length(ys) do
      {:error, "ShapeError"}
    else
      result = Enum.zip(xs, ys)
               |> Enum.map(fn {x, y} -> elemwise_add(x, y) end)
      case Enum.split_with(result, &match?({:ok, _}, &1)) do
        {oks, []} -> {:ok, {:list, Enum.map(oks, fn {:ok, v} -> v end)}}
        _ -> {:error, "ShapeError"}
      end
    end
  end
  defp elemwise_add(_, _), do: {:error, "ShapeError"}

  defp mat_mul({:list, rows}, {:list, vec}) do
    result = Enum.map(rows, fn row ->
      case row do
        {:list, cells} ->
          if length(cells) != length(vec) do
            {:error, "ShapeError"}
          else
            acc =
              Enum.zip(cells, vec)
              |> Enum.reduce_while({0, false}, fn {c, v}, {acc, is_float} ->
                   case {c, v} do
                     {{:num, cn}, {:num, vn}} -> {:cont, {acc + cn * vn, is_float}}
                     {{:fnum, cn}, {:fnum, vn}} -> {:cont, {acc + cn * vn, true}}
                     {{:num, cn}, {:fnum, vn}} -> {:cont, {acc + cn * 1.0 * vn, true}}
                     {{:fnum, cn}, {:num, vn}} -> {:cont, {acc + cn * vn * 1.0, true}}
                     _ -> {:halt, {:type_error, is_float}}
                   end
                 end)
            case acc do
              {:type_error, _} -> {:error, "TypeError"}
              {n, true} -> {:ok, {:fnum, n * 1.0}}
              {n, false} -> {:ok, {:num, n}}
            end
          end
        _ -> {:error, "ShapeError"}
      end
    end)
    case Enum.split_with(result, &match?({:ok, _}, &1)) do
      {oks, []} -> {:ok, {:list, Enum.map(oks, fn {:ok, v} -> v end)}}
      _ -> {:error, "ShapeError"}
    end
  end
  defp mat_mul(_, _), do: {:error, "ShapeError"}

  # ⊖ — element-wise subtraction (mirrors elemwise_add).
  defp elemwise_sub({:num, x}, {:num, y}), do: {:ok, {:num, x - y}}
  defp elemwise_sub({:fnum, x}, {:fnum, y}), do: {:ok, {:fnum, x - y}}
  defp elemwise_sub({:num, x}, {:fnum, y}), do: {:ok, {:fnum, x * 1.0 - y}}
  defp elemwise_sub({:fnum, x}, {:num, y}), do: {:ok, {:fnum, x - y * 1.0}}
  defp elemwise_sub({:list, xs}, {:list, ys}) do
    if length(xs) != length(ys) do
      {:error, "ShapeError"}
    else
      result = Enum.zip(xs, ys)
               |> Enum.map(fn {x, y} -> elemwise_sub(x, y) end)
      case Enum.split_with(result, &match?({:ok, _}, &1)) do
        {oks, []} -> {:ok, {:list, Enum.map(oks, fn {:ok, v} -> v end)}}
        _ -> {:error, "ShapeError"}
      end
    end
  end
  defp elemwise_sub(_, _), do: {:error, "ShapeError"}

  # ⊘ — element-wise division: num/num -> num when divisible, else fnum;
  # division by zero is a DivByZero error.
  defp elemwise_div({:num, x}, {:num, y}) when y != 0 do
    if rem(x, y) == 0, do: {:ok, {:num, div(x, y)}}, else: {:ok, {:fnum, x / y}}
  end
  defp elemwise_div({:num, _}, {:num, 0}), do: {:error, "DivByZero"}
  defp elemwise_div({:fnum, _}, {:fnum, y}) when y == 0.0, do: {:error, "DivByZero"}
  defp elemwise_div({:fnum, x}, {:fnum, y}), do: {:ok, {:fnum, x / y}}
  defp elemwise_div({:num, x}, {:fnum, y}) when y != 0.0, do: {:ok, {:fnum, x / y}}
  defp elemwise_div({:num, _}, {:fnum, y}) when y == 0.0, do: {:error, "DivByZero"}
  defp elemwise_div({:fnum, x}, {:num, y}) when y != 0, do: {:ok, {:fnum, x / y}}
  defp elemwise_div({:fnum, _}, {:num, 0}), do: {:error, "DivByZero"}
  defp elemwise_div({:list, xs}, {:list, ys}) do
    if length(xs) != length(ys) do
      {:error, "ShapeError"}
    else
      result = Enum.zip(xs, ys)
               |> Enum.map(fn {x, y} -> elemwise_div(x, y) end)
      case Enum.split_with(result, &match?({:ok, _}, &1)) do
        {oks, []} -> {:ok, {:list, Enum.map(oks, fn {:ok, v} -> v end)}}
        _ -> {:error, "ShapeError"}
      end
    end
  end
  defp elemwise_div(_, _), do: {:error, "ShapeError"}

  # ⊙ — element-wise multiplication (Hadamard, mirrors elemwise_add).
  defp elemwise_mul({:num, x}, {:num, y}), do: {:ok, {:num, x * y}}
  defp elemwise_mul({:fnum, x}, {:fnum, y}), do: {:ok, {:fnum, x * y}}
  defp elemwise_mul({:num, x}, {:fnum, y}), do: {:ok, {:fnum, x * 1.0 * y}}
  defp elemwise_mul({:fnum, x}, {:num, y}), do: {:ok, {:fnum, x * y * 1.0}}
  defp elemwise_mul({:list, xs}, {:list, ys}) do
    if length(xs) != length(ys) do
      {:error, "ShapeError"}
    else
      result = Enum.zip(xs, ys)
               |> Enum.map(fn {x, y} -> elemwise_mul(x, y) end)
      case Enum.split_with(result, &match?({:ok, _}, &1)) do
        {oks, []} -> {:ok, {:list, Enum.map(oks, fn {:ok, v} -> v end)}}
        _ -> {:error, "ShapeError"}
      end
    end
  end
  defp elemwise_mul(_, _), do: {:error, "ShapeError"}

  # ≡ — structural equality, returns num 1/0; mixed kinds are TypeError.
  defp value_eq({:num, x}, {:num, y}), do: {:ok, {:num, if(x == y, do: 1, else: 0)}}
  defp value_eq({:fnum, x}, {:fnum, y}), do: {:ok, {:num, if(x == y, do: 1, else: 0)}}
  defp value_eq({:list, xs}, {:list, ys}) do
    if length(xs) != length(ys) do
      {:ok, {:num, 0}}
    else
      Enum.reduce_while(Enum.zip(xs, ys), {:ok, {:num, 1}}, fn {x, y}, acc ->
        case value_eq(x, y) do
          {:ok, {:num, 1}} -> {:cont, acc}
          {:ok, {:num, 0}} -> {:halt, {:ok, {:num, 0}}}
          {:error, e} -> {:halt, {:error, e}}
        end
      end)
    end
  end
  defp value_eq(_, _), do: {:error, "TypeError"}

  # ≥ / ≤ — scalar comparison, returns num 1/0; lists are TypeError.
  defp value_cmp({:list, _}, _, _), do: {:error, "TypeError"}
  defp value_cmp(_, {:list, _}, _), do: {:error, "TypeError"}
  defp value_cmp(a, b, op) do
    {x, y} = {to_float(a), to_float(b)}
    case op do
      :ge -> {:ok, {:num, if(x >= y, do: 1, else: 0)}}
      :le -> {:ok, {:num, if(x <= y, do: 1, else: 0)}}
    end
  end

  defp to_float({:num, n}), do: n * 1.0
  defp to_float({:fnum, f}), do: f

  # ∈ — membership: element a in list b, returns num 1/0; non-list is TypeError.
  defp value_in(_, {:list, []}), do: {:ok, {:num, 0}}
  defp value_in(a, {:list, [h | t]}) do
    case value_eq(a, h) do
      {:ok, {:num, 1}} -> {:ok, {:num, 1}}
      {:error, e} -> {:error, e}
      {:ok, {:num, 0}} -> value_in(a, {:list, t})
    end
  end
  defp value_in(_, _), do: {:error, "TypeError"}

  defp index_into(target, idx) do
    path = collect_path(idx, [])
    Enum.reduce_while(path, {:ok, target}, fn i, {:ok, cur} ->
      case cur do
        {:list, items} ->
          case Enum.at(items, i) do
            nil -> {:halt, {:error, "OutOfBounds"}}
            v -> {:cont, {:ok, v}}
          end
        _ -> {:halt, {:error, "TypeError"}}
      end
    end)
  end

  defp collect_path({:num, n}, acc), do: acc ++ [n]
  defp collect_path({:list, items}, acc), do: Enum.reduce(items, acc, &collect_path/2)
  defp collect_path(_, acc), do: acc

  # Literal parsing: `2`, `0.5`, `[1,2,3]`, `[[1,2],[3,4]]`, `(1,0)`.
  defp parse_val(s) do
    # Normalize common Unicode minus/hyphen variants to ASCII '-' (M-4).
    t = s |> String.replace(["−", "﹣", "－", "‐", "‑"], "-") |> String.trim()
    cond do
      Regex.match?(~r/^-?\d+$/, t) ->
        {:ok, {:num, String.to_integer(t)}}
      Regex.match?(~r/^-?\d+\.\d+$/, t) ->
        {:ok, {:fnum, String.to_float(t)}}
      String.starts_with?(t, "[") and String.ends_with?(t, "]") ->
        parse_list(String.slice(t, 1..-2//1))
      String.starts_with?(t, "(") and String.ends_with?(t, ")") ->
        parse_list(String.slice(t, 1..-2//1))
      true ->
        :error
    end
  end

  defp parse_list(inner) do
    if String.trim(inner) == "" do
      {:ok, {:list, []}}
    else
      parts = split_all_top_level(inner, ?,) |> Enum.map(&String.trim/1)
      result = Enum.map(parts, &parse_val/1)
      case Enum.split_with(result, &match?({:ok, _}, &1)) do
        {oks, []} -> {:ok, {:list, Enum.map(oks, fn {:ok, v} -> v end)}}
        _ -> :error
      end
    end
  end

  # Split at the first depth-0 occurrence of sep (returns {left, right} or nil).
  defp split_top_level(s, sep), do: split_top_level(s, sep, 0, 0)

  defp split_top_level(s, _sep, i, _depth) when i >= byte_size(s), do: nil
  defp split_top_level(s, sep, i, depth) do
    c = :binary.at(s, i)
    cond do
      c in [?[, ?(] -> split_top_level(s, sep, i + 1, depth + 1)
      c in [?], ?)] -> split_top_level(s, sep, i + 1, max(depth - 1, 0))
      c == sep and depth == 0 ->
        left = binary_part(s, 0, i)
        right = binary_part(s, i + 1, byte_size(s) - i - 1)
        {left, right}
      true -> split_top_level(s, sep, i + 1, depth)
    end
  end

  defp split_all_top_level(s, sep), do: split_all_top_level(s, sep, 0, 0, 0, [])

  # Walk with a current-slice start; at a depth-0 separator, cut a piece.
  defp split_all_top_level(s, _sep, start, i, _depth, acc) when i >= byte_size(s) do
    piece = binary_part(s, start, i - start) |> String.trim()
    Enum.reverse([piece | acc])
  end
  defp split_all_top_level(s, sep, start, i, depth, acc) do
    c = :binary.at(s, i)
    cond do
      c in [?[, ?(] -> split_all_top_level(s, sep, start, i + 1, depth + 1, acc)
      c in [?], ?)] -> split_all_top_level(s, sep, start, i + 1, max(depth - 1, 0), acc)
      c == sep and depth == 0 ->
        piece = binary_part(s, start, i - start) |> String.trim()
        split_all_top_level(s, sep, i + 1, i + 1, depth, [piece | acc])
      true -> split_all_top_level(s, sep, start, i + 1, depth, acc)
    end
  end

  defp fmt({:num, n}), do: Integer.to_string(n)
  defp fmt({:fnum, f}), do: Float.to_string(f)
  defp fmt({:list, items}), do: "[" <> Enum.map_join(items, ",", &fmt/1) <> "]"

  # ============================================================
  # §SK — SocketKit Protocol: Auditable App Behavior
  # (spec/spec_p0_socketkit.md — mirrors impl/python/sigma_core.py §SK)
  # ============================================================

  # Task 状态机 (需求文档 §五): 0=open 1=in_progress 2=pending_review 3=completed
  @status_open 0
  @status_in_progress 1
  @status_pending 2
  @status_completed 3

  @doc "Task posting: (author, bounty) → [author, bounty, 0, 0] (open, unclaimed)."
  def task_create(author, bounty) when bounty >= 0, do: {:ok, [author, bounty, @status_open, 0]}
  def task_create(_author, bounty) when bounty < 0, do: {:error, "BountyErr"}

  @doc "Task claiming: status 0 → 1 (in_progress), hunter recorded."
  def accept_task([_a, _b, @status_open, 0] = task, hunter), do: {:ok, List.replace_at(List.replace_at(task, 2, @status_in_progress), 3, hunter)}
  def accept_task(_task, _hunter), do: {:error, "StateError"}

  @doc "Work submission: status 1 → 2 (pending_review), hunter preserved."
  def task_submit([_a, _b, @status_in_progress, _h] = task), do: {:ok, List.replace_at(task, 2, @status_pending)}
  def task_submit(_task), do: {:error, "StateError"}

  @doc "Acceptance confirmation: status 2 → 3 (completed), hunter preserved."
  def task_accept([_a, _b, @status_pending, _h] = task, caller) do
    if caller == hd(task) do
      {:ok, List.replace_at(task, 2, @status_completed)}
    else
      {:error, "AuthError"}
    end
  end
  def task_accept(_task, _caller), do: {:error, "StateError"}

  @doc "Review resolution: opinions[] → decision (1 = accept, 0 = reject)."
  def review_merge(opinions) do
    w_accept = opinions |> Enum.filter(fn [_, vote, _] -> vote == 1 end)
                        |> Enum.map(fn [_, _, w] -> w end) |> Enum.sum()
    w_reject = opinions |> Enum.filter(fn [_, vote, _] -> vote == 0 end)
                        |> Enum.map(fn [_, _, w] -> w end) |> Enum.sum()
    if w_accept >= w_reject, do: 1, else: 0
  end

  @doc "Contribution scoring: actions[] → points, fold ⊕ over deltas floored at 0."
  def contribution_score(actions) do
    total = actions |> Enum.map(fn [_, _, delta] -> delta end) |> Enum.sum()
    max(total, 0)
  end

  @doc "Credit scoring: events[] → credit (契分制). base 100; +5 per complete; breach ×0.7 (×7 ÷10, floor)."
  def credit_score(events) do
    credit = Enum.reduce(events, 100, fn e, acc ->
      [kind, count] = e
      case kind do
        0 -> acc + 5 * count
        1 -> Enum.reduce(1..count//1, acc, fn _, c -> div(c * 7, 10) end)
        _ -> acc
      end
    end)
    max(credit, 0)
  end

  defp encode_list(xs), do: encode_list(xs, 0)
  defp encode_list([], _), do: 0
  defp encode_list([x | rest], i), do: x * round(:math.pow(1000, i)) + encode_list(rest, i + 1)

  @doc "Law II — Task → ℕ."
  def encode_task(task), do: encode_list(task)

  @doc "Law II — Opinion → ℕ."
  def encode_opinion(opinion), do: encode_list(opinion)

  @doc "Law II — Action → ℕ."
  def encode_action(action), do: encode_list(action)

  @doc "Law II — Event → ℕ."
  def encode_event(event), do: encode_list(event)

  # ============================================================
  # §SK.3.9–3.11 — 找茬五大制度补齐 (v0.20, 需求文档 §四)
  # 额度制 quota / 积分制 points / 勋章制 badge_level
  # ============================================================

  @doc "额度制: 本月额度 = 剩余额度. §SK.3.9 — monthly ≥ 0."
  def quota_new(monthly) when monthly >= 0, do: {:ok, [monthly, monthly]}
  def quota_new(_monthly), do: {:error, "TypeError"}

  @doc "额度制: 扣减额度，不足则 ⊥ QuotaExhausted. §SK.3.9."
  def quota_use([monthly, remaining], amount) when amount <= remaining, do: {:ok, [monthly, remaining - amount]}
  def quota_use(_quota, _amount), do: {:error, "QuotaExhausted"}

  @doc "额度制: 月底清零，恢复满额. §SK.3.9."
  def quota_reset([monthly, _remaining]), do: [monthly, monthly]

  @doc "积分制: 无托管、无可用. §SK.3.10."
  def points_new(), do: [0, 0]

  @doc "积分制: 冻结（托管中）. §SK.3.10."
  def points_hold([escrow, available], amount), do: [escrow + amount, available]

  @doc "积分制: 释放入可用，不足托管则 ⊥ InsufficientEscrow. §SK.3.10."
  def points_release([escrow, available], amount) when amount <= escrow, do: {:ok, [escrow - amount, available + amount]}
  def points_release(_points, _amount), do: {:error, "InsufficientEscrow"}

  @doc "积分制: 提现，不足可用则 ⊥ InsufficientPoints. §SK.3.10."
  def points_withdraw([escrow, available], amount) when amount <= available, do: {:ok, [escrow, available - amount]}
  def points_withdraw(_points, _amount), do: {:error, "InsufficientPoints"}

  @doc "勋章制: 0=铜 1=银 2=金 3=钻石. §SK.3.11."
  def badge_level(score) when score < 100, do: 0
  def badge_level(score) when score < 300, do: 1
  def badge_level(score) when score < 600, do: 2
  def badge_level(_score), do: 3

  @doc "核验师签发勋章: (v, u, s) → [v, u, badge_level(s)]. §SK.3.12 — v ≥ 1000 授权核验师."
  def badge_issue(verifier, user, score) when verifier >= 1000, do: {:ok, [verifier, user, badge_level(score)]}
  def badge_issue(_verifier, _user, _score), do: {:error, "AuthError"}

  @doc "督导处理纠纷: evidence[] → decision (1 = 支持, 0 = 驳回). §SK.3.13."
  def dispute_review(evidence) do
    w_support = evidence |> Enum.filter(fn [_, side, _] -> side == 1 end)
                         |> Enum.map(fn [_, _, w] -> w end) |> Enum.sum()
    w_reject = evidence |> Enum.filter(fn [_, side, _] -> side == 0 end)
                        |> Enum.map(fn [_, _, w] -> w end) |> Enum.sum()
    if w_support >= w_reject, do: 1, else: 0
  end

  @doc "团机制: 受茬团/找茬团创建. §SK.3.14 — capacity ≥ 1 否则 ⊥ TypeError."
  def team_create(owner, kind, capacity) when capacity >= 1, do: {:ok, [owner, kind, 1, capacity]}
  def team_create(_owner, _kind, _capacity), do: {:error, "TypeError"}

  @doc "团机制: 加入团队. §SK.3.14 — 未满员则加入，满员 → ⊥ TeamFull."
  def team_join([owner, kind, size, capacity], _member) when size < capacity, do: {:ok, [owner, kind, size + 1, capacity]}
  def team_join(_team, _member), do: {:error, "TeamFull"}

  @doc "团内收益按贡献分配: shareᵢ = floor(r·cᵢ/Σc). §SK.3.15 — total = 0 → ⊥ DivByZero."
  def team_share(contribs, reward) do
    total = Enum.sum(Enum.map(contribs, fn [_, c] -> c end))
    cond do
      total == 0 -> {:error, "DivByZero"}
      true -> {:ok, Enum.map(contribs, fn [m, c] -> [m, div(reward * c, total)] end)}
    end
  end

  @doc "Law II — Quota → ℕ."
  def encode_quota(quota), do: encode_list(quota)

  @doc "Law II — Points → ℕ."
  def encode_points(points), do: encode_list(points)

  @doc "Run the §SK self-check (mirrors sigma_core.py §SK block); returns {passed, total}."
  def sk_self_check do
    # task_create returns {:ok, task}; unwrap once so accept_task/submit/accept
    # receive the bare task list (they take the state-machine form directly).
    {:ok, t100} = task_create(7, 100)
    {:ok, t50} = task_create(5, 50)
    {:ok, t0} = task_create(2, 0)
    {:ok, claimed} = accept_task(t100, 3)
    {:ok, claimed9} = accept_task(t0, 9)
    {:ok, submitted} = task_submit(claimed)
    {:ok, submitted9} = task_submit(claimed9)
    {:ok, done} = task_accept(submitted, 7)
    {:ok, done9} = task_accept(submitted9, 2)

    checks = [
      # §SK.3.1 task_create
      {"task_create_shape", task_create(1, 100) == {:ok, [1, 100, 0, 0]}},
      {"task_create_open", match?({:ok, [_, _, 0, _]}, task_create(5, 50))},
      {"task_create_unclaimed", match?({:ok, [_, _, _, 0]}, task_create(5, 50))},
      {"task_create_bounty_ge0", task_create(2, 0) == {:ok, [2, 0, 0, 0]}},
      {"task_create_neg_bounty_rejected", task_create(1, -5) == {:error, "BountyErr"}},
      # §SK.3.2 accept_task
      {"accept_task_claim", claimed == [7, 100, 1, 3]},
      {"accept_task_in_progress", match?([_, _, 1, _], claimed9)},
      {"accept_task_non_open_rejected", accept_task([7, 100, 1, 3], 5) == {:error, "StateError"}},
      # §SK.3.3 task_submit
      {"task_submit_pending", submitted == [7, 100, 2, 3]},
      {"task_submit_hunter_preserved", match?([_, _, _, 9], submitted9)},
      {"task_submit_non_in_progress_rejected", task_submit(t50) == {:error, "StateError"}},
      # §SK.3.4 task_accept
      {"task_accept_completed", done == [7, 100, 3, 3]},
      {"task_accept_hunter_preserved", match?([_, _, _, 9], done9)},
      {"task_accept_non_author_rejected", task_accept(submitted, 9) == {:error, "AuthError"}},
      {"task_accept_non_pending_rejected", task_accept(t50, 5) == {:error, "StateError"}},
      # §SK.3.6 review_merge
      {"review_merge_accept", review_merge([[1, 1, 3], [2, 1, 2]]) == 1},            # 5 ≥ 0
      {"review_merge_reject", review_merge([[1, 0, 3], [2, 1, 2]]) == 0},            # 2 < 3
      {"review_merge_tie_accept", review_merge([[1, 0, 3], [2, 1, 3]]) == 1},        # 3 ≥ 3
      {"review_merge_binary", review_merge([[1, 1, 1], [2, 0, 1]]) in [0, 1]},
      {"review_merge_order_indep",
       review_merge([[1, 1, 3], [2, 0, 2], [3, 1, 1]]) ==
       review_merge([[3, 1, 1], [1, 1, 3], [2, 0, 2]])},
      # §SK.3.5 contribution_score
      {"contribution_fold", contribution_score([[1, 1, 3], [2, 2, 4]]) == 7},
      {"contribution_floor_at_0", contribution_score([[1, 1, -5], [2, 2, 3]]) == 0}, # -2 floored
      {"contribution_zero_neutral",
       contribution_score([[1, 1, 3]]) == contribution_score([[1, 1, 3], [9, 0, 0]])},
      # §SK.3.7 credit_score
      {"credit_base", credit_score([]) == 100},
      {"credit_complete", credit_score([[0, 1]]) == 105},
      {"credit_breach", credit_score([[1, 1]]) == 70},                              # 100×0.7
      {"credit_breach_then_complete", credit_score([[1, 1], [0, 1]]) == 75},        # 70+5
      {"credit_double_breach", credit_score([[1, 2]]) == 49},                       # 70×0.7
      # §SK.3.9 额度制 quota
      {"quota_new_shape", quota_new(50) == {:ok, [50, 50]}},
      {"quota_use", quota_use([50, 50], 20) == {:ok, [50, 30]}},
      {"quota_reset", quota_reset([50, 30]) == [50, 50]},
      {"quota_use_exhausted_rejected", quota_use([50, 50], 60) == {:error, "QuotaExhausted"}},
      # §SK.3.10 积分制 points
      {"points_new_shape", points_new() == [0, 0]},
      {"points_hold", points_hold(points_new(), 100) == [100, 0]},
      {"points_release", points_release(points_hold(points_new(), 100), 100) == {:ok, [0, 100]}},
      {"points_withdraw",
       points_withdraw(elem(points_release(points_hold(points_new(), 100), 100), 1), 40) == {:ok, [0, 60]}},
      {"points_release_insufficient_escrow_rejected",
       points_release(points_new(), 10) == {:error, "InsufficientEscrow"}},
      {"points_withdraw_insufficient_available_rejected",
       points_withdraw(points_new(), 10) == {:error, "InsufficientPoints"}},
      # §SK.3.11 勋章制 badge_level
      {"badge_zero", badge_level(0) == 0},
      {"badge_bronze", badge_level(50) == 0},
      {"badge_silver", badge_level(150) == 1},
      {"badge_gold", badge_level(450) == 2},
      {"badge_diamond", badge_level(900) == 3},
      {"badge_bounded", badge_level(12345) in [0, 1, 2, 3]},
      {"badge_monotonic", badge_level(100) <= badge_level(200)},
      {"encode_quota_nat", encode_quota([50, 30]) >= 0},
      {"encode_points_nat", encode_points([0, 60]) >= 0},
      # §SK.3.12 核验师签发勋章 badge_issue
      {"badge_issue_silver", badge_issue(1001, 3, 105) == {:ok, [1001, 3, 1]}},
      {"badge_issue_gold", badge_issue(1002, 3, 450) == {:ok, [1002, 3, 2]}},
      {"badge_issue_diamond", badge_issue(1001, 3, 900) == {:ok, [1001, 3, 3]}},
      {"badge_issue_unauthorized_rejected", badge_issue(999, 3, 105) == {:error, "AuthError"}},
      # §SK.3.13 督导处理纠纷 dispute_review
      {"dispute_support", dispute_review([[1, 1, 3], [2, 1, 2]]) == 1},            # 5 ≥ 0
      {"dispute_reject", dispute_review([[1, 0, 5], [2, 1, 2]]) == 0},            # 2 < 5
      {"dispute_binary", dispute_review([[1, 1, 1], [2, 0, 1]]) in [0, 1]},
      {"dispute_order_indep",
       dispute_review([[1, 1, 3], [2, 0, 2], [3, 1, 1]]) ==
       dispute_review([[3, 1, 1], [1, 1, 3], [2, 0, 2]])},
      # §SK.3.14 团机制 team_create / team_join
      {"team_create_shape", team_create(7, 0, 3) == {:ok, [7, 0, 1, 3]}},
      {"team_create_finder", team_create(3, 1, 2) == {:ok, [3, 1, 1, 2]}},
      {"team_create_zero_capacity_rejected", team_create(7, 0, 0) == {:error, "TypeError"}},
      {"team_join", team_join([7, 0, 1, 3], 5) == {:ok, [7, 0, 2, 3]}},
      {"team_join_full_rejected", team_join([7, 0, 2, 2], 5) == {:error, "TeamFull"}},
      # §SK.3.15 团内收益按贡献分配 team_share
      {"team_share_even", team_share([[3, 2], [4, 4]], 6) == {:ok, [[3, 2], [4, 4]]}},
      {"team_share_weighted", team_share([[3, 1], [4, 3]], 10) == {:ok, [[3, 2], [4, 7]]}},
      {"team_share_zero_total_rejected", team_share([[3, 0], [4, 0]], 5) == {:error, "DivByZero"}},
      # §SK.4 encodings (Law II)
      {"encode_task_nat", encode_task([1, 2, 0, 0]) >= 0},
      {"encode_distinct", encode_task([1, 2, 0, 0]) != encode_task([1, 3, 0, 0])},
      {"encode_opinion_nat", encode_opinion([1, 1, 3]) >= 0},
      {"encode_action_nat", encode_action([1, 1, 3]) >= 0},
      {"encode_event_nat", encode_event([0, 1]) >= 0}
    ]

    failed = Enum.filter(checks, fn {_name, ok} -> not ok end)
    Enum.each(failed, fn {name, _} -> IO.puts("  ❌ SK.#{name}") end)
    {length(checks) - length(failed), length(checks)}
  end

  @doc "Run the §SK.6 MVP story (spec_p0_socketkit.md) — 12 steps + INV-1/3/4,
  mirroring sigma_app.py run_story and sigma-runtime --story (Law XIII)."
  def sk_story do
    {:ok, q0} = quota_new(50)
    {:ok, task} = task_create(7, 100)
    {:ok, q1} = quota_use(q0, 1)
    p0 = points_hold(points_new(), 100)
    {:ok, claimed} = accept_task(task, 3)
    {:ok, submitted} = task_submit(claimed)
    {:ok, done} = task_accept(submitted, 7)
    {:ok, p1} = points_release(p0, 100)
    {:ok, p2} = points_withdraw(p1, 100)
    credit = credit_score([[0, 1]])
    contribution = contribution_score([[3, 1, 10]])
    badge = badge_level(105)

    checks = [
      # §SK.6.1–12 十二步
      {"1 open_quota", q0 == [50, 50]},
      {"2 task_create", task == [7, 100, 0, 0]},
      {"3 quota_use", q1 == [50, 49]},
      {"4 points_hold", p0 == [100, 0]},
      {"5 accept_task", claimed == [7, 100, 1, 3]},
      {"6 task_submit", submitted == [7, 100, 2, 3]},
      {"7 task_accept", done == [7, 100, 3, 3]},
      {"8 points_release", p1 == [0, 100]},
      {"9 points_withdraw", p2 == [0, 0]},
      {"10 credit_score", credit == 105},
      {"11 contribution_score", contribution == 10},
      {"12 badge_level", badge == 1},
      # 剧本不变量 (spec §SK.6)
      {"INV-1 monotonic", [Enum.at(task, 2), Enum.at(claimed, 2),
                           Enum.at(submitted, 2), Enum.at(done, 2)] == [0, 1, 2, 3]},
      {"INV-3 bounty conserved", Enum.at(done, 1) == 100},
      {"INV-4 author accept", Enum.at(done, 0) == 7}
    ]

    failed = Enum.filter(checks, fn {_name, ok} -> not ok end)
    Enum.each(failed, fn {name, _} -> IO.puts("  ❌ SK.6.#{name}") end)
    {length(checks) - length(failed), length(checks)}
  end
end

# ============================================================
# CLI entry (mirrors the Rust verifier's exit-code contract)
# ============================================================

case System.argv() do
  ["--sk-self-check" | _] ->
    {passed, total} = SigmaVerify.sk_self_check()
    IO.puts("sigma_core self-check (§SK): #{passed}/#{total} passed")
    System.halt(if passed == total, do: 0, else: 1)

  ["--sk-story" | _] ->
    {passed, total} = SigmaVerify.sk_story()
    IO.puts("sigma_core story (§SK.6): #{passed}/#{total} passed")
    System.halt(if passed == total, do: 0, else: 1)

  [path | _] ->
    state = SigmaVerify.parse(path)
    {ok, violations} = SigmaVerify.check(state)
    {passed, total, test_failures} = SigmaVerify.run_tests(state)
    all = violations ++ test_failures
    if ok and all == [] do
      IO.puts("PASS: #{passed}/#{total} tests passed")
      System.halt(0)
    else
      IO.puts("FAIL: #{Enum.join(Enum.take(all, 3), "; ")}")
      System.halt(1)
    end

  _ ->
    IO.puts("usage: elixir sigma_verify.exs <module.md> | --sk-self-check | --sk-story")
    System.halt(2)
end
