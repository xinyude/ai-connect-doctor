import argparse
import json
import os
import platform
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request


def diagnose(host=None, url=None):
    checks = []

    def add(identifier, status, message):
        checks.append({"id": identifier, "status": status, "message": message})

    add("system.python", "ok", f"Python {platform.python_version()}")
    add("system.os", "ok", platform.system())
    add("system.tls", "ok", ssl.OPENSSL_VERSION)
    env = {key.lower(): value for key, value in os.environ.items()}
    for key in ("http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        if env.get(key):
            add("proxy." + key, "info", f"{key.upper()} is set (value hidden)")
    entries = env.get("no_proxy", "").split(",")
    if any(re.match(r"^\s*\[[^]]*:[^]]*\](?::\d+)?\s*$", x) for x in entries):
        add("proxy.no_proxy_ipv6", "warning", "Bracketed IPv6 in NO_PROXY can cause errors in some HTTP clients; check your client version and proxy settings.")
    if host:
        try:
            socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except (OSError, UnicodeError):
            add("network.dns", "warning", "DNS lookup failed for the requested host. Check DNS and network settings.")
        else:
            add("network.dns", "ok", "DNS lookup succeeded for the requested host.")
    if url:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirect())
        request = urllib.request.Request(url, method="HEAD")
        try:
            with opener.open(request, timeout=5) as response:
                add("network.https", "ok", f"HTTPS server responded (HTTP {response.status}).")
        except urllib.error.HTTPError as error:
            add("network.https", "ok", f"HTTPS server responded (HTTP {error.code}); this does not verify API access.")
        except (urllib.error.URLError, OSError, ValueError):
            add("network.https", "warning", "HTTPS connection failed. Check proxy, DNS, TLS and network settings.")
    return {"version": 1, "checks": checks}


def main():
    parser = argparse.ArgumentParser(description="Check your local AI development environment without revealing proxy values.")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    parser.add_argument("--dns", metavar="HOST", help="Optionally perform a DNS lookup for HOST")
    parser.add_argument("--url", metavar="HTTPS_ORIGIN", help="Optionally send a HEAD request to an HTTPS origin")
    args = parser.parse_args()
    if args.url:
        try:
            parsed = urllib.parse.urlsplit(args.url)
            valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                     and not parsed.password and parsed.path in ("", "/")
                     and not parsed.query and not parsed.fragment and parsed.port != 0)
        except ValueError:
            valid = False
        if not valid:
            parser.error("--url must be an HTTPS origin without credentials, path, query or fragment")
    report = diagnose(args.dns, args.url)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        for check in report["checks"]:
            print(f"[{check['status'].upper()}] {check['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
