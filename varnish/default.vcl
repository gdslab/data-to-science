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
    # set which backend to use
    if (req.url ~ "^/cog/") {
        # Extract signature from query parameters
        set req.http.dataProductId = regsub(req.url, ".*[?&]dataProductId=([^&]+).*", "\1");
        set req.http.expires = regsub(req.url, ".*[?&]expires=([^&]+).*", "\1");
        set req.http.secure = regsub(req.url, ".*[?&]secure=([^&]+).*", "\1");

        # Ensure all required parameters are present
        if (req.http.expires == "" || req.http.dataProductId == "" || req.http.secure == "") {
            return (synth(400, "Missing required parameters"));
        }

        # Check expiration
        if (std.integer(req.http.expires, 0) < std.time2integer(now, 0)) {
            return (synth(403, "URL expired"));
        }

        # Reconstruct the payload
        set req.http.payload = req.http.expires + req.http.dataProductId;

        # Compute the expected signature
        set req.http.expected_signature = digest.hmac_sha256(digest.base64_decode(std.getenv("TILE_SIGNING_SECRET_KEY")), req.http.payload);

        # Compare signatures
        if (req.http.secure != req.http.expected_signature) {
            return (synth(403, "Invalid signature"));
        }

        set req.backend_hint = titiler;
    } else {
        # Extract query parameters
        set req.http.expires = regsub(req.url, ".*[?&]expires=([^&]+).*", "\1");
        set req.http.filter = regsub(req.url, ".*[?&]filter=([^&]+).*", "\1");
        set req.http.limit = regsub(req.url, ".*[?&]limit=([^&]+).*", "\1");
        set req.http.secure = regsub(req.url, ".*[?&]secure=([^&]+).*", "\1");

        # Ensure all required parameters are present
        if (req.http.expires == "" || req.http.filter == "" || req.http.limit == "" || req.http.secure == "") {
            return (synth(400, "Missing required parameters"));
        }

        # Check expiration
        if (std.integer(req.http.expires, 0) < std.time2integer(now, 0)) {
            return (synth(403, "URL expired"));
        }

        # Reconstruct the payload
        set req.http.payload = req.http.expires + req.http.filter + req.http.limit;

        # Compute the expected signature
        set req.http.expected_signature = digest.hmac_sha256(digest.base64_decode(std.getenv("TILE_SIGNING_SECRET_KEY")), req.http.payload);

        # Compare signatures
        if (req.http.secure != req.http.expected_signature) {
            return (synth(403, "Invalid signature"));
        }

        set req.backend_hint = pg_tileserv;
    }

    # strip off port numbers from object hash
    set req.http.Host = regsub(req.http.Host, ":[0-9]+", "");

    # strip off trailing /?
    set req.url = regsub(req.url, "\?$", "");

    # allow purging from local server
    if (req.method == "PURGE") {
        if (!client.ip ~ purge) {
            return (synth(405, client.ip + " is not allowed to send PURGE requests."));
        }
        return (purge);
    }

    # limit HTTP methods to GET and HEAD requests
    if (req.method != "GET" && req.method != "HEAD") {
        return (synth(405, "Method Not Allowed"));
    }

    # only cache GET and HEAD requests
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }

    # indicate if https or http used in request with X-Forwarded-Proto header
    if (!req.http.X-Forwarded-Proto) {
        if(std.port(server.ip) == 443 || std.port(server.ip) == 8443) {
            set req.http.X-Forwarded-Proto = "https";
        } else {
            set req.http.X-Forwarded-Proto = "http";
        }
    }

    # strip off cookie and auth headers before caching new request
    # store access token temporarily before unsetting it
    if (req.http.Cookie ~ "access_token") {
        set req.http.x-temp-access-token = regsub(req.http.Cookie, ".*access_token=([^;]+);?.*", "\1");
    }
    unset req.http.Cookie;

    # asynchronously revalidate object while serving stale object if not past 10 seconds
    if (std.healthy(req.backend_hint)) {
        set req.grace = 10s;
    }

    # Only keep the following if VCL handling is complete
    return(hash);
}

sub vcl_synth {
    if (resp.status == 405) {
        set resp.http.Allow = "GET, HEAD";
        set resp.body = "Method not allowed";
        return (deliver);
    }
}

sub vcl_hash {
    hash_data(req.http.X-Forwarded-Proto);
}

sub vcl_backend_response {
    if (bereq.url ~ "^[^?]*\.(7z|avi|bmp|bz2|css|csv|doc|docx|eot|flac|flv|gif|gz|ico|jpeg|jpg|js|less|mka|mkv|mov|mp3|mp4|mpeg|mpg|odt|ogg|ogm|opus|otf|pdf|png|ppt|pptx|rar|rtf|svg|svgz|swf|tar|tbz|tgz|ttf|txt|txz|wav|webm|webp|woff|woff2|xls|xlsx|xml|xz|zip)(\?.*)?$") {
        unset beresp.http.Set-Cookie;
        set beresp.ttl = 1d;
    }

    set beresp.grace = 6h;
}

sub vcl_backend_fetch {
    # Add temp access token to request before forwarding to backend
    if (bereq.http.x-temp-access-token) {
        set bereq.http.Cookie = "access_token=" + bereq.http.x-temp-access-token + "; " + bereq.http.Cookie;
    }
}