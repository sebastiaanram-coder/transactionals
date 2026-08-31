#!/usr/bin/env python3
"""
Collect every image the live blocks reference into one flat folder for upload.

WHY A SCRIPT AND NOT A ONE-OFF COPY. The templates reference assets by exact
filename, so the folder and the templates have to agree. Doing that by hand once
is fine; doing it again after any email changes is where a typo ships a broken
image to every recipient. This regenerates the folder and fails if anything is
referenced but missing, or present but unreferenced.

COMMENTS ARE STRIPPED FIRST. Each block opens with a documentation comment that
says "every https://REPLACE-WITH-KLAVIYO-ASSET/... becomes the uploaded URL", and
reading that literally adds an asset called "..." to the list.

WHAT IS NOT COLLECTED, deliberately:
  - contentful.helloprint.com  our own CDN, already public and already localised
  - d3k81ch9hvuctc.cloudfront  Klaviyo's own hosted social icons
  - {{ catalog_item... }}      product imagery from the feed, resolved at send
"""
import io, os, re, shutil, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIVE = os.path.join(ROOT, "proposals")
OUT = os.path.join(ROOT, "klaviyo-assets")
SRC = os.path.join(ROOT, "assets")

SENTINEL = re.compile(r"REPLACE-WITH-KLAVIYO-ASSET/([A-Za-z0-9._-]+)")

# Klaviyo's own limits, worth failing on here rather than discovering at upload.
MAX_MB = 5.0
OK_EXT = (".jpg", ".jpeg", ".png", ".gif")


def referenced():
    """{filename: {emails that use it}}, from the live blocks only."""
    out = collections.defaultdict(set)
    for f in sorted(os.listdir(LIVE)):
        if not f.endswith("-klaviyo.html"):
            continue
        s = io.open(os.path.join(LIVE, f), encoding="utf-8").read()
        s = re.sub(r"<!--.*?-->", "", s, flags=re.S)     # see docstring
        for m in SENTINEL.finditer(s):
            out[m.group(1)].add(f[: -len("-klaviyo.html")])
    return out


def on_disk():
    """{filename: full path} for everything under assets/, recursively."""
    out = {}
    for root, _, files in os.walk(SRC):
        for fn in files:
            if fn.startswith("."):
                continue
            if fn in out:
                raise SystemExit(
                    "two files in assets/ are both called %r (%s and %s). The "
                    "templates reference by name alone, so this is ambiguous."
                    % (fn, out[fn], os.path.join(root, fn)))
            out[fn] = os.path.join(root, fn)
    return out


def main():
    ref, have, errs = referenced(), on_disk(), []
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    rows, total = [], 0
    for name in sorted(ref):
        src = have.get(name)
        if not src:
            errs.append("%s is referenced by %s but is not in assets/"
                        % (name, ", ".join(sorted(ref[name]))))
            continue
        ext = os.path.splitext(name)[1].lower()
        size = os.path.getsize(src)
        if ext not in OK_EXT:
            errs.append("%s is a %s. Email clients do not render it reliably; "
                        "export a PNG or JPG instead." % (name, ext or "no-extension"))
        if size > MAX_MB * 1024 * 1024:
            errs.append("%s is %.1f MB, over Klaviyo's %.0f MB limit"
                        % (name, size / 1048576.0, MAX_MB))
        shutil.copy2(src, os.path.join(OUT, name))
        rows.append((name, size, len(ref[name])))
        total += size

    print("%-46s %9s  %s" % ("FILE", "SIZE", "USED BY"))
    for name, size, n in sorted(rows, key=lambda r: -r[2]):
        print("%-46s %8.1f K  %d email%s" % (name, size / 1024.0, n,
                                            "" if n == 1 else "s"))
    print("\n%d files, %.1f MB total -> %s/"
          % (len(rows), total / 1048576.0, os.path.relpath(OUT, ROOT)))

    unused = sorted(set(have) - set(ref))
    if unused:
        print("\nIn assets/ but referenced by no live block (%d). Not copied - "
              "these are preview-only or superseded:" % len(unused))
        for u in unused[:40]:
            print("  %s" % u)

    if errs:
        print()
        for e in errs:
            print("  FAIL  " + e)
        raise SystemExit(1)
    print("\nEvery referenced asset is present and within limits.")


if __name__ == "__main__":
    main()
