from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional


@dataclass
class Task:
    title: str
    description: str
    duration_minutes: int
    time: str = "00:00"
    due_date: Optional[date] = None
    frequency: str = "once"
    is_complete: bool = False
    priority: str = "medium"
    category: str = "general"

    def set_duration(self, minutes: int) -> None:
        """Set the task duration in minutes."""
        self.duration_minutes = max(0, minutes)

    def set_frequency(self, frequency: str) -> None:
        """Set how often the task should repeat."""
        self.frequency = frequency

    def complete(self) -> None:
        """Mark this task as complete."""
        self.is_complete = True

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as complete and create the next occurrence if recurring."""
        self.complete()
        return self.create_next_occurrence()

    def next_due_date(self) -> Optional[date]:
        """Return the next due date for recurring tasks."""
        if self.frequency not in {"daily", "weekly"}:
            return None
        base_date = self.due_date or date.today()
        if self.frequency == "daily":
            return base_date + timedelta(days=1)
        if self.frequency == "weekly":
            return base_date + timedelta(weeks=1)
        return None

    def create_next_occurrence(self) -> Optional["Task"]:
        """Create the next recurring task instance if this task repeats."""
        next_date = self.next_due_date()
        if not next_date:
            return None
        return Task(
            title=self.title,
            description=self.description,
            duration_minutes=self.duration_minutes,
            time=self.time,
            due_date=next_date,
            frequency=self.frequency,
            priority=self.priority,
            category=self.category,
        )

    def reopen(self) -> None:
        """Mark this task as not complete."""
        self.is_complete = False

    def toggle_completion(self) -> None:
        """Toggle the task completion status."""
        self.is_complete = not self.is_complete

    def is_high_priority(self) -> bool:
        """Return whether the task has high priority."""
        return self.priority.lower() == "high"

    def summary(self) -> str:
        """Return a one-line summary of the task."""
        status = "done" if self.is_complete else "pending"
        return f"{self.title}: {self.description} ({self.duration_minutes}m, {self.frequency}, {status})"


@dataclass
class Pet:
    name: str
    species: str
    age: int
    care_needs: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a new task to the pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove a task by title from the pet."""
        for index, task in enumerate(self.tasks):
            if task.title == title:
                del self.tasks[index]
                return True
        return False

    def get_tasks(self) -> List[Task]:
        """Return a list of all tasks for the pet."""
        return list(self.tasks)

    def pending_tasks(self) -> List[Task]:
        """Return the pet's incomplete tasks."""
        return [task for task in self.tasks if not task.is_complete]

    def needs_task(self, task_type: str) -> bool:
        """Return whether the pet needs a specific type of task."""
        return task_type.lower() in [need.lower() for need in self.care_needs]

    def describe(self) -> str:
        """Return a short description of the pet."""
        needs = ", ".join(self.care_needs) if self.care_needs else "no special care needs"
        return f"{self.name} is a {self.age}-year-old {self.species} with {needs}."

    def is_valid_task(self, task: Task) -> bool:
        """Return whether a task matches the pet's care needs."""
        if not self.care_needs:
            return True
        return task.category.lower() in [need.lower() for need in self.care_needs]


class Owner:
    def __init__(self, name: str, available_time: int, preferences: Optional[Dict[str, str]] = None, contact_info: str = ""):
        """Create a scheduler for the given owner."""
        self.name = name
        self.available_time = max(0, available_time)
        self.preferences = preferences or {}
        self.contact_info = contact_info
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name from the owner."""
        for index, pet in enumerate(self.pets):
            if pet.name == pet_name:
                del self.pets[index]
                return True
        return False

    def get_all_pets(self) -> List[Pet]:
        """Return a list of the owner's pets."""
        return list(self.pets)

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across the owner's pets."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def get_pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks across the owner's pets."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.pending_tasks())
        return tasks

    def update_availability(self, minutes: int) -> None:
        """Update the owner's available daily time."""
        self.available_time = max(0, minutes)

    def set_preference(self, key: str, value: str) -> None:
        """Set an owner preference."""
        self.preferences[key] = value

    def can_schedule(self, task: Task) -> bool:
        """Return whether a task fits within available time."""
        return task.duration_minutes <= self.available_time

    def describe_preferences(self) -> str:
        """Return a summary of owner preferences."""
        if not self.preferences:
            return f"{self.name} has no saved preferences."
        preferences = ", ".join([f"{key}: {value}" for key, value in self.preferences.items()])
        return f"{self.name}'s preferences: {preferences}"


