vcl 4.1;

import std;
import digest;

backend pg_tileserv {
    .host = "pg_tileserv";
    .port = "7800";
    .max_connections = 100;
    .probe = {
        .request = 
            "GET /health HTTP/1.1"
            "Host: pg_tileserv"
            "Connection: close"
            "User-Agent: Varnish Health Probe";
        .interval  = 10s;
        .timeout   = 5s;
        .window    = 5;
        .threshold = 3;
    }
}

backend titiler {
    .host = "titiler";
    .port = "8888";
    .max_connections = 100;
    .probe = {
        .request =
            "GET /healthz HTTP/1.1"
            "Host: titiler"
            "Connection: close"
            "User-Agent: Varnish Health Probe";
        .interval  = 10s;
        .timeout   = 5s;
        .window    = 5;
        .threshold = 3;
    }
    .connect_timeout        = 5s;
    .first_byte_timeout     = 90s;
    .between_bytes_timeout  = 2s;
}

# only allow purge from local server
acl purge {
    "localhost";
    "127.0.0.1";
    "::1";
}

sub vcl_recv {
    # Extract query parameters for authorization
    set req.http.expires = regsub(req.url, ".*[?&]expires=([^&]+).*", "\1");
    set req.http.secure = regsub(req.url, ".*[?&]secure=([^&]+).*", "\1");

    # Ensure required parameters are present
    if (req.http.expires == "" || req.http.secure == "") {
        return (synth(400, "Missing required parameters"));
    }

    # Check if the request has expired
    if (std.integer(req.http.expires, 0) < std.time2integer(now, 0)) {
        return (synth(403, "URL expired"));
    }

    if (req.url ~ "^/cog/") {
        # TiTiler backend
        set req.http.dataProductId = regsub(req.url, ".*[?&]dataProductId=([^&]+).*", "\1");
        if (req.http.dataProductId == "") {
            return (synth(400, "Missing required parameters"));
        }
        set req.http.payload = req.http.expires + req.http.dataProductId;
        set req.backend_hint = titiler;
    } else {
        # pg_tilserv backend
        set req.http.filter = regsub(req.url, ".*[?&]filter=([^&]+).*", "\1");
        set req.http.limit = regsub(req.url, ".*[?&]limit=([^&]+).*", "\1");
        if (req.http.filter == "" || req.http.limit == "") {
            return (synth(400, "Missing required parameters"));
        }
        set req.http.payload = req.http.expires + req.http.filter + req.http.limit;
        set req.backend_hint = pg_tileserv;
    }

    # Compute the expected signature
    set req.http.expected_signature = digest.hmac_sha256(
        digest.base64_decode(std.getenv("TILE_SIGNING_SECRET_KEY")),
        req.http.payload
    );

    # Compare signatures
    if (req.http.secure != req.http.expected_signature) {
        return (synth(403, "Invalid signature"));
    }

    # Normalize query parameters for caching
    if (req.url ~ "[&?](expires|secure)=[^&]*") {
        # Remove the unwanted parameters (expires, secure)
        set req.url = regsuball(req.url, "[&?](expires|secure)=[^&]*", "");
    }

    # Unset authorization related headers
    unset req.http.secure;
    unset req.http.expires;
    unset req.http.payload;
    unset req.http.expected_signature;

    # Unset user/browser-specific headers
    unset req.http.User-Agent;
    unset req.http.Accept-Encoding;
    unset req.http.Accept-Language;
    unset req.http.Accept;
    unset req.http.Cookie;
    unset req.http.Referer;
    unset req.http.Sec-Fetch-Site;
    unset req.http.Sec-Fetch-Dest;
    unset req.http.Sec-Fetch-Mode;
    unset req.http.Sec-Fetch-User;
    unset req.http.Priority;

    # Only allow PURGE from local server
    if (req.method == "PURGE") {
        if (!client.ip ~ purge) {
            return (synth(405, client.ip + " is not allowed to send PURGE requests."));
        }
        return (purge);
    }

    # Limit HTTP methods to GET and HEAD
    if (req.method != "GET" && req.method != "HEAD") {
        return (synth(405, "Method Not Allowed"));
    }

    # Set X-Forwarded-Proto header
    if (!req.http.X-Forwarded-Proto) {
        if (std.port(server.ip) == 443 || std.port(server.ip) == 8443) {
            set req.http.X-Forwarded-Proto = "https";
        } else {
            set req.http.X-Forwarded-Proto = "http";
        }
    }

    # Enable grace period for cache revalidation
    if (std.healthy(req.backend_hint)) {
        set req.grace = 10s;
    }

    return (hash);
}

sub vcl_synth {
    if (resp.status == 405) {
        set resp.http.Allow = "GET, HEAD";
        set resp.body = "Method not allowed";
        return (deliver);
    }
}

sub vcl_hash {
    # Use protocol in cache key
    hash_data(req.http.X-Forwarded-Proto);

    # Use normalized URL without excluded parameters
    hash_data(req.url);

    # Optionally include the Host header
    if (req.http.Host) {
        hash_data(req.http.Host);
    }
}

sub vcl_backend_response {
    # Set TTL and grace period
    set beresp.ttl = 1d;
    set beresp.grace = 6h;
}
