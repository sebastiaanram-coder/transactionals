#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rewrite the Welcome Flow section of the overview from the current truth.

WHY THIS EXISTS. The section was hand-assembled and had drifted badly: it pointed
at RFB's old flow RXBWV9, described a list trigger and an "Ireland + United
Kingdom only (pilot market)" audience, and named HELLO10. Worse, the four
per-email "What this email is for" boxes were scrambled - email 1 carried email
4's goal, and email 4 carried an ABANDONED ORDER goal about recovering a basket
in the first hour, which has nothing to do with Welcome at all.

WHAT IT WRITES. Flow facts, and for each of the four has-not-ordered emails the
timing, subject, preview text, purpose and a link to its Klaviyo template.

IT LINKS THE MASTERS, NOT THE LIVE COPIES. Every push re-clones the per-message
copies with new ids, so a document linking those is stale the next time anyone
runs push_templates.py. The eight masters keep their ids.

URL FORMATS WERE PROBED, NOT GUESSED. Against a deliberate control:
  /flow/TEhf2p/edit      302 -> login   valid
  /templates/UCriVp      302 -> login   valid
  /flows/TEhf2p          404            wrong
  /email-template/...    404            wrong
  /definitely-not-real   404            the control
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "_lib"))
import offers  # noqa: E402

DOC = os.path.join(ROOT, "behavioural-email-overview.html")
FLOW = "TEhf2p"
FLOW_URL = "https://www.klaviyo.com/flow/%s/edit" % FLOW
TPL = "https://www.klaviyo.com/templates/%s"

# has-not-ordered email -> (timing, subject, preview, purpose, master template)
EMAILS = [
 ("Day 0 &middot; 3 hours after sign-up",
  "Welcome to Helloprint, and your 10% code",
  "Your 10% code is inside, and you have 5 days to use it.",
  "Get the code in front of them while the sign-up is still fresh - but not "
  "before the order they are already placing. Sign-up is account creation inside "
  "the checkout, and 46.7% of registrants order the same day, so an immediate "
  "send discounts an order in flight. The three-hour delay plus the "
  "open-checkout condition moves those buyers to the no-discount branch instead: "
  "about EUR 16k of margin a month at pilot volume.",
  "UCriVp", "BEH-1 WEL-1 Welcome + 10%"),
 ("Day 1",
  "Your 10% is waiting, and 4 days left to use it",
  "Printed closer to you by a certified B Corp. Your 10% has 4 days left.",
  "Give a reason to trust the platform - local partners, B Corp, the range - "
  "while keeping the code and its countdown in view.",
  "WRbYfy", "BEH-1 WEL-2 Behind the print"),
 ("Day 3",
  "Only 2 days left on your 10%",
  "Rated 4.5 from 34,000+ reviews. Only 2 days left to use your 10%.",
  "Proof from real Trustpilot reviews, with the countdown now leading the "
  "subject line rather than trailing it.",
  "XuNgUx", "BEH-1 WEL-3 Rated excellent"),
 ("Day 5",
  "Last day for your 10%",
  "Artwork or just an idea, we take it from there. Last day for your 10%.",
  "Final call on the code, and a route for anyone who stalled because getting "
  "the artwork right felt like the hard part.",
  "Ykhktb", "BEH-1 WEL-4 Send it over"),
]

FACTS = {
 "Trigger": (
   "<strong>Completed Signup</strong><br><span class=\"muted\">Fires on account "
   "creation, which happens inside the checkout. The event carries "
   "<code>store: drukzo.nl</code> or <code>drukzo.be</code> - the legacy names "
   "for Helloprint in NL and nl-BE, rebranded on the front end in November 2025. "
   "Consumer storefronts only today: the metric is new, and all 75 events so far "
   "are drukzo.nl. A sign-up from a <code>connect.*</code> storefront is routed "
   "to the no-discount branch, so a B2B buyer can never receive the consumer "
   "discount ladder.</span>"),
 "Audience": (
   "Everyone who completes sign-up, in all nine locales.<br><span class=\"muted\">"
   "Before every email the flow asks three questions, and any one of them moves "
   "the reader to the no-discount branch: has this person ordered since entering "
   "the flow, do they have a checkout open from the last 12 hours, and did they "
   "sign up on a Connect storefront. They still finish the series, without the "
   "offer. Language comes from the profile's native <code>locale</code>, with "
   "en-GB as the fallback.</span>"),
 "Cadence &amp; re-entry": (
   "Has not ordered: day 0 (+3h), 1, 3, 5<br>Has ordered: day 0 (+3h), 5, 10, 15"
   "<br><span class=\"muted\">The slower ordered cadence keeps this clear of "
   "Post-Purchase, which starts at day 18. Re-entry: once only.</span>"),
 # Concatenated, not %-formatted: these strings contain "10%" and "%s" would
 # not be the only thing the % operator tried to read.
 "Incentive": (
   "10% off the first order &middot; code <strong>" + offers.WELCOME_CODE +
   "</strong> &middot; up to " + str(offers.WELCOME_CAP) +
   " in the market's own currency &middot; expires " + str(offers.WELCOME_DAYS) +
   " days after sign-up &middot; one use per customer<br>"
   "<span class=\"muted\">Confirmed against the coupon on 2026-08-31. The "
   "no-discount branch carries none of it - no code, no countdown, no "
   "terms.</span>"),
}


