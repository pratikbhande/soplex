# 🎬 Complete Demo Recording Instructions

## 📋 Pre-Recording Setup

### 1. Activate Virtual Environment
```bash
cd /path/to/soplex
source venv/bin/activate
```

### 2. Install Demo Dependencies
```bash
cd benchmark_demo
pip install flask plotly pandas
```

### 3. Terminal Setup (for best video quality)
```bash
# Clean terminal
clear

# Set simple prompt
export PS1="$ "

# Increase font size for recording
# (Do this in your terminal preferences)
```

---

## 🎯 Demo Recording Flow

### **Part 1: Show the SOP (30 seconds)**

```bash
# Navigate to demo directory
cd benchmark_demo

# Show the complex SOP we'll be demonstrating
echo "📄 This is our enterprise KYC SOP - 21 complex steps:"
cat sops/enterprise_kyc.sop
```

**Talking Points:**
- "Here's a real-world UK KYC process"
- "21 steps including Companies House, AML screening, compliance"
- "Traditional agents would call expensive LLMs for every step"

---

### **Part 2: CLI Demonstration (2 minutes)**

```bash
# Activate environment first
source ../venv/bin/activate

# Show available commands
echo "🛠️ Let me show you soplex CLI capabilities:"
soplex --help
```

**Talking Points:**
- "Simple pip install soplex-ai gets you all these tools"

```bash
# Analyze the SOP structure
echo "📊 First, let's analyze our SOP:"
soplex analyze sops/enterprise_kyc.sop
```

**Talking Points:**
- "See how it classifies each step automatically"
- "Notice the cost estimates - traditional vs optimized"

```bash
# Compile to executable graph
echo "🏗️ Now let's compile it to an executable graph:"
soplex compile sops/enterprise_kyc.sop --output compiled/

# Show what was generated
ls -la compiled/
echo "✅ Executable graph created!"
```

**Talking Points:**
- "Converts plain English into executable code"
- "Ready for production deployment"

```bash
# Generate visualization
echo "🎨 Let's visualize the execution flow:"
soplex visualize compiled/enterprise_kyc.json --output results/kyc_flow.svg

# Show that it was created
ls -la results/
echo "✅ Flowchart generated!"
```

**Talking Points:**
- "Visual representation of the hybrid execution"
- "See the mix of LLM, code, and API calls"

---

### **Part 3: Launch Comparison UI (30 seconds)**

```bash
# Launch the fancy UI
echo "🚀 Now for the live cost comparison demo:"
python launch_demo_ui.py
```

**Talking Points:**
- "This opens our comparison interface"
- "You'll see the dramatic cost difference in real-time"

---

### **Part 4: UI Demo (2-3 minutes)**

Once the UI opens at http://localhost:5000:

1. **Show the Interface (15 seconds)**
   - Point out the key stats at the top
   - Highlight UK market focus

2. **Click "Start Live Comparison" (30 seconds)**
   - Watch the progress bar
   - Show live logs appearing
   - Let it complete both approaches

3. **Review Results (90 seconds)**
   - **Cost Comparison**: Point to 77% savings
   - **Performance**: Show 4x speed improvement
   - **Architecture**: Explain hybrid model
   - **UK Features**: Highlight Companies House integration

4. **Key Talking Points:**
   - "Traditional: $0.10+ and 16 LLM calls"
   - "Soplex: $0.02 and only 4 LLM calls"
   - "Same accuracy, dramatically lower cost"
   - "Perfect for UK compliance workloads"

---

## 🎯 Key Messages to Emphasize

### **Problem Statement**
- "Traditional AI agents are expensive and error-prone"
- "Every step requires costly LLM calls, even simple logic"
- "Hallucination risk on business-critical decisions"

### **Solution Benefits**
- "Soplex uses hybrid execution: LLM + Code + APIs"
- "77% cost reduction with better accuracy"
- "Built for UK market: Companies House, KYC/AML"
- "Production-ready: security, testing, monitoring"

### **Call to Action**
- "pip install soplex-ai to get started"
- "Perfect for UK fintech and enterprise"
- "Transform your AI agent costs today"

---

## 📱 Quick Commands Cheat Sheet

```bash
# Setup
cd benchmark_demo
source ../venv/bin/activate

# Demo sequence
cat sops/enterprise_kyc.sop                                    # Show SOP
soplex --help                                                  # Show capabilities
soplex analyze sops/enterprise_kyc.sop                        # Analyze structure
soplex compile sops/enterprise_kyc.sop --output compiled/     # Compile graph
soplex visualize compiled/enterprise_kyc.json --output flow.svg # Generate viz
python launch_demo_ui.py                                       # Launch UI
```

---

## 🎬 Video Structure Summary

| Time | Section | Focus |
|------|---------|-------|
| 0-30s | SOP Demo | Show complex real-world workflow |
| 30s-2:30 | CLI Demo | Demonstrate soplex capabilities |
| 2:30-3:00 | UI Launch | Transition to visual comparison |
| 3:00-6:00 | UI Demo | Live cost comparison and results |
| 6:00+ | Wrap-up | Call to action and next steps |

---

## 💡 Pro Tips for Great Recording

1. **Smooth Terminal Work**: Practice the commands beforehand
2. **Clear Narration**: Explain what you're doing as you do it
3. **Highlight Numbers**: Point out the 77% savings clearly
4. **Show UK Focus**: Emphasize Companies House, compliance
5. **Keep Energy High**: This is impressive tech - show enthusiasm!

---

**Ready to record? This demo will definitely impress UK companies! 🚀**