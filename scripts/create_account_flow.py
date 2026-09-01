#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BEH-1b Account created - the one service email for people who did not subscribe.

A NEW FLOW RATHER THAN A REUSE OF TEhf2p, and a correction: TEhf2p COULD have
been repurposed. Its trigger is already Completed Signup, and an action's links
are patchable, so pointing the first split's true branch at nothing and cutting
the chain after one email would have left exactly one email reachable. What it
would also leave is thirteen orphaned send-email actions sitting in the flow,
unreachable but present - in an account that already has five draft flows called
some version of "Welcome". A clean two-step flow is worth more than a reused id,
so TEhf2p should still be deleted.

WHAT THIS FLOW IS
    Completed Signup
      └─ wait 1 day        <- change to "wait until 9am" in the UI, see below
          └─ ordered since entering?
              ├─ YES  nothing. They bought; a nudge would be noise.
              └─ NO   ACC-1, the service message

TWO THINGS THIS SCRIPT CANNOT DO, both verified against the API:

  · THE MESSAGE MUST BE MARKED TRANSACTIONAL IN THE UI. The API accepts
    `transactional: true` and silently stores `false`. Until it is set, Klaviyo
    will skip every recipient in this segment, because none of them has a
    marketing consent record - so the flow would run and send nothing.

  · THE 9AM SEND TIME IS UI-ONLY. There is no time-of-day option on a flow
    delay in the API: `secondary_value` is minutes-only when the unit is hours,
    and `send_time` and `time_of_day` are both rejected as fields. The flow
    ships with a one-day delay, which sends at the same hour they signed up.
    Change the delay to "wait until 9am" in the UI. Account timezone is
    Europe/Amsterdam.

