#!/usr/bin/env python3
"""
Re-embed the current email HTML into behavioural-email-overview.html.

WHY THIS EXISTS. The overview carries a `const PREVIEWS = {...}` object holding a
snapshot of every finished email, and that is what its preview panel renders.
The snapshots are copies, so every builder change leaves the overview quietly
wrong while still looking finished - it was showing "33,000+ reviews", English
product names in the French tiles, and /en-ie/ links that had all been fixed.

WHICH ARTIFACT GOES IN, which took two wrong attempts to get right:

  NOT the live Klaviyo block. That carries all nine locales as {% if %} switches.
  Embedding it doubled the file to 1.8MB and would have shown the reader literal
  "{% if person.locale == 'en-IE' %}" text in the preview panel.

  NOT the -proposed.html preview as it sits on disk. That is English and
  Django-free, which is right, but its images are base64 data URIs, which is why
  those files are 30KB-650KB against a 3-21KB snapshot.

  The right artifact is the English preview with its data URIs swapped for the
  hosted CDN URLs - matched by CONTENT HASH against assets/, the same way
  translate_welcome.link_assets does it, so a renamed or reordered image cannot
  pair with the wrong file.

WHAT IS AND IS NOT TOUCHED. Keys beginning FIN- are OUR finished emails and are
re-embedded. The twelve bare-ID keys are RFB's originals, shown as the "before"
half of the comparison. They are a historical record, are not ours to
regenerate, and are left byte-for-byte alone.

THE MAPPING IS EXPLICIT AND WAS CHECKED AGAINST THE OLD SNAPSHOTS. Deriving it
by CSS class prefix at run time looked fine and was wrong: prefix "w2" matches
both welcome-02 and welcome-02-nocode, so glob order decided, and welcome-02 and
welcome-03 came out mapped to the no-discount build. The old snapshots all
contain the green promo bar, so all four welcome keys are the DISCOUNT version.
Guessing from a prefix is how you put the wrong email under a heading.

Run: python3 scripts/refresh_overview.py
"""
import base64, hashlib, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "_lib"))
import klaviyo_assets as ka   # noqa: E402

DOC = os.path.join(ROOT, "behavioural-email-overview.html")
PROP = os.path.join(ROOT, "proposals")
MARK = "const PREVIEWS = "

# PREVIEWS key -> (English preview file, a CSS prefix that proves the pairing)
MAP = {
    "FIN-CATNUDGE":    ("category-commercial-print-proposed.html", "catcp"),
    "FIN-CATNUDGE-cg": ("category-corporate-gifts-proposed.html",  "catcg"),
    "FIN-CATNUDGE-cp": ("category-commercial-print-proposed.html", "catcp"),
    "FIN-CATNUDGE-ct": ("category-clothing-textiles-proposed.html", "catct"),
    "FIN-CATNUDGE-lp": ("category-labels-packaging-proposed.html",  "catlp"),
    "FIN-CATNUDGE-so": ("category-signage-outdoor-proposed.html",   "catso"),
    "FIN-CATNUDGE-st": ("category-stationery-proposed.html",        "catst"),
    "FIN-POST01":      ("post-01-review-proposed.html",   "rev1"),
    "FIN-POST02":      ("post-02-reminder-proposed.html", "rev2"),
    "FIN-POST04":      ("post-04-expert-proposed.html",   "pex"),
    "FIN-POST05":      ("post-05-offer-proposed.html",    "off1"),
    "FIN-POST06":      ("post-06-lastday-proposed.html",  "off2"),
    "FIN-SJV6Kx":      ("browse-02-proposed.html",        "b2"),
    "FIN-SvQkfX":      ("order-02-low-proposed.html",     "ao2l"),
    "FIN-TduDdY":      ("order-01-high-proposed.html",    "ao1"),
    "FIN-UnTu7Q":      ("order-02-high-proposed.html",    "ao2"),
    "FIN-UtrHWs":      ("browse-03-proposed.html",        "b3"),
    "FIN-VtF4Ei":      ("order-03-high-proposed.html",    "ao3h"),
    "FIN-WB1H":        ("winback-01-high-proposed.html",  "wb1h"),
    "FIN-WB1L":        ("winback-01-low-proposed.html",   "wb1l"),
    "FIN-WB2H":        ("winback-02-high-proposed.html",  "wb2h"),
    "FIN-WB2L":        ("winback-02-low-proposed.html",   "wb2l"),
    "FIN-WB3H":        ("winback-03-high-proposed.html",  "wb3h"),
    "FIN-X2GaSL":      ("browse-01-proposed.html",        "b1"),
    "FIN-YrvM4D":      ("order-03-low-proposed.html",     "ao3l"),
    # All four welcome snapshots carry the promo bar, so all four are the
    # DISCOUNT build, not the -nodiscount / -nocode one.
    "FIN-Vb23CK":      ("welcome-01-proposed.html", "w1"),
    "FIN-TtjyZ4":      ("welcome-02-proposed.html", "w2"),
    "FIN-RpQvJH":      ("welcome-03-proposed.html", "w3"),
    "FIN-XVPf5F":      ("welcome-04-proposed.html", "w4"),
}

