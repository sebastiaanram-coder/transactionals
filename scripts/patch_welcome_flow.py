#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply the retention analysis to BEH-1 Welcome, in place. Flow TEhf2p, draft.

WHY IN PLACE. A flow's `definition` is NOT patchable - PATCH /flows/{id} accepts
`status` and nothing else, and rejects `definition` outright. Individual ACTIONS
are: PATCH /flow-actions/{id} takes a full definition, so a delay's value and a
split's conditions can both be changed. What cannot be done without rebuilding
the flow is ADDING an action, or setting the flow's trigger_filter or
profile_filter. That shapes everything below - see "what this cannot do".

===============================================================================
CHANGE 1 - THE MINUTE-ZERO CODE. The largest single margin exposure in the
programme: ~EUR 16k/month at pilot volume, EUR 77k at full rollout.

The flow entered, waited ZERO days, and then asked "has this person ordered
since the flow started?". At t=0 nobody has, so every single profile fell to the
FALSE branch and got WEL-1 WITH the 10% code - including the 46.7% of registrants
who order the same day, because sign-up happens INSIDE the checkout. The split
was not wrong; it was evaluated before it could ever be true.

THIS REVERSES AN EARLIER DECISION, DELIBERATELY. The zero delay was set on
purpose, with the reasoning "technically everyone gets the discount in the first
email, because nobody places an order in such a short timeframe". The retention
analysis measured that premise and it is false: 46.7% order the same day. The
delay comes back.

3 HOURS, NOT 6. The analysis sanctions 3-6 hours. Three is chosen because the
countdown copy is load-bearing: the code is valid 5 days FROM SIGN-UP, and email
1 says "expires in 5 days" in six languages. Every hour of delay makes that claim
optimistic by an hour. Three hours is 2.5% of the window rather than 5%, and the
open-checkout condition below - not the length of the delay - is what actually
catches the in-checkout cohort, who order within minutes.

THE OTHER SANCTIONED OPTION WAS REJECTED, and this is the reasoning. The analysis
also offers "send email 1 immediately without the code and introduce the code in
email 2". That is cheaper to build and catches every same-day buyer rather than
a 3-hour slice - but the sign-up form now promises "Ja, ik wil 10% korting op mijn
eerste bestelling", so an email 1 that does not mention the code contradicts the
promise the customer just accepted. That is a complaint, not a saving.

CHANGE 2 - OPEN CHECKOUT. A profile with a checkout open in the last 12 hours is
routed to the no-code branch. This is what makes a 3-hour delay enough: sign-up
happens inside checkout, so Started Checkout has ALREADY fired when the flow
starts, and it is caught whether or not the order has completed by hour three.

"IN THE LAST 12 HOURS", NOT "SINCE FLOW START". The checkout PRECEDES the
sign-up, so a since-flow-start window would not see it - the same boundary
problem that made the original split a no-op.

It is added to all four splits, not just the first. A profile in checkout on day
1, 3 or 5 is in BEH-3 Abandoned Order, which carries its own offer; two paid
levers landing on one person is the collision the analysis flags twice.

CHANGE 3 - CONNECT AND THE OTHER B2B STOREFRONTS. Connect is 28.7% of Placed
Order events in this account. Those buyers must never receive a consumer
discount ladder. Expressed as "did this person sign up from a store whose name
contains connect.?" - which works as a split condition because a profile-metric
condition accepts metric_filters on the event's own properties.

MEASURED, NOT ASSUMED: Completed Signup carries exactly one usable property,
`store`, and every Connect storefront in this account contains "connect."
(connect.helloprint.nl, .co.uk, .be, .es, connect.fr.helloprint.be). The window
is 30 days, not flow-start, so the condition still sees the sign-up on day 5.

===============================================================================
WHAT THIS CANNOT DO, and what it costs to finish.

1. FULL EXCLUSION of Connect needs the flow's trigger_filter, which is not
   patchable. What is done here ROUTES Connect to the no-code branch, so no
   discount can leak, but a Connect buyer would still receive four consumer
   emails. Finishing it is a one-field edit in the Klaviyo UI (trigger filter:
   store not-contains "connect." - the operator is `not-contains`, verified) or
   a flow rebuild. Not urgent: Completed Signup is one day old, has 75 events,
   and every one is drukzo.nl - there are no Connect sign-ups yet.

2. THE 10% HOLDOUT cannot be built here at all. There is no random-split action
   type in the flow API, and a census of all 29 flows in the account found only
   send-email, time-delay, conditional-split, send-sms, send-whatsapp,
   send-internal-alert and update-profile. A randomised holdout needs either
   Klaviyo's own experiment feature in the UI, or a random bucket written onto
   the profile by the data team, which a conditional split could then read.

  python3 scripts/patch_welcome_flow.py --dry-run
  python3 scripts/patch_welcome_flow.py
