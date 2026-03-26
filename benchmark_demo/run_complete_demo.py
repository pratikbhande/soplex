#!/usr/bin/env python3
"""
Complete Soplex Demo Runner
Orchestrates the entire demo sequence for seamless video recording
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path

def print_banner():
    banner = """
████████████████████████████████████████████████████████████████████████████████
██                                                                            ██
██    🚀 SOPLEX AI - COMPLETE BENCHMARK DEMO                                   ██
██                                                                            ██
██    📊 Traditional vs Hybrid Comparison                                     ██
██    🛠️ Complete CLI Showcase                                               ██
██    📈 Performance Benchmarks                                               ██
██    🎬 Perfect for LinkedIn Video Recording                                  ██
██                                                                            ██
████████████████████████████████████████████████████████████████████████████████
    """
    print(banner)

def wait_for_user(message: str, auto_continue: bool = False):
    if auto_continue:
        print(f"🤖 Auto-continuing: {message}")
        time.sleep(2)
    else:
        input(f"👆 {message} (Press Enter to continue...)")

def run_script(script_path: str, description: str) -> bool:
    print(f"\n🚀 Running: {description}")
    print("=" * 60)

    try:
        result = subprocess.run([sys.executable, script_path],
                              cwd=Path(__file__).parent,
                              check=False)

        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            return True
        else:
            print(f"❌ {description} failed with return code: {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_prerequisites():
    print("\n🔍 Checking Prerequisites...")

    # Check if soplex is installed by trying to activate venv and run help
    try:
        result = subprocess.run("source ../venv/bin/activate && soplex --help",
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ soplex CLI is installed and ready")
        else:
            print("❌ soplex CLI not found")
            print("💡 Trying to activate virtual environment...")
            return False
    except Exception:
        print("❌ soplex CLI not found. Please install with: pip install soplex-ai")
        return False

    # Check if required directories exist
    demo_dir = Path(__file__).parent
    required_dirs = ["sops", "traditional_approach", "soplex_approach"]

    for dir_name in required_dirs:
        if (demo_dir / dir_name).exists():
            print(f"✅ {dir_name} directory exists")
        else:
            print(f"❌ {dir_name} directory missing")
            return False

    print("✅ All prerequisites met!")
    return True

def display_final_summary():
    print("\n" + "🎉" * 60)
    print("DEMO COMPLETE - SUMMARY REPORT")
    print("🎉" * 60)

    # Try to load and display comparison results
    results_dir = Path(__file__).parent / "results"
    comparison_file = results_dir / "comparison_results.json"

    if comparison_file.exists():
        try:
            with open(comparison_file, 'r') as f:
                data = json.load(f)

            improvements = data.get("improvements", {})

            print(f"\n📊 KEY PERFORMANCE METRICS:")
            print(f"   💰 Cost Savings: {improvements.get('cost_savings_percent', 0):.1f}%")
            print(f"   ⚡ Speed Improvement: {improvements.get('time_savings_percent', 0):.1f}%")
            print(f"   🧠 LLM Call Reduction: {improvements.get('llm_reduction_percent', 0):.1f}%")
            print(f"   🎯 Accuracy: Deterministic logic eliminates hallucination risk")

        except Exception as e:
            print(f"⚠️ Could not load comparison results: {e}")

    print(f"\n📁 Generated Files:")
    print(f"   📊 results/comparison_results.json - Complete benchmark data")
    print(f"   🏗️ compiled/ - Executable agent graphs")
    print(f"   🎨 results/ - Flowchart visualizations")

    print(f"\n🎬 LINKEDIN VIDEO TALKING POINTS:")
    print(f"   1. Show the cost difference (70-80% savings)")
    print(f"   2. Highlight hybrid architecture (LLM + Code)")
    print(f"   3. Demonstrate UK compliance focus (KYC/AML)")
    print(f"   4. Show CLI ease-of-use")
    print(f"   5. Emphasize enterprise readiness")

    print(f"\n🔗 Next Steps:")
    print(f"   📦 Package: pip install soplex-ai")
    print(f"   📖 Docs: https://soplex.dev")
    print(f"   💻 GitHub: https://github.com/pratikbhande/soplex")

def main():
    print_banner()

    # Get demo mode
    print("\n🎮 Demo Modes:")
    print("   1. Interactive Mode (pause between sections)")
    print("   2. Auto Mode (continuous for recording)")

    mode = input("\nSelect mode (1 or 2): ").strip()
    auto_mode = (mode == "2")

    if auto_mode:
        print("\n🤖 Auto Mode Selected - Perfect for video recording!")
    else:
        print("\n👤 Interactive Mode Selected - You can pause between sections")

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix issues and try again.")
        sys.exit(1)

    wait_for_user("Ready to start the complete soplex demo?", auto_mode)

    # Part 1: Traditional vs Soplex Comparison
    print("\n" + "📊" * 20)
    print("PART 1: TRADITIONAL vs SOPLEX COMPARISON")
    print("📊" * 20)

    wait_for_user("About to run Traditional vs Soplex comparison", auto_mode)

    success = run_script("run_comparison.py",
                        "Traditional vs Soplex Comparison Demo")

    if not success:
        print("\n⚠️ Comparison demo had issues, but continuing...")

    wait_for_user("Comparison complete. Ready for CLI showcase?", auto_mode)

    # Part 2: CLI Showcase
    print("\n" + "🛠️" * 20)
    print("PART 2: CLI SHOWCASE")
    print("🛠️" * 20)

    wait_for_user("About to demonstrate all soplex CLI commands", auto_mode)

    success = run_script("cli_showcase/run_cli_demo.py",
                        "Complete CLI Showcase Demo")

    if not success:
        print("\n⚠️ CLI demo had issues, but continuing...")

    # Part 3: Final Summary
    display_final_summary()

    print(f"\n🎬 DEMO COMPLETE!")
    print(f"Ready for LinkedIn video! 🚀")

if __name__ == "__main__":
    main()