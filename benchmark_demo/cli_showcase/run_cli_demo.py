#!/usr/bin/env python3
"""
Soplex CLI Showcase Demo
Demonstrates all soplex CLI commands with clear output for video recording
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

class CLIDemo:
    def __init__(self):
        self.demo_dir = Path(__file__).parent.parent
        self.sops_dir = self.demo_dir / "sops"
        self.compiled_dir = self.demo_dir / "compiled"
        self.results_dir = self.demo_dir / "results"

        # Ensure directories exist
        self.compiled_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    def print_section(self, title: str, description: str = ""):
        print("\n" + "🔷" * 60)
        print(f"📋 {title.upper()}")
        if description:
            print(f"💡 {description}")
        print("🔷" * 60)
        print()

    def run_command(self, cmd: list, description: str, show_output: bool = True):
        print(f"🚀 Running: {' '.join(cmd)}")
        print(f"📖 {description}")
        print("-" * 50)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.demo_dir,
                capture_output=not show_output,
                text=True,
                timeout=60
            )

            if not show_output and result.stdout:
                print(result.stdout)

            if result.stderr:
                print(f"⚠️ Warnings: {result.stderr}")

            if result.returncode == 0:
                print("✅ Command completed successfully!")
            else:
                print(f"❌ Command failed with return code: {result.returncode}")

        except subprocess.TimeoutExpired:
            print("⏰ Command timed out")
        except FileNotFoundError:
            print("❌ soplex command not found - please ensure it's installed")
            print("💡 Try: pip install soplex-ai")
        except Exception as e:
            print(f"❌ Error running command: {e}")

        print()

    def demo_analyze(self):
        self.print_section(
            "SOPLEX ANALYZE",
            "Analyze SOP structure, classify steps, and estimate costs"
        )

        # Analyze different SOPs to show variety
        sop_files = [
            ("enterprise_kyc.sop", "Complex KYC onboarding process"),
            ("financial_fraud_detection.sop", "Real-time fraud detection pipeline"),
            ("customer_escalation_flow.sop", "Customer support escalation workflow")
        ]

        for sop_file, description in sop_files:
            print(f"📄 Analyzing {sop_file} - {description}")
            self.run_command([
                "soplex", "analyze",
                f"sops/{sop_file}"
            ], f"Analyze {description.lower()}")

            time.sleep(2)  # Pause for video clarity

    def demo_compile(self):
        self.print_section(
            "SOPLEX COMPILE",
            "Convert SOPs into executable agent graphs"
        )

        # Compile the main enterprise KYC SOP
        print("🏗️ Compiling Enterprise KYC SOP into executable graph...")
        self.run_command([
            "soplex", "compile",
            "sops/enterprise_kyc.sop",
            "--output", "compiled/"
        ], "Convert SOP text into executable agent graph with nodes and edges")

        # Show the generated files
        print("📁 Generated files:")
        try:
            for file in self.compiled_dir.glob("*.json"):
                print(f"   ✅ {file.name}")

                # Show a snippet of the compiled graph structure
                with open(file, 'r') as f:
                    data = json.load(f)
                    print(f"      📊 Nodes: {len(data.get('nodes', {}))}, Edges: {len(data.get('edges', []))}")
        except Exception as e:
            print(f"   ⚠️ Could not read compiled files: {e}")
        print()

    def demo_visualize(self):
        self.print_section(
            "SOPLEX VISUALIZE",
            "Generate flowchart diagrams from compiled graphs"
        )

        # Check if we have compiled graphs to visualize
        compiled_files = list(self.compiled_dir.glob("*.json"))

        if compiled_files:
            compiled_file = compiled_files[0]
            print(f"🎨 Creating flowchart for {compiled_file.name}...")

            output_file = self.results_dir / f"{compiled_file.stem}_flowchart.svg"
            self.run_command([
                "soplex", "visualize",
                str(compiled_file),
                "--output", str(output_file)
            ], "Generate SVG flowchart showing the agent execution graph")

            # Alternative: HTML output
            html_output = self.results_dir / f"{compiled_file.stem}_flowchart.html"
            print("🌐 Also generating HTML interactive flowchart...")
            self.run_command([
                "soplex", "visualize",
                str(compiled_file),
                "--output", str(html_output),
                "--format", "html"
            ], "Generate interactive HTML flowchart for web viewing")
        else:
            print("⚠️ No compiled graphs found. Run compile command first.")

    def demo_test(self):
        self.print_section(
            "SOPLEX TEST",
            "Run test scenarios against compiled agent graphs"
        )

        # First, create a test scenarios file
        test_scenarios = {
            "scenarios": [
                {
                    "name": "successful_kyc_onboarding",
                    "description": "Standard KYC process with clean customer",
                    "initial_state": {
                        "company_number": "12345678",
                        "director_name": "John Smith",
                        "director_id": "DIR-001"
                    },
                    "expected_outcome": "end_success"
                },
                {
                    "name": "pep_match_escalation",
                    "description": "Customer triggers PEP match requiring escalation",
                    "initial_state": {
                        "company_number": "12345678",
                        "director_name": "PEP Match",
                        "director_id": "DIR-002"
                    },
                    "expected_outcome": "escalate_compliance"
                }
            ]
        }

        scenarios_file = self.demo_dir / "tools" / "test_scenarios.yaml"
        scenarios_file.parent.mkdir(exist_ok=True)

        # Convert to YAML format (simplified)
        yaml_content = """scenarios:
  - name: successful_kyc_onboarding
    description: Standard KYC process with clean customer
    initial_state:
      company_number: "12345678"
      director_name: "John Smith"
      director_id: "DIR-001"
    expected_outcome: end_success

  - name: pep_match_escalation
    description: Customer triggers PEP match requiring escalation
    initial_state:
      company_number: "12345678"
      director_name: "PEP Match"
      director_id: "DIR-002"
    expected_outcome: escalate_compliance