# Strings the emails no longer contain ANYWHERE. Deliberately short.
#
# An earlier version also listed "ie.trustpilot.com/review" and
# "en-ie/standardflyers" and flagged three emails that were correct: in a live
# block those sit inside the {% if person.locale == 'en-IE' %} branch, where they
# belong. These snapshots are English, so an /en-ie/ link in them is right too.
STALE = ["33,000", "33.000"]


def hosted(html):
    """Swap every base64 data URI for its hosted URL, matched by content hash."""
    have = {}
    for root, _, files in os.walk(os.path.join(ROOT, "assets")):
        for fn in files:
            fp = os.path.join(root, fn)
            have[hashlib.sha1(io.open(fp, "rb").read()).hexdigest()] = fn
    missing = []

    def one(m):
        raw = base64.b64decode(m.group(2))
        name = have.get(hashlib.sha1(raw).hexdigest())
        if not name:
            missing.append("%s image, %d bytes" % (m.group(1), len(raw)))
            return m.group(0)
        return 'src="%s"' % ka.url(name)

    out = re.sub(r'src="data:image/(\w+);base64,([^"]+)"', one, html)
    return out, missing


def extract(s):
    """The PREVIEWS object and the byte range it occupies."""
    i = s.index(MARK) + len(MARK)
    depth, j, instr, esc = 0, i, False, False
    while j < len(s):
        c = s[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
        j += 1
    return json.loads(s[i:j + 1]), i, j + 1


def main():
    s = io.open(DOC, encoding="utf-8").read()
    obj, a, b = extract(s)
    before = len(s)
    errs, built, changed, kept = [], {}, 0, 0

    for key in sorted(obj):
        if not key.startswith("FIN"):
            kept += 1
            continue
        if key not in MAP:
            errs.append("%s is in the overview but not in MAP" % key)
            continue
        fname, prefix = MAP[key]
        path = os.path.join(PROP, fname)
        if not os.path.exists(path):
            errs.append("%s -> %s does not exist" % (key, fname))
            continue
        if ("hp-%s-" % prefix) not in obj[key]:
            errs.append("%s: the snapshot on file has no hp-%s-, MAP may be "
                        "pointing at the wrong email" % (key, prefix))
            continue
        raw = io.open(path, encoding="utf-8").read()
        if "{%" in raw or "{{" in raw:
            errs.append("%s: %s contains Django, which would show as literal "
                        "text in the preview panel" % (key, fname))
            continue
        new, missing = hosted(raw)
        if missing:
            errs.append("%s: %d embedded image(s) not in assets/: %s"
                        % (key, len(missing), missing[0]))
            continue
        if "base64" in new:
            errs.append("%s: a data URI survived the swap" % key)
            continue
        for bad in STALE:
            if bad in new:
                errs.append("%s still contains %r" % (key, bad))
        built[key] = new
        if obj[key] != new:
            changed += 1

    if errs:
        print("PROBLEMS (%d), nothing written:" % len(errs))
        for e in errs:
            print("  " + e)
        return 1

    obj.update(built)
    out = s[:a] + json.dumps(obj, ensure_ascii=False) + s[b:]
    io.open(DOC, "w", encoding="utf-8").write(out)

    again, _, _ = extract(io.open(DOC, encoding="utf-8").read())
    drift = [k for k, v in built.items() if again.get(k) != v]
    if drift:
        print("WROTE BUT DID NOT MATCH: %s" % ", ".join(sorted(drift)))
        return 1

    print("re-embedded %d of our emails (%d changed), left %d RFB originals alone"
          % (len(built), changed, kept))
    print("overview: %d KB -> %d KB" % (before // 1024, len(out) // 1024))
    print("no Django, no data URI, and no stale review count in any snapshot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
