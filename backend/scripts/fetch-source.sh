#!/usr/bin/env bash
#
# Downloads a source tarball for geobase.dockerfile.
#
#   fetch-source.sh <output-file> <url> [fallback-url ...]
#
# Release CDNs, GitHub's in particular, return intermittent 503s that outlast a
# plain curl --retry window. Each URL is retried on its own, then the whole list
# is walked again with a growing pause, so a mirror can cover for an outage at
# the primary host.

set -euo pipefail

output="$1"
shift

for round in 1 2 3 4 5; do
    for url in "$@"; do
        if curl -fsSL \
            --retry 3 \
            --retry-delay 5 \
            --retry-all-errors \
            --connect-timeout 30 \
            "$url" -o "$output"; then
            exit 0
        fi
        echo "fetch-source: round ${round} failed for ${url}" >&2
    done
    sleep $((round * 15))
done

echo "fetch-source: exhausted all mirrors for ${output}" >&2
exit 1
