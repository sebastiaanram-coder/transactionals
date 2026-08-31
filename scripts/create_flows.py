#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create BEH-2 Browse Abandonment and BEH-3 Abandoned Order in Klaviyo, in DRAFT.

Run once. It creates 9 templates and 2 flows, then records every id into
data/klaviyo-flow-browse-messages.json and data/klaviyo-flow-order-messages.json
so scripts/push_templates.py can redeploy content afterwards without any manual
import, exactly as it does for BEH-1.

  python3 scripts/create_flows.py --dry-run     # print the payloads, touch nothing
  python3 scripts/create_flows.py               # create
  python3 scripts/create_flows.py --only BEH-2  # one flow

===============================================================================
KLAVIYO'S FILTER LOGIC IS THE REVERSE OF THE USUAL CONVENTION. Read this before
editing any filter below.

  conditions INSIDE one condition_group are combined with OR
  condition_groups are combined with AND

That is Klaviyo's documented segment semantics and the flow definition reuses
the same `Filter` resource. It is backwards from almost every other rules engine,
and getting it backwards is not a harmless mistake in either direction:

  - put "is one of six markets" in six GROUPS and the flow never fires at all
  - put "has not ordered" and "has not added to cart" in ONE group and the filter
    becomes "has not ordered OR has not added to cart", which is true for almost
    everybody - so the flow would mail people who had already bought

So: one group per independent requirement, and alternatives listed as several
conditions inside a single group. Every group below is commented with which it is.

===============================================================================
SCHEMA, ESTABLISHED BY PROBING THE API (each shape below returned 201, and the
throwaway flows were deleted):

  trigger_filter        {"condition_groups":[{"conditions":[
                          {"type":"metric-property","metric_id":M,"field":F,
                           "filter":{"type":"string","operator":"contains",...}}]}]}
                        The field is `field`, NOT `property`; `property` is
                        rejected as not valid for MetricPropertyCondition.
  string operators      "contains" and "starts-with" only. "startswith",
                        "begins-with" and "matches-regex" are all rejected, and
                        there is no list/any operator - so "one of N" has to be
                        N conditions in one group.
  flow profile_filter   profile-metric with measurement/measurement_filter/
                        timeframe_filter, as BEH-1 already uses.
  a value split         conditional-split takes ONLY `profile_filter` -
                        trigger_filter, event_filter and metric_filter are all
                        rejected on ConditionalBranchActionData. So the cart
                        value is expressed as measurement "sum" of the trigger
                        metric since flow start. See THE SPLIT below.
  timeframe, relative   {"type":"date","operator":"in-the-last","quantity":7,
                         "unit":"day"}   ("relative-date" is not a type)
  reentry_criteria      {"duration":N,"unit":"day"}  - "days" is rejected

===============================================================================
WHICH MARKETS EACH FLOW MAY FIRE IN, and why they differ.

{% catalog %} HARD-FAILS: an unknown id returns 400 and the WHOLE email fails to
render, not just that block. So a market may only be let in if every id the
email can look up exists in its feed. Verified by fetching each id, 2026-08-31:

  BEH-2 constructs ids it was never given. browse-01's cross-sell builds
  `event.ProductID|slice:":3"|add:"<slug>"`, so all NINE slugs it can reach
  (flyera4, flyera6, flyerdl, canvafoldedleaflets, businesscardsstandard,
  posters, rollupbannersv2, stickers, letterheads) must exist per market:

     IE GB NL BE FR DE   all nine present   -> allowed
     ES                  3 missing (canvafoldedleaflets, businesscardsstandard,
                         rollupbannersv2)   -> excluded until the feed carries them
     SE                  3 missing (canvafoldedleaflets, rollupbannersv2,
                         letterheads)       -> excluded
     IT                  no catalog feed at all -> excluded

  This supersedes the proposal's "IE- or GB- only", which was written before the
  other feeds were checked. NL alone is 14% of checkouts and is where BEH-1 went
  live, so restricting to IE and GB would have aimed these flows at the two
  markets the programme is NOT launching in. IE is 1.5% of Started Checkout.

  BEH-3 constructs nothing - every lookup is `it.ProductID`, an item the customer
  just configured, so it exists by construction. It therefore needs only a feed
  to exist at all and a locale the email is actually built for:

     it-IT   IT has NO catalog feed (IT-flyerseco, IT-flyera5, IT-standardflyers
             and IT-adesivi all 404) -> excluded, or every Italian cart email
             fails to render
     en-US   5.1% of Started Checkout events. No US feed (US-flyera5 404s) and
             no en-US branch in any template, so a US reader would be shown the
             en-GB fallback in pounds -> excluded

