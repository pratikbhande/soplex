#!/usr/bin/env python3
"""
Test Complete Demo Flow
Validates that everything works end-to-end
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success/failure"""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Success: {description}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()[:200]}...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e.stderr.strip()[:200]}...")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def test_soplex_installation():
    """Test if soplex is properly installed"""
    print("\n" + "="*50)
    print("TESTING SOPLEX INSTALLATION")
    print("="*50)

    success = run_command(['soplex', '--help'], 'Check soplex CLI availability')
    if success:
        run_command(['soplex', 'analyze', 'sops/enterprise_kyc.sop'], 'Test soplex analyze')
    return success

def test_graph_compilation():
    """Test graph compilation"""
    print("\n" + "="*50)
    print("TESTING GRAPH COMPILATION")
    print("="*50)

    # Create directories
    os.makedirs('compiled', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    success = run_command([
        'soplex', 'compile', 'sops/enterprise_kyc.sop',
        '--output', 'compiled/'
    ], 'Compile SOP to graph')

    if success:
        # Check if files were created
        compiled_files = list(Path('compiled').glob('*.json'))
        if compiled_files:
            print(f"✅ Graph files created: {[f.name for f in compiled_files]}")

            # Check file content
            with open(compiled_files[0]) as f:
                try:
                    data = json.load(f)
                    print(f"✅ Valid JSON structure")
                    print(f"Graph keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    return True
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON in compiled file")
                    return False
        else:
            print(f"❌ No compiled files found")
            return False

    return success

def test_dependencies():
    """Test required Python dependencies"""
    print("\n" + "="*50)
    print("TESTING PYTHON DEPENDENCIES")
    print("="*50)

    dependencies = ['flask', 'plotly', 'networkx', 'pandas']
    all_good = True

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - installed")
        except ImportError:
            print(f"❌ {dep} - missing")
            all_good = False

    return all_good

def test_graph_visualizer():
    """Test the fixed graph visualizer"""
    print("\n" + "="*50)
    print("TESTING GRAPH VISUALIZER")
    print("="*50)

    try:
        sys.path.append('web_ui')
        from fixed_graph_visualizer import FixedSoplexGraphVisualizer

        visualizer = FixedSoplexGraphVisualizer()
        print("✅ Graph visualizer imported successfully")

        # Test with compiled graph
        compiled_files = list(Path('compiled').glob('*.json'))
        if compiled_files:
            try:
                graph_data = visualizer.generate_plotly_graph(str(compiled_files[0]))
                if graph_data:
                    print("✅ Graph visualization generated successfully")

                    stats = visualizer.get_graph_stats(str(compiled_files[0]))
                    print(f"✅ Graph stats: {stats}")
                    return True
                else:
                    print("❌ Graph visualization failed")
                    return False
            except Exception as e:
                print(f"❌ Graph visualization error: {e}")
                return False
        else:
            print("❌ No compiled graph files found for testing")
            return False

    except ImportError as e:
        print(f"❌ Cannot import graph visualizer: {e}")
        return False

def test_web_server():
    """Test if web server can start (quick test)"""
    print("\n" + "="*50)
    print("TESTING WEB SERVER")
    print("="*50)

    try:
        # Quick import test
        sys.path.append('web_ui')
        import app
        print("✅ Flask app imports successfully")
        print("💡 Server should start without errors")
        return True
    except Exception as e:
        print(f"❌ Flask app import error: {e}")
        return False

def main():
    print("🧪 SOPLEX COMPLETE DEMO FLOW TEST")
    print("="*60)

    # Change to demo directory
    os.chdir(Path(__file__).parent)
    print(f"Working directory: {os.getcwd()}")

    tests = [
        ("Dependencies", test_dependencies),
        ("Soplex Installation", test_soplex_installation),
        ("Graph Compilation", test_graph_compilation),
        ("Graph Visualizer", test_graph_visualizer),
        ("Web Server", test_web_server)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "🎯"*20)
    print("TEST SUMMARY")
    print("🎯"*20)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"🚀 Ready to launch demo UI:")
        print(f"   python launch_demo_ui.py")
    else:
        print(f"\n⚠️ Some tests failed. Fix issues before running demo.")
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"Failed tests: {', '.join(failed_tests)}")

if __name__ == "__main__":
    main()