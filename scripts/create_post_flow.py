#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create BEH-4 Post-Purchase in Klaviyo, in draft.

Design and evidence: proposals/post-purchase-proposal.md. What follows is only
the part the API forced, plus the decisions taken on 2026-09-07.

WHY THE CATEGORY SPLIT RIDES ON `Ordered Product` AND NOT ON THE TRIGGER.
A conditional-split accepts ONLY `profile_filter` - trigger_filter, event_filter
and metric_filter are all rejected - and a send-email action's
`additional_filters` rejects a `metric-property` condition with "an invalid field
type was passed in". So NOTHING in this flow can read `event.Categories` off the
triggering Placed Order, and the profile carries no category property either.

`Ordered Product` (XGuVCG) is the way through. It fires per line item, is
current, and carries the full category path:
    ["Commercial Print", "All Booklets", "Stapled Booklets"]
A `profile-metric` condition IS a profile filter, and it takes `metric_filters`,
so "ordered something in Commercial Print in the last day" is expressible. The
shape is not the one used elsewhere in this repo - `metric_filters` entries want
`property` and `filter`, with no `type` and no `metric_id`:
    {"property": "Categories", "filter": {"type": "string", ...}}
Getting that wrong returns "'property' is a required field for the resource
'ProfileMetricPropertyFilter'", which is how the shape was found.

THE RING, and why it is twelve splits and not six.
Sebastiaan wants the first nudge to match the category ordered, and a different
one on every re-entry, rotating for a year. That is two questions, so two passes
over the same six emails:

  Pass A   ordered THIS category in the last day AND not sent this email in a
           year  ->  send it. This is "the one you ordered in".
  Pass B   not sent this email in a year  ->  send it. This is the rotation, and
           it is only reached when Pass A found nothing - because every Pass A
           email links straight past Pass B to the next stage.

Each pass needs its OWN six email nodes, so there are twelve. The first
attempt pointed both passes at the same six, which the API accepted with a 201
and then SILENTLY SPLICED EVERY EMAIL OUT: a send-email node cannot take more
than one inbound link, so Klaviyo removed the node and reconnected its inbound
links straight to its outbound target. The flow came back with 28 actions
instead of 34, no category email at all, and twelve splits whose true branch
went to the day-45 delay. Delays tolerate convergence - the day-45 delay has
thirteen inbound links - emails do not. Nothing in the response said so, which
is why main() now reads the flow back and fails on any missing email.

A YEAR IS THE ROTATION WINDOW, per Sebastiaan: `Received Email` count 0 in the
last 365 days, scoped to that message. The message ids do not exist until the
flow does, so the scoping is patched in a second pass - see
scripts/patch_post_rotation.py.

WHAT HAPPENS TO CATEGORIES WITH NO EMAIL. Photo products (27 of 411 categorised
orders) and Services have no email and are not meant to. They match no Pass A
condition, so Pass B sends them the first category they have not seen - which is
a real cross-sell rather than a generic filler. Once all six have been seen
inside a year the ring exits to day 45 with no nudge at all, because no generic
variant exists and inventing one here would be worse than sending nothing.

NO ORDER SINCE = `Placed Order` count EQUALS 1 since flow start, not 0. The
trigger is Placed Order, so the triggering order is itself inside the window;
zero would never be true and the flow would stop dead after email 1.

  python3 scripts/create_post_flow.py --dry-run
  python3 scripts/create_post_flow.py
