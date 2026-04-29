import json
import os
from typing import Dict, List


class GuidelineRetriever:
    """
    RAG retriever: looks up care guidelines by species, age, and care needs.
    Input  → pet profile (species, age, care_needs)
    Output → list of matching guideline dicts from guideline.json
    """

    def __init__(self, path: str = "assets/guideline.json"):
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Skip any non-JSON prefix (e.g. editor-injected text like "Hide JSON")
        start = next((i for i, c in enumerate(content) if c in "[{"), 0)
        self.guidelines: List[Dict] = json.loads(content[start:])

    # ── Age group mapping ──────────────────────────────────────────────────────

    def _age_group(self, species: str, age: int) -> str:
        if species == "dog":
            if age < 1:  return "puppy"
            if age <= 7: return "adult"
            return "senior"
        if species == "cat":
            if age < 1:  return "kitten"
            if age <= 10: return "adult"
            return "senior"
        return ""  # "other" species have no age-group qualifier

    # ── Retrieve ───────────────────────────────────────────────────────────────

    def retrieve(self, species: str, age: int, care_needs: List[str]) -> List[Dict]:
        """Return guidelines matching the pet's species, age group, and care needs."""
        age_group = self._age_group(species, age)
        age_qualifiers = {"puppy", "kitten", "adult", "senior"}
        needs = [n.lower() for n in care_needs]
        results = []

        for g in self.guidelines:
            # Must match species
            if g["species"] != species:
                continue

            # Age-group filter (dog/cat only)
            if age_group:
                has_qualifier = any(q in g["id"] for q in age_qualifiers)
                if has_qualifier and age_group not in g["id"]:
                    continue

            # Category must be in care_needs (if care_needs provided)
            if needs and g["category"] not in needs:
                continue

            results.append(g)

        return results

    # ── Suggest new tasks ──────────────────────────────────────────────────────

    def suggest(self, species: str, age: int, care_needs: List[str],
                existing_categories: List[str]) -> List[Dict]:
        """Return guidelines whose category is not already covered by existing tasks."""
        covered = {c.lower() for c in existing_categories}
        return [
            g for g in self.retrieve(species, age, care_needs)
            if g["category"] not in covered
        ]

    # ── Format for prompt ──────────────────────────────────────────────────────

    def format_for_prompt(self, guidelines: List[Dict]) -> str:
        """Format retrieved guidelines as a readable block for Gemini context."""
        if not guidelines:
            return "No specific guidelines found."
        lines = []
        for g in guidelines:
            lines.append(
                f"[{g['category'].upper()}] {g['text']} "
                f"(suggested duration: {g['duration']}min, priority: {g['priority']})"
            )
        return "\n".join(lines)
