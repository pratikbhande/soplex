#!/usr/bin/env python3
"""
Fix and Run Complete Demo
One command to fix everything and launch the demo
"""

import subprocess
import sys
import os
from pathlib import Path

def run_cmd(cmd, description):
    print(f"🔧 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Done")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed: {e}")
        return False

def main():
    print("🚀 SOPLEX DEMO - COMPLETE FIX & RUN")
    print("="*50)

    # Step 1: Install dependencies
    print("\n📦 Installing dependencies...")
    deps = [
        "pip install networkx",
        "pip install flask",
        "pip install plotly",
        "pip install pandas"
    ]

    for dep in deps:
        run_cmd(dep, f"Installing {dep.split()[-1]}")

    # Step 2: Create directories
    print("\n📁 Creating directories...")
    os.makedirs('compiled', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    print("✅ Directories created")

    # Step 3: Compile graph
    print("\n🏗️ Compiling SOP to graph...")
    compile_success = run_cmd(
        "soplex compile sops/enterprise_kyc.sop --output compiled/",
        "Compiling SOP"
    )

    # Step 4: Test imports
    print("\n🧪 Testing imports...")
    try:
        import networkx
        import flask
        import plotly
        sys.path.append('web_ui')
        from fixed_graph_visualizer import FixedSoplexGraphVisualizer
        print("✅ All imports working")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Try running: pip install networkx flask plotly pandas")
        return

    # Step 5: Launch demo
    if compile_success:
        print("\n🚀 All fixed! Launching demo...")
        print("📱 Opening at: http://localhost:5000")
        print("🎬 Perfect for LinkedIn recording!")

        try:
            os.chdir('web_ui')
            subprocess.run([sys.executable, 'app.py'])
        except KeyboardInterrupt:
            print("\n✅ Demo stopped by user")
        except Exception as e:
            print(f"❌ Error launching: {e}")
            print("\n💡 Try manual launch:")
            print("cd web_ui && python app.py")
    else:
        print("\n⚠️ Graph compilation failed. Check soplex installation:")
        print("soplex --help")

if __name__ == "__main__":
    main()