#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set the subject of every BEH-1 Welcome message in nine locales.

The strings already exist: proposals/welcome-flow-subjects.json carries a source
and nine translations per message, and create_welcome_v2.py re-keys that file to
the new message ids when it rebuilds the flow. This pushes them.

WHY SUBJECTS GO THROUGH TRANSLATIONS AND NOT THE TEMPLATE. A subject is not part
of the template body, so the nine-way Django switch that localises everything
else cannot reach it - and a switch in subject_line does not fit either: the
field caps at 255 characters, measured, and a nine-locale chain is 560 to 747.

PREVIEW TEXT IS LEFT EMPTY, as it was on the old flow. Each email opens with its
own hidden preheader in the body, which is already localised by the template.
Setting a second one here would give two mechanisms authority over the same line.

  python3 scripts/push_welcome_subjects.py --dry-run
  python3 scripts/push_welcome_subjects.py
"""
import argparse, io, json, os, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
import klav

TARGETS = ["de", "en-GB", "en-IE", "es", "fr", "fr-BE", "it", "nl", "nl-BE"]
SOURCE_LOCALE = "en"
FALLBACK_LOCALE = "en-GB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    key, src = klav.load_key()
    print("key from %s%s\n" % (src, "   DRY RUN" if a.dry_run else ""))

    subj = json.load(io.open(os.path.join(ROOT, "proposals",
        "welcome-flow-subjects.json"), encoding="utf-8"))
    rec = json.load(io.open(os.path.join(ROOT, "data",
        "klaviyo-flow-welcome-messages.json"), encoding="utf-8"))
    print("%s   %s\n" % (rec["flow"], rec["flow_id"]))

    problems = 0
    for m in rec["messages"]:
        mid = m["message"]
        entry = subj.get(mid)
        if not entry:
            print("  %-36s NO SUBJECT RECORDED" % m["name"][:36])
            problems += 1
            continue
        tr = entry.get("translations") or {}
        missing = [l for l in TARGETS if not tr.get(l)]
        print("  %-36s %s" % (m["name"][:36], entry["key"]))
        if missing:
            print("      missing locales: %s" % missing)
            problems += 1
            continue
        if a.dry_run:
            print("      en %r  + %d locales" % (entry["source"], len(TARGETS)))
            continue

        tid = "flow-message::email::%s" % mid
        q = urllib.parse.quote(tid, safe="")
        st, _ = klav.call(key, "GET", "/translations/%s/" % q,
                          revision=klav.REVISION_BETA)
        if st != 200:
            st, res = klav.call(key, "POST", "/translations/", {"data": {
                "type": "translation", "attributes": {
                    "source_locale": SOURCE_LOCALE, "target_locales": TARGETS,
                    "fallback_locale": FALLBACK_LOCALE, "channel": "email"},
                "relationships": {"flow-message": {"data": {
                    "type": "flow-message", "id": mid}}}}},
                revision=klav.REVISION_BETA)
            if st not in (200, 201):
                print("      collection HTTP %s %s"
                      % (st, "; ".join(klav.errors(res))[:110]))
                problems += 1
                continue
        values = [{"id": "flow_message::%s::subject" % mid,
                   "translations": {l: tr[l] for l in TARGETS}}]
        st, res = klav.call(key, "PATCH", "/translations/%s/" % q, {"data": {
            "type": "translation", "id": tid,
            "attributes": {"values": values}}}, revision=klav.REVISION_BETA)
        if st not in (200, 201, 202):
            print("      values HTTP %s %s" % (st, "; ".join(klav.errors(res))[:130]))
            problems += 1
            continue
        st, res = klav.call(key, "GET", "/translations/%s/"
                            "?additional-fields[translation]=values" % q,
                            revision=klav.REVISION_BETA)
        got = (((res.get("data") or {}).get("attributes") or {}).get("values")) or []
        gs = next((v for v in got if v["id"].endswith("::subject")), {})
        n = sum(1 for v in (gs.get("translations") or {}).values() if v)
        print("      subject %d/%d locales   %s"
              % (n, len(TARGETS), "ok" if n == len(TARGETS) else "INCOMPLETE"))
        if n != len(TARGETS):
            problems += 1
        time.sleep(0.5)

    print("\nproblems: %d" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
