# Authentication and Authorization

This page explains the design of D2S authentication and authorization — how users prove their identity and how the platform decides what they can access.

## Authentication methods

### JWT tokens

D2S uses JSON Web Tokens (JWT) for session-based authentication:

- **Access tokens** are short-lived (15 minutes) and included in every API request via the `Authorization: Bearer <token>` header.
- **Refresh tokens** are long-lived (30 days) and stored as HTTP-only cookies. They are used to obtain new access tokens without re-entering credentials.

Tokens are signed using the `SECRET_KEY` environment variable. In production, `HTTP_COOKIE_SECURE` should be set to `1` to ensure cookies are only sent over HTTPS.

### Cross-origin login

By default the API answers cross-origin requests with `Access-Control-Allow-Origin: *` and allows only anonymous `GET` requests, which browsers reject for credentialed (cookie-bearing) requests. To let a partner web app log in from another origin, list its origin(s) in the `BACKEND_CORS_ORIGINS` environment variable. When set, the API returns the explicit origin together with `Access-Control-Allow-Credentials: true` and permits all methods, so the browser will send the auth cookie. This requires `HTTP_COOKIE_SECURE=1` (the production default), which issues the cookie with `SameSite=None; Secure; Partitioned` so it can be sent cross-origin. The `Partitioned` attribute ([CHIPS](https://developer.mozilla.org/en-US/docs/Web/Privacy/Guides/Privacy_sandbox/Partitioned_cookies)) keys the cookie by the partner app's top-level site, so the session survives even when the browser blocks third-party cookies (Safari and Firefox by default, Chrome in Incognito or with "Block third-party cookies" enabled). It also means a session started from a partner app is separate from one started on the D2S site itself. The partner app must send requests with `credentials: "include"`. See [Configuration](../reference/configuration.md) for details.

### API keys

For programmatic access, users can create up to five API keys from their profile page. Each key has an optional name and any combination of four scopes:

| Scope | Allows |
|-------|--------|
| `read` | `GET`, `HEAD`, and `OPTIONS` requests, including static file downloads |
| `create` | `POST` requests |
| `update` | `PUT` and `PATCH` requests |
| `delete` | `DELETE` requests |

The scopes are independent: no scope implies another. This lets a key that cannot be kept secret, such as one built into a mobile app, be limited to `create` alone. Anyone who extracts it can add records but cannot read other data, change existing records, or delete anything. A request made with a key that lacks the required scope is rejected with `403 Forbidden`. Scopes can be changed at any time without changing the key itself. Keys created before scopes were introduced were given all four scopes.

Keys are passed via the `X-API-Key` header, or the `API_KEY` query parameter for static files (useful for QGIS). They work only on the endpoints listed in [API key authentication](../reference/roles-permissions.md#api-key-authentication), and the key holder's project role still applies. Keys are managed through the `/api/v1/api-keys` endpoints, which require a logged-in session and cannot be called with an API key.

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
