#!/usr/bin/env python3
"""
Every *-proposed.html inlines its images as data URIs at build time, so editing
an asset does NOT update the previews - the builder has to be re-run. That is
silent, and it has caught me out once: the order banner was regenerated and the
previews kept serving the old one.

This checks every embedded image against assets/ by hash and names the builder
to re-run for anything stale.
"""
import base64, glob, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BUILDER = {
    "welcome-":  "(hand-written, no builder)",
    "browse-01": "scripts/build_browse_01.py",
    "browse-02": "scripts/build_browse_02.py",
    "browse-03": "scripts/build_browse_03.py",
    "order-01":  "scripts/build_order_01.py",
}

assets = {}
for p in glob.glob(os.path.join(ROOT, "assets", "*")):
    if os.path.isfile(p):
        assets[hashlib.md5(open(p, "rb").read()).hexdigest()] = os.path.basename(p)

stale, checked = [], 0
for f in sorted(glob.glob(os.path.join(ROOT, "proposals", "*-proposed.html"))):
    name = os.path.basename(f)
    s = open(f, encoding="utf-8").read()
    unknown = 0
    for m in re.finditer(r'data:image/(?:png|jpeg);base64,([A-Za-z0-9+/=]+)', s):
        checked += 1
        h = hashlib.md5(base64.b64decode(m.group(1))).hexdigest()
        if h not in assets:
            unknown += 1
    if unknown:
        key = next((k for k in BUILDER if name.startswith(k)), None)
        stale.append((name, unknown, BUILDER.get(key, "unknown builder")))

print("checked %d embedded images across %d previews"
      % (checked, len(glob.glob(os.path.join(ROOT, "proposals", "*-proposed.html")))))
if not stale:
    print("all embedded images match a current file in assets/")
    sys.exit(0)
print("\nSTALE - these previews embed images that no longer exist in assets/:")
for name, n, builder in stale:
    print("  %-34s %d image(s) unmatched   re-run: %s" % (name, n, builder))
sys.exit(1)
