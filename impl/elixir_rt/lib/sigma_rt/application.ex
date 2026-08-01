defmodule SigmaRT.Application do
  @moduledoc """
  SigmaRT Application — starts the supervision tree.
  """
  use Application

  def start(_type, _args) do
    children = [
      {Task.Supervisor, name: SigmaRT.Supervisor}
    ]

    opts = [strategy: :one_for_one, name: SigmaRT.SupervisorTree]
    Supervisor.start_link(children, opts)
  end
end