===============================================================================
HOSTS. Measured over 800 production Started Checkout events:

  www.helloprint.com          85.0%
  connect.helloprint.{nl,fr,be,es,co.uk,it}  14.3%   B2B storefront
  v4.staging.helloprint.dev    0.6%   staging writing to the PRODUCTION account

Connect buyers must not get consumer lifecycle mail, and a staging URL must
never reach a customer, so both flows filter on the host. Staging is the reason
the host filter cannot be skipped even though the locale filter looks sufficient:
a staging URL carries a real locale segment (/it-it/checkout/details), so only
the host separates it.
"""
import argparse, io, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import klav
import offers

TEST_BCC = "behavioral-email-tests@helloprint.com"   # REMOVE BEFORE GO-LIVE
FROM_EMAIL = "hello@helloprint.com"
FROM_LABEL = "HelloPrint"

M_VIEWED = "WX8EsF"
M_CHECKOUT = "T3uGk6"
M_ADDED = "SyZEtt"
M_ORDER = "TuC7Z7"
M_TICKET = "SyMxGj"

BROWSE_MARKETS = ["IE", "GB", "NL", "BE", "FR", "DE"]
ORDER_LOCALES = ["/en-ie/", "/en-gb/", "/nl-nl/", "/nl-be/",
                 "/fr-fr/", "/fr-be/", "/de-de/", "/es-es/"]

# How long a support conversation suppresses lifecycle mail. Klaviyo's own
# abandoned-cart guidance: someone mid-conversation with support should not be
# receiving "you left something behind". There is no "ticket is open" signal in
# the account - only the Ticket Created metric - so this is the implementable
# approximation, not the literal condition.
TICKET_DAYS = 7


# --------------------------------------------------------------- filter helpers
def cond_str(metric, field, operator, value):
    return {"type": "metric-property", "metric_id": metric, "field": field,
            "filter": {"type": "string", "operator": operator, "value": value}}


def group(*conditions):
    """One condition_group. Conditions inside it are OR'd - see the header."""
    return {"conditions": list(conditions)}


def never_did(metric, since_flow_start=True, days=None):
    """A group meaning "count of this metric is zero". Its own group = AND."""
    tf = ({"type": "date", "operator": "flow-start"} if since_flow_start
          else {"type": "date", "operator": "in-the-last",
                "quantity": days, "unit": "day"})
    return group({"type": "profile-metric", "metric_id": metric,
                  "measurement": "count",
                  "measurement_filter": {"type": "numeric", "operator": "equals",
                                         "value": 0},
                  "timeframe_filter": tf})


def delay(tid, nxt, unit, value):
    return {"type": "time-delay", "temporary_id": tid, "links": {"next": nxt},
            "data": {"unit": unit, "value": value, "timezone": "profile"}}


def email(tid, name, subject, preview, nxt=None):
    return {"type": "send-email", "temporary_id": tid,
            "links": ({"next": nxt} if nxt else {}),
            "data": {"status": "draft", "message": {
                "name": name, "subject_line": subject, "preview_text": preview,
                "from_email": FROM_EMAIL, "from_label": FROM_LABEL,
                "reply_to_email": FROM_EMAIL, "bcc_email": TEST_BCC,
                "smart_sending_enabled": True, "transactional": False,
                "add_tracking_params": False}}}


# ------------------------------------------------------------------ the templates
# name -> the built file it is loaded from. The name is what appears in the
# Klaviyo template list, so it carries the flow and the message it belongs to.
TEMPLATES = [
    ("BEH-2 BRW-1 The one you were looking at", "browse-01-klaviyo.html"),
    ("BEH-2 BRW-2 You do not need the artwork yet", "browse-02-klaviyo.html"),
    ("BEH-2 BRW-3 Tell us the job, we will price it", "browse-03-klaviyo.html"),
    ("BEH-3 ORD-1H Basket restored, high value", "order-01-high-klaviyo.html"),
    ("BEH-3 ORD-1L Basket restored, low value", "order-01-low-klaviyo.html"),
    ("BEH-3 ORD-2H Print expert, high value", "order-02-high-klaviyo.html"),
    ("BEH-3 ORD-2L 10 percent off, low value", "order-02-low-klaviyo.html"),
    ("BEH-3 ORD-3H Expert plus 10 percent, high value", "order-03-high-klaviyo.html"),
    ("BEH-3 ORD-3L 25 percent capped, low value", "order-03-low-klaviyo.html"),
]

