// LOC: 48
#include <iostream>
#include <string>
#include <unordered_map>
#include <memory>

struct PolicyStrategy {
    virtual bool allows(const std::string& user, const std::string& resource) const = 0;
    virtual ~PolicyStrategy() = default;
};

struct OwnerPolicy : PolicyStrategy {
    bool allows(const std::string& user, const std::string& resource) const override {
        return resource.rfind(user + ":", 0) == 0;
    }
};

struct RolePolicy : PolicyStrategy {
    std::string requiredRole;
    std::unordered_map<std::string,std::string> roles;
    bool allows(const std::string& user, const std::string&) const override {
        auto it = roles.find(user);
        return it != roles.end() && it->second == requiredRole;
    }
};

class AccessController {
    std::shared_ptr<PolicyStrategy> strategy;
public:
    AccessController(std::shared_ptr<PolicyStrategy> s) : strategy(s) {}
    void setStrategy(std::shared_ptr<PolicyStrategy> s) { strategy = s; }
    bool check(const std::string& u, const std::string& r) { return strategy->allows(u,r); }
};

int main() {
    AccessController ac(std::make_shared<OwnerPolicy>());
    std::cout << "OwnerPolicy alice:dataset1 -> " << ac.check("alice","alice:dataset1") << "\n";
    auto rp = std::make_shared<RolePolicy>();
    rp->requiredRole = "admin";
    rp->roles = {{"alice","admin"},{"bob","viewer"}};
    ac.setStrategy(rp);
    std::cout << "RolePolicy  alice admin    -> " << ac.check("alice","any") << "\n";
    std::cout << "RolePolicy  bob   admin    -> " << ac.check("bob","any") << "\n";
}
