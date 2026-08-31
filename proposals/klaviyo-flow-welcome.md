# BEH-1 Welcome · Completed Signup

Built in Klaviyo 31 August 2026. Flow `TEhf2p`, **draft**.
https://www.klaviyo.com/flow/TEhf2p/edit

## Naming convention

One line per flow, one per message, both sortable and both saying what the thing
is without opening it. The inherited flows were called `RFB // Welcome Flow`,
`RFB // Welcome Flow - New` and `RFB // Welcome Flow - CLONE SEB`, which is how
you end up activating the wrong one.

    Flow      BEH-<n> <Name> · <Trigger>
    Message   <FLOW>-<n>[B] <What it is> · <when>

`BEH` marks the behavioural programme, so it groups away from campaigns and
transactionals. `B` suffixes the variant of a message rather than inventing a
second number, so `WEL-1` and `WEL-1B` sit next to each other.

    BEH-1 Welcome · Completed Signup
    BEH-2 Browse Abandonment · Viewed Product
    BEH-3 Abandoned Order · Started Checkout
    BEH-4 Post-Purchase · Placed Order
    BEH-5 Winback · segment

## Structure

Two cadences, and a re-check before every email.

    Completed Signup  (metric WRvuHD)
      └─ wait 1 hour
          └─ S1: ordered since entering this flow?
              ├─ YES  WEL-1B  day 0     no discount, and then slowly:
              │       WEL-2B  day 5
              │       WEL-3B  day 10
              │       WEL-4B  day 15
              └─ NO   WEL-1   day 0     with the 10% code
                  └─ S2 (day 1): ordered yet?
                      ├─ YES  WEL-2B day 1 · WEL-3B day 6 · WEL-4B day 11
                      └─ NO   WEL-2   day 1
                          └─ S3 (day 3): ordered yet?
                              ├─ YES  WEL-3B day 3 · WEL-4B day 8
                              └─ NO   WEL-3   day 3
                                  └─ S4 (day 5): ordered yet?
                                      ├─ YES  WEL-4B day 5
                                      └─ NO   WEL-4   day 5

Re-entry: **never**.

**All four emails send on both sides.** An earlier version of this build dropped
emails 3 and 4 from the ordered path, on the reasoning that they "were" the
discount reminder and the last-day nudge. That was wrong, and checking the actual
content settled it: in both, the discount is a single green bar. Underneath,
email 3 is three real Trustpilot reviews and a 4.5 rating, and email 4 is John
and the print expert team with the how-it-works steps. Remove the bar and each is
still a complete email.

**Why the ordered side is slower.** Someone who has ordered is already receiving
transactionals, and Post-Purchase starts at **day 18**. A 0/5/10/15 cadence
threads between the two and lands just before that handoff. The unordered side
stays fast because the discount expires and the job is to get to a first order.

## Why it is 14 messages for 4 emails

Klaviyo flows are **trees, not graphs**. Verified, not assumed: a split whose two
branches point at the same action is accepted, but pointing at an action from a
*different* branch returns a 500. So there is no way to merge someone back onto
the ordered path - the ordered cadence has to be repeated under each split.

    S1 joins at email 1  ->  4 ordered messages
    S2 joins at email 2  ->  3
    S3 joins at email 3  ->  2
    S4 joins at email 4  ->  1
                             10 ordered + 4 unordered = 14

**14 messages, 8 templates.** The duplicates share templates, so content is
maintained in 8 places, not 14. Subject lines are the exception: they live on the
message, so a subject change to WEL-4B has to be made in four places. The `ord@S1`
to `ord@S4` suffix in each name says which split it hangs off.

## The no-discount variants

`welcome-01-nocode-klaviyo.html` and `welcome-02-nocode-klaviyo.html`, generated
by `scripts/translate_welcome.py` from the same source, so the translations,
images and design cannot drift from the originals.

Only the discount comes out. In welcome-01 that is the dashed code box, and the
call to action stops saying "Start your first order" to someone who just placed
one - it says "Browse the full range", translated into all six languages. In
welcome-02 it is the countdown bar.

## Not done yet

**Templates are not attached.** All six messages have `template_id: null`, so the
flow cannot send. The HTML exists and is ready.

| Messages | Template file |
|---|---|
| WEL-1 | `proposals/welcome-01-klaviyo.html` |
| WEL-2 | `proposals/welcome-02-klaviyo.html` |
| WEL-3 | `proposals/welcome-03-klaviyo.html` |
| WEL-4 | `proposals/welcome-04-klaviyo.html` |
| WEL-1B (×1) | `proposals/welcome-01-nocode-klaviyo.html` |
| WEL-2B (×2) | `proposals/welcome-02-nocode-klaviyo.html` |
| WEL-3B (×3) | `proposals/welcome-03-nocode-klaviyo.html` |
| WEL-4B (×4) | `proposals/welcome-04-nocode-klaviyo.html` |

**Subject lines are English only.** This is a programme-wide gap, not a Welcome
one: subject lines live on the flow message, not in the template, so nothing in
the translation work touched them. Every body is nine-locale and every subject
line is English.

Klaviyo subject lines do accept template tags, so the same
`{% if person.locale %}` switch should work - but it has never been rendered in
a subject line in this account, and the failure mode is the worst one available:
raw Django in the inbox, on the single most visible line. One preview send
settles it. Until then the drafts carry plain English.

**The `store` property.** The one `Completed Signup` event on the account carries
`{"store": "drukzo.nl"}`. If that metric fires for every label, this flow will
send Helloprint-branded email to people who signed up on Drukzo. Either the
trigger needs a filter on `store`, or the flow needs to be per-label. I have not
added the filter because I do not know the value Helloprint sends, and guessing
it would either leak or silently send to nobody.

**Marketing consent is no longer a blocker.** The signup event writes
`$consent: ["email"]`, which the old list-add trigger did not.