# Which template each message node takes. temporary_id -> template name.
ATTACH = {
    "b1": "BEH-2 BRW-1 The one you were looking at",
    "b2": "BEH-2 BRW-2 You do not need the artwork yet",
    "b3": "BEH-2 BRW-3 Tell us the job, we will price it",
    "h1": "BEH-3 ORD-1H Basket restored, high value",
    "l1": "BEH-3 ORD-1L Basket restored, low value",
    "h2": "BEH-3 ORD-2H Print expert, high value",
    "l2": "BEH-3 ORD-2L 10 percent off, low value",
    "h3": "BEH-3 ORD-3H Expert plus 10 percent, high value",
    "l3": "BEH-3 ORD-3L 25 percent capped, low value",
}


# ------------------------------------------------------------------ BEH-2 Browse
# Trigger  Viewed Product, production host, one of the six covered markets.
# Cadence  +1h, +24h, +3d. Three emails against a page view, not RFB's five: a
#          product view is a weak signal and this flow's volume feeds the same
#          sending reputation as everything else.
# Re-entry 14 days. Print is a considered purchase, so a genuine second look
#          weeks later deserves the email again.
BROWSE = {
    "name": "BEH-2 Browse Abandonment · Viewed Product",
    "definition": {
        "triggers": [{"type": "metric", "id": M_VIEWED, "trigger_filter": {
            "condition_groups": [
                # GROUP 1: production storefront only. Excludes Connect (B2B)
                # and staging. One condition, so nothing to OR.
                group(cond_str(M_VIEWED, "URL", "contains", "www.helloprint.com")),
                # GROUP 2: ONE OF the six markets whose feed carries every id
                # the cross-sell can build. Six conditions in ONE group = OR.
                group(*[cond_str(M_VIEWED, "ProductID", "starts-with", mk + "-")
                        for mk in BROWSE_MARKETS]),
            ]}}],
        "entry_action_id": "d1",
        "reentry_criteria": {"duration": 14, "unit": "day"},
        # Each requirement is its OWN group, so they AND. In one group they
        # would OR, and "has not ordered OR has not added to cart" is true of
        # nearly everyone - the filter would stop filtering.
        "profile_filter": {"condition_groups": [
            # Added to Cart hands the person over to BEH-3 cleanly: they are no
            # longer browsing, they have a basket, and BEH-3 is the flow that
            # can show it.
            never_did(M_ADDED),
            never_did(M_ORDER),
            never_did(M_TICKET, since_flow_start=False, days=TICKET_DAYS),
        ]},
        "actions": [
            delay("d1", "b1", "hours", 1),
            email("b1", "BRW-1 The one you were looking at · +1h",
                  "The print you were looking at",
                  "Delivery and VAT are already in the number you saw. Change the "
                  "quantity and the price moves with it.", "d2"),
            # 23, not 24: the clock starts at the view, and email 1 already spent
            # an hour of it. Same reasoning for the 2-day gap to email 3.
            delay("d2", "b2", "hours", 23),
            email("b2", "BRW-2 You do not need the artwork yet · +24h",
                  "You do not need the finished artwork yet",
                  "We check every file for free before it prints. Or our designers "
                  "can make it for you.", "d3"),
            delay("d3", "b3", "days", 2),
            email("b3", "BRW-3 Tell us the job, we will price it · +3d",
                  "Need a price you can forward?",
                  "An odd spec, a tight deadline, or someone else's signature. Our "
                  "quotation team comes back within 24 hours."),
        ]},
}


