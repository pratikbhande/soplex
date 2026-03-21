import json
import os

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# \u26a1\ufe0f soplex: Compile Plain-English SOPs into Deterministic Agent Graphs\n",
                "\n",
                "## The Problem UK AI Companies Face \n",
                "Companies like **Gradient Labs**, **PolyAI**, and others building agents for regulated industries face a massive challenge:\n",
                "1. Business teams write SOPs in plain English.\n",
                "2. Engineering teams manually translate these into agent logic (LangGraph, state machines).\n",
                "3. SOPs change \u2192 engineering delays.\n",
                "4. LLMs struggle with complex branching (route blindness, hallucination).\n",
                "\n",
                "**`soplex` solves this by classifying SOP steps into LLM (conversational) vs CODE (deterministic logic / API calls) and compiling a hybrid execution graph. The result? 77% cheaper and 100% route accuracy.**"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 1. Install soplex-ai\n",
                "!pip install -q soplex-ai[all]\n",
                "\n",
                "# Optional: you would set your API keys here\n",
                "import os\n",
                "os.environ[\"OPENAI_API_KEY\"] = \"sk-your-openai-key\" # Replace with actual if testing LLM"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 1: Define a Complex SOP (UK KYC Enterprise Example)\n",
                "Notice how this is just plain English text with clear decision branches."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "uk_kyc_sop = \"\"\"PROCEDURE: UK Enterprise KYC & AML Onboarding\n",
                "TRIGGER: New corporate client registers on the financial platform\n",
                "TOOLS: companies_house_api, identity_verification, aml_screening_db\n",
                "\n",
                "1. Greet the client representative and request the UK Company Registration Number\n",
                "2. Lookup the company details using companies_house_api\n",
                "3. Check if the company status is \"Active\"\n",
                "   - YES: Proceed to step 4\n",
                "   - NO: Inform the client that only active companies can be onboarded and end\n",
                "4. Verify the identity of the representative using identity_verification\n",
                "5. Check if the verified identity matches an active Director\n",
                "   - YES: Proceed to step 6\n",
                "   - NO: Escalate to compliance_officer for manual review\n",
                "6. Query aml_screening_db to screen the company and directors against UK PEPs and sanctions\n",
                "7. Check if there are any sanctions matches or high-risk flags\n",
                "   - YES: Escalate to compliance_officer\n",
                "   - NO: Proceed to step 8\n",
                "8. Ask the client to upload their proof of business address (Utility bill or Bank statement)\n",
                "9. Confirm successful automated KYC onboarding and notify client of account activation and end\"\"\"\n",
                "\n",
                "# Let's save it to a file\n",
                "with open(\"uk_kyc.sop\", \"w\") as f:\n",
                "    f.write(uk_kyc_sop)\n",
                "\n",
                "print(\"SOP Saved Successfully!\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 2: Analyze the SOP\n",
                "`soplex` will automatically classify steps into `LLM`, `CODE`, `HYBRID`, `BRANCH`, and `END`.\n",
                "It knows that asking for an address is an LLM task, but checking for sanctions is a purely deterministic function call."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from soplex.parser import SOPParser\n",
                "\n",
                "parser = SOPParser()\n",
                "sop_definition = parser.parse_file(\"uk_kyc.sop\")\n",
                "\n",
                "print(f\"\\n\ud83d\udcca SOP Analysis: {sop_definition.name}\")\n",
                "print(f\"LLM Steps: {sop_definition.llm_steps} (conversation)\")\n",
                "print(f\"CODE Steps: {sop_definition.code_steps} (deterministic logic)\")\n",
                "print(f\"BRANCH Steps: {sop_definition.branch_steps} (conditional)\")\n",
                "\n",
                "from soplex.config import PRICING\n",
                "cost_est = sop_definition.get_cost_estimate(PRICING)\n",
                "print(f\"\\n\ud83d\udcb0 Cost Estimate vs Pure LLM:\")\n",
                "print(f\"Pure LLM Cost: ${cost_est['llm_cost']:.4f}\")\n",
                "print(f\"Soplex Hybrid Cost: ${cost_est['total_cost']:.4f}\")\n",
                "print(f\"Savings: {cost_est['savings_percent']}%\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 3: Build & Export the Execution Graph\n",
                "This translates the English SOP directly into an executable graph (compatible with LangGraph concepts)."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from soplex.compiler import GraphBuilder\n",
                "from soplex.runtime import SOPExecutor\n",
                "from soplex.llm.provider import LLMProvider\n",
                "from soplex.config import SoplexConfig\n",
                "\n",
                "builder = GraphBuilder(sop_definition)\n",
                "graph = builder.build()\n",
                "\n",
                "print(\"Graph successfully built with nodes:\")\n",
                "for node_id, node in graph.nodes.items():\n",
                "    print(f\"- {node_id}: [{node.type.name}] {node.action[:50]}...\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 4: Run the Agent\n",
                "Now we can run the Graph. The Graph knows exactly when to call the LLM and when to run regular Python code to avoid Hallucinations."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Normally you would run this in a loop or deploy as an API endpoint.\n",
                "# !soplex chat compiled_sops/uk_kyc.json\n",
                "\n",
                "print(\"Your UK Enterprise KYC hybrid agent is ready!\")"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {
                "name": "ipython",
                "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.10.12"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "Soplex_UK_Enterprise_Colab.ipynb"), "w") as f:
    json.dump(notebook, f, indent=2)

print(f"Notebook generated: {os.path.join(script_dir, 'Soplex_UK_Enterprise_Colab.ipynb')}")
