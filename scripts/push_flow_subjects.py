#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set the subject and preview text of every BEH-2 / BEH-3 message, in nine locales.

WHY THIS IS NOT DONE IN THE TEMPLATE. A subject line is not part of the template
body, so the nine-way Django switch that localises everything else cannot reach
it - and putting a switch in subject_line does not work either: the field caps at
255 characters, measured, and a nine-locale chain is 560 to 747. Klaviyo's
Translations feature is the mechanism that exists for this, so subjects and
preview texts go through it.

WHAT IT WRITES, per message:
  the message itself   English subject and preview  (the source_locale value)
  the translation      the same two strings in de, en-GB, en-IE, es, fr, fr-BE,
                       it, nl and nl-BE

THE BODY BLOCK IS LEFT EMPTY ON PURPOSE. Creating a translation exposes four
blocks: subject, preview_text, from_label and the template body. The body is
already localised by the template's own Django, so filling its translation would
give two mechanisms authority over the same text. from_label stays empty too -
"HelloPrint" is a name, not a phrase.

SOURCE OF TRUTH IS data/translations.json, the same store the translation CSV is
exported from, so a string the translation team corrects lands here and then in
Klaviyo without being retyped.

THE OFFER NUMBERS ARE CHECKED, NOT TRUSTED. Four of these subjects state a
percentage and a deadline. Those come from scripts/_lib/offers.py, and a subject
that says 10% while the code gives 15% is the kind of error that generates
complaints from exactly the customers who acted on it. So the English strings are
asserted against offers.py and the run fails rather than shipping a mismatch.

  python3 scripts/push_flow_subjects.py --dry-run
  python3 scripts/push_flow_subjects.py
