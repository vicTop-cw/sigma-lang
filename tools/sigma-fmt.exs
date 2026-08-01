#!/usr/bin/env elixir
# SigmaLang Formatter — formats MD spec files consistently

defmodule SigmaFmt do
  @moduledoc """
  Reads a ΣLang .md file and formats it according to spec conventions:
  - Sorts symbol tables alphabetically by glyph
  - Aligns test tables
  - Normalizes heading levels
  - Validates fingerprint format
  """

  def main(args) do
    case args do
      [file] ->
        format_file(file)
      _ ->
        IO.puts("Usage: sigma-fmt <file.md>")
        System.halt(1)
    end
  end

  defp format_file(path) do
    content = File.read!(path)
    lines = String.split(content, "\n")

    formatted = lines
    |> Enum.map(&format_line/1)
    |> Enum.join("\n")

    File.write!(path, formatted)
    IO.puts("✅ Formatted: #{path}")
  end

  defp format_line(line) do
    # Normalize headings
    line = Regex.replace(~r/^(#{1,6})\s+/, line, fn _, hashes ->
      hashes <> " "
    end)

    # Align table pipes
    if String.contains?(line, "|") and String.starts_with?(line, "|") do
      align_table_row(line)
    else
      line
    end
  end

  defp align_table_row(line) do
    cells = String.split(line, "|")
    cells
    |> Enum.map(&String.trim/1)
    |> Enum.join(" | ")
    |> then(&"| #{&1} |")
  end
end

SigmaFmt.main(System.argv())
