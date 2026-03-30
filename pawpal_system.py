from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    category: str

    def set_duration(self, minutes: int) -> None:
        pass

    def set_priority(self, priority: str) -> None:
        pass

    def is_high_priority(self) -> bool:
        pass

    def estimate_score(self) -> float:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    care_needs: List[str] = field(default_factory=list)

    def needs_task(self, task_type: str) -> bool:
        pass

    def describe(self) -> str:
        pass

  

class Owner:
    def __init__(self, name: str, available_time: int, preferences: Optional[Dict[str, str]] = None, contact_info: str = ""):
        self.name = name
        self.available_time = available_time
        self.preferences = preferences or {}
        self.contact_info = contact_info

    def update_availability(self, minutes: int) -> None:
        pass

    def set_preference(self, key: str, value: str) -> None:
        pass

    def can_schedule(self, task: Task) -> bool:
        pass

    def describe_preferences(self) -> str:
        pass


class DailyPlan:
    def __init__(self, date: str):
        self.date = date
        self.scheduled_tasks: List[Task] = []
        self.total_duration: int = 0
        self.remaining_time: int = 0

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def order_tasks(self) -> None:
        pass

    def validate(self) -> bool:
        pass
