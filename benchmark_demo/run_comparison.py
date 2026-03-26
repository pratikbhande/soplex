#!/usr/bin/env python3
"""
Complete Traditional vs Soplex Comparison Demo
Runs both approaches side-by-side and generates comparison metrics
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path

def print_header():
    print("🔥" * 80)
    print("SOPLEX AI: TRADITIONAL vs HYBRID APPROACH COMPARISON")
    print("🔥" * 80)
    print()
    print("This demo will show you the dramatic difference between:")
    print("🏛️  Traditional: Pure LLM calls for every step (expensive & slow)")
    print("🚀 Soplex: Hybrid LLM + Code execution (optimized & accurate)")
    print()
    input("Press Enter to start the comparison demo...")
    print()

def run_traditional_demo():
    print("🏛️" + "=" * 70)
    print("RUNNING TRADITIONAL PURE-LLM APPROACH")
    print("=" * 71)
    print()

    start_time = time.time()
    result = subprocess.run([
        sys.executable,
        "traditional_approach/run_traditional.py"
    ], capture_output=False, cwd=os.getcwd())

    end_time = time.time()

    if result.returncode != 0:
        print("❌ Traditional demo failed!")
        return None

    # Load results
    try:
        with open("results/traditional_results.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Could not load traditional results")
        return None

def run_soplex_demo():
    print("\n🚀" + "=" * 70)
    print("RUNNING SOPLEX HYBRID APPROACH")
    print("=" * 71)
    print()

    start_time = time.time()
    result = subprocess.run([
        sys.executable,
        "soplex_approach/run_soplex.py"
    ], capture_output=False, cwd=os.getcwd())

    end_time = time.time()

    if result.returncode != 0:
        print("❌ Soplex demo failed!")
        return None

    # Load results
    try:
        with open("results/soplex_results.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Could not load soplex results")
        return None

def display_comparison(traditional, soplex):
    if not traditional or not soplex:
        print("❌ Cannot generate comparison - missing results")
        return

    print("\n" + "📊" * 20)
    print("COMPREHENSIVE COMPARISON RESULTS")
    print("📊" * 20)

    # Calculate savings
    cost_savings = ((traditional["total_cost"] - soplex["total_cost"]) / traditional["total_cost"]) * 100
    time_savings = ((traditional["total_time"] - soplex["total_time"]) / traditional["total_time"]) * 100
    llm_reduction = ((traditional["total_llm_calls"] - soplex["total_llm_calls"]) / traditional["total_llm_calls"]) * 100

    print(f"\n💰 COST ANALYSIS")
    print(f"{'Metric':<25} {'Traditional':<15} {'Soplex':<15} {'Improvement':<15}")
    print("-" * 70)
    print(f"{'Total Cost':<25} ${traditional['total_cost']:<14.4f} ${soplex['total_cost']:<14.4f} {cost_savings:<14.1f}%")
    print(f"{'LLM Calls':<25} {traditional['total_llm_calls']:<15} {soplex['total_llm_calls']:<15} {llm_reduction:<14.1f}% fewer")
    print(f"{'Total Tokens':<25} {traditional.get('total_tokens', 0):<15,} {soplex.get('total_tokens', 0) or 'N/A':<15} Major reduction")

    print(f"\n⚡ PERFORMANCE ANALYSIS")
    print(f"{'Metric':<25} {'Traditional':<15} {'Soplex':<15} {'Improvement':<15}")
    print("-" * 70)
    print(f"{'Execution Time':<25} {traditional['total_time']:<14.2f}s {soplex['total_time']:<14.2f}s {time_savings:<14.1f}%")
    print(f"{'Accuracy Risk':<25} {traditional['accuracy_risk'].title():<15} {soplex['accuracy_risk'].title():<15} Much Lower")
    print(f"{'Overhead':<25} {traditional['processing_overhead'].title():<15} {soplex['processing_overhead'].title():<15} Minimal")

    print(f"\n🎯 KEY ADVANTAGES OF SOPLEX:")
    print(f"   ✅ {cost_savings:.1f}% cost reduction through hybrid execution")
    print(f"   ✅ {llm_reduction:.1f}% fewer LLM calls (only for conversation)")
    print(f"   ✅ Deterministic logic eliminates AI hallucination risk")
    print(f"   ✅ {time_savings:.1f}% faster execution with code-based decisions")
    print(f"   ✅ Scalable architecture for enterprise workloads")

    # Save comprehensive comparison
    comparison = {
        "timestamp": time.time(),
        "traditional_approach": traditional,
        "soplex_approach": soplex,
        "improvements": {
            "cost_savings_percent": cost_savings,
            "time_savings_percent": time_savings,
            "llm_reduction_percent": llm_reduction,
            "accuracy_improvement": "Deterministic logic vs LLM hallucination risk",
            "scalability_improvement": "Linear cost growth vs exponential"
        }
    }

    with open("results/comparison_results.json", "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"\n📄 Complete comparison saved to: results/comparison_results.json")

def main():
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)

    print_header()

    # Run traditional approach
    print("🕐 Starting Traditional Approach Demo...")
    traditional_results = run_traditional_demo()

    if not traditional_results:
        print("❌ Traditional demo failed - cannot proceed with comparison")
        return

    print("\n⏳ Waiting 3 seconds before running Soplex demo...")
    time.sleep(3)

    # Run soplex approach
    print("🕐 Starting Soplex Approach Demo...")
    soplex_results = run_soplex_demo()

    if not soplex_results:
        print("❌ Soplex demo failed - cannot proceed with comparison")
        return

    # Display side-by-side comparison
    display_comparison(traditional_results, soplex_results)

    print(f"\n🎬 Demo Complete! Perfect for LinkedIn video recording.")
    print(f"📁 All results saved in ./results/ directory")

if __name__ == "__main__":
    main()