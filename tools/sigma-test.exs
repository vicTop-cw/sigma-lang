#!/usr/bin/env elixir
# SigmaLang Test Runner — runs canonical tests against an AI implementation

defmodule SigmaTest do
  @moduledoc """
  Reads a ΣLang .md spec file, extracts test tables,
  and runs them against an AI-provided implementation module.

  Usage: sigma-test <spec.md> <impl_module>
  """

  def main(args) do
    case args do
      [spec_path, impl_module] ->
        run_tests(spec_path, impl_module)
      _ ->
        IO.puts("Usage: sigma-test <spec.md> <impl_module>")
        System.halt(1)
    end
  end

  defp run_tests(spec_path, impl_module) do
    content = File.read!(spec_path)

    tests = extract_tests(content)
    impl = String.to_atom("Elixir." <> impl_module)

    IO.puts("ΣLang Test Runner")
    IO.puts(String.duplicate("=", 50))
    IO.puts("Spec: #{spec_path}")
    IO.puts("Impl: #{impl_module}")
    IO.puts("")

    results = Enum.map(tests, fn {op, input, expected} ->
      actual = apply(impl, :run, [op, input])
      ok = actual == expected
      {op, input, expected, actual, ok}
    end)

    Enum.each(results, fn {op, input, expected, actual, ok} ->
      status = if ok, do: "✅", else: "❌"
      IO.puts("#{status} #{op}(#{input}) → expected #{expected}, got #{actual}")
    end)

    passed = Enum.count(results, fn {_,_,_,_,ok} -> ok end)
    total = length(results)

    IO.puts("")
    IO.puts("#{passed}/#{total} tests passed")

    if passed == total do
      IO.puts("🎉 All tests passed!")
      System.halt(0)
    else
      IO.puts("💥 Some tests failed.")
      System.halt(1)
    end
  end

  defp extract_tests(content) do
    # Simplified: looks for test tables in MD
    # In production: full MD AST parser
    content
    |> String.split("\n")
    |> extract_tests_from_lines([], nil)
  end

  defp extract_tests_from_lines([], acc, _), do: Enum.reverse(acc)
  defp extract_tests_from_lines([line | rest], acc, current_op) do
    cond do
      # Detect operation header
      Regex.match?(~r/###\s+(\w+)/, line) ->
        op = Regex.run(~r/###\s+(\w+)/, line) |> List.last()
        extract_tests_from_lines(rest, acc, op)

      # Detect test row
      String.starts_with?(line, "|") and current_op != nil ->
        cells = parse_table_row(line)
        if length(cells) >= 2 do
          input = Enum.at(cells, 0)
          expected = Enum.at(cells, 1)
          extract_tests_from_lines(rest, [{current_op, input, expected} | acc], current_op)
        else
          extract_tests_from_lines(rest, acc, current_op)
        end

      true ->
        extract_tests_from_lines(rest, acc, current_op)
    end
  end

  defp parse_table_row(line) do
    line
    |> String.split("|")
    |> Enum.map(&String.trim/1)
    |> Enum.reject(&(&1 == ""))
  end
end

SigmaTest.main(System.argv())
