"""
CLI interface for soplex using Typer + Rich.
Provides commands for analyze, compile, chat, visualize, stats, and test.
"""
import time
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
    tools: Optional[Path] = typer.Option(None, "--tools", "-t", help="Tools YAML file"),
) -> None:
    """Compile SOP to executable graph."""
    # Initialize config with CLI overrides
    config_overrides = {}
    if provider:
        config_overrides["provider"] = provider
    if model:
        config_overrides["model"] = model

    config = get_config(**config_overrides)

    try:
        from .parser.sop_parser import SOPParser
        from .parser.models import Tool
        from .compiler.graph_builder import GraphBuilder
        import yaml

        # Check if SOP file exists
        if not sop_file.exists():
            console.print(f"❌ SOP file not found: {sop_file}", style="red")
            raise typer.Exit(1)

        # Load tools if provided
        tool_definitions = {}
        if tools and tools.exists():
            with open(tools) as f:
                tools_data = yaml.safe_load(f)
                for tool_name, tool_config in tools_data.items():
                    tool_definitions[tool_name] = Tool(
                        name=tool_name,
                        description=tool_config.get("description", ""),
                        parameters=tool_config.get("parameters", {}),
                        mock_response=tool_config.get("mock_responses", {})
                    )

        # Parse SOP
        sop_text = sop_file.read_text()
        parser = SOPParser()
        sop_def = parser.parse(sop_text, tool_definitions)

        console.print(f"📝 Parsed SOP: [bold]{sop_def.name}[/bold] ({len(sop_def.steps)} steps)")

        # Build graph
        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Set output directory
        if not output:
            output = Path("compiled_sops")

        output.mkdir(parents=True, exist_ok=True)

        # Save compiled graph
        graph_file = output / f"{sop_file.stem}.json"
        graph.save(graph_file)

        console.print(f"✅ Compiled successfully: [green]{graph_file}[/green]")

        # Show summary
        summary = graph.summary()
        console.print(f"   📊 Nodes: {summary['total_nodes']} | Edges: {summary['total_edges']}")
        console.print(f"   🔧 Provider: {config['provider']} | Model: {config['model']}")

    except Exception as e:
        console.print(f"❌ Compilation failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def chat(
    graph_file: Path = typer.Argument(..., help="Path to compiled graph"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Interactive mode"),
    initial_input: Optional[str] = typer.Option(None, "--input", "-i", help="Initial input message"),
) -> None:
    """Interactive chat with compiled agent."""
    # Initialize config
    config_overrides = {}
    if provider:
        config_overrides["provider"] = provider
    if model:
        config_overrides["model"] = model

    config = get_config(**config_overrides)

    try:
        from .compiler.graph import ExecutionGraph
        from .runtime.executor import SOPExecutor
        from .runtime.tool_registry import default_registry
        from .llm.provider import LLMProvider
        from .utils.cost_tracker import record_session_costs

        # Check if graph file exists
        if not graph_file.exists():
            console.print(f"❌ Graph file not found: {graph_file}", style="red")
            raise typer.Exit(1)

        # Load graph
        graph = ExecutionGraph.load(graph_file)
        console.print(f"🔄 Loaded graph: [bold]{graph.name}[/bold]")

        # Initialize LLM provider
        try:
            llm_provider = LLMProvider(config)
            console.print(f"🤖 Using {config['provider']}: {config['model']}")
        except Exception as e:
            console.print(f"❌ Failed to initialize LLM provider: {e}", style="red")
            raise typer.Exit(1)

        # Load mock tools from examples
        try:
            tools_file = Path("examples/tools.yaml")
            if tools_file.exists():
                default_registry.load_tools_from_yaml(tools_file)
                console.print(f"🔧 Loaded {len(default_registry.get_tool_names())} tools")
        except Exception:
            console.print("⚠️  No tools loaded", style="yellow")

        # Create executor
        executor = SOPExecutor(llm_provider=llm_provider, tool_registry=default_registry)

        console.print("\n🚀 Starting SOP execution...\n")

        # Execute graph
        if interactive:
            # Interactive execution
            state = None

            for i, step_result in enumerate(executor.execute_interactive(graph)):
                # Display step result
                step_emoji = {
                    "llm": "🧠",
                    "code": "⚡",
                    "hybrid": "🔀",
                    "branch": "🔀",
                    "end": "🏁",
                    "escalate": "🚨"
                }.get(step_result.step_type, "❓")

                console.print(f"{step_emoji} Step {step_result.step_number}: {step_result.action}")

                if step_result.llm_response:
                    console.print(f"   💬 {step_result.llm_response}")

                if step_result.step_type == "code" and step_result.result:
                    console.print(f"   ⚡ {step_result.result}")

                if step_result.status == "failed":
                    console.print(f"   ❌ Error: {step_result.error}", style="red")

                # For demo, pause between steps
                if i < 10:  # Don't pause too much
                    time.sleep(0.5)

            state = executor.execute(graph, initial_input=initial_input)
        else:
            # Non-interactive execution
            state = executor.execute(graph, initial_input=initial_input)

        # Show final results
        summary = state.get_summary()

        console.print(f"\n✅ Execution completed: [bold]{summary['status']}[/bold]")
        console.print(f"   ⏱️  Duration: {summary['duration_seconds']:.2f}s")
        console.print(f"   💰 Cost: ${summary['costs']['total_cost']:.6f}")
        console.print(f"   🧠 LLM calls: {summary['usage']['llm_calls']}")
        console.print(f"   ⚡ Code calls: {summary['usage']['code_calls']}")

        # Record costs
        record_session_costs(state, graph.name, config['provider'], config['model'])

    except Exception as e:
        console.print(f"❌ Chat session failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def visualize(
    graph_file: Path = typer.Argument(..., help="Path to compiled graph"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    format: str = typer.Option("mermaid", "--format", "-f", help="Output format (mermaid, html)"),
    execution_path: Optional[str] = typer.Option(None, "--path", "-p", help="Comma-separated execution path to highlight"),
) -> None:
    """Generate flowchart visualization."""
    try:
        from .compiler.graph import ExecutionGraph
        from .visualizer.mermaid import generate_sop_flowchart

        # Check if graph file exists
        if not graph_file.exists():
            console.print(f"❌ Graph file not found: {graph_file}", style="red")
            raise typer.Exit(1)

        # Load graph
        graph = ExecutionGraph.load(graph_file)
        console.print(f"📊 Visualizing: [bold]{graph.name}[/bold]")

        # Parse execution path if provided
        path_nodes = None
        if execution_path:
            path_nodes = [node.strip() for node in execution_path.split(",")]

        # Generate flowchart
        title = f"SOP: {graph.name}"
        mermaid_content = generate_sop_flowchart(
            graph,
            title=title,
            execution_path=path_nodes
        )

        # Set output file
        if not output:
            output = graph_file.with_suffix(f".{format}")

        # Save to file
        from .visualizer.mermaid import MermaidGenerator
        generator = MermaidGenerator()
        generator.save_to_file(mermaid_content, output, format)

        console.print(f"✅ Visualization saved: [green]{output}[/green]")

        # Show statistics
        summary = graph.summary()
        console.print(f"   📊 Nodes: {summary['total_nodes']} | Edges: {summary['total_edges']}")

        if format == "html":
            console.print(f"   🌐 Open in browser: file://{output.absolute()}")

    except Exception as e:
        console.print(f"❌ Visualization failed: {e}", style="red")
        raise typer.Exit(1)


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
    if scenarios:
        console.print(f"   With scenarios: {scenarios}")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    export: Optional[Path] = typer.Option(None, "--export", "-e", help="Export data to file"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, csv)"),
) -> None:
    """Show execution statistics."""
    try:
        from .utils.cost_tracker import get_cost_tracker

        tracker = get_cost_tracker()

        # Get aggregate stats
        stats = tracker.get_aggregate_stats(days)

        if stats["total_sessions"] == 0:
            console.print(f"📊 No execution data found for the last {days} days", style="yellow")
            return

        # Display stats
        console.print(f"\n📊 Execution Statistics (Last {days} days)\n")

        # Main stats table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim", width=20)
        table.add_column("Value", width=20)

        table.add_row("Total Sessions", str(stats["total_sessions"]))
        table.add_row("Total Savings", f"${stats['total_savings']:.4f}")
        table.add_row("Average Savings", f"{stats['average_savings_percent']:.1f}%")
        table.add_row("Total Cost", f"${stats['total_cost']:.4f}")
        table.add_row("LLM Calls", str(stats["total_llm_calls"]))
        table.add_row("Code Calls", str(stats["total_code_calls"]))
        table.add_row("Efficiency Ratio", f"{stats['efficiency_ratio']:.1f}% code")
        table.add_row("Average Duration", f"{stats['average_duration']:.2f}s")
        table.add_row("Error Rate", f"{stats['error_rate']:.1f}%")
        table.add_row("Most Used Provider", stats["most_used_provider"])
        table.add_row("Most Used Model", stats["most_used_model"])

        console.print(table)

        # Get savings breakdown
        breakdown = tracker.get_savings_breakdown(days)
        if breakdown["sop_breakdown"]:
            console.print("\n💰 Savings by SOP:")

            for sop_name, sop_stats in list(breakdown["sop_breakdown"].items())[:5]:  # Top 5
                savings_pct = sop_stats["avg_savings_percent"]
                sessions = sop_stats["sessions"]
                total_savings = sop_stats["total_savings"]
                console.print(f"   • {sop_name}: ${total_savings:.4f} saved ({savings_pct:.1f}%) across {sessions} sessions")

        # Export data if requested
        if export:
            tracker.export_data(export, format)
            console.print(f"\n📁 Data exported: [green]{export}[/green]")

    except Exception as e:
        console.print(f"❌ Failed to get statistics: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show soplex version."""
    from . import __version__
    console.print(f"soplex {__version__}")


if __name__ == "__main__":
    app()