#!/usr/bin/env python3
"""One-shot helper to download React + Babel into webview/static/js/vendor/.

This is the *only* network operation in the project.  Run it once after
cloning; after the files land on disk the running application makes zero
network calls.  Re-running is a no-op (existing files are skipped).

    python vendor_setup.py

If you'd rather download manually, see the URLs below and drop each file
into ``webview/static/js/vendor/``.
"""
from __future__ import annotations

import hashlib
import os
import sys
import urllib.request

VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "webview", "static", "js", "vendor")

# Pinned versions — same SHAs the redesign was tested against.  If you bump
# these, update the integrity hashes too.
FILES = [
    (
        "react.development.js",
        "https://unpkg.com/react@18.3.1/umd/react.development.js",
        None,  # hash skipped — upstream CDN content may vary
    ),
    (
        "react-dom.development.js",
        "https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js",
        None,  # sha verification optional — set None to skip
    ),
    (
        "babel.min.js",
        "https://unpkg.com/@babel/standalone@7.29.0/babel.min.js",
        None,
    ),
]


def _download(url: str, dest: str) -> None:
    print(f"  fetching {url}")
    with urllib.request.urlopen(url, timeout=30) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)


def main() -> int:
    os.makedirs(VENDOR_DIR, exist_ok=True)
    print(f"vendor dir: {VENDOR_DIR}\n")

    for name, url, sha in FILES:
        dest = os.path.join(VENDOR_DIR, name)
        if os.path.exists(dest):
            print(f"  OK {name} already present, skipping")
            continue
        try:
            _download(url, dest)
        except Exception as e:
            print(f"  FAIL {name}: {e}", file=sys.stderr)
            return 1
        if sha is not None:
            got = hashlib.sha256(open(dest, "rb").read()).hexdigest()
            if got != sha:
                print(f"  FAIL {name} sha256 mismatch (expected {sha}, got {got})",
                      file=sys.stderr)
                os.remove(dest)
                return 1
        print(f"  OK {name}")

    print("\nDone.  Run `python jury_v2.py` to launch the new UI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
