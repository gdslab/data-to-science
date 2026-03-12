# Authentication and Authorization

This page explains the design of D2S authentication and authorization — how users prove their identity and how the platform decides what they can access.

## Authentication methods

### JWT tokens

D2S uses JSON Web Tokens (JWT) for session-based authentication:

- **Access tokens** are short-lived (15 minutes) and included in every API request via the `Authorization: Bearer <token>` header.
- **Refresh tokens** are long-lived (30 days) and stored as HTTP-only cookies. They are used to obtain new access tokens without re-entering credentials.

Tokens are signed using the `SECRET_KEY` environment variable. In production, `HTTP_COOKIE_SECURE` should be set to `1` to ensure cookies are only sent over HTTPS.

### API keys

For programmatic access, users can generate API keys. These are passed via the `X-API-Key` header and currently support a limited set of read-only endpoints (project details, flight listings, vector layer access).

### Single-use tokens

Email verification and password reset flows use single-use tokens that expire after use. These are stored in the database and validated on submission.

## Authorization model

D2S uses project-level role-based access control (RBAC). Every user's access to a resource is determined by their membership role in the containing project (or team).

### Role hierarchy

| Role | Level | Capabilities |
|------|-------|-------------|
| **Owner** | 3 | Full control — create, read, update, delete |
| **Manager** | 2 | Read and write — cannot delete |
| **Viewer** | 1 | Read-only access |

### How permissions are checked

Authorization is enforced via FastAPI dependency injection. Each endpoint declares its required permission level using dependency functions:

```python
@router.get("/projects/{project_id}/flights")
def list_flights(
    project = Depends(can_read_project),
    current_user = Depends(get_current_approved_user),
):
    ...
```

The dependency functions (`can_read_project`, `can_read_write_flight`, etc.) look up the user's membership in the relevant project and verify the role meets the minimum level. If not, a 403 response is returned.

### Permission inheritance

When a project is created with a team association:

- All team members are automatically added as project members.
- Team roles are inherited as project roles (e.g., a team Manager becomes a project Manager).

### Signed URLs for tile access

Map tile requests do not use JWT or API key authentication. Instead, the backend generates time-limited signed URLs that encode the allowed resource and expiration. The Varnish caching layer validates these signatures before forwarding requests to TiTiler or pg_tileserv.

This approach allows tiles to be cached and served efficiently without requiring authentication on every tile request.

## Further reading

- [Roles and Permissions](../reference/roles-permissions.md) — Complete permission matrix for all resources
- [API Reference](../reference/api.md) — Endpoint details and authentication requirements
