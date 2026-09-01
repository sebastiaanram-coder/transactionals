#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rebuild BEH-1 Welcome as a SUBSCRIBER flow: the 10% is what the tick-box buys.

WHY A REBUILD AND NOT A PATCH. Three of the four changes live on the flow's
`definition`, and `PATCH /flows/{id}` accepts `status` and nothing else - it
rejects `definition`, `name` and `profile_filter` outright. Individual actions
are patchable, which is how the retention-analysis changes went in without a
rebuild, but you cannot change a flow's TRIGGER, set a flow-level filter, or
remove an action. All three are needed here.

===============================================================================
WHAT CHANGED, AND WHY

1. THE TRIGGER IS THE NEWSLETTER LIST, NOT THE SIGN-UP EVENT.

   The offer is now "10% for ticking subscribe", so subscribing IS the entry
   condition - someone who does not tick it should never see this flow at all.
   Triggering on the list expresses that directly.

   MEASURED, NOT ASSUMED: the tick-box already writes to the Newsletter list
   (VAh232) - 1 of the 14 most recent sign-ups is in it. Marketing consent on
   the profile is NOT usable: `subscriptions.email.marketing.consent` is unset
   on all 14, so list membership is the only reliable signal.

   WHY NOT "Completed Signup + a filter on list membership": a race. The
   tick-box write and the sign-up event are independent, and a flow filter is
   evaluated at entry - if the event lands first, the filter sees no membership
   and the person never enters. A list trigger cannot have that bug.

   SIDE EFFECT WORTH KNOWING: anyone who subscribes by another route - footer
   form, pop-up - now also enters. That is consistent with the offer (they
   ticked a box promising 10%) but it is wider than "account sign-up".

2. EMAIL 1 IS THE ENTRY ACTION, IMMEDIATE, WITH THE CODE FOR EVERYONE.

   This deliberately gives back the 3-hour delay and the open-checkout
   suppression added yesterday, and the reason is that the retention analysis's
   objection no longer applies in the same way. That objection was that the code
   discounted an order already in flight. Now the code is the CONSIDERATION for
   subscribing: withholding it from someone who ticked the box and then bought
   the same day is not a saving, it is a broken promise.

   The exposure also shrinks by roughly the subscribe rate. The analysis costed
   the leak across ALL registrants; only subscribers now enter, which is about
   7% of sign-ups today.

3. THE SPLIT MOVES TO DAY 1, AND ONLY DECIDES WHETHER TO REMIND.

   There is no split before email 1 any more, so the four "ordered at S1"
   messages disappear with it - nobody can have ordered before an email that
   goes out on entry. Ten messages instead of fourteen, and the WEL-1B template
   (the no-discount welcome) is no longer used by this flow.

   From day 1 on, each split asks one question - has this person ordered since
   entering the flow - and routes to a variant that does not mention the code.

   THE OPEN-CHECKOUT CONDITION IS GONE FROM THESE SPLITS, on purpose. It was
   there to stop a SECOND paid lever landing on someone mid-checkout. But the
   code is already in their hands from email 1, so a reminder costs nothing that
   has not already been committed - suppressing it would only make the email less
   useful. What still matters is whether they ordered, which is what is asked.

4. CONNECT IS EXCLUDED AT THE FLOW LEVEL, not routed.

   28.7% of Placed Order events in this account are Connect, and those buyers
   must never receive a consumer discount ladder. Yesterday's version could only
   route them to a no-code branch because a trigger filter was unreachable; a
   rebuild can exclude them outright. Expressed as "no Completed Signup from a
   store containing connect. in the last 30 days" - every Connect storefront in
   the account matches that (connect.helloprint.nl, .co.uk, .be, .es,
   connect.fr.helloprint.be).

THE CADENCES ARE UNCHANGED and so is every countdown claim: emails at day 0, 1,
3 and 5 on the has-not-ordered path, and the slower 5-day gaps on the ordered
path, which keep it clear of Post-Purchase at day 18.

  python3 scripts/create_welcome_v2.py --dry-run
  python3 scripts/create_welcome_v2.py