"""
import argparse, io, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
import klav

FLOW = "TEhf2p"
M_ORDER = "TuC7Z7"
M_CHECKOUT = "T3uGk6"
M_SIGNUP = "WRvuHD"

ENTRY_DELAY = {"unit": "hours", "value": 3, "timezone": "profile"}
# 21 hours, so email 2 still lands at EXACTLY day 1 and the "4 days left"
# countdown stays true. The three hours are taken out of this interval rather
# than pushing every later email three hours late, which would put email 4 -
# "Last day for your 10%" - three hours PAST the code's expiry.
FIRST_GAP = {"unit": "hours", "value": 21, "timezone": "profile"}

OPEN_CHECKOUT = {
    "type": "profile-metric", "metric_id": M_CHECKOUT, "measurement": "count",
    "measurement_filter": {"type": "numeric", "operator": "greater-than-or-equal",
                           "value": 1},
    "timeframe_filter": {"type": "date", "operator": "in-the-last",
                         "quantity": 12, "unit": "hour"}}

CONNECT_SIGNUP = {
    "type": "profile-metric", "metric_id": M_SIGNUP, "measurement": "count",
    "measurement_filter": {"type": "numeric", "operator": "greater-than-or-equal",
                           "value": 1},
    "timeframe_filter": {"type": "date", "operator": "in-the-last",
                         "quantity": 30, "unit": "day"},
    "metric_filters": [{"property": "store",
                        "filter": {"type": "string", "operator": "contains",
                                   "value": "connect."}}]}


def fetch(key):
    st, res = klav.call(key, "GET",
                        "/flows/%s/?additional-fields[flow]=definition" % FLOW)
    if st != 200:
        sys.exit("reading %s failed: %s" % (FLOW, klav.errors(res)))
    at = (res.get("data") or {}).get("attributes") or {}
    return at, (at.get("definition") or {})


def patch_action(key, act, data, dry):
    body = {"data": {"type": "flow-action", "id": act["id"], "attributes": {
        "definition": {"type": act["type"], "id": act["id"],
                       "links": act.get("links") or {}, "data": data}}}}
    if dry:
        return True, "would patch"
    st, res = klav.call(key, "PATCH", "/flow-actions/%s/" % act["id"], body)
    time.sleep(0.35)
    return st == 200, ("HTTP %s %s" % (st, "; ".join(klav.errors(res))[:120])
                       if st != 200 else "ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    key, src = klav.load_key()
    print("key from %s%s\n" % (src, "   DRY RUN" if a.dry_run else ""))

    at, d = fetch(key)
    if at.get("status") != "draft":
        sys.exit("%s is %r, not draft - refusing to edit a live flow"
                 % (FLOW, at.get("status")))
    acts = {x["id"]: x for x in d.get("actions") or []}
    entry = acts.get(d.get("entry_action_id"))
    if not entry or entry["type"] != "time-delay":
        sys.exit("expected the entry action to be the pre-split delay, got %r"
                 % (entry or {}).get("type"))

    problems = 0

    # 1. the entry delay
    ok, msg = patch_action(key, entry, ENTRY_DELAY, a.dry_run)
    print("entry delay  %s %s -> %s %s   %s"
          % (entry["id"], entry["data"].get("value"), ENTRY_DELAY["value"],
             ENTRY_DELAY["unit"], msg))
    problems += 0 if ok else 1

    # 2. the WEL-1 -> WEL-2 gap, so email 2 still lands at day 1
    #    found by walking from the entry split's FALSE branch: email, then delay
    split1 = acts.get((entry.get("links") or {}).get("next"))
    first_email = acts.get((split1.get("links") or {}).get("next_if_false"))
    gap = acts.get((first_email.get("links") or {}).get("next"))
    if not gap or gap["type"] != "time-delay":
        print("could not find the WEL-1 -> WEL-2 delay; not retimed")
        problems += 1
    else:
        ok, msg = patch_action(key, gap, FIRST_GAP, a.dry_run)
        print("first gap    %s %s %s -> %s %s   %s"
              % (gap["id"], gap["data"].get("value"), gap["data"].get("unit"),
                 FIRST_GAP["value"], FIRST_GAP["unit"], msg))
        problems += 0 if ok else 1

    # 3. every conditional split gains the two new OR conditions
    for act in d.get("actions") or []:
        if act["type"] != "conditional-split":
            continue
        groups = ((act["data"].get("profile_filter") or {}).get("condition_groups")
                  or [{"conditions": []}])
        conds = list(groups[0].get("conditions") or [])
        have = {(c.get("metric_id"), bool(c.get("metric_filters"))) for c in conds}
        added = []
        for cond, label in ((OPEN_CHECKOUT, "open-checkout"),
                            (CONNECT_SIGNUP, "connect-signup")):
            if (cond["metric_id"], bool(cond.get("metric_filters"))) in have:
                continue
            conds.append(cond)
            added.append(label)
        if not added:
            print("split        %s already carries both conditions" % act["id"])
            continue
        # ONE group, so the conditions are OR'd - Klaviyo's semantics are the
        # reverse of the usual convention. "ordered OR in checkout OR came from
        # Connect" all route to the no-code branch, which is what TRUE means here.
        data = {"profile_filter": {"condition_groups": [{"conditions": conds}]}}
        ok, msg = patch_action(key, act, data, a.dry_run)
        print("split        %s + %-28s %s" % (act["id"], ",".join(added), msg))
        problems += 0 if ok else 1

    print("\nproblems: %d" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
