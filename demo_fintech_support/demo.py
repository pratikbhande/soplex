"""
Soplex Fintech Support Demo
This script demonstrates how Soplex compiles a plain-English SOP into a
cost-optimized hybrid execution graph, saving ~77% on LLM inference costs.
Perfect for high-volume customer support operations.
"""
import os
import sys

# Ensure soplex is in path if running from source
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from soplex.parser.sop_parser import SOPParser
from soplex.compiler.graph_builder import GraphBuilder
from soplex.config import PRICING
from rich.console import Console
from rich.panel import Panel

console = Console()

def run_demo():
    console.print(Panel.fit("[bold blue]Soplex-AI Fintech Demo[/bold blue]\nTarget: High-volume customer support automation"))
    
    sop_path = os.path.join(os.path.dirname(__file__), "fintech_support.sop")
    with open(sop_path, "r") as f:
        sop_text = f.read()
    
    # 1. Parse
    console.print("\n[bold green]Parsing Procedure Instructions...[/bold green]")
    parser = SOPParser()
    sop_def = parser.parse(sop_text)
    
    # 2. Analyze costs
    console.print("[bold green]Analyzing Execution Graph...[/bold green]")
    cost_estimate = sop_def.get_cost_estimate(PRICING)
    
    console.print(f"\n📊 SOP Analysis: [bold]{sop_def.name}[/bold]")
    console.print(f"🧠 LLM Steps:      {sop_def.llm_steps}")
    console.print(f"⚡ CODE Steps:     {sop_def.code_steps}")
    console.print(f"🔀 BRANCH Steps:   {sop_def.branch_steps}")
    
    savings_pct = cost_estimate['savings_percent']
    
    console.print("\n[bold yellow]Why this matters for Fintech Operations:[/bold yellow]")
    console.print("1. [bold]Strict Compliance[/bold]: Business logic (Step 3, Step 5, Step 7) runs as deterministic code.")
    console.print("2. [bold]Zero Hallucination[/bold]: No risk of an LLM incorrectly approving a 90-day old transaction dispute.")
    console.print(f"3. [bold]Unit Economics[/bold]: [bold green]{savings_pct:.1f}% cost reduction[/bold green] per ticket resolved compared to pure LLMs.")
    
    # 3. Build Graph
    builder = GraphBuilder()
    graph = builder.build_graph(sop_def)
    
    console.print("\n[bold cyan]Graph successfully compiled into executable nodes![/bold cyan]")
    console.print("\nTo run an interactive demo of this agent, use:")
    console.print("  [bold]soplex compile demo_fintech_support/fintech_support.sop --output compiled/[/bold]")
    console.print("  [bold]soplex chat compiled/fintech_support.json[/bold]")

if __name__ == "__main__":
    run_demo()
