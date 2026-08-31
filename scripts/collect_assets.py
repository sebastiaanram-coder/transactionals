#!/usr/bin/env python3
"""
Collect the images the emails use into one folder, and say what still needs uploading.

WHY THIS CHANGED SHAPE. It used to find assets by looking for the
REPLACE-WITH-KLAVIYO-ASSET sentinel in the built HTML. That worked until the
sentinel was replaced with real hosted URLs, at which point it found nothing and
reported success - a tool that silently stops doing its job.

data/klaviyo-assets.json is the manifest now: every asset in use is in it,
because klaviyo_assets.url() raises on a name it does not know and the build
fails. So the mapping and the set of assets in use are the same thing, and that
is asserted below rather than assumed.

WHAT NEEDS UPLOADING is a separate question, answered by scanning the builders
for image filenames and reporting any that exist in assets/ but have no mapping.
That scan reads quoted literals, so it cannot see a name built at runtime; the
build failing on an unmapped name is the real backstop, and this is the
convenience that tells you before you get there.
"""
import io, json, os, re, shutil, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
import klaviyo_assets as ka

OUT = os.path.join(ROOT, "klaviyo-assets")
SRC = os.path.join(ROOT, "assets")
LIVE = os.path.join(ROOT, "proposals")

MAX_MB = 5.0
OK_EXT = (".jpg", ".jpeg", ".png", ".gif")
IMG_LITERAL = re.compile(r"['\"]([A-Za-z0-9._-]+\.(?:jpg|jpeg|png|gif|svg))['\"]")


def on_disk():
    out = {}
    for root, _, files in os.walk(SRC):
        for fn in files:
            if not fn.startswith("."):
                out.setdefault(fn, os.path.join(root, fn))
    return out


def referenced_names():
    """Image filenames named as literals anywhere in the build scripts."""
    names = set()
    for p in glob.glob(os.path.join(HERE, "build_*.py")) + \
             [os.path.join(HERE, "translate_welcome.py")]:
        if os.path.exists(p):
            names |= set(IMG_LITERAL.findall(io.open(p, encoding="utf-8").read()))
    return names


def main():
    have, mapped, errs = on_disk(), ka.uploaded(), []

    # 1. the mapping must match what the live blocks actually load
    known = {v["url"] for v in mapped.values()}
    used = set()
    for f in glob.glob(os.path.join(LIVE, "*-klaviyo.html")):
        s = re.sub(r"<!--.*?-->", "",
                   io.open(f, encoding="utf-8").read(), flags=re.S)
        used |= set(re.findall(
            r'src="(https://d3k81ch9hvuctc\.cloudfront\.net/company/[^"]+)"', s))
    for u in sorted(used - known):
        errs.append("a live block loads %s, which is not in the mapping" % u)
    unused = sorted(n for n, v in mapped.items() if v["url"] not in used)
    if unused:
        errs.append("mapped but no longer loaded by any email: %s"
                    % ", ".join(unused))

    # 2. anything referenced and on disk but never uploaded
    todo = sorted(n for n in referenced_names()
                  if n in have and n not in mapped)

    # 3. rebuild the folder from the mapping
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    rows, total = [], 0
    for name in sorted(mapped):
        src = have.get(name)
        if not src:
            errs.append("%s is mapped but has no file in assets/, so it cannot "
                        "be re-uploaded or checked" % name)
            continue
        ext, size = os.path.splitext(name)[1].lower(), os.path.getsize(src)
        if ext not in OK_EXT:
            errs.append("%s is a %s; email clients do not render it reliably"
                        % (name, ext))
        if size > MAX_MB * 1024 * 1024:
            errs.append("%s is %.1f MB, over Klaviyo's %.0f MB limit"
                        % (name, size / 1048576.0, MAX_MB))
        shutil.copy2(src, os.path.join(OUT, name))
        rows.append((name, size)); total += size

    print("IN KLAVIYO AND IN USE: %d assets, %.1f MB, copied to %s/"
          % (len(rows), total / 1048576.0, os.path.relpath(OUT, ROOT)))
    if todo:
        print("\nNEEDS UPLOADING (%d): referenced and present in assets/, but no "
              "hosted URL recorded." % len(todo))
        for n in todo:
            print("  %s" % n)
        print("  Upload each, then add it to data/klaviyo-assets.json.")
    else:
        print("\nNothing awaiting upload.")

    if errs:
        print()
        for e in errs:
            print("  FAIL  " + e)
        raise SystemExit(1)
    print("Mapping and built output agree.")


if __name__ == "__main__":
    main()
