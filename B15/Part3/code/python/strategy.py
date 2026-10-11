# LOC: 30
from abc import ABC, abstractmethod

class PolicyStrategy(ABC):
    @abstractmethod
    def allows(self, user: str, resource: str) -> bool: ...

class OwnerPolicy(PolicyStrategy):
    def allows(self, user, resource):
        return resource.startswith(f"{user}:")

class RolePolicy(PolicyStrategy):
    def __init__(self, required_role: str, roles: dict):
        self.required_role = required_role
        self.roles = roles
    def allows(self, user, resource):
        return self.roles.get(user, "viewer") == self.required_role

class AccessController:
    def __init__(self, strategy: PolicyStrategy):
        self.strategy = strategy
    def check(self, user: str, resource: str) -> bool:
        return self.strategy.allows(user, resource)

if __name__ == "__main__":
    roles = {"alice": "admin", "bob": "viewer"}
    ac = AccessController(OwnerPolicy())
    print("OwnerPolicy alice:dataset1 ->", ac.check("alice", "alice:dataset1"))
    ac.strategy = RolePolicy("admin", roles)
    print("RolePolicy  alice admin    ->", ac.check("alice", "any"))
    print("RolePolicy  bob   admin    ->", ac.check("bob", "any"))