# ----------------------------------------------------------- BEH-3 Abandoned Order
#
# THE SPLIT. The two branches need the cart value, and a conditional-split accepts
# only a profile_filter - every event-side key (trigger_filter, event_filter,
# metric_filter) is rejected outright by the API. So the value is expressed as
#
#     sum of Started Checkout $value, since this flow started, >= 150
#
# WHY THAT IS THE RIGHT READING, and where it differs from "the triggering cart".
# The window opens when the flow starts, which is the triggering event, so on the
# common case - one checkout, then nothing - the sum IS the cart that triggered
# the flow. It diverges only if the same person starts checkout again inside the
# first hour, and then the sum is the total of both. Two 80 carts would read as
# 160 and take the high branch: the high branch offers a person and holds the
# discount back, so the failure mode is a more expensive email, not a margin leak.
#
# WHY THE SPLIT SITS AFTER THE 1-HOUR DELAY and not at entry. "Since flow start"
# evaluated at t=0 is a boundary case - the triggering event may not yet be inside
# its own window, which would read every cart as 0 and send every customer down
# the low branch, silently. BEH-1 already proved that a split placed after a delay
# reads flow-start events correctly, so the delay goes first. It costs nothing:
# email 1 is due at +1h anyway.
#
# THE 150 IS THE SAME NUMBER IN BOTH CURRENCIES and is not a conversion (GBP 150
# is about EUR 176). Both distributions independently put 24% of carts above 150,
# carrying 56% of GB value and 68% of EUR value.
SPLIT = offers.ORDER_SPLIT

# Re-entry 30 days, and this one is a commercial control rather than a courtesy.
# The low branch reaches 25% off within 72 hours of a single abandoned checkout,
# which is a discoverable pattern: configure something cheap, abandon it, wait
# three days. Monthly re-entry still serves a genuine repeat abandoner - the
# median cart is 60 and most people abandon once - while capping that loop at
# twelve times a year instead of once a week.
ORDER_REENTRY_DAYS = 30

ORDER = {
    "name": "BEH-3 Abandoned Order · Started Checkout",
    "definition": {
        "triggers": [{"type": "metric", "id": M_CHECKOUT, "trigger_filter": {
            "condition_groups": [
                # GROUP 1: production host. Excludes Connect (14.3% of events)
                # and staging (0.6%). Staging is why this cannot be dropped in
                # favour of the locale filter alone - a staging URL carries a
                # real locale segment.
                group(cond_str(M_CHECKOUT, "CheckoutURL", "contains",
                               "www.helloprint.com")),
                # GROUP 2: ONE OF the eight locales this flow can render. Eight
                # conditions in ONE group = OR. Excludes it-IT (no catalog feed
                # at all, so every Italian cart email would fail to render) and
                # en-US (no feed, and no en-US branch in any template).
                group(*[cond_str(M_CHECKOUT, "CheckoutURL", "contains", loc)
                        for loc in ORDER_LOCALES]),
            ]}}],
        "entry_action_id": "d1",
        "reentry_criteria": {"duration": ORDER_REENTRY_DAYS, "unit": "day"},
        # One group per requirement, so they AND. No "not Added to Cart" here:
        # this flow is FOR people who have a basket.
        "profile_filter": {"condition_groups": [
            never_did(M_ORDER),
            never_did(M_TICKET, since_flow_start=False, days=TICKET_DAYS),
        ]},
        "actions": [
            delay("d1", "sp", "hours", 1),
            {"type": "conditional-split", "temporary_id": "sp",
             "links": {"next_if_true": "h1", "next_if_false": "l1"},
             "data": {"profile_filter": {"condition_groups": [group(
                 {"type": "profile-metric", "metric_id": M_CHECKOUT,
                  "measurement": "sum",
                  "measurement_filter": {"type": "numeric",
                                         "operator": "greater-than-or-equal",
                                         "value": SPLIT},
                  "timeframe_filter": {"type": "date", "operator": "flow-start"}}
             )]}}},

            # HIGH VALUE, ~24% of carts and ~56-68% of the value. The blocker on
            # a basket this size is confidence or sign-off rather than price, and
            # a person answers that more cheaply than a discount does - so the
            # expert stays the headline even in email 3 and the code sits under it.
            email("h1", "ORD-1H Basket restored · high · +1h",
                  "Left something behind?",
                  "Every line exactly as you configured it, and a link straight "
                  "back into your basket.", "hd2"),
            delay("hd2", "h2", "hours", 23),
            email("h2", "ORD-2H Print expert · high · +24h",
                  "Want a print expert to look at it first?",
                  "Someone checks the spec, confirms the delivery date, and can "
                  "invoice instead of taking a card.", "hd3"),
            delay("hd3", "h3", "hours", 48),
            email("h3", "ORD-3H Expert plus 10 percent · high · +72h",
                  "Still happy to go through this with you",
                  "The offer of a print expert stands, and there is %d%% off for "
                  "the next %d hours." % (offers.ORDER_PERCENT_10,
                                          offers.ORDER_HOURS_10)),

            # LOW VALUE, ~76% of carts. Self-serving, price-sensitive buyer, so
            # the incentive does the work and can go hard at the end.
            email("l1", "ORD-1L Basket restored · low · +1h",
                  "Left something behind?",
                  "Every line exactly as you configured it, and a link straight "
                  "back into your basket.", "ld2"),
            delay("ld2", "l2", "hours", 23),
            email("l2", "ORD-2L 10 percent off · low · +24h",
                  "%d%% off, for the next %d hours"
                  % (offers.ORDER_PERCENT_10, offers.ORDER_HOURS_10),
                  "Change the quantity, watch the price move, and order in three "
                  "clicks.", "ld3"),
            delay("ld3", "l3", "hours", 48),
            email("l3", "ORD-3L 25 percent capped · low · +72h",
                  "%d%% off, for the next %d hours"
                  % (offers.ORDER_PERCENT_25, offers.ORDER_HOURS_25),
                  "Last email in this sequence. The deadline is the message."),
        ]},
}

