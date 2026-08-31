#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Push built content into BEH-2 and BEH-3, and re-clone what they send. No import.

Same two-phase loop scripts/push_templates.py runs for BEH-1, and for the same
measured reason: attaching a saved template to a flow message makes a PRIVATE
COPY owned by that message, the copy is what sends, and the copy CANNOT be
patched - /api/templates/{id} returns 404 for it even though template-render
renders it happily. So:

  1. push   - PATCH each library master with the freshly built HTML
  2. attach - PATCH each flow action to point at its master, which re-clones it,
              then record the new copy id

Copy ids therefore change on every push, which is why they are recorded rather
than remembered.

VERIFICATION IS SEMANTIC, NOT BYTE-FOR-BYTE. Klaviyo rewrites HTML on save: it
pretty-prints CSS, shortens #ffffff to #fff, turns &middot; into the character
and reorders attributes. A byte comparison would fail on every push and prove
nothing. Each push is verified by reading the template back and checking that
the locale switches are all still there and still closed, that the unsubscribe
tag survived, and that a canary string only present in the new build arrived.

  python3 scripts/push_flows.py                 # push, re-attach, verify
  python3 scripts/push_flows.py --dry-run
  python3 scripts/push_flows.py --only ORD-3    # substring match on message name
  python3 scripts/push_flows.py --push-only     # masters only, no re-attach
"""
import argparse, io, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import klav
from create_flows import TEMPLATES, MESSAGE_DEFAULTS, TEST_BCC

FILES = ["klaviyo-flow-browse-messages.json", "klaviyo-flow-order-messages.json"]
SRC = {name: fname for name, fname in TEMPLATES}

# Strings that must be in the stored HTML after a push. Each is NEW in this
# version and contains no HTML entity for Klaviyo to rewrite. {% comment %} is
# the fix that made five of these nine render at all - see scripts/_lib/doc.py.
CANARIES = ["{% comment %}", '<html lang="{% if person.locale']


_COMMENT_BLOCK = re.compile(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", re.S)


def shape(html):
    """The properties a push must preserve. Whitespace and entities excluded.

    THE DOC HEADER IS EXCLUDED FIRST. It sits inside {% comment %} and quotes
    {% catalog %} and {% with %} as documentation, so counting tags across the
    whole file counts examples that never execute - and the header is exactly
    where an unbalanced example is harmless.

    ALL ifs ARE COUNTED, not only the locale switches. BEH-1's version of this
    check compared locale-switch count against TOTAL endif count, which only
    balances when every if in the file is a locale switch. These templates also
    guard the catalog block and the quantity phrase, so that comparison called
    all nine unbalanced. Locale switches are still counted, as the thing whose
    survival proves the push carried the translations.
    """
    live = _COMMENT_BLOCK.sub("", html)
    return {"ifs": len(re.findall(r"\{%\s*if\b", live)),
            "endifs": len(re.findall(r"\{%\s*endif\s*%\}", live)),
            "switches": len(re.findall(r"\{%\s*if\s+person\.locale", live)),
            "unsub": len(re.findall(r"\{%\s*unsubscribe", live)),
            "catalog": len(re.findall(r"\{%\s*catalog\b", live)),
            "endcatalog": len(re.findall(r"\{%\s*endcatalog\s*%\}", live))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--push-only", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    key, src = klav.load_key()
    print("key loaded from %s%s\n" % (src, "   DRY RUN" if a.dry_run else ""))

    bad = 0
    for f in FILES:
        path = os.path.join(ROOT, "data", f)
        rec = json.load(io.open(path, encoding="utf-8"))
        print("%s   %s" % (rec["flow"], rec["flow_id"]))
        changed = False
        for m in rec["messages"]:
            if a.only and a.only.lower() not in m["name"].lower():
                continue
            fname = SRC.get(m["template_name"])
            if not fname:
                print("  %-46s no source file mapped" % m["name"][:46]); bad += 1; continue
            html = io.open(os.path.join(ROOT, "proposals", fname), encoding="utf-8").read()
            want = shape(html)
            cans = [c for c in CANARIES if c in html]
            if want["ifs"] != want["endifs"] or want["catalog"] != want["endcatalog"]:
                print("  %-46s UNBALANCED locally, not pushed" % m["name"][:46])
                bad += 1; continue
            print("  %-46s %3d KB  %d switches" % (m["name"][:46], len(html)//1024,
                                                   want["switches"]))
            if a.dry_run:
                print("      would push master %s and re-attach" % m["template_saved"])
                continue
            st, res = klav.call(key, "PATCH", "/templates/%s/" % m["template_saved"],
                {"data": {"type": "template", "id": m["template_saved"],
                          "attributes": {"html": html}}})
            if st not in (200, 201):
                print("      master %s HTTP %s %s" % (m["template_saved"], st,
                                                      "; ".join(klav.errors(res))[:130]))
                bad += 1; continue
            st, res = klav.call(key, "GET", "/templates/%s/?fields[template]=html"
                                % m["template_saved"])
            got = ((res.get("data") or {}).get("attributes") or {}).get("html") or ""
            g = shape(got)
            miss = [c for c in cans if c not in got]
            ok = (g["switches"] == want["switches"] and g["ifs"] == g["endifs"]
                  and g["catalog"] == g["endcatalog"] and g["unsub"] == want["unsub"]
                  and not miss)
            print("      master %s  %s  switches %d/%d  catalog %d/%d%s"
                  % (m["template_saved"], "ok" if ok else "MISMATCH",
                     g["switches"], want["switches"], g["catalog"], g["endcatalog"],
                     "" if not miss else "  missing canary %r" % miss[0]))
            if not ok:
                bad += 1; continue
            if a.push_only:
                continue

            st, res = klav.call(key, "PATCH", "/flow-actions/%s/" % m["action"],
                {"data": {"type": "flow-action", "id": m["action"], "attributes": {
                    "definition": {"type": "send-email", "id": m["action"],
                        "links": ({"next": m["next"]} if m.get("next") else {}),
                        "data": {"status": "draft", "message": dict(
                            MESSAGE_DEFAULTS, id=m["message"], name=m["name"],
                            subject_line=m["subject"], preview_text=m["preview"],
                            template_id=m["template_saved"])}}}}})
            if st != 200:
                print("      attach HTTP %s %s" % (st, "; ".join(klav.errors(res))[:130]))
                bad += 1; continue
            st, res = klav.call(key, "GET", "/flow-actions/%s/"
                                "?fields[flow-action]=definition.data.message" % m["action"])
            msg = ((((res.get("data") or {}).get("attributes") or {}).get("definition")
                    or {}).get("data") or {}).get("message") or {}
            m["template_live"] = msg.get("template_id")
            changed = True
            print("      copy %-8s subj %s  bcc %s"
                  % (msg.get("template_id"),
                     "kept" if msg.get("subject_line") == m["subject"] else "CHANGED",
                     "set" if msg.get("bcc_email") == TEST_BCC else "MISSING"))
            time.sleep(0.4)
        if changed and not a.dry_run:
            rec["pushed"] = "2026-08-31"
            io.open(path, "w", encoding="utf-8").write(
                json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
            print("  recorded new copy ids in data/%s" % f)
        print()
    print("problems: %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
