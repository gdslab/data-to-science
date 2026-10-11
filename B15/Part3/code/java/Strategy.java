// LOC: 45
interface PolicyStrategy { boolean allows(String user, String resource); }

class OwnerPolicy implements PolicyStrategy {
    public boolean allows(String user, String resource) {
        return resource.startsWith(user + ":");
    }
}

class RolePolicy implements PolicyStrategy {
    private final String requiredRole;
    private final java.util.Map<String,String> roles;
    RolePolicy(String requiredRole, java.util.Map<String,String> roles) {
        this.requiredRole = requiredRole; this.roles = roles;
    }
    public boolean allows(String user, String resource) {
        return requiredRole.equals(roles.getOrDefault(user,"viewer"));
    }
}

class AccessController {
    private PolicyStrategy strategy;
    AccessController(PolicyStrategy strategy) { this.strategy = strategy; }
    void setStrategy(PolicyStrategy s) { this.strategy = s; }
    boolean check(String user, String resource) { return strategy.allows(user, resource); }
}

public class Strategy {
    public static void main(String[] args) {
        java.util.Map<String,String> roles = new java.util.HashMap<>();
        roles.put("alice","admin"); roles.put("bob","viewer");
        AccessController ac = new AccessController(new OwnerPolicy());
        System.out.println("OwnerPolicy alice:dataset1 -> " + ac.check("alice","alice:dataset1"));
        ac.setStrategy(new RolePolicy("admin", roles));
        System.out.println("RolePolicy  alice admin    -> " + ac.check("alice","any"));
        System.out.println("RolePolicy  bob   admin    -> " + ac.check("bob","any"));
    }
}
