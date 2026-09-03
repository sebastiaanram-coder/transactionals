#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render all 14 BEH-1 Welcome messages in all nine locales and check the claims.

Written for the retiming that the retention analysis forced. The flow's copy is
load-bearing on timing: the code is valid five days from sign-up, and the emails
count it down - "expires in 5 days", "4 days left", "2 days left", "last day" -
in six languages across nine locales. Moving email 1 by three hours could have
pushed email 4 past the expiry it announces, so the send offsets and the copy
have to be checked against each other, not just eyeballed.

WHAT IS ASSERTED
  · every message renders in every locale (a 400 here is a market that gets
    nothing, and {% catalog %} hard-fails)
  · <html lang> is the reader's locale
  · the DISCOUNT emails claim the right number of days left for their send day
  · the no-discount B variants claim no expiry at all - they are the branch for
    someone who has already ordered, and a countdown there is a live offer
  · the Welcome code appears only in the discount emails, and no other flow's
    code appears anywhere
"""
import io, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
import klav, offers

LOCALES = ["en-IE", "en-GB", "en-US", "nl-NL", "nl-BE", "fr-FR", "fr-BE", "de-DE",
           "es-ES", "it-IT", "sv-SE"]

# The words each language counts days in. GERMAN NEEDS BOTH FORMS: the terms say
# "in 5 Tagen" (dative) and the countdown says "Noch 2 Tage" (nominative), both
# correct German. A dictionary with only "Tagen" reported the German countdown as
# missing, which is a bug in the check and not in the email.
DAYWORDS = {"en-IE": ["days"], "en-GB": ["days"], "en-US": ["days"],
            "nl-NL": ["dagen"], "nl-BE": ["dagen"],
            "fr-FR": ["jours"], "fr-BE": ["jours"],
            "de-DE": ["Tagen", "Tage"],
            "es-ES": ["días"], "it-IT": ["giorni"],
            "sv-SE": ["dagar", "dag"]}

# THE CODE'S TOTAL VALIDITY IS ALSO A DAY NUMBER. Every discount email states it
# in the offer terms ("the code expires 5 days after sign-up"), so 5 is allowed
# alongside whatever the countdown says. An earlier version of this demanded the
# countdown number and NOTHING else, and reported all eight locales of emails 2
# and 3 as wrong when the terms line was the only thing it had found.
TOTAL_VALIDITY = 5

# message-name prefix -> the countdown it must state for its own send day, from
# the flow as patched: WEL-1 at T+3h, WEL-2 at day 1, WEL-3 at day 3, WEL-4 at
# day 5. WEL-4's countdown is "Last day", which carries no number, so it asserts
# only that nothing OTHER than the validity appears.
# WEL-1B is gone: email 1 now goes out on entry with the code for everyone, so
# there is no split before it and nobody can have ordered first.
EXPECT = {"WEL-1 ": 5, "WEL-2 ": 4, "WEL-3 ": 2, "WEL-4 ": None,
          "WEL-2B": "nocode", "WEL-3B": "nocode", "WEL-4B": "nocode"}

# How the offer shows up on welcome-01's product tiles. None of these contains
# "10%" or the code, which is how a visibly discounted no-code variant passed
# every check for a week: a struck-out list price, the discounted price beside
# it, and a per-tile countdown.
TILE_OFFER = ('class="hp-w1-tiwas"', 'class="hp-w1-tinow"',
              'class="hp-w1-tiexp"')


def main():
    key, _ = klav.load_key()
    msgs = json.load(io.open(os.path.join(ROOT, "data",
        "klaviyo-flow-welcome-messages.json"), encoding="utf-8"))["messages"]
    fails, n = [], 0
    for m in msgs:
        name = m["name"]
        pref = next((p for p in EXPECT if name.startswith(p)), None)
        want_days = EXPECT.get(pref)
        tid = m.get("template_live")
        print("%-34s copy %-8s" % (name[:34], tid), end="", flush=True)
        for loc in LOCALES:
            html, res = klav.render(key, tid, loc)
            n += 1
            if not html:
                msg = "; ".join(klav.errors(res))[:110]
                fails.append("%s @ %s: render failed %s" % (name, loc, msg))
                print("  %s:FAIL" % loc, end="", flush=True)
                continue
            bad = []
            if "{%" in html or "{{" in html:
                bad.append("unrendered Django")
            if 'lang="%s"' % loc not in html:
                got = re.search(r'<html lang="([^"]*)"', html)
                bad.append("lang=%r" % (got.group(1) if got else None))
            vis = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
            vis = re.sub(r"<[^>]+>", " ", vis)
            vis = vis.replace("&nbsp;", " ").replace("&middot;", "·")
            vis = re.sub(r"\s+", " ", vis)
            # every "N <dayword>" claim in this locale
            found = set()
            for w in DAYWORDS[loc]:
                found |= set(int(x) for x in re.findall(
                    r"(\d+)\s*%s\b" % re.escape(w), vis))
            wants_code = pref in ("WEL-1 ", "WEL-2 ", "WEL-3 ", "WEL-4 ")
            if want_days == "nocode":
                # The no-code branch must carry no offer at all. Day numbers are
                # NOT the test here - welcome-03 quotes a Trustpilot review that
                # says "delivered in 2 days", which is a customer's words about
                # delivery, not a countdown. The offer's own markers are.
                for marker in TILE_OFFER + ('10%',):
                    if marker in html:
                        bad.append("no-code variant still carries %r" % marker)
            elif want_days is None:
                extra = found - {TOTAL_VALIDITY}
                if extra:
                    bad.append("claims %s; only the %d-day validity is expected"
                               % (sorted(extra), TOTAL_VALIDITY))
            else:
                if want_days not in found:
                    bad.append("does not state its %d-day countdown (found %s)"
                               % (want_days, sorted(found)))
                extra = found - {want_days, TOTAL_VALIDITY}
                if extra:
                    bad.append("also claims %s" % sorted(extra))
            code_in = offers.WELCOME_CODE in html
            if wants_code and not code_in:
                bad.append("missing the welcome code")
            if not wants_code and code_in:
                bad.append("carries the welcome code on the ordered branch")
            for other in offers.NOT_WELCOME:
                if other in html:
                    bad.append("carries %s from another flow" % other)
            if bad:
                fails.append("%s @ %s: %s" % (name, loc, "; ".join(bad)))
            print("  %s%s" % (loc, "" if not bad else "!"), end="", flush=True)
            time.sleep(0.2)
        print()
    print("\n%d renders checked, %d problems" % (n, len(fails)))
    for f in fails:
        print("  FAIL %s" % f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