FLOWS = [("BEH-2", BROWSE, "klaviyo-flow-browse-messages.json"),
         ("BEH-3", ORDER, "klaviyo-flow-order-messages.json")]


# ------------------------------------------------------------------------ do it
def existing_templates(key):
    """{name: id} for every saved template, so a re-run does not duplicate."""
    out, url = {}, "/templates/?fields[template]=name&page[size]=10"
    while url:
        st, res = klav.call(key, "GET", url)
        if st != 200:
            sys.exit("listing templates failed: %s" % klav.errors(res))
        for d in res.get("data") or []:
            out[(d.get("attributes") or {}).get("name")] = d["id"]
        nxt = (res.get("links") or {}).get("next") or ""
        url = nxt.split("a.klaviyo.com/api", 1)[-1] if nxt else None
    return out


def create_templates(key, dry):
    """Create the 9 masters, or reuse one that already carries the name."""
    have = {} if dry else existing_templates(key)
    ids = {}
    for name, fname in TEMPLATES:
        path = os.path.join(ROOT, "proposals", fname)
        html = io.open(path, encoding="utf-8").read()
        if name in have:
            ids[name] = have[name]
            print("  reuse  %-50s %s  (%d KB)" % (name[:50], have[name], len(html)//1024))
            continue
        if dry:
            print("  would create %-44s from %s (%d KB)" % (name[:44], fname, len(html)//1024))
            ids[name] = "DRY-" + name[:6]
            continue
        st, res = klav.call(key, "POST", "/templates/", {"data": {
            "type": "template", "attributes": {
                "name": name, "editor_type": "CODE", "html": html}}})
        if st not in (200, 201):
            sys.exit("  create %s failed: %s" % (name, klav.errors(res)))
        ids[name] = res["data"]["id"]
        print("  create %-50s %s  (%d KB)" % (name[:50], ids[name], len(html)//1024))
        time.sleep(0.4)
    return ids


def create_flow(key, spec, dry):
    if dry:
        print(json.dumps(spec, ensure_ascii=False, indent=1)[:1400])
        return None
    st, res = klav.call(key, "POST", "/flows/", {"data": {
        "type": "flow", "attributes": spec}})
    if st not in (200, 201):
        print("  FAILED HTTP %s" % st)
        for e in klav.errors(res):
            print("    %s" % e)
        return None
    return res["data"]["id"]


def read_actions(key, fid):
    """[(action_id, message_id, name, next_action_id, temporary_id-guess)]

    The create call takes temporary_ids and hands back real ones, so the mapping
    from a temporary_id to a real action has to be recovered. It is recovered by
    MESSAGE NAME, which is unique per flow and is the one field this script sets
    deliberately - not by position, which the API is under no obligation to keep.
    """
    st, res = klav.call(key, "GET", "/flows/%s/?additional-fields[flow]=definition" % fid)
    if st != 200:
        sys.exit("reading back flow %s failed: %s" % (fid, klav.errors(res)))
    d = ((res.get("data") or {}).get("attributes") or {}).get("definition") or {}
    rows = []
    for a in d.get("actions") or []:
        if a.get("type") != "send-email":
            continue
        msg = ((a.get("data") or {}).get("message") or {})
        rows.append({"action": a.get("id"), "message": msg.get("id"),
                     "name": msg.get("name"),
                     "next": (a.get("links") or {}).get("next")})
    return rows, d


def attach(key, rows, tpl_ids, name_to_temp, dry):
    """Point each message at its master. Klaviyo clones it; the clone sends."""
    out = []
    for r in rows:
        temp = name_to_temp.get(r["name"])
        tname = ATTACH.get(temp)
        tid = tpl_ids.get(tname)
        if not tid:
            print("    %-46s NO TEMPLATE (temp=%r)" % (r["name"][:46], temp))
            continue
        if dry:
            print("    would attach %-40s -> %s" % (r["name"][:40], tname))
            continue
        st, res = klav.call(key, "PATCH", "/flow-actions/%s/" % r["action"], {
            "data": {"type": "flow-action", "id": r["action"], "attributes": {
                "definition": {"type": "send-email", "id": r["action"],
                    "links": ({"next": r["next"]} if r["next"] else {}),
                    "data": {"status": "draft", "message": dict(
                        MESSAGE_DEFAULTS, id=r["message"], name=r["name"],
                        subject_line=r["subject"], preview_text=r["preview"],
                        template_id=tid)}}}}})
        if st != 200:
            print("    %-46s HTTP %s %s" % (r["name"][:46], st,
                                            "; ".join(klav.errors(res))[:150]))
            continue
        st, res = klav.call(key, "GET", "/flow-actions/%s/"
                            "?fields[flow-action]=definition.data.message" % r["action"])
        m = ((((res.get("data") or {}).get("attributes") or {}).get("definition")
              or {}).get("data") or {}).get("message") or {}
        r["template_saved"] = tid
        r["template_live"] = m.get("template_id")
        r["template_name"] = tname
        print("    %-46s copy %-8s subj %s  bcc %s"
              % (r["name"][:46], m.get("template_id"),
                 "kept" if m.get("subject_line") == r["subject"] else "CHANGED",
                 "set" if m.get("bcc_email") == TEST_BCC else "MISSING"))
        out.append(r)
        time.sleep(0.4)
    return out


MESSAGE_DEFAULTS = {
    "from_email": FROM_EMAIL, "from_label": FROM_LABEL,
    "reply_to_email": FROM_EMAIL, "bcc_email": TEST_BCC,
    "smart_sending_enabled": True, "transactional": False,
    "add_tracking_params": False,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    key, src = klav.load_key()
    print("key loaded from %s%s\n" % (src, "   DRY RUN" if a.dry_run else ""))

    print("templates")
    tpl_ids = create_templates(key, a.dry_run)
    print()

    for tag, spec, outfile in FLOWS:
        if a.only and a.only.lower() not in tag.lower():
            continue
        print("%s  %s" % (tag, spec["name"]))
        # temporary_id <-> message name, so the read-back can be mapped
        name_to_temp, subj, prev = {}, {}, {}
        for act in spec["definition"]["actions"]:
            if act["type"] != "send-email":
                continue
            m = act["data"]["message"]
            name_to_temp[m["name"]] = act["temporary_id"]
            subj[m["name"]] = m["subject_line"]
            prev[m["name"]] = m["preview_text"]

        fid = create_flow(key, spec, a.dry_run)
        if not fid:
            continue
        print("  flow %s  https://www.klaviyo.com/flow/%s/edit" % (fid, fid))
        rows, defn = read_actions(key, fid)
        for r in rows:
            r["subject"] = subj.get(r["name"], "")
            r["preview"] = prev.get(r["name"], "")
        done = attach(key, rows, tpl_ids, name_to_temp, a.dry_run)

        if not a.dry_run:
            io.open(os.path.join(ROOT, "data", outfile), "w", encoding="utf-8").write(
                json.dumps({
                    "flow": spec["name"], "flow_id": fid, "status": "draft",
                    "created": "2026-08-31",
                    "url": "https://www.klaviyo.com/flow/%s/edit" % fid,
                    "note": ("Klaviyo clones a saved template per flow message on "
                             "attach. 'template_saved' is the library master, which "
                             "scripts/push_templates.py patches; 'template_live' is "
                             "the per-message copy the flow actually sends. A copy "
                             "is NOT patchable - /api/templates/{id} returns 404 for "
                             "it - so the master is pushed and the message "
                             "re-attached, which mints a fresh copy. Copy ids "
                             "therefore CHANGE on every push."),
                    "messages": done}, ensure_ascii=False, indent=2) + "\n")
            print("  recorded %d messages in data/%s" % (len(done), outfile))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
