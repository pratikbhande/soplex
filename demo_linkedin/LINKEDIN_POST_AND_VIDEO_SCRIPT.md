# Soplex LinkedIn Post & Demo Video Guide

## The LinkedIn Post Draft

**Caption Idea:**

Every UK AI engineering team building for regulated industries (like Gradient Labs, PolyAI, etc.) eventually hits this wall: Complex SOP-driven workflows fail when handed entirely to an LLM.

Academic benchmarks (SOP-Maze/Agent-S) show that even GPT-4o only gets ~30-70% accuracy on complex SOPs due to:
❌ Route blindness (skips steps)
❌ Conversational fragility
❌ Calculation hallucinations

At Gradient Labs, they’ve solved this using "Limited Tool Exposure" per step in Otto.
I wanted to automate this.

Meet **`soplex`** — An open-source compiler that transforms plain-English SOPs into Deterministic Hybrid Agent Graphs. ⚡️

It automatically parses your SOP text and classifies each step:
🧠 LLM Step (Conversations, Extraction)
⚡️ CODE Step (API calls, lookups)
🔀 BRANCH Step (Deterministic if/else logic)

The Result:
✅ **77% Cheaper** because logic and databases run as pure code, not LLM reasoning steps.
✅ **100% Route Accuracy** because decisions are deterministic. Zero hallucination risk on branch logic.
✅ **LangGraph-compatible** export out-of-the-box.

I’ve uploaded a full Google Colab walkthrough for a **UK Enterprise KYC & AML Onboarding** use case.
Check out the demo video below and the Github repo in the comments! 👇

[Your Github Repo Link] | [Your Colab Notebook Link]

#soplex #agenticai #llm #aiengineering #automation #artificialintelligence

---

## 🎬 Demo Video Recording Script (SOP)

**Total video length:** ~60 seconds to 90 seconds max (optimized for LinkedIn attention).

**Setup Before Recording:**
1. Open your IDE with `demo_linkedin/uk_kyc.sop` on the left pane and a terminal on the right.
2. Have the graphs open in a separate image viewer window.

**Recording Steps:**

1. **[0:00 - 0:10] The Problem & The SOP**
   - **Visual:** Show `uk_kyc.sop` side-by-side with your terminal.
   - **Voiceover/Text-on-screen:** "Companies spend weeks manually translating SOPs into complex agent frameworks. With Soplex, you just write the SOP in plain English."
   - **Action:** Highlight the `uk_kyc.sop` structure (TRIGGER, TOOLS, and the branching logic at steps 3 and 5).

2. **[0:10 - 0:25] Analyzing the SOP**
   - **Visual:** Terminal.
   - **Action:** Run the command: `soplex analyze demo_linkedin/uk_kyc.sop`
   - **Voiceover/Text-on-screen:** "Soplex's compiler analyzes every step. It knows exactly which steps need an LLM for conversation, and which steps can just be deterministic code."
   - **Visual point:** Hover mouse over the terminal output showing the breakdown of LLM/CODE/BRANCH steps and the "Savings" percentage.

3. **[0:25 - 0:40] Running the Agent (The Magic)**
   - **Visual:** Terminal.
   - **Action:** Run `soplex compile demo_linkedin/uk_kyc.sop --output demo_linkedin/compiled/` then run `soplex chat demo_linkedin/compiled/uk_kyc.json`.
   - **Action:** Interact with the agent. Type a mock company registration number when prompted.
   - **Voiceover/Text-on-screen:** "When we run the agent, Soplex uses the LLM only for the chat. The database checks and branching logic run as pure, fast code. Zero hallucination risk."

4. **[0:40 - 0:55] Visualizing the Graph**
   - **Visual:** Terminal & Browser (Mermaid chart).
   - **Action:** Run `soplex visualize demo_linkedin/compiled/uk_kyc.json`
   - **Voiceover/Text-on-screen:** "It automatically generates a LangGraph-compatible state machine graph that you can export into your existing codebase."

5. **[0:55 - 1:10] The Benchmarks (Closing)**
   - **Visual:** Switch to the generated graphs (`cost_comparison.png` and `accuracy_comparison.png`).
   - **Voiceover/Text-on-screen:** "The result? We decrease per-execution cost by up to 77% and boost branching logic accuracy to 100%. Check out the open-source repo and Colab notebook to try it yourself."

**Tips for Screen Recording:**
- Zoom in on your terminal so the text is huge. LinkedIn videos are watched on phones!
- Keep pacing fast. Don't let the silence drag.
- Use a high-quality mic if doing voiceover. (If no voiceover, add nice captions and upbeat background music).
