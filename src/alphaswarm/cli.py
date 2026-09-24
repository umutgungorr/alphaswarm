"""Command Line Interface for AlphaSwarm."""

import argparse
import http.server
import json
import socketserver
import sys
import threading
from pathlib import Path
from alphaswarm.graph import AlphaSwarmGraph
from alphaswarm.market_data import get_market_data
from alphaswarm.models import AgentThought, ConsensusVerdict
from alphaswarm.reporters import generate_html_report, generate_markdown_report


# ANSI color helpers
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RESET = "\033[0m"

# Ensure UTF-8 support on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



def print_agent_thought(thought: AgentThought, round_num: int):
    role_color = (
        CYAN if thought.role.value == "TECHNICAL"
        else MAGENTA if thought.role.value == "SENTIMENT"
        else RED
    )
    stance_color = (
        GREEN if "BULL" in thought.stance.value
        else RED if "BEAR" in thought.stance.value
        else YELLOW
    )
    role_icon = (
        "📐" if thought.role.value == "TECHNICAL"
        else "📰" if thought.role.value == "SENTIMENT"
        else "🛡️"
    )

    sys.stdout.write(
        f"\n  {role_icon} {role_color}{BOLD}[R{round_num} // {thought.callsign}] {thought.agent_name}{RESET} "
        f"&bull; {stance_color}{thought.stance.value} ({thought.confidence * 100:.0f}%){RESET}\n"
    )
    sys.stdout.write(f"    {DIM}\"{thought.thesis}\"{RESET}\n")
    for kp in thought.key_points[:2]:
        sys.stdout.write(f"    {GREEN}+ {kp}{RESET}\n")
    for rk in thought.identified_risks[:2]:
        sys.stdout.write(f"    {RED}- ⚠️ {rk}{RESET}\n")


def print_verdict_card(verdict: ConsensusVerdict):
    stance_color = (
        GREEN if "BULL" in verdict.final_stance.value
        else RED if "BEAR" in verdict.final_stance.value
        else YELLOW
    )

    sys.stdout.write("\n" + "═" * 65 + "\n")
    sys.stdout.write(f"  {BOLD}⚡ ALPHASWARM CONSENSUS DOSSIER // {verdict.symbol}{RESET}\n")
    sys.stdout.write("═" * 65 + "\n")
    sys.stdout.write(f"  Market Price:       {BOLD}${verdict.market_price:,.2f}{RESET}\n")
    sys.stdout.write(f"  Consensus Stance:   {stance_color}{BOLD}{verdict.final_stance.value}{RESET} ({verdict.confidence_score}% Conviction)\n")
    sys.stdout.write(f"  Key Invalidation:   {RED}${verdict.key_invalidation_level:,.2f}{RESET}\n")
    sys.stdout.write(f"  Horizon:            {CYAN}{verdict.time_horizon}{RESET}\n")
    sys.stdout.write(f"  Thesis:             {DIM}{verdict.primary_thesis}{RESET}\n")
    sys.stdout.write("═" * 65 + "\n\n")


