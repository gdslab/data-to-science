#!/usr/bin/env bash
#
# Downloads and verifies a source tarball for geobase.dockerfile.
#
#   fetch-source.sh <output-file> <sha256> <url> [fallback-url ...]
#
# Release CDNs, GitHub's in particular, return intermittent 503s that outlast a
# plain curl --retry window. Each URL is retried on its own, then the whole list
# is walked again with a growing pause, so a mirror can cover for an outage at
# the primary host.
#
# The checksum is what makes that fallback safe: a mirror serving something other
# than the expected bytes is discarded and the next one is tried, rather than
# being built. Expected hashes live next to the version arguments in
# geobase.dockerfile so a version bump and its hash move together.

set -euo pipefail

output="$1"
sha256="$2"
shift 2

rounds=5
for round in $(seq 1 "$rounds"); do
    for url in "$@"; do
        if ! curl -fsSL \
            --retry 3 \
            --retry-delay 5 \
            --retry-all-errors \
            --connect-timeout 30 \
            "$url" -o "$output"; then
            echo "fetch-source: round ${round} could not download ${url}" >&2
            continue
        fi

        if echo "${sha256}  ${output}" | sha256sum -c - >/dev/null 2>&1; then
            exit 0
        fi

        echo "fetch-source: ${url} returned unexpected content" >&2
        echo "fetch-source:   expected ${sha256}" >&2
        echo "fetch-source:   received $(sha256sum "$output" | cut -d' ' -f1)" >&2
        rm -f "$output"
    done

    [ "$round" -lt "$rounds" ] && sleep $((round * 15))
done

echo "fetch-source: exhausted all mirrors for ${output}" >&2
exit 1
