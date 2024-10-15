vcl 4.1;

import std;

backend default {
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
    if (req.url ~ "^[^?]*\.(7z|avi|bmp|bz2|css|csv|doc|docx|eot|flac|flv|gif|gz|ico|jpeg|jpg|js|less|mka|mkv|mov|mp3|mp4|mpeg|mpg|odt|ogg|ogm|opus|otf|pdf|png|ppt|pptx|rar|rtf|svg|svgz|swf|tar|tbz|tgz|ttf|txt|txz|wav|webm|webp|woff|woff2|xls|xlsx|xml|xz|zip)(\?.*)?$") {
        # store access token temporarily before unsetting it
        if (req.http.Cookie ~ "access_token") {
            set req.http.x-temp-access-token = regsub(req.http.Cookie, ".*access_token=([^;]+);?.*", "\1");
        }
        unset req.http.Cookie;
        # Only keep the following if VCL handling is complete
        return(hash);
    }

    # asynchronously revalidate object while serving stale object if not past 10 seconds
    if (std.healthy(req.backend_hint)) {
        set req.grace = 10s;
    }
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