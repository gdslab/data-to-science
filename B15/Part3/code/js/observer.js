// LOC: 30
class WorkflowEngine {
  constructor() { this._observers = []; }
  attach(obs) { this._observers.push(obs); }
  run(job) {
    ["STARTED","PROCESSING","DONE"].forEach(s => this._notify(job, s));
  }
  _notify(job, status) {
    this._observers.forEach(o => o.onStatusChange(job, status));
  }
}

class Logger {
  onStatusChange(job, status) { console.log(`[LOG] ${job} -> ${status}`); }
}

class Notifier {
  onStatusChange(job, status) {
    if (status === "DONE") console.log(`[NOTIFY] Job ${job} completed!`);
  }
}

const engine = new WorkflowEngine();
engine.attach(new Logger());
engine.attach(new Notifier());
engine.run("experiment_42");
