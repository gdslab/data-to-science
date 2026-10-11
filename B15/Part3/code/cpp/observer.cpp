// LOC: 42
#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <functional>

struct WorkflowObserver {
    virtual void onStatusChange(const std::string& job, const std::string& status) = 0;
    virtual ~WorkflowObserver() = default;
};

class WorkflowEngine {
    std::vector<std::shared_ptr<WorkflowObserver>> observers;
public:
    void attach(std::shared_ptr<WorkflowObserver> o) { observers.push_back(o); }
    void run(const std::string& job) {
        for (auto& s : {"STARTED","PROCESSING","DONE"}) notify(job, s);
    }
    void notify(const std::string& job, const std::string& status) {
        for (auto& o : observers) o->onStatusChange(job, status);
    }
};

struct Logger : WorkflowObserver {
    void onStatusChange(const std::string& job, const std::string& status) override {
        std::cout << "[LOG] " << job << " -> " << status << "\n";
    }
};

struct Notifier : WorkflowObserver {
    void onStatusChange(const std::string& job, const std::string& status) override {
        if (status == "DONE") std::cout << "[NOTIFY] Job " << job << " completed!\n";
    }
};

int main() {
    WorkflowEngine engine;
    engine.attach(std::make_shared<Logger>());
    engine.attach(std::make_shared<Notifier>());
    engine.run("experiment_42");
}
