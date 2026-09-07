#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scope BEH-4's rotation gates to the messages they are about.

create_post_flow.py leaves each ring split saying "received NO email at all in
the last 365 days", which is nearly never true and would stop the ring dead. The
real condition is "has not been sent THIS category's nudge in a year", and it
needs the message id - which does not exist until the flow does. Hence a second
pass.

WHY EACH GATE CHECKS TWO MESSAGES. The ring has two nodes per category, one for
"you ordered this" (Pass A) and one for the rotation (Pass B), because a
send-email cannot take two inbound links. They carry the SAME template, so from
the reader's point of view they are one email - and a gate that only knew about
its own node would resend the same content: Pass B sends the Commercial Print
nudge, then on the next order Pass A checks only its own node, finds nothing, and
sends it again. So both gates for a category check both of its message ids.

Conditions inside a condition_group OR; groups AND. "Received neither" is
therefore TWO groups of one condition each, not one group of two - one group
would mean "received neither A or received neither B", which is true whenever
either is unsent.

Idempotent: re-running rewrites the same filters.

  python3 scripts/patch_post_rotation.py --dry-run
  python3 scripts/patch_post_rotation.py
"""
import argparse, copy, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
import klav                                                    # noqa: E402

REC = os.path.join(ROOT, "data", "klaviyo-flow-post-messages.json")
M_RECEIVED = "UxHsCy"


def received_zero(message_id):
    """One group: this message has not been sent in the last 365 days."""
    return {"conditions": [{
        "type": "profile-metric", "metric_id": M_RECEIVED,
        "measurement": "count",
        "measurement_filter": {"type": "numeric", "operator": "equals",
                               "value": 0},
        "timeframe_filter": {"type": "date", "operator": "in-the-last",
                             "quantity": 365, "unit": "day"},
        "metric_filters": [{"property": "$message",
                            "filter": {"type": "string", "operator": "equals",
                                       "value": message_id}}]}]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    key, src = klav.load_key()
    rec = json.loads(io.open(REC, encoding="utf-8").read())
    fid = rec["flow_id"]
    print("%s   %s\n" % (rec["flow"], fid))

    st, res = klav.call(key, "GET", "/flows/%s/flow-actions/" % fid)
    ids = [x["id"] for x in res.get("data") or []]
    node = {}
    for aid in ids:
        st, one = klav.call(key, "GET", "/flow-actions/%s/" % aid)
        node[aid] = ((one.get("data") or {}).get("attributes") or {}
                     ).get("definition") or {}

    # slug -> both message ids, read off the message names the builder set
    by_slug = {}
    for aid, d in node.items():
        if d.get("type") != "send-email":
            continue
        m = (d.get("data") or {}).get("message") or {}
        mo = re.match(r"POST-3 (\S+) · (ordered|rotation) · ", m.get("name") or "")
        if mo:
            by_slug.setdefault(mo.group(1), {})[mo.group(2)] = m.get("id")
    print("category message ids found:")
    for slug, pair in sorted(by_slug.items()):
        print("   %-18s ordered=%s rotation=%s"
              % (slug, pair.get("ordered"), pair.get("rotation")))
    bad = [s for s, p in by_slug.items() if not (p.get("ordered") and p.get("rotation"))]
    if len(by_slug) != 6 or bad:
        print("\nFAILED: expected 6 categories with both nodes; incomplete: %s"
              % (bad or "count=%d" % len(by_slug)))
        return 1

    # which split feeds which category node
    target = {}
    for aid, d in node.items():
        if d.get("type") != "conditional-split":
            continue
        t = (d.get("links") or {}).get("next_if_true")
        td = node.get(str(t)) or {}
        if td.get("type") == "send-email":
            m = (td.get("data") or {}).get("message") or {}
            mo = re.match(r"POST-3 (\S+) · (ordered|rotation) · ",
                          m.get("name") or "")
            if mo:
                target[aid] = (mo.group(1), mo.group(2))
    print("\nring splits to patch: %d" % len(target))
    if len(target) != 12:
        print("FAILED: expected 12 ring splits, found %d" % len(target))
        return 1

    problems = 0
    for aid, (slug, which) in sorted(target.items(), key=lambda kv: kv[1]):
        d = copy.deepcopy(node[aid])
        cgs = ((d.get("data") or {}).get("profile_filter") or {}
               ).get("condition_groups") or []
        # keep the Ordered Product group (Pass A only), replace the rest
        keep = [g for g in cgs
                if any((c.get("metric_id") == "XGuVCG")
                       for c in g.get("conditions") or [])]
        pair = by_slug[slug]
        d["data"]["profile_filter"]["condition_groups"] = keep + [
            received_zero(pair["ordered"]), received_zero(pair["rotation"])]
        print("   %-18s %-8s groups %d -> %d" % (slug, which, len(cgs),
                                                 len(keep) + 2))
        if a.dry_run:
            continue
        st, r = klav.call(key, "PATCH", "/flow-actions/%s/" % aid, {"data": {
            "type": "flow-action", "id": aid, "attributes": {"definition": d}}})
        if st not in (200, 201, 202):
            print("      HTTP %s %s" % (st, "; ".join(klav.errors(r))[:150]))
            problems += 1
    if a.dry_run:
        print("\ndry run, nothing written")
        return 0

    # read back: every ring split must now name two messages
    st, res = klav.call(key, "GET",
                        "/flows/%s/?additional-fields[flow]=definition" % fid)
    stored = ((res.get("data") or {}).get("attributes") or {}
              ).get("definition") or {}
    ok = 0
    for x in stored.get("actions") or []:
        if x.get("type") != "conditional-split":
            continue
        vals = []
        for g in (((x.get("data") or {}).get("profile_filter") or {}
                   ).get("condition_groups") or []):
            for c in g.get("conditions") or []:
                for mf in c.get("metric_filters") or []:
                    if mf.get("property") == "$message":
                        vals.append(mf["filter"]["value"])
        if len(vals) == 2:
            ok += 1
    print("\nverify: %d ring splits now scoped to two message ids each" % ok)
    if ok != 12:
        print("FAILED: expected 12")
        return 1
    print("problems: %d" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