class Scheduler:
    def __init__(self, owner: Owner):
        """Create a scheduler for the given owner."""
        self.owner = owner

    def retrieve_all_tasks(self) -> List[Task]:
        """Retrieve all tasks from the owner."""
        return self.owner.get_all_tasks()

    def retrieve_pending_tasks(self) -> List[Task]:
        """Retrieve all pending tasks from the owner."""
        return self.owner.get_pending_tasks()

    def sort_tasks_by_priority(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks by priority."""
        tasks_to_sort = tasks if tasks is not None else self.retrieve_all_tasks()
        priority_order = {"high": 1, "medium": 2, "low": 3}
        return sorted(
            tasks_to_sort,
            key=lambda task: priority_order.get(task.priority.lower(), 2),
        )

    def sort_tasks_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks by their time string in HH:MM format."""
        tasks_to_sort = tasks if tasks is not None else self.retrieve_all_tasks()
        return sorted(
            tasks_to_sort,
            key=lambda task: tuple(map(int, task.time.split(':'))),
        )

    def group_tasks_by_pet(self) -> Dict[str, List[Task]]:
        """Group tasks by the pet they belong to."""
        grouped: Dict[str, List[Task]] = {}
        for pet in self.owner.get_all_pets():
            grouped[pet.name] = pet.get_tasks()
        return grouped

    def generate_day_plan(self, available_minutes: Optional[int] = None) -> List[Task]:
        """Build a daily plan of tasks that fit in available time."""
        time_left = available_minutes if available_minutes is not None else self.owner.available_time
        selected: List[Task] = []
        for task in self.sort_tasks_by_priority(self.retrieve_pending_tasks()):
            if task.duration_minutes <= time_left:
                selected.append(task)
                time_left -= task.duration_minutes
        return selected

    def detect_time_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Detect tasks that share the same time and return warning messages."""
        tasks_to_check = tasks if tasks is not None else self.retrieve_pending_tasks()
        if not tasks_to_check:
            return []

        time_map: Dict[str, List[Task]] = {}
        for task in tasks_to_check:
            time_map.setdefault(task.time, []).append(task)

        warnings: List[str] = []
        for task_time, same_time_tasks in time_map.items():
            if len(same_time_tasks) > 1:
                titles = ", ".join([task.title for task in same_time_tasks])
                warnings.append(
                    f"Conflict at {task_time}: multiple tasks scheduled at the same time ({titles})."
                )
        return warnings

    def explain_plan(self, tasks: List[Task]) -> str:
        """Build a readable explanation of the selected tasks."""
        if not tasks:
            return "No tasks were selected for today."
        lines = ["Today's plan includes the following tasks:"]
        for task in tasks:
            priority = task.priority.capitalize()
            lines.append(f"- {task.title} ({task.duration_minutes}m, {priority})")
        return "\n".join(lines)

    def complete_task(self, pet_name: str, task_title: str) -> bool:
        """Mark a pending task complete for a given pet and reschedule recurring tasks."""
        for pet in self.owner.get_all_pets():
            if pet.name == pet_name:
                for task in pet.tasks:
                    if (
                        task.title == task_title
                        and not task.is_complete
                        and (task.due_date is None or task.due_date <= date.today())
                    ):
                        next_task = task.mark_complete()
                        if next_task:
                            pet.add_task(next_task)
                        return True
        return False

    def get_schedule_summary(self, tasks: Optional[List[Task]] = None) -> str:
        """Return a summary string for the selected schedule."""
        plan = tasks if tasks is not None else self.generate_day_plan()
        total = sum(task.duration_minutes for task in plan)
        return f"Selected {len(plan)} tasks totaling {total} minutes."

    # ── Step 1: Adapt ─────────────────────────────────────────────────────────

    def resolve_conflicts(self, tasks: List[Task]) -> List[Task]:
        """Keep only the highest-priority task at each conflicting time slot."""
        priority_order = {"high": 1, "medium": 2, "low": 3}
        time_map: Dict[str, List[Task]] = {}
        for task in tasks:
            time_map.setdefault(task.time, []).append(task)

        resolved: List[Task] = []
        for slot_tasks in time_map.values():
            if len(slot_tasks) == 1:
                resolved.append(slot_tasks[0])
            else:
                winner = min(slot_tasks, key=lambda t: priority_order.get(t.priority.lower(), 2))
                resolved.append(winner)
        return resolved

    # ── Step 2: Full agentic loop ─────────────────────────────────────────────

    def run_agent(self, available_minutes: Optional[int] = None) -> Dict:
        """Retrieve → Plan → Evaluate → Adapt → Output."""
        plan = self.generate_day_plan(available_minutes)
        conflicts = self.detect_time_conflicts(plan)
        if conflicts:
            plan = self.resolve_conflicts(plan)
        return {
            "plan": self.sort_tasks_by_time(plan),
            "explanation": self.explain_plan(plan),
            "summary": self.get_schedule_summary(plan),
            "conflicts_resolved": conflicts,
        }