"""
import argparse, io, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import klav

NEWSLETTER_LIST = "VAh232"
M_ORDER = "TuC7Z7"
M_SIGNUP = "WRvuHD"
TEST_BCC = "behavioral-email-tests@helloprint.com"   # REMOVE BEFORE GO-LIVE
FROM_EMAIL = "hello@helloprint.com"
FROM_LABEL = "HelloPrint"
FLOW_NAME = "BEH-1 Welcome · Newsletter subscribers"

MESSAGE_DEFAULTS = {
    "from_email": FROM_EMAIL, "from_label": FROM_LABEL,
    "reply_to_email": FROM_EMAIL, "bcc_email": TEST_BCC,
    "smart_sending_enabled": True, "transactional": False,
    "add_tracking_params": False,
}

# message name -> the Klaviyo template that sends it
ATTACH = {
    "WEL-1 Welcome · day 0":            "BEH-1 WEL-1 Welcome + 10%",
    "WEL-2 Behind the print · day 1":   "BEH-1 WEL-2 Behind the print",
    "WEL-3 Rated excellent · day 3":    "BEH-1 WEL-3 Rated excellent",
    "WEL-4 Send it over · day 5":       "BEH-1 WEL-4 Send it over",
    "WEL-2B Behind the print · ord@S2": "BEH-1 WEL-2B Behind the print, no discount",
    "WEL-3B Rated excellent · ord@S2":  "BEH-1 WEL-3B Rated excellent, no discount",
    "WEL-3B Rated excellent · ord@S3":  "BEH-1 WEL-3B Rated excellent, no discount",
    "WEL-4B Send it over · ord@S2":     "BEH-1 WEL-4B Send it over, no discount",
    "WEL-4B Send it over · ord@S3":     "BEH-1 WEL-4B Send it over, no discount",
    "WEL-4B Send it over · ord@S4":     "BEH-1 WEL-4B Send it over, no discount",
}

# the old message name each new one inherits its subject and nine translations
# from. Only WEL-1 is renamed - it is no longer "(3h)".
INHERIT = dict((n, n) for n in ATTACH)
INHERIT["WEL-1 Welcome · day 0"] = "WEL-1 Welcome · day 0 (3h)"


def ordered_since_entry():
    return {"condition_groups": [{"conditions": [
        {"type": "profile-metric", "metric_id": M_ORDER, "measurement": "count",
         "measurement_filter": {"type": "numeric",
                                "operator": "greater-than-or-equal", "value": 1},
         "timeframe_filter": {"type": "date", "operator": "flow-start"}}]}]}


def not_connect():
    """No sign-up from a Connect storefront. One group, so it simply ANDs."""
    return {"condition_groups": [{"conditions": [
        {"type": "profile-metric", "metric_id": M_SIGNUP, "measurement": "count",
         "measurement_filter": {"type": "numeric", "operator": "equals", "value": 0},
         "timeframe_filter": {"type": "date", "operator": "in-the-last",
                              "quantity": 30, "unit": "day"},
         "metric_filters": [{"property": "store",
             "filter": {"type": "string", "operator": "contains",
                        "value": "connect."}}]}]}]}


def email(tid, name, nxt=None):
    return {"type": "send-email", "temporary_id": tid,
            "links": ({"next": nxt} if nxt else {}),
            "data": {"status": "draft", "message": dict(
                MESSAGE_DEFAULTS, name=name, subject_line="placeholder",
                preview_text="")}}


def delay(tid, nxt, unit, value):
    return {"type": "time-delay", "temporary_id": tid, "links": {"next": nxt},
            "data": {"unit": unit, "value": value, "timezone": "profile"}}


def split(tid, t, f):
    return {"type": "conditional-split", "temporary_id": tid,
            "links": {"next_if_true": t, "next_if_false": f},
            "data": {"profile_filter": ordered_since_entry()}}


def definition():
    return {
        "triggers": [{"type": "list", "id": NEWSLETTER_LIST}],
        "entry_action_id": "w1",
        # 365 DAYS, NOT "NEVER", AND THAT IS FORCED BY THE API. On a
        # list-triggered flow {"duration": 1, "unit": "alltime"} - the form the
        # old metric-triggered flow used for "never" - is accepted with a 201
        # and then stored as null. A concrete duration is stored faithfully,
        # verified by reading it back.
        #
        # NULL IS NOT GOOD ENOUGH HERE. This flow hands out a discount on
        # joining a list, so "what happens if someone unsubscribes and
        # resubscribes" has to have a stated answer rather than a default
        # nobody has checked. At most once a year is that answer.
        "reentry_criteria": {"duration": 365, "unit": "day"},
        "profile_filter": not_connect(),
        "actions": [
            email("w1", "WEL-1 Welcome · day 0", "d1"),
            delay("d1", "s2", "days", 1),
            split("s2", "o2", "w2"),

            # ordered by day 1: three reminders with no offer in them, on the
            # slower cadence that keeps this clear of Post-Purchase at day 18
            email("o2", "WEL-2B Behind the print · ord@S2", "od2"),
            delay("od2", "o3", "days", 5),
            email("o3", "WEL-3B Rated excellent · ord@S2", "od3"),
            delay("od3", "o4", "days", 5),
            email("o4", "WEL-4B Send it over · ord@S2"),

            # has not ordered: the countdown continues
            email("w2", "WEL-2 Behind the print · day 1", "d2"),
            delay("d2", "s3", "days", 2),
            split("s3", "p3", "w3"),
            email("p3", "WEL-3B Rated excellent · ord@S3", "pd3"),
            delay("pd3", "p4", "days", 5),
            email("p4", "WEL-4B Send it over · ord@S3"),

            email("w3", "WEL-3 Rated excellent · day 3", "d3"),
            delay("d3", "s4", "days", 2),
            split("s4", "q4", "w4"),
            email("q4", "WEL-4B Send it over · ord@S4"),
            email("w4", "WEL-4 Send it over · day 5"),
        ]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    key, src = klav.load_key()
    print("key from %s%s\n" % (src, "   DRY RUN" if a.dry_run else ""))

    # the templates, by name, from the library
    have, url = {}, "/templates/?fields[template]=name&page[size]=10"
    while url:
        st, res = klav.call(key, "GET", url)
        for d in res.get("data") or []:
            have[(d.get("attributes") or {}).get("name")] = d["id"]
        nxt = (res.get("links") or {}).get("next") or ""
        url = nxt.split("a.klaviyo.com/api", 1)[-1] if nxt else None
    missing = sorted(set(ATTACH.values()) - set(have))
    if missing:
        sys.exit("these templates are not in Klaviyo: %s" % missing)
    print("templates found: %d" % len(set(ATTACH.values())))

    old_subj = json.load(io.open(os.path.join(ROOT, "proposals",
        "welcome-flow-subjects.json"), encoding="utf-8"))
    by_name = {v["name"]: v for v in old_subj.values()}
    # RESOLVE BY THE NEW NAME FIRST. This script REWRITES the subjects file it
    # reads, so on a re-run the entries are already keyed by the new names and
    # looking only for the old one fails on a file that is perfectly correct.
    resolved = {}
    for new_name, old_name in INHERIT.items():
        got = by_name.get(new_name) or by_name.get(old_name)
        if not got:
            sys.exit("no subject recorded for %r (nor its predecessor %r)"
                     % (new_name, old_name))
        resolved[new_name] = got

    defn = definition()
    if a.dry_run:
        print(json.dumps(defn, ensure_ascii=False, indent=1)[:1200])
        print("\n... %d actions, %d emails"
              % (len(defn["actions"]),
                 sum(1 for x in defn["actions"] if x["type"] == "send-email")))
        return 0

    st, res = klav.call(key, "POST", "/flows/",
                        {"data": {"type": "flow",
                                  "attributes": {"name": FLOW_NAME, "definition": defn}}})
    if st not in (200, 201):
        for e in klav.errors(res):
            print("  %s" % e)
        sys.exit("creating the flow failed")
    fid = res["data"]["id"]
    print("flow %s  https://www.klaviyo.com/flow/%s/edit\n" % (fid, fid))

    st, res = klav.call(key, "GET",
                        "/flows/%s/?additional-fields[flow]=definition" % fid)
    acts = ((res.get("data") or {}).get("attributes") or {}).get("definition")["actions"]
    rows = []
    for act in acts:
        if act["type"] != "send-email":
            continue
        m = (act.get("data") or {}).get("message") or {}
        rows.append({"action": act["id"], "message": m.get("id"),
                     "name": m.get("name"),
                     "next": (act.get("links") or {}).get("next")})

    out, subj_out = [], {}
    for r in rows:
        tname = ATTACH.get(r["name"])
        tid = have.get(tname)
        inherited = resolved[r["name"]]
        source = inherited["source"]
        st, res = klav.call(key, "PATCH", "/flow-actions/%s/" % r["action"], {
            "data": {"type": "flow-action", "id": r["action"], "attributes": {
                "definition": {"type": "send-email", "id": r["action"],
                    "links": ({"next": r["next"]} if r["next"] else {}),
                    "data": {"status": "draft", "message": dict(
                        MESSAGE_DEFAULTS, id=r["message"], name=r["name"],
                        subject_line=source, preview_text="",
                        template_id=tid)}}}}})
        if st != 200:
            print("  %-36s attach HTTP %s %s"
                  % (r["name"][:36], st, "; ".join(klav.errors(res))[:110]))
            continue
        st, res = klav.call(key, "GET", "/flow-actions/%s/"
                            "?fields[flow-action]=definition.data.message" % r["action"])
        msg = ((((res.get("data") or {}).get("attributes") or {}).get("definition")
                or {}).get("data") or {}).get("message") or {}
        r.update(template_saved=tid, template_live=msg.get("template_id"),
                 template_name=tname, subject=source, preview="")
        out.append(r)
        subj_out[r["message"]] = {
            "name": r["name"], "scope": inherited["scope"],
            "key": inherited["key"], "source": source,
            "translations": inherited["translations"]}
        print("  %-36s copy %-8s subj kept  bcc %s"
              % (r["name"][:36], msg.get("template_id"),
                 "set" if msg.get("bcc_email") == TEST_BCC else "MISSING"))
        time.sleep(0.35)

    io.open(os.path.join(ROOT, "data", "klaviyo-flow-welcome-messages.json"), "w",
            encoding="utf-8").write(json.dumps({
        "flow": FLOW_NAME, "flow_id": fid, "status": "draft",
        "trigger": "joined list %s (Newsletter)" % NEWSLETTER_LIST,
        "created": "2026-09-01",
        "url": "https://www.klaviyo.com/flow/%s/edit" % fid,
        "supersedes": "TEhf2p, which triggered on Completed Signup and split "
                      "before email 1. Delete it in the UI - a flow cannot be "
                      "renamed or re-triggered through the API.",
        "note": "Klaviyo clones a saved template per flow message on attach. "
                "'template_saved' is the library master, which "
                "scripts/push_templates.py patches; 'template_live' is the "
                "per-message copy the flow actually sends. A copy is NOT "
                "patchable, so the master is pushed and the message re-attached, "
                "which mints a fresh copy. Copy ids change on every push.",
        "messages": out}, ensure_ascii=False, indent=2) + "\n")
    io.open(os.path.join(ROOT, "proposals", "welcome-flow-subjects.json"), "w",
            encoding="utf-8").write(
        json.dumps(subj_out, ensure_ascii=False, indent=2) + "\n")
    print("\nrecorded %d messages; subjects re-keyed to the new message ids" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