"""
import argparse, io, json, os, re, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import klav, offers
from create_flows import MESSAGE_DEFAULTS, TEST_BCC

# Klaviyo target locale -> the language column in data/translations.json.
# en-IE and en-GB share English; nl-BE takes Dutch and fr-BE takes French,
# which is how every other string in this programme is handled.
LOCALE_LANG = {"en-GB": "en", "en-IE": "en", "nl": "nl", "nl-BE": "nl",
               "fr": "fr", "fr-BE": "fr", "de": "de", "es": "es", "it": "it"}
TARGETS = sorted(LOCALE_LANG)
SOURCE_LOCALE = "en"
FALLBACK_LOCALE = "en-GB"

# message-name prefix -> (scope, subject key, preview key)
KEYS = [
    ("BRW-1",  "flow-browse", "subj.brw1",  "pre.brw1"),
    ("BRW-2",  "flow-browse", "subj.brw2",  "pre.brw2"),
    ("BRW-3",  "flow-browse", "subj.brw3",  "pre.brw3"),
    # ORD-1 is one string used by both branches: the email differs, the promise
    # in the inbox does not, and two subjects would be two things to translate.
    ("ORD-1H", "flow-order",  "subj.ord1",  "pre.ord1"),
    ("ORD-1L", "flow-order",  "subj.ord1",  "pre.ord1"),
    ("ORD-2H", "flow-order",  "subj.ord2h", "pre.ord2h"),
    ("ORD-2L", "flow-order",  "subj.ord2l", "pre.ord2l"),
    ("ORD-3H", "flow-order",  "subj.ord3h", "pre.ord3h"),
    ("ORD-3L", "flow-order",  "subj.ord3l", "pre.ord3l"),
]

FILES = ["klaviyo-flow-browse-messages.json", "klaviyo-flow-order-messages.json"]


def check_offers(tr):
    """Every stated percentage and deadline must match offers.py."""
    want = [
        ("subj.ord2l", offers.ORDER_PERCENT_10, offers.ORDER_HOURS_10),
        ("pre.ord3h",  offers.ORDER_PERCENT_10, offers.ORDER_HOURS_10),
        ("subj.ord3l", offers.ORDER_PERCENT_25, offers.ORDER_HOURS_25),
    ]
    bad = []
    for key, pct, hours in want:
        en = (tr["flow-order"].get(key) or {}).get("en", "")
        nums = [int(n) for n in re.findall(r"\d+", en)]
        if pct not in nums:
            bad.append("%s: %r does not state %d%%" % (key, en, pct))
        if hours not in nums:
            bad.append("%s: %r does not state %d hours" % (key, en, hours))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    tr = json.load(io.open(os.path.join(ROOT, "data", "translations.json"),
                           encoding="utf-8"))
    bad = check_offers(tr)
    if bad:
        for b in bad:
            print("OFFER MISMATCH  %s" % b)
        sys.exit("the subjects disagree with scripts/_lib/offers.py")
    print("offer numbers agree with offers.py\n")

    key, src = klav.load_key()
    print("key loaded from %s%s\n" % (src, "   DRY RUN" if a.dry_run else ""))

    problems = 0
    for f in FILES:
        path = os.path.join(ROOT, "data", f)
        rec = json.load(io.open(path, encoding="utf-8"))
        print("%s   %s" % (rec["flow"], rec["flow_id"]))
        changed = False
        for m in rec["messages"]:
            row = next((r for r in KEYS if m["name"].startswith(r[0] + " ")), None)
            if not row:
                print("  %-46s no translation keys mapped" % m["name"][:46])
                problems += 1; continue
            _, scope, sk, pk = row
            subj = tr[scope][sk]
            prev = tr[scope][pk]
            print("  %-46s %s" % (m["name"][:46], sk))
            if a.dry_run:
                print("      en subject %r" % subj["en"])
                print("      en preview %r" % prev["en"][:70])
                print("      would set %d target locales" % len(TARGETS))
                continue

            # 1. the English source, on the message itself
            m["subject"], m["preview"] = subj["en"], prev["en"]
            st, res = klav.call(key, "PATCH", "/flow-actions/%s/" % m["action"],
                {"data": {"type": "flow-action", "id": m["action"], "attributes": {
                    "definition": {"type": "send-email", "id": m["action"],
                        "links": ({"next": m["next"]} if m.get("next") else {}),
                        "data": {"status": "draft", "message": dict(
                            MESSAGE_DEFAULTS, id=m["message"], name=m["name"],
                            subject_line=subj["en"], preview_text=prev["en"],
                            template_id=m["template_saved"])}}}}})
            if st != 200:
                print("      source HTTP %s %s" % (st, "; ".join(klav.errors(res))[:120]))
                problems += 1; continue
            # re-attaching re-clones, so the copy id has to be re-recorded
            st, res = klav.call(key, "GET", "/flow-actions/%s/"
                                "?fields[flow-action]=definition.data.message" % m["action"])
            msg = ((((res.get("data") or {}).get("attributes") or {}).get("definition")
                    or {}).get("data") or {}).get("message") or {}
            m["template_live"] = msg.get("template_id")
            changed = True

            # 2. the translation collection
            tid = "flow-message::email::%s" % m["message"]
            q = urllib.parse.quote(tid, safe="")
            st, _ = klav.call(key, "GET", "/translations/%s/" % q,
                              revision=klav.REVISION_BETA)
            if st != 200:
                st, res = klav.call(key, "POST", "/translations/", {"data": {
                    "type": "translation", "attributes": {
                        "source_locale": SOURCE_LOCALE, "target_locales": TARGETS,
                        "fallback_locale": FALLBACK_LOCALE, "channel": "email"},
                    "relationships": {"flow-message": {"data": {
                        "type": "flow-message", "id": m["message"]}}}}},
                    revision=klav.REVISION_BETA)
                if st not in (200, 201):
                    print("      collection HTTP %s %s"
                          % (st, "; ".join(klav.errors(res))[:120]))
                    problems += 1; continue

            values = [
                {"id": "flow_message::%s::subject" % m["message"],
                 "translations": {loc: subj[LOCALE_LANG[loc]] for loc in TARGETS}},
                {"id": "flow_message::%s::preview_text" % m["message"],
                 "translations": {loc: prev[LOCALE_LANG[loc]] for loc in TARGETS}},
            ]
            st, res = klav.call(key, "PATCH", "/translations/%s/" % q, {"data": {
                "type": "translation", "id": tid,
                "attributes": {"values": values}}}, revision=klav.REVISION_BETA)
            if st not in (200, 201, 202):
                print("      values HTTP %s %s" % (st, "; ".join(klav.errors(res))[:160]))
                problems += 1; continue

            # 3. read it back and count what actually stored
            st, res = klav.call(key, "GET", "/translations/%s/"
                                "?additional-fields[translation]=values" % q,
                                revision=klav.REVISION_BETA)
            got = (((res.get("data") or {}).get("attributes") or {}).get("values")) or []
            gs = next((v for v in got if v["id"].endswith("::subject")), {})
            gp = next((v for v in got if v["id"].endswith("::preview_text")), {})
            ns = sum(1 for v in (gs.get("translations") or {}).values() if v)
            npv = sum(1 for v in (gp.get("translations") or {}).values() if v)
            ok = ns == len(TARGETS) and npv == len(TARGETS)
            print("      subject %d/%d locales   preview %d/%d   %s"
                  % (ns, len(TARGETS), npv, len(TARGETS), "ok" if ok else "INCOMPLETE"))
            if not ok:
                problems += 1
            time.sleep(0.5)

        if changed and not a.dry_run:
            rec["subjects_pushed"] = "2026-08-31"
            io.open(path, "w", encoding="utf-8").write(
                json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
            print("  recorded in data/%s" % f)
        print()
    print("problems: %d" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
