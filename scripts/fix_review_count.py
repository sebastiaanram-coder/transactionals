# -*- coding: utf-8 -*-
"""
Put ONE review count in the programme, written the way each language writes it.

Welcome 01 said "more than 33,000" while Welcome 03 said "more than 34,000", so
a reader who got both saw the number go up by a thousand in three days. The count
is now 34,000+ everywhere, and the "+" carries the "at least" sense that the
"more than" wording used to, which also shortens every string.

Run: python3 scripts/fix_review_count.py
Writes data/translations.json in place, then the email builders must re-run.
"""
import json, re, io, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "translations.json")

# A NON-BREAKING space, not a plain one. French groups thousands with a space,
# and a plain space lets a mail client wrap "34" onto one line and "000+" onto
# the next. The store previously held U+0020 here.
NB = " "

# language -> (pattern for the old "more than N" phrase, the "N+" replacement)
RULES = {
    "en": (r"more than 3[34],000",      "34,000+"),
    "nl": (r"meer dan 3[34]\.000",      "34.000+"),
    "fr": (r"plus de 3[34][   ]000", "34" + NB + "000+"),
    "de": (r"mehr als 3[34]\.000",      "34.000+"),
    "es": (r"más de 3[34]\.000",   "34.000+"),
    "it": (r"oltre 3[34]\.000",         "34.000+"),
}

KEYS = [("_shared", "tp.verified_line"), ("browse-01", "reviews_note"),
        ("welcome-01", "reviews_note"), ("welcome-03", "pre"),
        ("welcome-03", "score_line")]


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + "/" + str(k))
    elif isinstance(o, str):
        yield p, o


def main():
    d = json.loads(io.open(P, encoding="utf-8").read())
    changed, problems = [], []

    for scope, key in KEYS:
        node = d.get(scope, {}).get(key)
        if node is None:
            problems.append("%s/%s is missing from the store" % (scope, key))
            continue
        for lang, (pat, rep) in RULES.items():
            old = node.get(lang)
            if old is None:
                problems.append("%s/%s/%s is missing" % (scope, key, lang))
                continue
            new, n = re.subn(pat, rep, old)
            if n == 0:
                problems.append("%s/%s/%s did not match: %s" % (scope, key, lang, old))
            else:
                node[lang] = new
                changed.append((scope, key, lang, old, new))

    # No string anywhere may still carry a bare count. Catches a sixth key
    # someone adds later, and catches a rule that silently stopped matching.
    ok = ("34,000+", "34.000+", "34" + NB + "000+")
    leaks = [(p, v) for p, v in walk(d)
             if re.search(r"3[34][ ,.  ]000", v)
             and not any(o in v for o in ok)]

    print("rewritten: %d of %d" % (len(changed), len(KEYS) * len(RULES)))
    for s, k, l, o, n in changed:
        print("  %-10s %-18s %s" % (s, k, l))
        print("      - %s" % o)
        print("      + %s" % n)

    if problems:
        print("\nPROBLEMS (%d):" % len(problems))
        for x in problems:
            print("  " + x)
    if leaks:
        print("\nSTILL CARRYING A BARE COUNT (%d):" % len(leaks))
        for p, v in leaks:
            print("  %s => %s" % (p, v))
    if problems or leaks:
        print("\nnothing written")
        return 1

    # indent=1, sort_keys=False reproduces the file's existing formatting, so the
    # diff is only the strings that actually changed.
    with io.open(P, "w", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1))
        f.write("\n")
    print("\nwritten %s" % os.path.relpath(P, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
