# 🎬 Soplex AI Demo Guide
## Self-Explanatory Demo for Video Recording

### 📋 Demo Overview
This demo showcases soplex-ai's cost optimization and accuracy advantages through:
1. **Traditional vs Soplex Comparison** - Side-by-side execution with metrics
2. **CLI Showcase** - All soplex commands in action
3. **Complex SOP Benchmarks** - Real-world enterprise scenarios

### 🚀 Demo Execution Order

#### Part 1: Traditional vs Soplex Comparison (2-3 minutes)
```bash
# Navigate to demo directory
cd benchmark_demo

# Run traditional approach (pure LLM)
python traditional_approach/run_traditional.py

# Run soplex approach (hybrid)
python soplex_approach/run_soplex.py

# View comparison results
cat results/comparison_results.json
```

#### Part 2: CLI Showcase (2-3 minutes)
```bash
# Analyze SOP structure and costs
soplex analyze sops/enterprise_kyc.sop

# Compile SOP to executable graph
soplex compile sops/enterprise_kyc.sop --output compiled/

# Generate flowchart visualization
soplex visualize compiled/enterprise_kyc.json --output results/kyc_flow.svg

# Interactive chat with agent
soplex chat compiled/enterprise_kyc.json

# Run test scenarios
soplex test compiled/enterprise_kyc.json --scenarios tools/test_scenarios.yaml
```

#### Part 3: Complex SOP Demonstration (1-2 minutes)
```bash
# Show multiple complex SOPs
ls sops/

# Quick analysis of each
soplex analyze sops/financial_fraud_detection.sop
soplex analyze sops/customer_escalation_flow.sop
soplex analyze sops/regulatory_compliance.sop
```

### 📊 Expected Results
- **Cost Savings**: 70-80% reduction vs pure LLM
- **Accuracy**: 99%+ on decision branches
- **Speed**: 3-5x faster execution
- **Scalability**: Linear cost growth vs exponential

### 🎯 Key Talking Points
1. **Hybrid Architecture**: LLM + Code + APIs
2. **UK Market Focus**: KYC/AML compliance examples
3. **Enterprise Ready**: Security, testing, monitoring
4. **Developer Friendly**: CLI + Python API + Visualization

### 📁 File Structure
```
benchmark_demo/
├── DEMO_GUIDE.md              # This guide
├── sops/                      # Complex SOP examples
├── traditional_approach/      # Pure LLM implementation
├── soplex_approach/          # Hybrid soplex implementation
├── cli_showcase/             # CLI demonstration scripts
├── results/                  # Output files and metrics
└── tools/                    # Test scenarios and utilities
```

### ⚡ Quick Start
```bash
# Install soplex if needed
pip install soplex-ai[all]

# Run complete demo
./run_complete_demo.sh
```