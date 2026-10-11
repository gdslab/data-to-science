# LOC: 28
from typing import Protocol

class WorkflowObserver(Protocol):
    def on_status_change(self, job: str, status: str) -> None: ...

class WorkflowEngine:
    def __init__(self):
        self._observers: list = []
    def attach(self, obs):
        self._observers.append(obs)
    def run(self, job: str):
        for status in ["STARTED", "PROCESSING", "DONE"]:
            self._notify(job, status)
    def _notify(self, job, status):
        for o in self._observers:
            o.on_status_change(job, status)

class Logger:
    def on_status_change(self, job, status):
        print(f"[LOG] {job} -> {status}")

class Notifier:
    def on_status_change(self, job, status):
        if status == "DONE":
            print(f"[NOTIFY] Job {job} completed!")

if __name__ == "__main__":
    engine = WorkflowEngine()
    engine.attach(Logger())
    engine.attach(Notifier())
    engine.run("experiment_42")
