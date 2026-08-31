#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read BEH-2 and BEH-3 back out of Klaviyo and print what they ACTUALLY are.

Written because create_flows.py sending a payload is not evidence that Klaviyo
stored it. The API accepts a definition, rewrites parts of it, and hands back
real ids for temporary ones; the only way to know what the flow does is to read
it back and walk it. This walks the tree from entry_action_id and prints the
path a person takes, so a wrong link or a dropped filter is visible rather than
implied.
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
import klav

FILES = ["klaviyo-flow-browse-messages.json", "klaviyo-flow-order-messages.json"]


def describe_filter(f, indent):
    """Groups AND, conditions inside a group OR - Klaviyo's own semantics."""
    if not f:
        return ["%sno filter" % indent]
    out = []
    groups = f.get("condition_groups") or []
    for gi, g in enumerate(groups):
        conds = g.get("conditions") or []
        parts = []
        for c in conds:
            t = c.get("type")
            if t == "metric-property":
                fl = c.get("filter") or {}
                parts.append("%s %s %r" % (c.get("field"), fl.get("operator"),
                                           fl.get("value")))
            elif t == "profile-metric":
                mf = c.get("measurement_filter") or {}
                tf = c.get("timeframe_filter") or {}
                when = tf.get("operator")
                if when == "in-the-last":
                    when = "in the last %s %s" % (tf.get("quantity"), tf.get("unit"))
                parts.append("%s(%s) %s %s  [%s]"
                             % (c.get("measurement"), c.get("metric_id"),
                                mf.get("operator"), mf.get("value"), when))
            else:
                parts.append(json.dumps(c)[:90])
        joiner = "\n%s      OR " % indent
        out.append("%s  AND group %d: %s" % (indent, gi + 1, joiner.join(parts))
                   if gi else "%s      group %d: %s" % (indent, gi + 1, joiner.join(parts)))
    return out


def walk(defn, key):
    acts = {a["id"]: a for a in defn.get("actions") or []}
    seen, lines = set(), []

    def go(aid, depth, label=""):
        if not aid or aid in seen:
            if aid in seen:
                lines.append("%s(rejoins %s)" % ("  " * depth, aid))
            return
        seen.add(aid)
        a = acts.get(aid)
        if not a:
            lines.append("%s?? unknown action %s" % ("  " * depth, aid))
            return
        pad = "  " * depth
        t = a.get("type")
        d = a.get("data") or {}
        lk = a.get("links") or {}
        if t == "time-delay":
            lines.append("%s%swait %s %s" % (pad, label, d.get("value"), d.get("unit")))
            go(lk.get("next"), depth)
        elif t == "send-email":
            m = d.get("message") or {}
            lines.append("%s%sEMAIL  %s" % (pad, label, m.get("name")))
            lines.append("%s         subject  %s" % (pad, m.get("subject_line")))
            lines.append("%s         preview  %s" % (pad, (m.get("preview_text") or "")[:72]))
            lines.append("%s         template %s   bcc %s   smart-sending %s"
                         % (pad, m.get("template_id"), m.get("bcc_email") or "NONE",
                            m.get("smart_sending_enabled")))
            go(lk.get("next"), depth)
        elif t == "conditional-split":
            lines.append("%s%sSPLIT" % (pad, label))
            for l in describe_filter((d.get("profile_filter") or {}), pad + "    "):
                lines.append(l)
            go(lk.get("next_if_true"), depth + 1, "TRUE  -> ")
            go(lk.get("next_if_false"), depth + 1, "FALSE -> ")
        else:
            lines.append("%s%s%s" % (pad, label, t))
            go(lk.get("next"), depth)

    go(defn.get("entry_action_id"), 1)
    orphans = [i for i in acts if i not in seen]
    return lines, orphans


def main():
    key, _ = klav.load_key()
    bad = 0
    for f in FILES:
        rec = json.load(io.open(os.path.join(ROOT, "data", f), encoding="utf-8"))
        fid = rec["flow_id"]
        st, res = klav.call(key, "GET",
                            "/flows/%s/?additional-fields[flow]=definition" % fid)
        at = (res.get("data") or {}).get("attributes") or {}
        defn = at.get("definition") or {}
        print("=" * 78)
        print("%s   %s   status=%s" % (fid, at.get("name"), at.get("status")))
        print("  https://www.klaviyo.com/flow/%s/edit" % fid)
        if at.get("status") != "draft":
            print("  *** NOT DRAFT ***"); bad += 1
        tr = (defn.get("triggers") or [{}])[0]
        print("\n  TRIGGER  metric %s" % tr.get("id"))
        for l in describe_filter(tr.get("trigger_filter"), "  "):
            print(l)
        rc = defn.get("reentry_criteria") or {}
        print("\n  RE-ENTRY  every %s %s" % (rc.get("duration"), rc.get("unit")))
        print("\n  FLOW FILTER (re-checked before every send)")
        for l in describe_filter(defn.get("profile_filter"), "  "):
            print(l)
        print("\n  PATH")
        lines, orphans = walk(defn, key)
        for l in lines:
            print(l)
        if orphans:
            print("\n  *** %d ORPHANED ACTION(S), unreachable: %s ***"
                  % (len(orphans), orphans)); bad += 1
        print()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