def section(head):
    i = head.index("Welcome Flow", head.index("Rebuild tracker"))
    j = head.index("Browse Abandonment", i)
    return i, j


def main():
    s = io.open(DOC, encoding="utf-8").read()
    cut = s.index("const PREVIEWS = ")
    head, tail = s[:cut], s[cut:]
    i, j = section(head)
    sec = head[i:j]
    before = len(sec)
    notes = []

    # --- the flow link in the subtitle
    new_sub = ('4 emails &middot; Flow <a href="%s" target="_blank" '
               'rel="noopener">%s' % (FLOW_URL, FLOW))
    sec, n = re.subn(r'4 emails &middot; Flow <a href="[^"]*" target="_blank" '
                     r'rel="noopener">[A-Za-z0-9]+', new_sub, sec, count=1)
    notes.append("flow link -> %s" % FLOW if n else "!! flow link not found")

    # --- the four fact boxes
    for label, body in FACTS.items():
        pat = (r'(<div class="lbl">(?:<span class="ic ">.*?</span>)?%s</div>)<p>.*?</p>'
               % re.escape(label))
        sec, n = re.subn(pat, lambda m: m.group(1) + "<p>" + body + "</p>",
                         sec, count=1, flags=re.S)
        notes.append(("fact %s" % label) if n else "!! fact %s not found" % label)

    # --- the four mail rows
    rows = list(re.finditer(r'class="mail-row[^"]*">', sec))
    if len(rows) != 4:
        print("expected 4 mail rows, found %d - nothing written" % len(rows))
        return 1
    for idx in range(3, -1, -1):        # last first, so offsets stay valid
        start = rows[idx].end()
        end = rows[idx + 1].start() if idx + 1 < len(rows) else len(sec)
        blk = sec[start:end]
        when, subj, prev, why, tid, tname = EMAILS[idx]
        blk, a = re.subn(r'(class="when">).*?(</span>)',
                         lambda m: m.group(1) + when + m.group(2), blk, count=1, flags=re.S)
        blk, b = re.subn(r'(class="subj">).*?(</h3>)',
                         lambda m: m.group(1) + subj + m.group(2), blk, count=1, flags=re.S)
        blk, c = re.subn(r'(class="prev">).*?(</p>)',
                         lambda m: m.group(1) + prev + m.group(2), blk, count=1, flags=re.S)
        blk, e = re.subn(
            r'(<div class="lbl">What this email is for</div>)<p>.*?</p>',
            lambda m: m.group(1) + "<p>" + why + "</p>", blk, count=1, flags=re.S)
        # a template link, right after the badge
        link = ('<p class="prev"><a href="%s" target="_blank" rel="noopener">'
                'Klaviyo template: %s</a></p>' % (TPL % tid, tname))
        if "Klaviyo template:" in blk:
            blk = re.sub(r'<p class="prev"><a href="[^"]*"[^>]*>Klaviyo template:[^<]*</a></p>',
                         link, blk, count=1)
            f = 1
        else:
            blk, f = re.subn(r'(<span class="badge badge-green">.*?</span>)',
                             lambda m: m.group(1) + link, blk, count=1, flags=re.S)
        notes.append("email %d: when=%d subj=%d prev=%d why=%d tpl=%d"
                     % (idx + 1, a, b, c, e, f))
        sec = sec[:start] + blk + sec[end:]

    out = head[:i] + sec + head[j:] + tail
    io.open(DOC, "w", encoding="utf-8").write(out)
    for x in notes:
        print("  " + x)
    print("\nWelcome section %d -> %d chars; doc %d KB"
          % (before, len(sec), len(out) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
