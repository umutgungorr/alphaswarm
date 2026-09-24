"""Unit tests for AlphaSwarm CLI."""

import json
from pathlib import Path
from alphaswarm.cli import main


def test_cli_analyze_markdown(tmp_path: Path, capsys):
    out_file = tmp_path / "report.md"
    ret = main(["analyze", "BTC", "--offline", "-o", str(out_file), "-f", "md"])
    assert ret == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "AlphaSwarm Intelligence Dossier: BTC" in content
    assert "Multi-Agent Debate Transcript" in content


def test_cli_analyze_html(tmp_path: Path, capsys):
    out_file = tmp_path / "report.html"
    ret = main(["analyze", "ETH", "--offline", "-o", str(out_file), "-f", "html"])
    assert ret == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "AlphaSwarm Intelligence: ETH" in content


def test_cli_analyze_json(tmp_path: Path, capsys):
    out_file = tmp_path / "report.json"
    ret = main(["analyze", "NVDA", "--offline", "-o", str(out_file), "-f", "json"])
    assert ret == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["symbol"] == "NVDA"
    assert "confidence_score" in data


def test_cli_scan(capsys):
    ret = main(["scan", "BTC", "ETH", "--offline"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "AlphaSwarm Screening Watchlist" in out
    assert "BTC" in out
    assert "ETH" in out


def test_cli_parser_serve():
    from alphaswarm.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["serve", "--port", "9090"])
    assert args.command == "serve"
    assert args.port == 9090
