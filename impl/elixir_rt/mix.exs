defmodule SigmaElixir.MixProject do
  use Mix.Project

  def project do
    [
      app: :sigma_elixir,
      version: "0.1.0",
      elixir: "~> 1.15",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  # No external deps: sigma_verify.exs and the runtime use only the stdlib.
  # (jason was declared but never used; offline environments could not fetch it.)
  defp deps do
    []
  end
end
