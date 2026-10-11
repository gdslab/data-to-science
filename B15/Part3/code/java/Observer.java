// LOC: 38
import java.util.*;
interface WorkflowObserver { void onStatusChange(String job, String status); }

class WorkflowEngine {
    private List<WorkflowObserver> observers = new ArrayList<>();
    void attach(WorkflowObserver o) { observers.add(o); }
    void run(String job) {
        notify(job,"STARTED"); notify(job,"PROCESSING"); notify(job,"DONE");
    }
    private void notify(String job, String status) {
        for (WorkflowObserver o : observers) o.onStatusChange(job, status);
    }
}

class Logger implements WorkflowObserver {
    public void onStatusChange(String job, String status) {
        System.out.println("[LOG] " + job + " -> " + status);
    }
}

class Notifier implements WorkflowObserver {
    public void onStatusChange(String job, String status) {
        if ("DONE".equals(status))
            System.out.println("[NOTIFY] Job " + job + " completed!");
    }
}

public class Observer {
    public static void main(String[] args) {
        WorkflowEngine engine = new WorkflowEngine();
        engine.attach(new Logger());
        engine.attach(new Notifier());
        engine.run("experiment_42");
    }
}
