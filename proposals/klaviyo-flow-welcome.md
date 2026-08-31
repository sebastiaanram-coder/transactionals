# BEH-1 Welcome · Completed Signup

Built in Klaviyo 31 August 2026. Flow `V8EmeH`, **draft**.
https://www.klaviyo.com/flow/V8EmeH/edit

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

    Completed Signup  (metric WRvuHD)
      │
      └─ wait 1 hour                                    ← signup happens inside
          │                                               checkout, so many people
          │                                               order within the hour
          └─ Placed Order since entering this flow?
              │
              ├─ YES ─ WEL-1B Welcome, already ordered · 1h     (no code)
              │          └─ wait 1 day
              │             WEL-2B Behind the print · day 1     (no bar)   ends
              │
              └─ NO ── WEL-1 Welcome + 10% · 1h
                         └─ wait 1 day
                            WEL-2 Behind the print · day 1
                              └─ wait 2 days
                                 WEL-3 Reviews + reminder · day 3   ⟨skip if ordered⟩
                                   └─ wait 2 days
                                      WEL-4 Last day · day 5        ⟨skip if ordered⟩

Re-entry: **never**. A welcome flow that can run twice is a bug.

## The three decisions worth challenging

**1. The split is on "Placed Order since entering this flow", not on a profile
property.** Klaviyo has a `flow-start` timeframe filter, so the condition is
exact and needs nothing written to the profile. It is verified present in the
created flow, not assumed.

**2. Branches never rejoin in Klaviyo.** So the ordered path is a separate path
for the rest of the flow, and someone who orders on day 2 has already passed the
split. That is what the `⟨skip if ordered⟩` filters on WEL-3 and WEL-4 are for:
they re-check at send time, so a later order stops the discount chasing.

**3. The ordered path ends after two emails, and this is the judgement call.**
WEL-3 IS the discount reminder and WEL-4 IS the last-day nudge. Strip the
discount and there is no email left, only a subject line with nothing behind it.
Meanwhile Post-Purchase already picks this customer up from their order, so
running four more Welcome emails at them means two flows talking at once.

If you would rather they get four either way, WEL-3B and WEL-4B need to be
written as content, not derived: reviews without the reminder, and John's team
without the deadline.

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

| Message | Template file |
|---|---|
| WEL-1 | `proposals/welcome-01-klaviyo.html` |
| WEL-1B | `proposals/welcome-01-nocode-klaviyo.html` |
| WEL-2 | `proposals/welcome-02-klaviyo.html` |
| WEL-2B | `proposals/welcome-02-nocode-klaviyo.html` |
| WEL-3 | `proposals/welcome-03-klaviyo.html` |
| WEL-4 | `proposals/welcome-04-klaviyo.html` |

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
