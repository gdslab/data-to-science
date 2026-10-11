// LOC: 32
class OwnerPolicy {
  allows(user, resource) { return resource.startsWith(`${user}:`); }
}

class RolePolicy {
  constructor(requiredRole, roles) {
    this.requiredRole = requiredRole;
    this.roles = roles;
  }
  allows(user, resource) {
    return (this.roles[user] || "viewer") === this.requiredRole;
  }
}

class AccessController {
  constructor(strategy) { this.strategy = strategy; }
  setStrategy(s) { this.strategy = s; }
  check(user, resource) { return this.strategy.allows(user, resource); }
}

const roles = { alice: "admin", bob: "viewer" };
const ac = new AccessController(new OwnerPolicy());
console.log("OwnerPolicy alice:dataset1 ->", ac.check("alice", "alice:dataset1"));
ac.setStrategy(new RolePolicy("admin", roles));
console.log("RolePolicy  alice admin    ->", ac.check("alice", "any"));
console.log("RolePolicy  bob   admin    ->", ac.check("bob", "any"));
