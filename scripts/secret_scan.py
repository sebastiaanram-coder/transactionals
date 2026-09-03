#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fail if a real credential appears in the working tree or a commit range.

WHY THIS REPLACES THE INLINE GREP. The scan used through this project was

    git diff --cached | grep -c -E 'pk_[A-Za-z0-9]|CFPAT-|TRUSTPILOT_API|sk_[a-z]' \
      || echo "clean"

which fails at both ends. `grep -c` EXITS 0 WHEN IT FINDS SOMETHING, so the
`|| echo clean` branch runs only when the tree is clean and a hit prints a count
that is easy to read past - a commit with 15 hits went through on exactly that.
And `sk_[a-z]` matches the ordinary word "ask_how", so it cried wolf: all 15 of
those hits were the translation keys ask_h, ask_how and ask_mail.

WHAT IT DOES INSTEAD. The authoritative test is not a shape, it is the VALUE:
every secret this repo can leak is already sitting in .env, so it compares
against those literal values and never needs to guess a pattern. Shape patterns
are kept as a backstop for a credential that is not in .env yet, but they are
anchored tightly enough not to match prose.

A secret's VALUE IS NEVER PRINTED - only its .env variable name, the file and
the line.

  python3 scripts/secret_scan.py              # working tree (tracked files)
  python3 scripts/secret_scan.py --staged     # what is about to be committed
  python3 scripts/secret_scan.py --range HEAD~3..HEAD
"""
import io, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_LEN = 12          # below this a value is not a credential, it is a word

# NOT EVERY .env VALUE IS A SECRET. A Contentful SPACE ID is a public identifier
# that appears in the path of every asset URL
# (contentful.helloprint.com/<space>/<asset>/...), so it is necessarily present
# in every embedded email preview - 296 times in the tracked tree. Treating it
# as a credential makes the scan cry wolf, and a scan that always fails is a
# scan nobody reads. The tokens beside it in the same file ARE secrets.
PUBLIC = {"CONTENTFUL_SPACE_ID", "CONTENTFUL_ENVIRONMENT"}

SHAPES = [
    ("Klaviyo private key", re.compile(r"\bpk_[0-9a-f]{30,}\b")),
    ("Contentful token",    re.compile(r"\bCFPAT-[\w-]{20,}\b")),
    ("Stripe-style key",    re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("Klaviyo public+priv", re.compile(r"\bpk_live_[A-Za-z0-9]{16,}\b")),
    ("generic bearer",      re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{24,}\b")),
]


def env_values():
    """{value: NAME} for every non-trivial secret in .env. Values never logged."""
    out = {}
    for path in (os.path.join(ROOT, ".env"), os.path.join(ROOT, "..", ".env")):
        if not os.path.exists(path):
            continue
        for line in io.open(path, encoding="utf-8", errors="replace"):
            k, sep, v = line.strip().partition("=")
            if not sep:
                continue
            v = v.strip().strip('"').strip("'")
            k = k.strip()
            if (len(v) >= MIN_LEN and not v.startswith("pk_your")
                    and k not in PUBLIC):
                out[v] = k
    return out


def haystack(mode, rng):
    if mode == "staged":
        return [("<staged diff>",
                 subprocess.run(["git", "diff", "--cached"], cwd=ROOT,
                                capture_output=True, text=True).stdout)]
    if mode == "range":
        return [("<%s>" % rng,
                 subprocess.run(["git", "log", "-p", rng], cwd=ROOT,
                                capture_output=True, text=True).stdout)]
    files = subprocess.run(["git", "ls-files"], cwd=ROOT,
                           capture_output=True, text=True).stdout.split()
    out = []
    for f in files:
        p = os.path.join(ROOT, f)
        try:
            if os.path.getsize(p) > 8 * 1024 * 1024:
                continue
            out.append((f, io.open(p, encoding="utf-8", errors="replace").read()))
        except (IOError, OSError):
            pass
    return out


def main():
    mode, rng = "tree", None
    if "--staged" in sys.argv:
        mode = "staged"
    elif "--range" in sys.argv:
        mode, rng = "range", sys.argv[sys.argv.index("--range") + 1]

    vals = env_values()
    if not vals:
        print("no .env values to compare against - shape patterns only")
    hits = []
    for name, text in haystack(mode, rng):
        for i, line in enumerate(text.split("\n"), 1):
            for v, var in vals.items():
                if v in line:
                    hits.append((name, i, "%s (value from .env)" % var))
            for what, rx in SHAPES:
                if rx.search(line):
                    hits.append((name, i, what))
    print("scanned %s: %d file(s)/blob(s), %d .env value(s)"
          % (mode, len(haystack(mode, rng)), len(vals)))
    if not hits:
        print("CLEAN - no credential found")
        return 0
    print("\nSECRETS FOUND - do not commit or push:")
    for f, i, what in hits[:40]:
        print("  %s:%s  %s" % (f, i, what))
    print("\n%d hit(s). Remove them, then re-run." % len(hits))
    return 1


if __name__ == "__main__":
    sys.exit(main())
