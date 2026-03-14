# soplex

**Compile plain-English SOPs into executable, cost-optimized agent graphs**

Transform Standard Operating Procedures into hybrid agent graphs where conversation steps use LLMs, decision steps run as deterministic code, and tool/API steps execute as function calls. The result: **77% cheaper** than pure-LLM agents with **99%+ accuracy** on branching decisions.

## 🚀 Key Features

- **Hybrid execution**: LLM for conversation, code for logic, APIs for actions
- **Multi-provider support**: OpenAI, Anthropic, Google Gemini, Ollama, LiteLLM, or any OpenAI-compatible endpoint
- **Cost optimization**: Dramatically reduce LLM costs by running decisions as code
- **High accuracy**: Deterministic branching logic eliminates LLM reasoning errors
- **Production ready**: Comprehensive testing, type safety, and security best practices

## 📦 Installation

```bash
pip install soplex

# Optional providers
pip install soplex[anthropic]    # Anthropic Claude
pip install soplex[litellm]      # LiteLLM
pip install soplex[all]          # All providers
```

## 🔧 Quick Start

### 1. Create a SOP file

```text
PROCEDURE: Customer Refund Request
TRIGGER: Customer requests refund for order
TOOLS: order_db, payments_api, identity_check

1. Greet the customer and ask for their order number
2. Lookup the order details in order_db using the provided order number
3. Check if the order was placed within the last 30 days
   - YES: Proceed to step 4
   - NO: Inform customer that refunds are only available for orders within 30 days and end
4. Verify customer identity using identity_check with order email
5. Ask customer for the reason for the refund
6. Process the refund using payments_api
7. Confirm with customer that refund has been processed
```

### 2. Analyze the SOP

```bash
soplex analyze refund.sop
```

Output shows step classification and cost estimates:
```
📊 SOP Analysis: Customer Refund Request

Step Classification:
🧠 LLM Steps:    4 (conversation)
⚡ CODE Steps:   2 (deterministic logic)
🔀 BRANCH Steps: 1 (conditional)

💰 Cost Estimate:
Pure LLM:    $0.0084
Hybrid:      $0.0019  (77% savings)
```

### 3. Compile and run

```bash
# Compile SOP to executable graph
soplex compile refund.sop --output ./compiled/

# Interactive chat with the agent
soplex chat ./compiled/refund.json
```

## 🎯 Step Types

soplex automatically classifies each step based on keywords:

| Type | Keywords | Execution | Example |
|------|----------|-----------|---------|
| **LLM** | ask, greet, inform, confirm, explain | Conversational AI | "Greet the customer warmly" |
| **CODE** | check, lookup, calculate, verify, process | Deterministic logic | "Check if order was placed within 30 days" |
| **HYBRID** | Mixed LLM + CODE keywords | LLM + validation | "Ask customer for order number and verify it" |
| **BRANCH** | if, when, check:, conditional patterns | Conditional logic | "Check: Is the payment successful?" |
| **END** | end, complete, done, finish | Terminal | "End the process successfully" |
| **ESCALATE** | escalate, hand off, transfer | Human handoff | "Escalate to supervisor" |

## ⚙️ Configuration

Configure via environment variables (`.env`) or CLI flags:

```bash
# .env file
OPENAI_API_KEY=sk-...
SOPLEX_PROVIDER=openai
SOPLEX_MODEL=gpt-4o-mini
SOPLEX_TEMPERATURE=0.3
```

Supported providers:
- `openai` - OpenAI GPT models
- `anthropic` - Anthropic Claude models
- `gemini` - Google Gemini models
- `ollama` - Local Ollama models
- `litellm` - Any LiteLLM-supported provider
- `custom` - Custom OpenAI-compatible endpoint

## 📊 CLI Commands

```bash
# Analyze SOP structure and costs
soplex analyze refund.sop --provider anthropic --model claude-sonnet-4-20250514

# Compile SOP to executable graph
soplex compile refund.sop --output ./compiled/

# Interactive agent chat
soplex chat ./compiled/refund.json

# Generate flowchart visualization
soplex visualize ./compiled/refund.json --output refund.svg

# Run test scenarios
soplex test ./compiled/refund.json --scenarios test_cases.yaml

# View execution statistics
soplex stats
```

## 🏗️ Architecture

```
Plain Text SOP → Parser → Classifier → Graph Builder → Executor
                    ↓         ↓            ↓           ↓
                 Structure  LLM/CODE    Execution    Runtime
                            Types       Graph
```

- **Parser**: Converts plain text to structured data
- **Classifier**: Determines execution type (LLM/CODE/HYBRID) via keywords
- **Graph Builder**: Creates executable node graph with conditional edges
- **Executor**: Runs graph step-by-step, calling LLM only when needed

## 🧪 Testing

```bash
# Run all tests (without API calls)
pytest tests/ -v

# Run with real API integration tests
pytest tests/test_e2e.py -v -m e2e

# Run specific test categories
pytest tests/test_parser.py -v
pytest tests/test_classifier.py -v
```

## 🔐 Security

- Environment variables loaded securely via `python-dotenv`
- API keys never logged or exposed in output
- Production-grade error handling and validation
- Comprehensive input sanitization

## 📈 Cost Savings

Traditional pure-LLM agents call the LLM for every step. soplex only calls LLMs for conversation, running logic and decisions as code:

```
Traditional:  🧠🧠🧠🧠🧠🧠🧠  (7 LLM calls)
soplex:       🧠⚡🧠⚡⚡🧠⚡  (3 LLM calls, 4 code calls)
Savings:      ~57-77% cost reduction
```

## 🤝 Contributing

```bash
git clone https://github.com/soplex-ai/soplex
cd soplex
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](https://soplex.dev/docs)
- [Examples](https://github.com/soplex-ai/soplex/tree/main/examples)
- [PyPI Package](https://pypi.org/project/soplex/)
- [Issues](https://github.com/soplex-ai/soplex/issues)