#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export the translations to a CSV for the translation team, and read it back.

  python3 scripts/translations_csv.py export            # welcome flow
  python3 scripts/translations_csv.py export --all      # whole programme
  python3 scripts/translations_csv.py export --beh23    # BEH-2 + BEH-3 only
  python3 scripts/translations_csv.py import FILE.csv   # apply their edits
  python3 scripts/translations_csv.py import FILE.csv --dry-run

ONE ROW PER STRING, ONE COLUMN PER LANGUAGE. `scope` and `key` are the identity
of a string and must come back unchanged - they are how the import finds where a
row belongs. Everything else in the row is editable.

WHAT CAN GO WRONG IN A SPREADSHEET, and what this checks on the way back in:

  Tokens. @@CAP@@ is replaced at build time with the discount cap in the market's
  own currency. A translator who "translates" it, or drops it, silently removes
  the cap from that language's email. Every token in a source string must still
  be present in every translation, or the import refuses the row.

  HTML entities. &middot; &rsquo; &ldquo; are markup, not text. Sheets will not
  mangle them by itself but a translator retyping a line easily will, and a raw
  "&" that is not an entity breaks the HTML.

  The non-breaking space. French groups thousands with U+00A0 - "34 000+". It is
  invisible in a spreadsheet cell, so a translator retyping the number will use a
  normal space, and the number can then wrap across two lines in the email. The
  import restores it and says so rather than failing.

  Formula injection. A cell beginning = + - @ is read as a formula by Sheets and
  Excel. The export prefixes those with a zero-width joiner-free apostrophe guard
  and the import strips it. No string currently starts with one, but a translator
  can easily produce one.

