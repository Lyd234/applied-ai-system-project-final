import json
import logging
import os
from datetime import datetime
from typing import Dict, List

import google.generativeai as genai

from pawpal_system import Owner, Scheduler, Task

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODEL = "gemini-1.5-flash"
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))


# ── ASCII timeline ─────────────────────────────────────────────────────────────

def ascii_timeline(plan: List[Task], available_minutes: int) -> str:
    if not plan:
        return "  (no tasks scheduled)"

    BAR_MAX = 24
    peak = max(t.duration_minutes for t in plan)
    used = sum(t.duration_minutes for t in plan)

    lines = [
        "",
        "  DAILY PLAN",
        "  " + "─" * 55,
    ]
    for t in plan:
        bar = "█" * max(1, int(t.duration_minutes / peak * BAR_MAX))
        tag = {"high": "[ HIGH ]", "medium": "[ MED  ]", "low": "[ LOW  ]"}.get(t.priority, "[  ?   ]")
        lines.append(f"  {t.time}  {bar:<{BAR_MAX}}  {t.title[:22]:<22}  {t.duration_minutes:>3}min  {tag}")
    lines += [
        "  " + "─" * 55,
        f"  {used} / {available_minutes} min used",
        "",
    ]
    return "\n".join(lines)


# ── Agent ──────────────────────────────────────────────────────────────────────

class PawPalAgent:
    """
    Simple agentic loop:
      Retrieve → Guardrail → Gemini Plan → Act → Gemini Explain → Output
    """

    def __init__(self, owner: Owner):
        self.owner = owner
        self.scheduler = Scheduler(owner)
        self.gemini = genai.GenerativeModel(MODEL)
        self.logs: List[Dict] = []

    # ── Logging ────────────────────────────────────────────────────────────────

    def _log(self, step: str, detail: str) -> None:
        entry = {"time": datetime.now().strftime("%H:%M:%S"), "step": step, "detail": detail}
        self.logs.append(entry)
        logger.info("[%s] %s", step, detail)

    # ── Guardrail ──────────────────────────────────────────────────────────────

    def _validate(self) -> List[str]:
        issues = []
        for pet in self.owner.get_all_pets():
            for t in pet.pending_tasks():
                if t.duration_minutes <= 0:
                    issues.append(f"'{t.title}': duration must be > 0")
                if len(t.time) != 5 or ":" not in t.time:
                    issues.append(f"'{t.title}': time must be HH:MM")
                if t.priority not in {"high", "medium", "low"}:
                    issues.append(f"'{t.title}': unknown priority '{t.priority}'")
        return issues

    # ── Gemini: plan ───────────────────────────────────────────────────────────

    def _gemini_plan(self, pending: List[Task]) -> List[Task]:
        task_lines = "\n".join(
            f"- {t.title} | {t.priority} | {t.duration_minutes}min | {t.time}"
            for t in pending
        )
        prompt = (
            f"You are a pet care assistant.\n"
            f"Owner '{self.owner.name}' has {self.owner.available_time} minutes available today.\n\n"
            f"Pending tasks:\n{task_lines}\n\n"
            f"Pick the best tasks for today. Prefer high-priority. Stay within the time budget.\n"
            f'Reply ONLY with JSON: {{"selected_tasks": ["Task A", "Task B"], "reasoning": "one sentence"}}'
        )
        try:
            raw = self.gemini.generate_content(prompt).text.strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            self._log("PLAN", f"Gemini response: {raw[:150]}")
            data = json.loads(raw)
            titles = {t.lower() for t in data.get("selected_tasks", [])}
            chosen = [t for t in pending if t.title.lower() in titles]
            self._log("PLAN", f"Selected {len(chosen)} task(s). Reason: {data.get('reasoning', '')}")
            return chosen if chosen else self._fallback(pending)
        except Exception as e:
            self._log("GUARDRAIL", f"Gemini plan failed ({e}). Using fallback.")
            return self._fallback(pending)

    def _fallback(self, pending: List[Task]) -> List[Task]:
        self._log("GUARDRAIL", "Falling back to rule-based planner.")
        return self.scheduler.generate_day_plan()

    # ── Gemini: explain ────────────────────────────────────────────────────────

    def _gemini_explain(self, plan: List[Task]) -> str:
        plan_text = "\n".join(
            f"- {t.time}  {t.title}  ({t.priority}, {t.duration_minutes}min)" for t in plan
        )
        prompt = (
            f"Write a friendly 2-sentence explanation of this pet care plan for the owner.\n\n"
            f"Plan:\n{plan_text}"
        )
        try:
            return self.gemini.generate_content(prompt).text.strip()
        except Exception as e:
            self._log("GUARDRAIL", f"Gemini explain failed ({e}).")
            return "Your plan has been generated based on priority and available time."

    # ── Main run ───────────────────────────────────────────────────────────────

    def run(self) -> Dict:
        self._log("START", f"Agent started for '{self.owner.name}'")

        # Guardrail
        issues = self._validate()
        for i in issues:
            self._log("GUARDRAIL", i)

        # Retrieve
        pending = self.scheduler.retrieve_pending_tasks()
        self._log("RETRIEVE", f"{len(pending)} pending task(s) found")

        if not pending:
            self._log("OUTPUT", "No tasks to schedule.")
            return {
                "plan": [],
                "graph": "  (no tasks)",
                "explanation": "No pending tasks for today.",
                "summary": "0 tasks, 0 minutes.",
                "conflicts_resolved": [],
                "logs": self.logs,
                "issues": issues,
            }

        # Gemini plans
        plan = self._gemini_plan(pending)

        # Act: enforce time budget
        budget, used, safe = self.owner.available_time, 0, []
        for t in plan:
            if used + t.duration_minutes <= budget:
                safe.append(t)
                used += t.duration_minutes
        plan = safe
        self._log("ACT", f"{len(plan)} task(s) fit within {budget} min budget")

        # Act: resolve conflicts
        conflicts = self.scheduler.detect_time_conflicts(plan)
        conflicts_resolved: List[str] = []
        if conflicts:
            plan = self.scheduler.resolve_conflicts(plan)
            conflicts_resolved = conflicts
            self._log("ACT", f"Resolved {len(conflicts)} conflict(s)")

        # Sort by time
        plan = self.scheduler.sort_tasks_by_time(plan)

        # Gemini explains
        explanation = self._gemini_explain(plan)
        self._log("OUTPUT", self.scheduler.get_schedule_summary(plan))

        return {
            "plan": plan,
            "graph": ascii_timeline(plan, self.owner.available_time),
            "explanation": explanation,
            "summary": self.scheduler.get_schedule_summary(plan),
            "conflicts_resolved": conflicts_resolved,
            "logs": self.logs,
            "issues": issues,
        }
