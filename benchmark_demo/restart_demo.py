#!/usr/bin/env python3
"""
Restart Demo UI with Updates
Simple script to restart the demo with all the new improvements
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    print("🔄 Restarting Soplex AI Demo with Improved UI...")

    # Navigate to the web UI directory
    web_ui_path = Path(__file__).parent / "web_ui"
    os.chdir(web_ui_path)

    print("🌟 New Features:")
    print("   ✅ Removed UK Market section")
    print("   ✅ Added side-by-side comparison")
    print("   ✅ Static metrics display before running")
    print("   ✅ Enhanced visual design")
    print("   ✅ Better charts and graphs")
    print("   ✅ Improved responsive layout")

    print(f"\n🚀 Starting improved demo UI...")
    print(f"📱 URL: http://localhost:5000")
    print(f"🎬 Perfect for LinkedIn recording!")

    # Small delay for message reading
    time.sleep(2)

    try:
        # Start the Flask app
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n🎉 Demo UI stopped!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you've activated the virtual environment:")
        print("   source ../../venv/bin/activate")

if __name__ == "__main__":
    main()