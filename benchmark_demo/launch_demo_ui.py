#!/usr/bin/env python3
"""
Launch Soplex AI Demo UI
Simple command to start the web interface for demonstrations
"""

import subprocess
import sys
import os
import webbrowser
import time
from pathlib import Path

def install_dependencies():
    """Install required dependencies for the demo UI"""
    print("📦 Installing demo UI dependencies...")

    dependencies = [
        "flask",
        "plotly",
        "pandas"  # In case we need it for data processing
    ]

    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep],
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"⚠️ Failed to install {dep}, but continuing...")

def main():
    print("🚀 Soplex AI Demo UI Launcher")
    print("=" * 40)

    # Check if we're in the right directory
    demo_ui_path = Path(__file__).parent / "web_ui"
    if not demo_ui_path.exists():
        print("❌ Demo UI directory not found!")
        print("Please run this script from the benchmark_demo directory")
        sys.exit(1)

    # Install dependencies
    install_dependencies()

    # Change to web_ui directory
    os.chdir(demo_ui_path)

    print("\n🌐 Starting Soplex AI Demo UI...")
    print("📱 The demo will open at: http://localhost:5000")
    print("🎬 Perfect for video recording!")
    print("\n💡 Demo Features:")
    print("   ⚡ Live cost comparison")
    print("   📊 Interactive charts and metrics")
    print("   🏗️ Architecture visualization")
    print("   🇬🇧 UK market focus")

    # Wait a moment for the message to be read
    time.sleep(2)

    # Start the Flask app
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:5000')

        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Run the Flask app
        subprocess.run([sys.executable, "app.py"], check=True)

    except KeyboardInterrupt:
        print("\n\n🎉 Demo UI stopped!")
        print("Thanks for using Soplex AI!")
    except Exception as e:
        print(f"\n❌ Error starting demo UI: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you're in the benchmark_demo directory")
        print("   2. Activate your virtual environment: source ../venv/bin/activate")
        print("   3. Install dependencies: pip install flask plotly")
        print("   4. Try running manually: cd web_ui && python app.py")

if __name__ == "__main__":
    main()