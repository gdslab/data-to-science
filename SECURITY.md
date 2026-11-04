# Security Policy

## Supported Versions

Security fixes land on `main` and ship in the next tagged release. Only `main` and the latest `v*` release receive fixes. Deployments running an older tag should upgrade rather than expect a backport.

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.

Use GitHub's private vulnerability reporting instead: open the repository's **Security** tab and choose **Report a vulnerability**, or go directly to https://github.com/gdslab/data-to-science/security/advisories/new. If that is unavailable to you, email support@d2s.org.

Please include as much of the following as you can:

- The component affected (API, web application, Celery tasks, upload service, deployment configuration) and the version or commit
- Steps to reproduce, or a proof of concept
- The impact you believe it has and any conditions required to exploit it
- A suggested fix, if you have one

## What to Expect

- An acknowledgement within five business days
- A maintainer assigned to investigate, who will keep you informed of progress
- Coordination with you on a disclosure date once a fix is ready
- Credit in the release notes and the advisory, unless you prefer not to be named

## Scope

This policy covers the code in this repository and the public instance at https://ps2.d2s.org, which the Geospatial Data Science Lab at Purdue University operates. Issues specific to a third party's self-hosted deployment (their reverse proxy, TLS, or host configuration) are outside it, but if an issue traces back to a default in this repository's compose files or example configuration, report it here.
