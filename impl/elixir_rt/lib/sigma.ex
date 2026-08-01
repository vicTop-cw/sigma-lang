defmodule Sigma do
  @moduledoc """
  ΣLang Elixir Runtime — BEAM backend for ΣLang semantics.

  This module provides the Elixir-side runtime for executing
  ΣLang modules that have passed Verifier certification.
  """

  # ==========================================================================
  # Core Types (mirroring ΣLang core@1.0)
  # ==========================================================================

  @type natural :: non_neg_integer()
  # integer() is a built-in Elixir type; no custom alias needed.
  @type rational :: {integer(), pos_integer()}
  @type real :: float()
  @type complex :: {real(), real()}
  # boolean() is a built-in Elixir type; keep ΣLang's ⊤/⊥ under a distinct name.
  @type sigma_boolean :: :"⊤" | :"⊥"
  @type symbol :: atom()
  @type sigma_string :: String.t()

  # Result type (from §E)
  @type result(v, e) :: {:ok, v} | {:err, e}

  # Confidence type (from §C)
  @type confidence :: float() # ∈ [0.0, 1.0]
  @type p_value(t) :: {t, confidence()}

  # Effect tags (from §I)
  @type effect :: :pure | :io | :comm | :net | :fs | :time | :rand

  # ==========================================================================
  # Result Monad (§E)
  # ==========================================================================

  @doc "Return a successful result."
  def ok(v), do: {:ok, v}

  @doc "Return an error result."
  def err(e), do: {:err, e}

  @doc "Bind: monadic composition (>>=)."
  def bind({:ok, v}, f), do: f.(v)
  def bind({:err, e}, _f), do: {:err, e}

  @doc "Map over ok value."
  def map({:ok, v}, f), do: {:ok, f.(v)}
  def map({:err, e}, _f), do: {:err, e}

  @doc "Map over err value."
  def map_err({:ok, v}, _f), do: {:ok, v}
  def map_err({:err, e}, f), do: {:err, f.(e)}

  @doc "Flatten nested results."
  def flatten({:ok, {:ok, v}}), do: {:ok, v}
  def flatten({:ok, {:err, e}}), do: {:err, e}
  def flatten({:err, e}), do: {:err, e}

  @doc "Alternative: try fallback on error."
  def or_else({:ok, v}, _fallback), do: {:ok, v}
  def or_else({:err, _}, fallback), do: fallback.()

  @doc "Unwrap with default."
  def unwrap_or({:ok, v}, _default), do: v
  def unwrap_or({:err, _}, default), do: default

  # ==========================================================================
  # Confidence Operations (§C)
  # ==========================================================================

  @doc "Confidence multiplication (independent events)."
  def conf_mul(c1, c2), do: c1 * c2

  @doc "Confidence addition (probabilistic union)."
  def conf_add(c1, c2), do: c1 + c2 - c1 * c2

  @doc "Confidence negation."
  def conf_not(c), do: 1.0 - c

  @doc "Confidence minimum (AND / pessimistic)."
  def conf_min(c1, c2), do: min(c1, c2)

  @doc "Confidence maximum (OR)."
  def conf_max(c1, c2), do: max(c1, c2)

  @doc "Attach confidence to a value."
  def with_conf(v, c), do: {v, c}

  @doc "Extract confidence from P⟨T⟩."
  def get_conf({_v, c}), do: c

  @doc "Extract value from P⟨T⟩."
  def get_val({v, _c}), do: v

  # ==========================================================================
  # Lift Functions (§C.8)
  # ==========================================================================

  @doc "Lift a unary function into P⟨T⟩."
  def lift(f, {v, c}), do: {f.(v), c}

  @doc "Lift a binary function into P⟨T⟩ (pessimistic: min conf)."
  def lift2(f, {v1, c1}, {v2, c2}), do: {f.(v1, v2), min(c1, c2)}

  # ==========================================================================
  # Consensus (§C.10)
  # ==========================================================================

  @doc "Weighted consensus from multiple AI messages."
  def consensus(messages) when is_list(messages) do
    total_conf = Enum.sum(for {_v, c} <- messages, do: c)

    if total_conf == 0 do
      nil
    else
      weighted_sum =
        Enum.reduce(messages, 0.0, fn {v, c}, acc ->
          acc + v * c
        end)

      pooled_conf =
        Enum.reduce(messages, 0.0, fn {_v, c}, acc ->
          acc + c * c
        end) / (total_conf * total_conf)

      {weighted_sum / total_conf, pooled_conf}
    end
  end

  @doc "Take the more confident message."
  def combine_msgs(m1, m2) do
    if get_conf(m1) > get_conf(m2), do: m1, else: m2
  end

  # ==========================================================================
  # Time & Causal Order (§T)
  # ==========================================================================

  defmodule Clock do
    @moduledoc "Lamport logical clock."

    defstruct [:id, :time]

    def new(id), do: %__MODULE__{id: id, time: 0}

    def tick(%__MODULE__{time: t} = clock) do
      %{clock | time: t + 1}
    end

    def send(%__MODULE__{time: t} = clock) do
      {%{clock | time: t + 1}, t + 1}
    end

    def recv(%__MODULE__{time: local_t} = clock, remote_t) do
      new_t = max(local_t, remote_t) + 1
      %{clock | time: new_t}
    end
  end

  defmodule VectorClock do
    @moduledoc "Vector clock for causal ordering."

    defstruct [:id, :n_agents, :v]

    def new(n_agents, id) do
      %__MODULE__{id: id, n_agents: n_agents, v: List.duplicate(0, n_agents)}
    end

    def tick(%__MODULE__{id: id, v: v} = vc) do
      new_v = List.replace_at(v, id, Enum.at(v, id) + 1)
      %{vc | v: new_v}
    end

    def send(%__MODULE__{} = vc) do
      vc = tick(vc)
      {vc, vc.v}
    end

    def recv(%__MODULE__{v: local_v} = vc, remote_v) do
      max_v = Enum.zip(local_v, remote_v) |> Enum.map(fn {a, b} -> max(a, b) end)
      vc = tick(%{vc | v: max_v})
      vc
    end

    @doc "Check if vc1 happens-before vc2."
    def happens_before?(%{v: v1}, %{v: v2}) do
      Enum.all?(Enum.zip(v1, v2), fn {a, b} -> a <= b end) and
        Enum.any?(Enum.zip(v1, v2), fn {a, b} -> a < b end)
    end

    @doc "Check if two events are concurrent."
    def concurrent?(vc1, vc2) do
      not happens_before?(vc1, vc2) and not happens_before?(vc2, vc1)
    end
  end

  # ==========================================================================
  # I/O Operations (§I) — with capability checks
  # ==========================================================================

  defmodule IO do
    @moduledoc "I/O operations with capability enforcement."

    @type capability :: :read_file | :write_file | :network | :cmd_exec | :spawn_agent

    defstruct [:capabilities]

    def new(), do: %__MODULE__{capabilities: MapSet.new()}
    def grant(%__MODULE__{} = io, cap), do: %{io | capabilities: MapSet.put(io.capabilities, cap)}
    def revoke(%__MODULE__{} = io, cap), do: %{io | capabilities: MapSet.delete(io.capabilities, cap)}
    def has_cap?(%__MODULE__{} = io, cap), do: MapSet.member?(io.capabilities, cap)

    @doc "Read file (requires :read_file)."
    def read_file(%__MODULE__{} = io, path) do
      if has_cap?(io, :read_file) do
        case File.read(path) do
          {:ok, content} -> {:ok, content}
          {:error, _} -> {:err, :not_found}
        end
      else
        {:err, {:missing_capability, :read_file}}
      end
    end

    @doc "Write file (requires :write_file)."
    def write_file(%__MODULE__{} = io, path, content) do
      if has_cap?(io, :write_file) do
        case File.write(path, content) do
          :ok -> {:ok, nil}
          {:error, _} -> {:err, :io_error}
        end
      else
        {:err, {:missing_capability, :write_file}}
      end
    end

    @doc "HTTP GET (requires :network)."
    def http_get(%__MODULE__{} = io, url) do
      if has_cap?(io, :network) do
        # In production: use HTTPoison or similar
        # For now: stub
        {:ok, "response_from_#{url}"}
      else
        {:err, {:missing_capability, :network}}
      end
    end

    @doc "Execute command (requires :cmd_exec)."
    def exec_cmd(%__MODULE__{} = io, cmd) do
      if has_cap?(io, :cmd_exec) do
        case System.cmd("sh", ["-c", cmd]) do
          {output, 0} -> {:ok, output}
          {_output, _code} -> {:err, :exec_failed}
        end
      else
        {:err, {:missing_capability, :cmd_exec}}
      end
    end
  end

  # ==========================================================================
  # Resource Safety (§I.6)
  # ==========================================================================

  defmodule Resource do
    @moduledoc "Linear resource tracking."

    defstruct [:path, :closed]

    def open(path) do
      {:ok, %__MODULE__{path: path, closed: false}}
    end

    def close(%__MODULE__{closed: true}), do: {:err, :double_close}
    def close(%__MODULE__{closed: false} = r), do: {:ok, %{r | closed: true}}

    def use(%__MODULE__{closed: true}, _f), do: {:err, :use_after_close}
    def use(%__MODULE__{closed: false}, f), do: {:ok, f.()}

    @doc "RAII-style with_file."
    def with_file(io, path, func) do
      case IO.read_file(io, path) do
        {:ok, content} ->
          result = func.(content)
          {:ok, result}
        err -> err
      end
    end
  end

  # ==========================================================================
  # Retry & Timeout (§T.5)
  # ==========================================================================

  @doc "Retry an effect n times."
  def retry(_eff, 0), do: {:err, :exhausted_retries}
  def retry(eff, n) do
    case eff.() do
      {:ok, result} -> {:ok, result}
      {:err, _} -> retry(eff, n - 1)
    end
  end

  @doc "Timeout wrapper (simplified: checks deadline)."
  def timeout(eff, deadline_ms) do
    # In production: use Task.await with timeout
    task = Task.async(eff)
    case Task.await(task, deadline_ms) do
      {:ok, result} -> {:ok, result}
      {:timeout, _} -> {:err, :timeout}
      other -> other
    end
  end

  @doc "Race two effects (first to complete wins)."
  def race(eff1, eff2) do
    # Simplified: run both, return first result
    # Production: use Task.yield_many
    t1 = Task.async(eff1)
    t2 = Task.async(eff2)

    # Poll for first completion
    case Task.yield(t1, 100) || Task.yield(t2, 100) do
      {_, {:ok, result}} -> {:ok, result}
      _ -> {:err, :race_failed}
    end
  end

  # ==========================================================================
  # Safe Retry (§I.9)
  # ==========================================================================

  @safe_ops [:http_get, :read_file, :exists, :list_dir, :recv, :connect, :now, :rand, :log]

  def safe_retry(op_name, max_retries) when op_name in @safe_ops do
    # Safe ops can be retried
    {:ok, "retried_#{op_name}_#{max_retries}_times"}
  end

  def safe_retry(op_name, _max_retries) do
    {:err, {:unsafe_retry_attempted, op_name}}
  end

  # ==========================================================================
  # Verification Helpers
  # ==========================================================================

  @doc "Check if a function is pure (no IO calls)."
  def is_pure?(func_body) when is_binary(func_body) do
    not String.contains?(func_body, "read_file") and
      not String.contains?(func_body, "write_file") and
      not String.contains?(func_body, "http_") and
      not String.contains?(func_body, "send") and
      not String.contains?(func_body, "recv")
  end

  @doc "Verify effect type matches body."
  def verify_effect(func_name, body, declared_effect) do
    body_has_io = String.contains?(body, "read_file") or
                  String.contains?(body, "write_file") or
                  String.contains?(body, "http_") or
                  String.contains?(body, "send")

    cond do
      body_has_io and declared_effect == :pure ->
        {:err, {:undeclared_effect, func_name, :io}}

      not body_has_io and declared_effect != :pure ->
        {:err, {:unnecessary_effect, func_name}}

      true ->
        {:ok, :verified}
    end
  end
end
