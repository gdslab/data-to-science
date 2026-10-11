# Host-level nginx rate limiting

The app stack provides application-layer rate limiting via `slowapi` (see `RATE_LIMIT_ENABLED` in `backend.example.env`). This document describes the **host-level nginx** configuration recommended as a second line of defence — sitting in front of the docker-compose `proxy` container and dropping abusive requests before they enter the docker network.

**Nothing in the app stack's `nginx/` directory needs to change.** These snippets belong in the nginx instance that terminates public traffic and forwards to the `proxy` container.

## Why two layers?

| Layer | What it stops |
|---|---|
| Host nginx `limit_req` | DoS-style flooding — drops the request before it reaches the docker network. No worker consumed. |
| App-layer slowapi | Business-logic abuse — credential stuffing, email amplification, scraping. Returns a proper 429 with `Retry-After`. |

## Recommended host nginx snippet

Add the zones to the `http {}` block and apply them to the server block forwarding to the app stack:

```nginx
# http {} block — shared-memory zones, ~16 k unique IPs each
limit_req_zone $binary_remote_addr zone=d2s_api_general:10m   rate=30r/s;
limit_req_zone $binary_remote_addr zone=d2s_api_sensitive:10m rate=5r/s;
limit_req_status 429;

# server {} block forwarding to the app stack proxy container
server {
    # ...TLS termination, server_name, etc...

    # Sensitive auth/registration paths — tighter limit
    location ~ ^/api/v1/(auth|users)(/|$) {
        limit_req zone=d2s_api_sensitive burst=10 nodelay;
        proxy_pass http://<app-stack-proxy>;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # General API traffic
    location /api {
        limit_req zone=d2s_api_general burst=60 nodelay;
        proxy_pass http://<app-stack-proxy>;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # DO NOT apply limit_req to these paths — they are legitimately bursty or
    # offloaded to Varnish and never reach the backend:
    #   /cog          → Varnish → TiTiler (bypasses FastAPI)
    #   /mvt/         → Varnish → pg_tileserv (bypasses FastAPI)
    #   /static       → FastAPI ProtectedStaticFiles (Potree COPC range requests)
    #   /files        → tusd upload service
    #   /potree       → static Potree assets
    #   /share-potree → static assets
    #   /pc-gltf-viewer → static assets
}
```

## Real client IP forwarding

The `X-Real-IP` and `X-Forwarded-For` headers in the snippet above are required for `slowapi`'s per-IP limits to work correctly inside FastAPI. Without them, all requests appear to originate from the proxy container's docker-bridge IP, which collapses all counters to a single shared key.

The app stack's uvicorn is already started with `--proxy-headers` (`backend/backend-start.sh`), so it will trust and unwrap these headers automatically.

## Tuning guidance

The rates above (`30r/s` general, `5r/s` sensitive) are starting points. After one week of production traffic, review the access log for 429 entries:

```sh
grep '"status": 429' /app/logs/backend.log | jq -r .path | sort | uniq -c | sort -rn
```

Raise any limit that is regularly firing against legitimate users. Lower any limit that shows no legitimate traffic at those rates. The `burst` value controls how many requests over the rate are queued/allowed instantly; `nodelay` serves them immediately rather than introducing artificial delay.
