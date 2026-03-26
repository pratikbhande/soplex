# 🎬 Video Recording Guide for LinkedIn

## 🎯 Video Structure (1-2 minutes total)

### Opening Hook (0-15 seconds)
```
"What if I told you that you could reduce AI agent costs by 77%
while improving accuracy to 99%? Let me show you soplex-ai."
```

### Problem Statement (15-30 seconds)
- Traditional AI agents call expensive LLMs for EVERY step
- Even simple logic like "if status = active" costs $0.03-0.06 per call
- Prone to hallucination errors in business decisions

### Solution Demo (30-90 seconds)

#### Quick Comparison Demo
```bash
cd benchmark_demo
python run_comparison.py
```

**Key Callouts:**
- Traditional: 16 LLM calls, $0.0084
- Soplex: 4 LLM calls, $0.0019 (77% savings)
- Show hybrid execution: 🧠→⚡→🧠→⚡

#### CLI Showcase (30 seconds)
```bash
# Show analysis
soplex analyze sops/enterprise_kyc.sop

# Show compilation
soplex compile sops/enterprise_kyc.sop --output compiled/

# Show visualization
soplex visualize compiled/enterprise_kyc.json --output flow.svg
```

### UK Market Focus (90-105 seconds)
- "Perfect for UK fintech and compliance"
- Show KYC/AML pipeline with Companies House API
- Highlight regulatory compliance features

### Call to Action (105-120 seconds)
```
"Ready to cut your AI costs by 77%?
pip install soplex-ai
Visit soplex.dev for more info
#soplex #aioptimization #fintech #uktech"
```

## 🎥 Recording Tips

### Terminal Setup
```bash
# Use large font for readability
export PS1="$ "
clear
```

### Demo Commands (Run in order)
```bash
# 1. Navigate to demo
cd benchmark_demo

# 2. Quick analysis (10 seconds)
soplex analyze sops/enterprise_kyc.sop

# 3. Full comparison (30 seconds)
python run_comparison.py

# 4. CLI showcase (optional, if time allows)
soplex visualize compiled/enterprise_kyc.json --output results/flow.svg
```

## 📝 Key Talking Points

1. **Cost Optimization**
   - "77% cost reduction through hybrid execution"
   - "LLMs only for conversation, code for logic"

2. **UK Market Relevance**
   - "Built for UK compliance: KYC, AML, Companies House"
   - "Perfect for London fintech scene"

3. **Enterprise Ready**
   - "Production-grade security and testing"
   - "Deterministic decisions, no AI hallucination"

4. **Developer Friendly**
   - "Simple pip install soplex-ai"
   - "CLI + Python API + visualization"

## 🎨 Visual Elements to Highlight

- **Terminal output** showing cost comparison
- **File structure** in the demo directory
- **Generated visualizations** (if time permits)
- **Performance metrics** from comparison

## 📱 Social Media Copy

### LinkedIn Post
```
🚀 Just built soplex-ai: an AI agent framework that cuts costs by 77%

Traditional agents: 🧠🧠🧠🧠🧠🧠 (expensive LLM calls for everything)
soplex agents: 🧠⚡🧠⚡⚡🧠 (LLM + code hybrid)

Perfect for UK fintech:
✅ Companies House integration
✅ KYC/AML compliance
✅ 99%+ decision accuracy
✅ Deterministic logic (no hallucination)

pip install soplex-ai

#AI #fintech #optimization #uktech #compliance
```

### Hashtags
```
#soplex #aioptimization #fintech #uktech #compliance
#kyc #aml #companieshouse #llm #aiagents #automation
#pythonai #opensource #linkedin #ukstartup
```

## 🔧 Backup Commands (if demo fails)

```bash
# If soplex not installed
pip install soplex-ai[all]

# If virtual environment needed
source venv/bin/activate

# Quick fallback demo
python soplex_approach/run_soplex.py
```