class ProgressReporter:
    """Prints progress to stdout at each milestone percentage."""

    def __init__(self, total: int, label: str, milestone_percent: int = 20) -> None:
        self.total = total
        self.label = label
        self.milestone_percent = milestone_percent
        self.completed = 0
        self.last_reported_percentage = 0

    def tick(self) -> None:
        """Record one completed item and print a milestone line if a new threshold has been crossed."""
        self.completed += 1
        current = int((self.completed / self.total) * 100)
        milestone = (current // self.milestone_percent) * self.milestone_percent
        if milestone > self.last_reported_percentage:
            print(f"{self.label} {self.completed}/{self.total}")
            self.last_reported_percentage = milestone