The importer NEVER writes a partially-valid file: it validates every row first
and only then writes, so a single bad cell cannot leave the store half-updated.
"""
import csv, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "_lib"))
STORE = os.path.join(ROOT, "data", "translations.json")
LANGS = ["en", "nl", "fr", "de", "es", "it"]
NBSP = " "
# LOCALE VARIANTS, WHICH ARE NOT LANGUAGES. en-US reads English prose and
# overrides only the handful of strings where American English makes a different
# CLAIM, not a different word: "includes VAT" is false where there is no VAT.
# i18n.get() resolves an exact locale key ahead of the language, so a blank cell
# here means "no override, use en" - which is why, unlike a language column, an
# empty variant cell is NOT an error on import.
VARIANTS = ["en-US"]
HEADER = ["scope", "key", "where", "keep_exactly"] + LANGS + VARIANTS

WELCOME_SCOPES = ["welcome-01", "welcome-02", "welcome-03", "welcome-04",
                  "flow-welcome"]

# BEH-2 Browse Abandonment and BEH-3 Abandoned Order, exported as one batch
# because they were built together and share most of their shared strings.
BEH23_SCOPES = ["flow-browse", "browse-01", "browse-02", "browse-03",
                "flow-order", "order-01", "order-02-high", "order-02-low",
                "order-03-high", "order-03-low"]
# the _shared strings these four emails actually substitute
WELCOME_SHARED = ["wc.discount", "wc.waiting", "wc.expires5", "wc.help",
                  "wc.terms", "alt.cs_agents", "help.chat", "help.centre",
                  "foot.unsub"]

EMAIL_NAME = {
    "welcome-01": "Welcome 1 - day 0, has the code",
    "welcome-02": "Welcome 2 - day 1, behind the print",
    "welcome-03": "Welcome 3 - day 3, rated excellent",
    "welcome-04": "Welcome 4 - day 5, send it over",
    "flow-welcome": "Subject lines (Klaviyo flow message)",
    "_shared": "Shared across the four welcome emails",
    "flow-browse": "SUBJECTS + PREVIEWS - Browse Abandonment (Klaviyo flow)",
    "browse-01": "Browse 1 - +1h, the product you viewed",
    "browse-02": "Browse 2 - +24h, you do not need the artwork yet",
    "browse-03": "Browse 3 - +3d, tell us the job and we price it",
    "flow-order": "SUBJECTS + PREVIEWS - Abandoned Order (Klaviyo flow)",
    "order-01": "Abandoned order 1 - +1h, the basket restored (both branches)",
    "order-02-high": "Abandoned order 2 HIGH value - +24h, the print expert",
    "order-02-low": "Abandoned order 2 LOW value - +24h, 10% off",
    "order-03-high": "Abandoned order 3 HIGH value - +72h, expert plus 10%",
    "order-03-low": "Abandoned order 3 LOW value - +72h, 25% capped",
}
# what a key is, for a translator with no access to the template
WHERE = {
    "pre": "hidden preheader - the inbox snippet",
    "pre_ordered": "preheader for people who already ordered (no discount)",
    "h1": "main headline",
    "sub": "line under the headline",
    "eyebrow": "small green line above the headline",
    "codelbl": "label above the code, inside the dashed box",
    "code_line": "note under the code",
    "ctanote": "small line under the button",
    "cta": "button",
    "cta2": "second button",
    "sect_h": "section heading",
    "sect_sub": "line under the section heading",
    "expires": "countdown, on the product tiles",
    "lastday": "countdown in the green bar",
    "reviews_note": "under the Trustpilot stars",
    "score_line": "Trustpilot score line",
    "wc.terms": "offer conditions, small print in the footer",
    "wc.discount": "green bar at the top",
    "wc.waiting": "green bar at the top",
    "wc.expires5": "green bar, validity",
    "foot.unsub": "unsubscribe link label",
    "subj.wel1": "SUBJECT day 0", "subj.wel2": "SUBJECT day 1",
    "subj.wel3": "SUBJECT day 3", "subj.wel4": "SUBJECT day 5",
    "subj.brw1": "SUBJECT browse +1h", "pre.brw1": "PREVIEW browse +1h",
    "subj.brw2": "SUBJECT browse +24h", "pre.brw2": "PREVIEW browse +24h",
    "subj.brw3": "SUBJECT browse +3d", "pre.brw3": "PREVIEW browse +3d",
    "subj.ord1": "SUBJECT abandoned order +1h, both branches",
    "pre.ord1": "PREVIEW abandoned order +1h, both branches",
    "subj.ord2h": "SUBJECT abandoned order +24h high value",
    "pre.ord2h": "PREVIEW abandoned order +24h high value",
    "subj.ord2l": "SUBJECT abandoned order +24h low value",
    "pre.ord2l": "PREVIEW abandoned order +24h low value",
    "subj.ord3h": "SUBJECT abandoned order +72h high value",
    "pre.ord3h": "PREVIEW abandoned order +72h high value",
    "subj.ord3l": "SUBJECT abandoned order +72h low value",
    "pre.ord3l": "PREVIEW abandoned order +72h low value",
}


def load():
    return json.loads(io.open(STORE, encoding="utf-8").read())


def rows(d, mode):
    """mode is "all", "beh23" or "welcome"."""
    out = []
    if mode == "all":
        pairs = [(sc, k) for sc in sorted(d) for k in sorted(d[sc])]
    elif mode == "beh23":
        pairs = [(sc, k) for sc in BEH23_SCOPES for k in sorted(d.get(sc) or {})]
    else:
        pairs = [(sc, k) for sc in WELCOME_SCOPES for k in sorted(d.get(sc) or {})]
        pairs += [("_shared", k) for k in WELCOME_SHARED if k in (d.get("_shared") or {})]
    for sc, k in pairs:
        node = d[sc][k]
        if not isinstance(node, dict) or "en" not in node:
            continue
        en = node["en"]
        keep = sorted(set(re.findall(r"@@[A-Z]+@@", en))
                      | set(re.findall(r"&[a-z]+;", en))
                      | set(re.findall(r"\d+%", en)))
        out.append({"scope": sc, "key": k,
                    "where": "%s | %s" % (EMAIL_NAME.get(sc, sc),
                                          WHERE.get(k, k)),
                    "keep_exactly": " ".join(keep),
                    **{lg: node.get(lg, "") for lg in LANGS},
                    **{v: node.get(v, "") for v in VARIANTS}})
    return out


def guard(v):
    """Stop a spreadsheet reading a cell as a formula."""
    return "'" + v if v[:1] in ("=", "+", "-", "@") else v


def unguard(v):
    return v[1:] if v[:1] == "'" and v[1:2] in ("=", "+", "-", "@") else v


NAMES = {"all": "translations-all.csv",
         "beh23": "translations-browse-order.csv",
         "welcome": "translations-welcome.csv"}


def do_export(mode):
    d = load()
    rs = rows(d, mode)
    name = NAMES[mode]
    path = os.path.join(ROOT, name)
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in rs:
            w.writerow({k: guard(r[k]) if k in LANGS + VARIANTS else r[k]
                        for k in HEADER})
    tok = sum(1 for r in rs if r["keep_exactly"])
    print("%d strings -> %s" % (len(rs), name))
    print("   columns: %s" % ", ".join(HEADER))
    print("   %d rows carry something that must survive editing (keep_exactly)" % tok)
    print("   encoded utf-8 with BOM, so Sheets and Excel both read the accents")
    var = sum(1 for r in rs if any(r.get(v) for v in VARIANTS))
    print("   %d rows carry an en-US override (blank = use the en wording)" % var)
    print("\nTell the team: edit only the language columns. scope, key, where and")
    print("keep_exactly are how the import finds the string again.")
    return 0


def do_import(path, dry):
    d = load()
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        got = list(csv.DictReader(f))
    if not got:
        print("empty CSV"); return 1
    missing_cols = [c for c in ("scope", "key") + tuple(LANGS)
                    if c not in got[0]]
    if missing_cols:
        print("CSV is missing columns: %s" % ", ".join(missing_cols)); return 1

    errs, changes, fixed = [], [], []
    for i, r in enumerate(got, 2):          # row 1 is the header
        sc, k = r["scope"].strip(), r["key"].strip()
        if sc not in d or k not in d[sc]:
            errs.append("row %d: %s/%s is not in the store - scope or key edited?"
                        % (i, sc, k))
            continue
        node = d[sc][k]
        en = node["en"]
        tokens = set(re.findall(r"@@[A-Z]+@@", en))
        for lg in LANGS:
            new = unguard((r.get(lg) or "").replace("\r\n", "\n").strip())
            if not new:
                errs.append("row %d: %s/%s %s is empty" % (i, sc, k, lg))
                continue
            for t in tokens:
                if t not in new:
                    errs.append("row %d: %s/%s %s lost the token %s"
                                % (i, sc, k, lg, t))
            if re.search(r"&(?![a-z]+;|#\d+;)", new):
                errs.append("row %d: %s/%s %s has a bare & - breaks the HTML"
                            % (i, sc, k, lg))
            # the invisible French thousands space
            if lg == "fr" and NBSP in (node.get("fr") or "") and NBSP not in new:
                cand = re.sub(r"(\d) (\d{3})", r"\1" + NBSP + r"\2", new)
                if NBSP in cand:
                    fixed.append("%s/%s fr: restored the non-breaking space" % (sc, k))
                    new = cand
            if new != node.get(lg):
                changes.append((sc, k, lg, node.get(lg), new))
        for v in VARIANTS:
            if v not in r:
                continue                # column absent: nothing to say
            new = unguard((r.get(v) or "").replace("\r\n", "\n").strip())
            if not new:
                # BLANK IS MEANINGFUL AND NOT AN ERROR: it means this string has
                # no American variant and should fall through to en.
                if node.get(v):
                    changes.append((sc, k, v, node.get(v), ""))
                continue
            for t in tokens:
                if t not in new:
                    errs.append("row %d: %s/%s %s lost the token %s"
                                % (i, sc, k, v, t))
            if re.search(r"&(?![a-z]+;|#\d+;)", new):
                errs.append("row %d: %s/%s %s has a bare & - breaks the HTML"
                            % (i, sc, k, v))
            if new != node.get(v):
                changes.append((sc, k, v, node.get(v), new))
                if not dry:
                    node[lg] = new

    print("rows read: %d" % len(got))
    if fixed:
        print("\nrepaired automatically (%d):" % len(fixed))
        for x in fixed: print("   " + x)
    if errs:
        print("\nPROBLEMS (%d) - nothing written:" % len(errs))
        for e in errs[:40]: print("   " + e)
        if len(errs) > 40: print("   ... and %d more" % (len(errs) - 40))
        return 1
    print("\nchanged: %d strings" % len(changes))
    for sc, k, lg, o, n in changes[:60]:
        print("   %s/%s %s" % (sc, k, lg))
        print("      - %s" % (o or "")[:110])
        print("      + %s" % n[:110])
    if len(changes) > 60:
        print("   ... and %d more" % (len(changes) - 60))
    if dry:
        print("\n--dry-run: nothing written")
        return 0
    if changes:
        io.open(STORE, "w", encoding="utf-8").write(
            json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        print("\nwritten data/translations.json")
        print("Now: python3 scripts/translate_welcome.py && "
              "python3 scripts/push_templates.py && "
              "python3 scripts/refresh_overview.py")
    else:
        print("\nnothing to change")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("export", "import"):
        print(__doc__); return 1
    if sys.argv[1] == "export":
        mode = ("all" if "--all" in sys.argv else
                "beh23" if "--beh23" in sys.argv else "welcome")
        return do_export(mode)
    if len(sys.argv) < 3:
        print("import needs a CSV path"); return 1
    return do_import(sys.argv[2], "--dry-run" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())