"""
import argparse, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
import klav, offers                                            # noqa: E402

FROM_EMAIL, FROM_LABEL = "hello@helloprint.com", "HelloPrint"
TEST_BCC = "behavioral-email-tests@helloprint.com"
REC = os.path.join(ROOT, "data", "klaviyo-flow-post-messages.json")

M_PLACED   = "TuC7Z7"      # Placed Order      - the trigger
M_ORDPROD  = "XGuVCG"      # Ordered Product   - carries Categories
M_RECEIVED = "UxHsCy"      # Received Email    - the rotation window
M_CLICK    = "Y8zdDw"      # Clicked Email     - the reminder gate
M_CANCEL   = "YwbT5y"      # Cancelled Order
M_REFUND   = "Vtt9n3"      # Refunded Order

LOCALES = ["en-IE", "en-GB", "en-US", "nl-NL", "nl-BE", "fr-FR", "fr-BE",
           "de-DE", "es-ES", "it-IT", "sv-SE"]

# ring order from the proposal, with Stationery last: it did not appear once in
# 600 orders, but Sebastiaan wants it wired for later.
#   slug, the Categories values that mean it, subject, preview
RING = [
    ("commercial-print", ["Commercial Print"],
     "What are you promoting next?",
     "The print that puts your next campaign in front of people."),
    ("signage-outdoor", ["Signage & Outdoor"],
     "For the next event, or the front of the building?",
     "Signs, flags and banners, for a day out or a decade."),
    # Labels and Packaging arrive as SEPARATE top-level values (35 and 3 in 600
    # orders) and share one email. Two conditions in one group, which OR.
    ("labels-packaging", ["Labels", "Packaging"],
     "Running low on labels, or on bags?",
     "Labels, stickers and the packaging they go on."),
    ("clothing-textiles", ["Clothing & Textiles"],
     "Kitting out the team?",
     "Shirts and textiles with your logo on them."),
    ("corporate-gifts", ["Corporate Gifts"],
     "Something to hand out at the next event?",
     "Things that stay in use long after a flyer is in the bin."),
    ("stationery", ["Stationery"],
     "Running low on office stationery?",
     "The print that runs out quietly, and what to top up."),
]


def group(*conditions):
    """One condition_group. Conditions inside it OR; groups AND."""
    return {"conditions": list(conditions)}


def metric_count(metric, op, value, days=None, filters=None):
    tf = ({"type": "date", "operator": "flow-start"} if days is None
          else {"type": "date", "operator": "in-the-last",
                "quantity": days, "unit": "day"})
    c = {"type": "profile-metric", "metric_id": metric, "measurement": "count",
         "measurement_filter": {"type": "numeric", "operator": op,
                                "value": value},
         "timeframe_filter": tf}
    if filters:
        c["metric_filters"] = filters
    return c


def cat_filter(value):
    """metric_filters entry: this Ordered Product was in that category."""
    return [{"property": "Categories",
             "filter": {"type": "string", "operator": "contains",
                        "value": value}}]


def ordered_in(values):
    """A group: ordered ANY of these categories in the last day (conditions OR)."""
    return group(*[metric_count(M_ORDPROD, "greater-than-or-equal", 1,
                                days=1, filters=cat_filter(v))
                   for v in values])


def not_sent_in_a_year():
    """Placeholder - patched with the message id by patch_post_rotation.py."""
    return group(metric_count(M_RECEIVED, "equals", 0, days=365))


def no_further_order():
    return group(metric_count(M_PLACED, "equals", 1))


def delay(tid, nxt, days):
    return {"type": "time-delay", "temporary_id": tid, "links": {"next": nxt},
            "data": {"unit": "days", "value": days, "timezone": "profile"}}


def split(tid, groups, t, f):
    return {"type": "conditional-split", "temporary_id": tid,
            "links": {"next_if_true": t, "next_if_false": f},
            "data": {"profile_filter": {"condition_groups": list(groups)}}}


def email(tid, name, subject, preview, nxt=None):
    return {"type": "send-email", "temporary_id": tid,
            "links": ({"next": nxt} if nxt else {}),
            "data": {"status": "draft", "message": {
                "name": name, "subject_line": subject, "preview_text": preview,
                "from_email": FROM_EMAIL, "from_label": FROM_LABEL,
                "reply_to_email": FROM_EMAIL, "bcc_email": TEST_BCC,
                "smart_sending_enabled": True, "transactional": False,
                "add_tracking_params": False}}}


def build():
    a = []
    a.append(delay("d1", "e1", 18))
    a.append(email("e1", "POST-1 Review request · day 18",
                   "Would you tell other businesses how it went?",
                   "A minute on Trustpilot, if you can spare it.", "d2"))
    a.append(delay("d2", "sclick", 7))
    # DID NOT CLICK. Scoped to the whole flow rather than to email 1, and that
    # is not a compromise here: email 1 is the only email sent between flow
    # start and this point, so "no click since flow start" IS "did not click
    # email 1". It also needs no message id, so it works on the first pass.
    a.append(split("sclick", [group(metric_count(M_CLICK, "equals", 0))],
                   "e2", "d3"))
    a.append(email("e2", "POST-2 Review reminder · day 25",
                   "Nobody takes a printer's word for it",
                   "A line about how it went carries further than our own "
                   "marketing.", "d3"))
    a.append(delay("d3", "sord1", 7))                       # day 32
    a.append(split("sord1", [no_further_order()], "A-0", None))

    # ---- the ring. Pass A links past Pass B; Pass B falls through to day 45.
    # Twelve email nodes, not six: see the header on why they cannot converge.
    # Both nodes for a category take the SAME template, so the copy exists once
    # even though the flow graph needs two of them.
    for i, (slug, values, subj, pre) in enumerate(RING):
        nxt_a = "A-%d" % (i + 1) if i + 1 < len(RING) else "B-0"
        a.append(split("A-%d" % i, [ordered_in(values), not_sent_in_a_year()],
                       "eA-%s" % slug, nxt_a))
        a.append(email("eA-%s" % slug, "POST-3 %s · ordered · day 32" % slug,
                       subj, pre, "d4"))
    for i, (slug, values, subj, pre) in enumerate(RING):
        nxt_b = "B-%d" % (i + 1) if i + 1 < len(RING) else "d4"
        a.append(split("B-%d" % i, [not_sent_in_a_year()],
                       "eB-%s" % slug, nxt_b))
        a.append(email("eB-%s" % slug, "POST-3 %s · rotation · day 32" % slug,
                       subj, pre, "d4"))

    a.append(delay("d4", "sord2", 13))                      # day 45
    a.append(split("sord2", [no_further_order()], "e4", None))
    a.append(email("e4", "POST-4 A print expert, personally · day 45",
                   "How did the last job turn out?",
                   "A note from John, not a campaign.", "d5"))
    a.append(delay("d5", "sord3", 15))                      # day 60
    a.append(split("sord3", [no_further_order()], "e5", None))
    a.append(email("e5", "POST-5 10 percent off · day 60",
                   "Something coming up? This takes 10% off it",
                   "Your code is inside, and it is good for %d days."
                   % offers.POST_DAYS, "d6"))
    a.append(delay("d6", "sord4", 13))                      # day 73
    a.append(split("sord4", [no_further_order()], "e6", None))
    a.append(email("e6", "POST-6 Last day on the code · day 73",
                   "Today is the last day for your 10%",
                   "Last day on your code."))

    return {
        "name": "BEH-4 Post-Purchase · Placed Order",
        "definition": {
            "triggers": [{"type": "metric", "id": M_PLACED, "trigger_filter": {
                "condition_groups": [
                    # Connect is 30% of orders and gets its own flows later.
                    group({"type": "metric-property", "metric_id": M_PLACED,
                           "field": "ShopName",
                           "filter": {"type": "string",
                                      # "does-not-contain" is rejected;
                                      # the API spells it "not-contains"
                                      "operator": "not-contains",
                                      "value": "connect."}}),
                    # only the locales this flow is actually built for, so an
                    # unbuilt market cannot fall through to English
                    group(*[{"type": "metric-property", "metric_id": M_PLACED,
                             "field": "Locale",
                             "filter": {"type": "string", "operator": "equals",
                                        "value": l}} for l in LOCALES]),
                ]}}],
            "entry_action_id": "d1",
            "reentry_criteria": {"duration": 60, "unit": "day"},
            # Each its own group, so they AND. A cancelled or refunded order
            # must not be followed by "how did it go?".
            "profile_filter": {"condition_groups": [
                group(metric_count(M_CANCEL, "equals", 0)),
                group(metric_count(M_REFUND, "equals", 0)),
            ]},
            "actions": a,
        }}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    spec = build()
    acts = spec["definition"]["actions"]
    print("%s\n  %d actions: %d emails, %d splits, %d delays"
          % (spec["name"], len(acts),
             sum(1 for x in acts if x["type"] == "send-email"),
             sum(1 for x in acts if x["type"] == "conditional-split"),
             sum(1 for x in acts if x["type"] == "time-delay")))
    if args.dry_run:
        print(json.dumps(spec, ensure_ascii=False, indent=1)[:2000])
        return 0
    key, src = klav.load_key()
    st, res = klav.call(key, "POST", "/flows/", {"data": {"type": "flow",
                                                          "attributes": spec}})
    if st not in (200, 201):
        print("FAILED HTTP %s" % st)
        for e in klav.errors(res):
            print("   %s" % e)
        return 1
    fid = res["data"]["id"]
    print("created flow %s (draft)" % fid)
    io.open(REC, "w", encoding="utf-8").write(json.dumps(
        {"flow": spec["name"], "flow_id": fid,
         "note": "Created by scripts/create_post_flow.py. Rotation gates still "
                 "need scripts/patch_post_rotation.py to scope Received Email "
                 "to each message id."}, ensure_ascii=False, indent=1) + "\n")
    print("recorded in %s" % os.path.relpath(REC, ROOT))

    # READ IT BACK. A 201 is not proof the graph survived - the API silently
    # drops a send-email that has more than one inbound link.
    want = sorted(x["data"]["message"]["name"] for x in acts
                  if x["type"] == "send-email")
    st, res = klav.call(key, "GET",
                        "/flows/%s/?additional-fields[flow]=definition" % fid)
    stored = ((res.get("data") or {}).get("attributes") or {}).get("definition") or {}
    sacts = stored.get("actions") or []
    got = sorted((((x.get("data") or {}).get("message") or {}).get("name") or "")
                 for x in sacts if x.get("type") == "send-email")
    missing = [n for n in want if n not in got]
    print("\nverify: %d actions asked for, %d stored; %d emails asked for, "
          "%d stored" % (len(acts), len(sacts), len(want), len(got)))
    if missing:
        print("FAILED - the API dropped these emails:")
        for n in missing:
            print("   %s" % n)
        return 1
    print("every email survived the graph")
    return 0


if __name__ == "__main__":
    sys.exit(main())
