#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point the overview's flow links at the flows that now exist.

The Browse Abandonment and Abandoned Order sections linked to Wzhp2m and VCVzm6,
which are RFB's flows - the ones being REPLACED. That was right while these were
proposals and nothing had been built; it is wrong now, because a reader following
the link lands in the old flow and could edit or activate it.

Driven by data/klaviyo-flow-*-messages.json so the ids cannot drift from what was
actually created, and it appends "replaces RFB <id>" rather than deleting the old
id, because knowing which flow to switch off is the whole point of the migration.

  python3 scripts/refresh_overview_flows.py
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "behavioural-email-overview.html")

# heading in the doc -> (recorded data file, the RFB flow it replaces)
FLOWS = [("Browse Abandonment", "klaviyo-flow-browse-messages.json", "Wzhp2m"),
         ("Abandoned Order", "klaviyo-flow-order-messages.json", "VCVzm6")]


def main():
    s = io.open(DOC, encoding="utf-8").read()
    before = s
    for heading, f, old in FLOWS:
        rec = json.load(io.open(os.path.join(ROOT, "data", f), encoding="utf-8"))
        new = rec["flow_id"]
        n_href = s.count("/flow/%s/edit" % old)
        if not n_href:
            print("  %-22s already pointing at %s" % (heading, new))
            continue
        s = s.replace("/flow/%s/edit" % old, "/flow/%s/edit" % new)
        # the visible link text is the bare id, immediately after the anchor
        s = re.sub(r'(rel="noopener">)%s(\s)' % re.escape(old),
                   lambda m: m.group(1) + new + m.group(2), s)
        # Say what it replaces - ANCHORED TO THIS SECTION'S OWN PARAGRAPH.
        # A plain replace of "</a> · Status: draft</p>" matches the flowsub of
        # every flow in the document, and annotated all seven with the same
        # note. The pattern therefore has to contain the new flow id.
        note = " · replaces RFB %s" % old
        pat = re.compile(
            r'(<p class="flowsub">[^<]*<a href="https://www\.klaviyo\.com/flow/'
            + re.escape(new) + r'/edit".*?</a> · Status: draft)(</p>)', re.S)
        s, k = pat.subn(lambda m: m.group(1) + note + m.group(2), s, count=1)
        if k != 1 and note not in s:
            print("  WARNING %s: could not annotate the section" % heading)
        got = len(rec["messages"])
        print("  %-22s %s -> %s   %d messages   %s"
              % (heading, old, new, got, rec["status"]))
    if s == before:
        print("nothing to change")
        return 0
    # nothing else in the document may have moved
    if len(re.findall(r"const PREVIEWS = ", s)) != 1:
        sys.exit("the PREVIEWS object was disturbed - not writing")
    io.open(DOC, "w", encoding="utf-8").write(s)
    for _, f, old in FLOWS:
        if old in s:
            print("  note: %s still appears in the doc (prose, not a link)" % old)
    print("overview updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
