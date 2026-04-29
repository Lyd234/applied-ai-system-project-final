🐾 PawPal+
AI-Powered Pet Care Scheduler with RAG + Agentic Workflow

Original Project (Modules 1–3)
The original PawPal+ was built in Modules 1–3 as a structured pet care planning system. It modelled owners, pets, and tasks as Python dataclasses and exposed a deterministic greedy scheduler that built a daily care plan by selecting and ordering pending tasks by priority and available time. The system included conflict detection, recurring task support, and a Streamlit UI for manual data entry — but had no AI integration and required owners to type in every task by hand.

Title & Summary
PawPal+ helps pet owners plan their daily care routines without manual form-filling. An owner describes their pets in plain language — "Bella is a senior border collie, she needs a walk and her arthritis meds" — and the system extracts structured tasks, retrieves species-specific care guidelines, schedules the day intelligently, and verifies the plan before displaying it.
It matters because generic scheduling tools don't know that senior dogs need shorter walks, or that medication tasks must always be high priority. PawPal+ retrieves vetted care guidelines before generating any tasks, so the schedule reflects real domain knowledge rather than guesswork.

Architecture Overview
Data flows through four stages:
User (plain language)
        |
        v
  [Retriever]  ──────────────────>  ChromaDB knowledge base
  retriever.py                      care_guidelines.json
  embeds input, returns top-3       (35 entries, dog/cat/other)
  care guideline chunks
        |
        v
  [Claude Agent]
  agent.py
  system prompt = input + retrieved context
  calls add_task / flag_issue tools
  populates Pet.tasks
        |
        v
  [Scheduler]  <── unchanged from Modules 1-3
  pawpal_system.py
  generate_day_plan(), detect_time_conflicts()
        |
        v
  [Claude Verifier]  ──── agentic loop ────>  back to Scheduler
  second Claude call                           if issues found,
  checks plan for gaps/conflicts               re-runs with
  returns JSON issues list                     reduced time
        |
        v
  [Streamlit UI]
  app.py
  displays plan + warnings + explain_plan()

  [pawpal.log]  <── logs every tool call, retrieval, and API error
Key principle: pawpal_system.py is completely unchanged from Modules 1–3. The agent feeds data into it — it does not replace it.

Setup Instructions
Prerequisites: Python 3.10+, an Anthropic API key from console.anthropic.com
bash# 1. Clone the project
git clone https://github.com/your-username/pawpal-plus.git
cd pawpal-plus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...

# 4. Build the knowledge base (run once)
python retriever.py --build

# 5. Launch the app
streamlit run app.py

# 6. (Optional) Run the reliability tests
pytest tests/ -v
requirements.txt
streamlit
anthropic
chromadb
pytest
python-dotenv
.env.example
ANTHROPIC_API_KEY=your_key_here

Sample Interactions
Example 1 — Senior dog with medication
Input:

"Rex is a 9-year-old golden retriever. He needs his heart medication at 8am, a gentle walk, and his evening meal."

Retrieved guidelines: dog-meds-general (high, 5m), dog-walk-senior (medium, 20m), dog-feed-senior (high, 10m)
Output:
Today's plan:
- Heart medication   5m   High    08:00
- Evening meal      10m   High    18:00
- Morning walk      20m   Medium  09:00

No conflicts detected.
Total: 35 minutes of 90 available.

Example 2 — Kitten and adult cat with a time conflict
Input:

"Luna is a 4-month-old kitten. Shadow is a 5-year-old cat. Both need feeding at 7am and playtime."

Retrieved guidelines: cat-feed-kitten (3 meals/day), cat-feed-adult (2 meals/day), cat-play-kitten (high, 20m), cat-play-adult (medium, 15m)
Output:
Today's plan:
- Luna feeding       10m   High    07:00
- Luna play session  20m   High    08:00
- Shadow feeding     10m   High    07:00
- Shadow play        15m   Medium  15:00

⚠ Warning: Conflict at 07:00 — Luna feeding and Shadow feeding
  are scheduled at the same time.
  Suggestion: stagger feedings by 5 minutes.

Example 3 — Limited time, multi-pet
Input:

"I only have 45 minutes today. Mochi (adult lab) needs a walk and feeding. Piper (adult cat) needs play and feeding."

Output (first pass):
Today's plan:
- Mochi morning walk  45m   High

⚠ Verifier flagged: Feeding tasks for both pets were dropped.
  Two high-priority tasks are missing from the plan.
Output (after agentic revision):
Agent revised plan (owner prompted to update available time to 90m):
- Mochi morning walk   45m   High
- Mochi feeding        10m   High
- Piper feeding        10m   High

Piper play session deferred — insufficient time remaining.
Total: 65 minutes.

Design Decisions
1. Algorithmic core, AI on top
The scheduling logic (Scheduler, Task, Pet, Owner) is pure Python — no AI dependency. This means the app works even when the Gemini API fails. AI sits as a layer on top, not underneath.

2. Greedy planner over optimal
generate_day_plan() uses a greedy algorithm (sort by priority, take tasks that fit). It's deterministic, fast, and easy to test. An optimal solver would be overkill for a daily pet care list.

3. Guardrails before the API call
Input is validated before anything is sent to Gemini. If Gemini returns bad JSON or hits a quota error, the code falls back to the rule-based planner silently. The app never crashes because of the AI layer.

4. Two Gemini calls, not one
Gemini is called twice — once to plan (select tasks), once to explain (write the summary). Keeping them separate means a failed explanation doesn't break the plan, and each prompt is focused and smaller.

5. RAG over fine-tuning
Care guidelines live in a static JSON file. Retrieval filters by species + age group + care needs before augmenting the Gemini prompt. This is cheaper and more transparent than training a model — guidelines can be updated without touching code.

6. Conflict resolution in Python, not AI
Time conflict detection and resolution (detect_time_conflicts, resolve_conflicts) are deterministic Python rules. AI doesn't need to reason about this — "keep the highest-priority task at a conflicting slot" is a clear rule, not a judgment call.

7. Recurring tasks via spawning
mark_complete() creates a new Task instance for the next occurrence rather than mutating a recurring record. This keeps each task's history clean and makes testing straightforward.

8. .env + .gitignore from the start
The API key is never hardcoded. python-dotenv loads it at runtime, and .gitignore prevents it from being committed — a security decision made before any code was pushed.

9. Session state drives the UI loop
Streamlit reruns the whole script on every interaction. st.session_state holds the owner, last agent result, and scheduler so state survives across reruns without re-running the agent unnecessarily.

Trade-offs:

LLM outputs aren't 100% deterministic. Task title capitalisation can vary across runs — the reliability test normalises to lowercase to handle this.
Every natural-language submission makes two Claude API calls. For production this would need caching; for a class project it's acceptable.
The 35-entry knowledge base covers common pets. Exotic species would need extension.


Testing Summary
What worked:
The rag pipline was able to suggest appropriate task based on the guideline
The systen was able to successfully fall back on the greedy algorith to schedule  when the ai agent wasn't woking or quota exceeded 

What didn't work as expected:
Gemini Api runned quota exceeded before runnig sufficent tests



Reflection
- when incorporating Agentic workflow it is necessary to make sure that there is a fall back system the design and adding guardrails is necessary . testing all of the cases separately is necessary.
- separating the algorithm from the AI workflow allows easy debugging.
- Adding Rag pipeline enhances the quality of the answer more relevant even with the presence of an agentic workflow.