"""
CLI interface for soplex using Typer + Rich.
Provides commands for analyze, compile, chat, visualize, stats, and test.
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
from typing import Optional

from .config import get_config, PRICING
from .parser.sop_parser import SOPParser
from .parser.models import StepType

app = typer.Typer(
    name="soplex",
    help="Compile plain-English SOPs into executable, cost-optimized agent graphs",
    no_args_is_help=True
)
console = Console()


@app.command()
def analyze(
    sop_file: Path = typer.Argument(..., help="Path to SOP file"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider (openai, anthropic, gemini, ollama, litellm, custom)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature (0.0-2.0)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format (table, json)"),
) -> None:
    """Analyze SOP structure and estimate costs."""
    # Initialize config with CLI overrides
    config_overrides = {}
    if provider:
        config_overrides["provider"] = provider
    if model:
        config_overrides["model"] = model
    if temperature is not None:
        config_overrides["temperature"] = temperature

    config = get_config(**config_overrides)

    try:
        # Parse SOP file
        if not sop_file.exists():
            console.print(f"❌ SOP file not found: {sop_file}", style="red")
            raise typer.Exit(1)

        sop_text = sop_file.read_text()
        parser = SOPParser()
        sop_def = parser.parse(sop_text)

        # Display analysis
        console.print(f"\n📊 SOP Analysis: [bold]{sop_def.name}[/bold]\n")

        # Step classification table
        table = Table(title="Step Classification", show_header=True, header_style="bold magenta")
        table.add_column("Step #", style="dim", width=8)
        table.add_column("Type", width=10)
        table.add_column("Action", width=50)
        table.add_column("Confidence", width=12)

        # Step type emojis
        type_emojis = {
            StepType.LLM: "🧠",
            StepType.CODE: "⚡",
            StepType.HYBRID: "🔀",
            StepType.BRANCH: "🔀",
            StepType.END: "🏁",
            StepType.ESCALATE: "🚨",
        }

        for step in sop_def.steps:
            emoji = type_emojis.get(step.type, "❓")
            confidence_color = "green" if step.confidence >= 0.8 else "yellow" if step.confidence >= 0.6 else "red"
            table.add_row(
                str(step.number),
                f"{emoji} {step.type.value.upper()}",
                step.action[:47] + "..." if len(step.action) > 50 else step.action,
                f"[{confidence_color}]{step.confidence:.2f}[/{confidence_color}]"
            )

        console.print(table)

        # Cost estimate
        cost_estimate = sop_def.get_cost_estimate(PRICING)

        cost_panel = Panel(
            f"""💰 Cost Estimate (vs Pure LLM):

🧠 LLM Steps:      {sop_def.llm_steps} (conversation)
⚡ CODE Steps:     {sop_def.code_steps} (deterministic logic)
🔀 HYBRID Steps:   {sop_def.hybrid_steps} (LLM + validation)
🔀 BRANCH Steps:   {sop_def.branch_steps} (conditional)

Pure LLM Cost:     ${cost_estimate['pure_llm_cost']:.4f}
Hybrid Cost:       ${cost_estimate['total_cost']:.4f}
Savings:           ${cost_estimate['savings']:.4f} ({cost_estimate['savings_percent']:.1f}%)
            """,
            title="Cost Analysis",
            border_style="green"
        )
        console.print(cost_panel)

        # Validation warnings
        issues = parser.validate_sop(sop_def)
        if issues:
            console.print("\n⚠️  Validation Warnings:", style="yellow")
            for issue in issues:
                console.print(f"  • {issue}", style="yellow")

        # Provider info
        console.print(f"\n🤖 Provider: {config['provider']} | Model: {config['model']}")

    except Exception as e:
        console.print(f"❌ Error analyzing SOP: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def compile(
    sop_file: Path = typer.Argument(..., help="Path to SOP file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
) -> None:
    """Compile SOP to executable graph (Phase 2 feature)."""
    console.print("🚧 Compile command will be available in Phase 2", style="yellow")
    console.print(f"Would compile: {sop_file}")


@app.command()
def chat(
    graph_file: Path = typer.Argument(..., help="Path to compiled graph"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
) -> None:
    """Interactive chat with compiled agent (Phase 4 feature)."""
    console.print("🚧 Chat command will be available in Phase 4", style="yellow")
    console.print(f"Would run chat with: {graph_file}")


@app.command()
def visualize(
    graph_file: Path = typer.Argument(..., help="Path to compiled graph"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (SVG/PNG)"),
    format: Optional[str] = typer.Option("mermaid", "--format", "-f", help="Output format"),
) -> None:
    """Generate flowchart visualization (Phase 4 feature)."""
    console.print("🚧 Visualize command will be available in Phase 4", style="yellow")
    console.print(f"Would visualize: {graph_file}")


@app.command()
def test(
    graph_file: Path = typer.Argument(..., help="Path to compiled graph"),
    scenarios: Optional[Path] = typer.Option(None, "--scenarios", "-s", help="Test scenarios YAML"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
) -> None:
    """Run test scenarios (Phase 5 feature)."""
    console.print("🚧 Test command will be available in Phase 5", style="yellow")
    console.print(f"Would test: {graph_file}")


@app.command()
def stats() -> None:
    """Show execution statistics (Phase 4 feature)."""
    console.print("🚧 Stats command will be available in Phase 4", style="yellow")


@app.command()
def version() -> None:
    """Show soplex version."""
    from . import __version__
    console.print(f"soplex {__version__}")


if __name__ == "__main__":
    app()