WHY THE FILTER IS "NO ORDER", NOT "NOT SUBSCRIBED". Klaviyo already enforces the
second one: a marketing message never reaches a profile without consent, and a
transactional one reaches everyone. So the audience is decided by the flag, not
by a filter - and adding a "not in the Newsletter list" condition would be a
second, weaker copy of a rule Klaviyo applies anyway. Someone who subscribes
between sign-up and the send simply gets BEH-1 Welcome as well, which is the
better email.
"""
import argparse, io, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import klav

M_SIGNUP = "WRvuHD"
M_ORDER = "TuC7Z7"
TEST_BCC = "behavioral-email-tests@helloprint.com"   # REMOVE BEFORE GO-LIVE
FROM_EMAIL = "hello@helloprint.com"
FROM_LABEL = "HelloPrint"
FLOW_NAME = "BEH-1b Account created · service message"
TEMPLATE = "BEH-1b ACC-1 Account created"
MSG_NAME = "ACC-1 Account created · next morning"
SOURCE_FILE = "account-01-klaviyo.html"

SUBJECT = "Your Helloprint account is ready"

MESSAGE_DEFAULTS = {
    "from_email": FROM_EMAIL, "from_label": FROM_LABEL,
    "reply_to_email": FROM_EMAIL, "bcc_email": TEST_BCC,
    "smart_sending_enabled": True,
    # SET THIS IN THE UI. The API stores False whatever is sent here.
    "transactional": True,
    "add_tracking_params": False,
}


def definition():
    return {
        "triggers": [{"type": "metric", "id": M_SIGNUP}],
        "entry_action_id": "d1",
        "reentry_criteria": {"duration": 1, "unit": "alltime"},
        "actions": [
            {"type": "time-delay", "temporary_id": "d1", "links": {"next": "s1"},
             "data": {"unit": "days", "value": 1, "timezone": "profile"}},
            {"type": "conditional-split", "temporary_id": "s1",
             "links": {"next_if_true": None, "next_if_false": "e1"},
             "data": {"profile_filter": {"condition_groups": [{"conditions": [
                {"type": "profile-metric", "metric_id": M_ORDER,
                 "measurement": "count",
                 "measurement_filter": {"type": "numeric",
                     "operator": "greater-than-or-equal", "value": 1},
                 "timeframe_filter": {"type": "date", "operator": "flow-start"}}]}]}}},
            {"type": "send-email", "temporary_id": "e1",
             "data": {"status": "draft", "message": dict(
                 MESSAGE_DEFAULTS, name=MSG_NAME, subject_line=SUBJECT,
                 preview_text="")}},
        ]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    key, src = klav.load_key()
    print("key from %s%s\n" % (src, "   DRY RUN" if a.dry_run else ""))

    html = io.open(os.path.join(ROOT, "proposals", SOURCE_FILE),
                   encoding="utf-8").read()

    have, url = {}, "/templates/?fields[template]=name&page[size]=10"
    while url:
        st, res = klav.call(key, "GET", url)
        for d in res.get("data") or []:
            have[(d.get("attributes") or {}).get("name")] = d["id"]
        nxt = (res.get("links") or {}).get("next") or ""
        url = nxt.split("a.klaviyo.com/api", 1)[-1] if nxt else None

    if a.dry_run:
        print("would %s template %r (%d KB) and create %r"
              % ("update" if TEMPLATE in have else "create", TEMPLATE,
                 len(html) // 1024, FLOW_NAME))
        return 0

    if TEMPLATE in have:
        tid = have[TEMPLATE]
        st, res = klav.call(key, "PATCH", "/templates/%s/" % tid, {"data": {
            "type": "template", "id": tid, "attributes": {"html": html}}})
        print("template %s updated (%d KB)" % (tid, len(html) // 1024))
    else:
        st, res = klav.call(key, "POST", "/templates/", {"data": {
            "type": "template", "attributes": {
                "name": TEMPLATE, "editor_type": "CODE", "html": html}}})
        if st not in (200, 201):
            sys.exit("template create failed: %s" % klav.errors(res))
        tid = res["data"]["id"]
        print("template %s created (%d KB)" % (tid, len(html) // 1024))

    st, res = klav.call(key, "POST", "/flows/", {"data": {"type": "flow",
        "attributes": {"name": FLOW_NAME, "definition": definition()}}})
    if st not in (200, 201):
        for e in klav.errors(res):
            print("  %s" % e)
        sys.exit("creating the flow failed")
    fid = res["data"]["id"]
    print("flow %s  https://www.klaviyo.com/flow/%s/edit" % (fid, fid))

    st, res = klav.call(key, "GET",
                        "/flows/%s/?additional-fields[flow]=definition" % fid)
    acts = ((res.get("data") or {}).get("attributes") or {}).get("definition")["actions"]
    act = next(x for x in acts if x["type"] == "send-email")
    mid = ((act.get("data") or {}).get("message") or {}).get("id")
    st, res = klav.call(key, "PATCH", "/flow-actions/%s/" % act["id"], {"data": {
        "type": "flow-action", "id": act["id"], "attributes": {"definition": {
            "type": "send-email", "id": act["id"], "links": {},
            "data": {"status": "draft", "message": dict(
                MESSAGE_DEFAULTS, id=mid, name=MSG_NAME,
                subject_line=SUBJECT, preview_text="",
                template_id=tid)}}}}})
    st, res = klav.call(key, "GET", "/flow-actions/%s/"
                        "?fields[flow-action]=definition.data.message" % act["id"])
    msg = ((((res.get("data") or {}).get("attributes") or {}).get("definition")
            or {}).get("data") or {}).get("message") or {}
    print("  %-38s copy %-8s transactional=%s  bcc %s"
          % (MSG_NAME, msg.get("template_id"), msg.get("transactional"),
             "set" if msg.get("bcc_email") == TEST_BCC else "MISSING"))
    if not msg.get("transactional"):
        print("\n  *** transactional came back False - the API ignores it. ***")
        print("  Set it in the Klaviyo UI or this email reaches nobody:")
        print("  every profile in this segment has no marketing consent record.")

    io.open(os.path.join(ROOT, "data", "klaviyo-flow-account-messages.json"), "w",
            encoding="utf-8").write(json.dumps({
        "flow": FLOW_NAME, "flow_id": fid, "status": "draft",
        "trigger": "Completed Signup (%s)" % M_SIGNUP,
        "created": "2026-09-01",
        "url": "https://www.klaviyo.com/flow/%s/edit" % fid,
        "ui_todo": ["mark the message transactional - the API cannot",
                    "change the 1-day delay to 'wait until 9am' - the API cannot"],
        "messages": [{"action": act["id"], "message": mid, "name": MSG_NAME,
                      "next": None, "template_saved": tid,
                      "template_live": msg.get("template_id"),
                      "template_name": TEMPLATE, "subject": SUBJECT,
                      "preview": ""}]}, ensure_ascii=False, indent=2) + "\n")
    print("\nrecorded in data/klaviyo-flow-account-messages.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
