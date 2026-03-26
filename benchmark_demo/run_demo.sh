#!/bin/bash
# Demo runner script that ensures virtual environment is activated

echo "🚀 Soplex AI Benchmark Demo"
echo "Activating virtual environment..."

# Activate the virtual environment
source ../venv/bin/activate

# Check if soplex is available
if command -v soplex &> /dev/null; then
    echo "✅ soplex CLI found and ready"
    echo ""

    # Run the demo
    python3 run_complete_demo.py
else
    echo "❌ soplex CLI not found even in virtual environment"
    echo "💡 Installing soplex-ai..."
    pip install "soplex-ai[all]"

    if command -v soplex &> /dev/null; then
        echo "✅ soplex CLI installed successfully"
        echo ""
        python3 run_complete_demo.py
    else
        echo "❌ Failed to install soplex CLI"
        exit 1
    fi
fi