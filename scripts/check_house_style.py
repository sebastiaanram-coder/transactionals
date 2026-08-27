#!/usr/bin/env python3
"""
House style, checked across every built email at once.

WHY A REPO-LEVEL CHECK AND NOT FOURTEEN BUILDER CHECKS. The em dash rule arrived
after fourteen emails had already shipped one, and five of those came from builders
whose own check sections I would have had to edit one by one to catch it. A rule
that applies to every email should be enforced somewhere that sees every email, so
a builder written next month is covered without anyone remembering to add a line.

build_overview.py runs this, and the overview is rebuilt in every pass, so this
runs before every commit whether or not anyone thinks to run it.
"""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
import housestyle as hs

# The Klaviyo templates are what actually sends, and the previews are what gets
# signed off, so both have to be clean.
files = sorted(glob.glob(os.path.join(ROOT, "proposals", "*-klaviyo.html"))
               + glob.glob(os.path.join(ROOT, "proposals", "*-proposed.html")))

errs = []
for f in files:
    name = os.path.basename(f).replace("-klaviyo.html", "").replace("-proposed.html", "")
    errs += hs.violations(open(f, encoding="utf-8").read(), name)

print("house style: checked %d built emails" % len(files))
if errs:
    print("\nFAILED")
    for e in errs:
        print("  " + e)
    sys.exit(1)
print("no em dashes and no jargon in any of them")