"""

        with open(scenarios_file, 'w') as f:
            f.write(yaml_content)

        print("📝 Created test scenarios file...")

        # Run tests if we have compiled graphs
        compiled_files = list(self.compiled_dir.glob("*.json"))
        if compiled_files:
            compiled_file = compiled_files[0]
            print(f"🧪 Running test scenarios against {compiled_file.name}...")

            self.run_command([
                "soplex", "test",
                str(compiled_file),
                "--scenarios", str(scenarios_file)
            ], "Execute predefined test scenarios and validate outcomes")
        else:
            print("⚠️ No compiled graphs found. Run compile command first.")

    def demo_stats(self):
        self.print_section(
            "SOPLEX STATS",
            "View execution statistics and performance metrics"
        )

        print("📈 Displaying soplex usage statistics...")
        self.run_command([
            "soplex", "stats"
        ], "Show execution statistics, cost savings, and performance metrics")

    def demo_chat_preview(self):
        self.print_section(
            "SOPLEX CHAT (Interactive Preview)",
            "Interactive chat with compiled agent - showing non-interactive preview"
        )

        compiled_files = list(self.compiled_dir.glob("*.json"))
        if compiled_files:
            compiled_file = compiled_files[0]

            print(f"💬 Interactive chat mode with {compiled_file.name}")
            print("📝 Note: In actual demo, this would open an interactive session")
            print("🎯 Example conversation flow:")
            print("   User: Hello, I need to onboard my company")
            print("   Agent: Hello! I'd be happy to help with KYC onboarding...")
            print("   User: My company number is 12345678")
            print("   Agent: [Executes lookup] I found TechCorp Ltd...")
            print()
            print("🎮 To start interactive mode manually:")
            print(f"   soplex chat {compiled_file}")
        else:
            print("⚠️ No compiled graphs found. Run compile command first.")

def main():
    print("🎬" * 20)
    print("SOPLEX CLI SHOWCASE DEMO")
    print("Perfect for video recording!")
    print("🎬" * 20)

    demo = CLIDemo()

    print("\n🚀 This demo will showcase all soplex CLI commands:")
    print("   📊 analyze  - Analyze SOP structure and costs")
    print("   🏗️ compile  - Convert SOPs to executable graphs")
    print("   🎨 visualize - Generate flowchart diagrams")
    print("   🧪 test     - Run automated test scenarios")
    print("   📈 stats    - View performance statistics")
    print("   💬 chat     - Interactive agent conversations")

    input("\nPress Enter to start CLI showcase...")

    # Run all CLI demos
    demo.demo_analyze()
    demo.demo_compile()
    demo.demo_visualize()
    demo.demo_test()
    demo.demo_stats()
    demo.demo_chat_preview()

    print("\n🎉" * 20)
    print("SOPLEX CLI SHOWCASE COMPLETE!")
    print("🎉" * 20)
    print("\n📁 Generated files:")
    print(f"   📊 Compiled graphs: {demo.compiled_dir}")
    print(f"   📋 Test results: {demo.results_dir}")
    print(f"   🎨 Visualizations: {demo.results_dir}")
    print("\n🎬 Ready for LinkedIn video recording!")

if __name__ == "__main__":
    main()