def handle_analyze(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper().strip()
    sys.stdout.write(f"{BOLD}⚡ Ingesting telemetry and launching consensus swarm for {CYAN}{symbol}{RESET}...\n")

    market_data = get_market_data(symbol, force_offline=args.offline)
    ind = market_data.indicators

    sys.stdout.write(
        f"  {DIM}Last Price: ${market_data.current_price:,.2f} ({market_data.change_24h_pct:+.2f}%) | "
        f"RSI-14: {ind.rsi_14:.1f} | 50/200: {ind.trend_50_200}{RESET}\n"
    )
    sys.stdout.write(f"{BOLD}── Multi-Agent Debate Commencing ──{RESET}\n")

    graph = AlphaSwarmGraph(max_rounds=args.rounds)

    def on_round(r: int):
        sys.stdout.write(f"\n{BOLD}{CYAN}▶ Debate Round #{r}{RESET}")

    verdict = graph.propagate(
        market_data,
        on_agent_speak=print_agent_thought,
        on_round_start=on_round,
    )

    print_verdict_card(verdict)

    # Export if requested
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if args.fmt == "html":
            content = generate_html_report(verdict, market_data)
        elif args.fmt == "json":
            content = json.dumps(verdict.to_dict(), indent=2)
        else:
            content = generate_markdown_report(verdict, market_data)
        out_path.write_text(content, encoding="utf-8")
        sys.stdout.write(f"{GREEN}✓ Dossier saved to {args.output}{RESET}\n")

    return 0


def handle_scan(args: argparse.Namespace) -> int:
    symbols = [s.upper().strip() for s in args.symbols]
    sys.stdout.write(f"{BOLD}⚡ AlphaSwarm Screening Watchlist ({len(symbols)} tickers)...{RESET}\n")
    sys.stdout.write("─" * 72 + "\n")
    sys.stdout.write(f"{BOLD}{'Ticker'.ljust(8)} {'Price'.ljust(12)} {'24h %'.ljust(10)} {'RSI'.ljust(8)} {'Consensus'.ljust(15)} {'Conviction'}{RESET}\n")
    sys.stdout.write("─" * 72 + "\n")

    graph = AlphaSwarmGraph(max_rounds=1)
    for sym in symbols:
        md = get_market_data(sym, force_offline=args.offline)
        verdict = graph.propagate(md)

        stance_color = (
            GREEN if "BULL" in verdict.final_stance.value
            else RED if "BEAR" in verdict.final_stance.value
            else YELLOW
        )
        chg_color = GREEN if md.change_24h_pct >= 0 else RED

        p_str = f"${md.current_price:,.2f}"
        c_str = f"{md.change_24h_pct:+.2f}%"
        rsi_str = f"{md.indicators.rsi_14:.1f}" if md.indicators else "—"

        sys.stdout.write(
            f"{BOLD}{sym.ljust(8)}{RESET} {p_str.ljust(12)} {chg_color}{c_str.ljust(10)}{RESET} "
            f"{rsi_str.ljust(8)} {stance_color}{verdict.final_stance.value.ljust(15)}{RESET} "
            f"{verdict.confidence_score}%\n"
        )
    sys.stdout.write("─" * 72 + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alphaswarm",
        description="⚡ Autonomous Multi-Agent Market Intelligence Hub & Consensus Graph.",
    )
    parser.add_argument("--version", action="version", version="alphaswarm 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # analyze
    analyze_p = subparsers.add_parser("analyze", help="Execute multi-agent debate and consensus on a symbol")
    analyze_p.add_argument("symbol", help="Asset ticker (e.g. BTC, ETH, SOL, NVDA, AAPL)")
    analyze_p.add_argument("-r", "--rounds", type=int, default=1, help="Debate rounds (1 to 3, default: 1)")
    analyze_p.add_argument("-f", "--format", dest="fmt", default="md", choices=["md", "html", "json"], help="Output report format")
    analyze_p.add_argument("-o", "--output", default=None, help="Save intelligence report to file")
    analyze_p.add_argument("--offline", action="store_true", help="Force deterministic offline simulation data")

    # scan
    scan_p = subparsers.add_parser("scan", help="Run rapid multi-agent screening across multiple tickers")
    scan_p.add_argument("symbols", nargs="+", help="List of tickers (e.g. BTC ETH SOL NVDA)")
    scan_p.add_argument("--offline", action="store_true", help="Force offline simulation data")

    # serve
    serve_p = subparsers.add_parser("serve", help="Launch interactive visual Web Dashboard")
    serve_p.add_argument("-p", "--port", type=int, default=5050, help="Web dashboard server port (default: 5050)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "analyze":
        return handle_analyze(args)
    elif args.command == "scan":
        return handle_scan(args)
    elif args.command == "serve":
        from alphaswarm.server import start_server
        start_server(port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
