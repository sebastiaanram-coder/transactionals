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
# FROM THE RECORD, NOT A LITERAL. The flow was rebuilt when it moved to a
# Newsletter-list trigger, and a flow id cannot be preserved across a rebuild -
# the definition is not patchable, so the trigger and the entry action can only
# change by creating a new flow.
FLOW = json.load(io.open(os.path.join(ROOT, "data",
    "klaviyo-flow-welcome-messages.json"), encoding="utf-8"))["flow_id"]
FLOW_URL = "https://www.klaviyo.com/flow/%s/edit" % FLOW
TPL = "https://www.klaviyo.com/templates/%s"

# has-not-ordered email -> (timing, subject, preview, purpose, master template)
# WHY THESE THREE EXTRA FIELDS EXIST.
#
# build_overview.py holds the editorial metadata keyed by TEMPLATE ID, and those
# ids are placeholders inherited from the pre-rebuild document. The refresh below
# rewrote the subject, preheader and goal around them but not these, so every
# Welcome email displayed ANOTHER email's rationale: email 1 said "Day 5, last
# call", email 2 "Day 3, leads with reviews", and email 4 carried an ABANDONED
# ORDER note about recovering a high-value basket. Owning them here means the
# section is right after a refresh instead of right only after a full rebuild.
#
#   (journey, variant note, [(bullet lead, bullet rest), ...])
EXTRA = [
 ("Day 0 of the Welcome flow, immediately on subscribing.",
  "The only Welcome email everyone gets, and the one that carries the code.",
  [("The code, up front.", "It is what the tick-box bought.")]),
 ("Day 1 of the Welcome flow.",
  "Reasons to trust the platform, with the code and its countdown still in view.",
  [("Platform over product.", "Who prints it, and how close to you.")]),
 ("Day 3 of the Welcome flow.",
  "The only Welcome email that leads with reviews rather than product.",
  [("Proof, then the code.", "Reviews first, deadline second.")]),
 ("Day 5, the day the code and the flow both end.",
  "No product grid at all - a route to a person instead.",
  [("A person, not a page.", "For anyone who did not order from the first three.")]),
]

EMAILS = [
 ("Day 0 &middot; immediately on subscribing",
  "Welcome to Helloprint, and your 10% code",
  "Your 10% code is inside, and you have 5 days to use it.",
  "The code is what the tick-box buys, so it goes out on entry and every "
  "subscriber gets it. That is a deliberate reversal of the three-hour delay "
  "added for the retention analysis: withholding the code from someone who "
  "ticked the box and then ordered the same day is not a saving, it is a broken "
  "promise. The exposure shrinks with the audience instead - only subscribers "
  "enter, about 7% of sign-ups today.",
  "UCriVp", "BEH-1 WEL-1 Welcome + 10%"),
 ("Day 1",
  "Your 10% is waiting &mdash; 4 days left",
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
   "<strong>Joined the Newsletter list</strong><br><span class=\"muted\">The "
   "sign-up form's subscribe tick-box writes to this list, so subscribing IS the "
   "entry condition - someone who does not tick it never enters. Measured: 1 of "
   "the 14 most recent sign-ups is in the list, and marketing consent on the "
   "profile is unset on all of them, so list membership is the only reliable "
   "signal. Anyone who subscribes by another route - footer, pop-up - also "
   "enters, which is consistent with the offer. A sign-up from a "
   "<code>connect.*</code> storefront is excluded from the flow "
   "entirely.</span>"),
 "Audience": (
   "Newsletter subscribers, in all nine locales.<br><span class=\"muted\">"
   "Email 1 goes to everyone with the code. From day 1 on, each split asks one "
   "question - has this person ordered since entering the flow - and routes them "
   "to a variant that does not mention the code. They still finish the series, "
   "without the reminder. Language comes from the profile's native "
   "<code>locale</code>, with en-GB as the fallback.</span>"),
 "Cadence &amp; re-entry": (
   "Has not ordered: day 0, 1, 3, 5<br>Ordered mid-sequence: the remaining "
   "emails move to 5-day gaps"
   "<br><span class=\"muted\">The slower cadence after an order keeps this clear of "
   "Post-Purchase, which starts at day 18. Re-entry: at most once a year - a "
   "list-triggered flow cannot store \"never\", so the window is stated "
   "explicitly rather than left to a default.</span>"),
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
        journey, variant, bullets = EXTRA[idx]
        blk, g = re.subn(
            r'(<div class="lbl">Why here in the journey</div>)<p>.*?</p>',
            lambda m: m.group(1) + "<p>" + journey + "</p>",
            blk, count=1, flags=re.S)
        # the amber variant callout: <div class="varbox"><div class="lbl">
        # ...icon...Welcome</div><p>THIS</p>
        blk, h = re.subn(
            r'(<div class="varbox"><div class="lbl">.*?</div>)<p>.*?</p>',
            lambda m: m.group(1) + "<p>" + variant + "</p>",
            blk, count=1, flags=re.S)
        lis = "".join("<li><strong>%s</strong> %s</li>" % (a_, b_)
                      for a_, b_ in bullets)
        blk, k = re.subn(
            r'(<div class="changehead">What is in it, and why</div>)'
            r'<ul class="ellist">.*?</ul>',
            lambda m: m.group(1) + '<ul class="ellist">' + lis + "</ul>",
            blk, count=1, flags=re.S)
        notes.append("email %d: when=%d subj=%d prev=%d why=%d tpl=%d "
                     "journey=%d variant=%d bullets=%d"
                     % (idx + 1, a, b, c, e, f, g, h, k))
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
