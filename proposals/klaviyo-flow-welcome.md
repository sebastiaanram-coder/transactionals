# BEH-1 Welcome · Newsletter subscribers

Rebuilt 1 September 2026 as a subscriber flow. Flow `YzcnqL`, **draft**.
https://www.klaviyo.com/flow/YzcnqL/edit

`TEhf2p` was the 31 August build and is superseded — delete it.

## Rebuilt as a subscriber flow, 1 September 2026

Flow [`YzcnqL`](https://www.klaviyo.com/flow/YzcnqL/edit) — **BEH-1 Welcome ·
Newsletter subscribers**, draft. Supersedes `TEhf2p`, which is still in the
account and should be deleted: a flow cannot be renamed through the API, and two
draft flows called BEH-1 Welcome is exactly the confusion the naming convention
was written to prevent.

**The 10% is now what the tick-box buys.** Anyone who does not subscribe never
enters the flow.

### Why a rebuild rather than a patch

Three of the four changes live on the flow's `definition`, and `PATCH /flows/{id}`
accepts `status` and nothing else — it rejects `definition`, `name` and
`profile_filter` outright. Individual actions *are* patchable, which is how the
retention-analysis changes went in without a rebuild, but a flow's **trigger**,
its **flow-level filter** and the **removal of an action** are all unreachable.

### 1 · The trigger is the Newsletter list, not the sign-up event

Subscribing *is* the entry condition, so the trigger says so directly: joined
list `VAh232` (Newsletter).

**Measured, not assumed.** The tick-box already writes to that list — 1 of the 14
most recent sign-ups is in it, so the wiring works and roughly 7% tick it today.
Marketing consent on the profile is **not** usable: `subscriptions.email.
marketing.consent` is unset on all 14, so list membership is the only reliable
signal.

**Why not "Completed Signup + a filter on list membership":** a race. The tick-box
write and the sign-up event are independent, and a flow filter is evaluated at
entry — if the event lands first, the filter sees no membership and the person
never enters at all. A list trigger cannot have that bug.

**Side effect worth knowing.** Anyone who subscribes by another route — footer
form, pop-up — now also enters. That is consistent with the offer (they ticked a
box promising 10%) but it is wider than "account sign-up".

### 2 · Email 1 is the entry action, immediate, with the code for everyone

This deliberately gives back yesterday's 3-hour delay and open-checkout
suppression, and the reason is that the retention analysis's objection no longer
applies in the same form. That objection was that the code discounted an order
already in flight. The code is now the **consideration for subscribing**:
withholding it from someone who ticked the box and then bought the same day is
not a saving, it is a broken promise.

The exposure also shrinks with the audience. The analysis costed the leak across
*all* registrants; only subscribers enter now — about 7% of sign-ups.

### 3 · The split moves to day 1 and only decides whether to remind

No split before email 1 means the four "ordered at S1" messages disappear with
it: nobody can have ordered before an email that goes out on entry. **Ten
messages instead of fourteen**, and the WEL-1B template — the no-discount welcome
— is no longer used by any flow message. It is still built, so reverting is a
matter of putting the entry back, not rebuilding a template.

From day 1 on, each split asks one question — *has this person ordered since
entering the flow* — and routes to a variant that does not mention the code.

**The open-checkout condition is gone from these splits, on purpose.** It existed
to stop a *second* paid lever landing on someone mid-checkout. But the code is
already in their hands from email 1, so a reminder costs nothing that has not
already been committed — suppressing it would only make the email less useful.

### 4 · Connect is excluded at the flow level, not routed

28.7% of Placed Order events in this account are Connect, and those buyers must
never receive a consumer discount ladder. Yesterday's version could only *route*
them to a no-code branch because a trigger filter was unreachable; a rebuild
excludes them outright, as *no Completed Signup from a store containing
`connect.` in the last 30 days*.

### 5 · Re-entry is 365 days, and the API forced that

On a **list-triggered** flow, `{"duration": 1, "unit": "alltime"}` — the form the
old metric-triggered flow used for "never" — is accepted with a 201 and then
**stored as `null`**. A concrete duration is stored faithfully, verified by
reading it back.

`null` is not good enough here: this flow hands out a discount on joining a list,
so "what happens if someone unsubscribes and resubscribes" needs a stated answer
rather than a default nobody has checked. At most once a year is that answer.

### Shape

    joined Newsletter (VAh232) · not a Connect sign-up
      └─ WEL-1  day 0, immediate, 10% code for everyone
          └─ day 1 · ordered since entering?
              ├─ YES  WEL-2B day 1 · WEL-3B day 6 · WEL-4B day 11
              └─ NO   WEL-2  day 1
                  └─ day 3 · ordered?
                      ├─ YES  WEL-3B day 3 · WEL-4B day 8
                      └─ NO   WEL-3  day 3
                          └─ day 5 · ordered?
                              ├─ YES  WEL-4B day 5
                              └─ NO   WEL-4  day 5

Every countdown claim is unchanged and still exact: emails at day 0, 1, 3 and 5
against a code valid five days from sign-up, and the coupon expires **after** day
5, so email 4's "last day" lands inside the window. Verified by
`scripts/render_check_welcome.py` — 90 renders, all ten messages in all nine
locales, 0 problems.

### Still open

- **Delete `TEhf2p`.** It cannot be renamed through the API. Note the Slack draft
  and any link already shared point at it.
- **The 10% holdout** is still not buildable: no random-split action type exists,
  and a census of all 29 flows found only `send-email`, `time-delay`,
  `conditional-split`, `send-sms`, `send-whatsapp`, `send-internal-alert` and
  `update-profile`. Needs Klaviyo's experiment feature or a random bucket on the
  profile.
- **`TEST_BCC` is on all ten messages.** Remove before go-live.
- **Volume drops to the subscribe rate** — about 7% of sign-ups until the 10% on
  the form lifts it. Worth watching, because it is also the measure of whether
  the incentive works.

## Retention analysis applied, 1 September 2026

Source: *Behavioural Emails, Re-priced* — the cohort analysis of 171,512 first-time
customers, June 2024 to May 2026, Endlabel isolated. Three of its changes touch
this flow. All three are applied; the flow is still **draft**.

### 1 · The minute-zero code — the largest margin exposure in the programme

**What was wrong.** The flow entered, waited **zero days**, and then asked "has
this person ordered since the flow started?". At t=0 nobody has, so every profile
fell to the FALSE branch and received WEL-1 **with** the 10% code — including the
**46.7% of registrants who order the same day**, because sign-up is account
creation *inside the checkout*. The split was not wrong; it was evaluated before
it could ever be true. Roughly **€16k of margin a month at pilot volume, €77k at
full rollout**.

**This reverses an earlier decision, deliberately.** The zero delay was set on
purpose, with the reasoning *"technically everyone gets the discount in the first
email, because nobody places an order in such a short timeframe."* The analysis
measured that premise and it is false.

**What changed.** The entry delay is **3 hours**, and the split now also asks
whether the profile has **a checkout open in the last 12 hours**. The checkout
condition is what does the real work: sign-up happens *inside* checkout, so
Started Checkout has already fired when the flow starts, and it catches the buyer
whether or not the order has completed by hour three.

**Why 3 hours and not 6.** The analysis sanctions 3–6. The countdown copy is
load-bearing — the code is valid five days **from sign-up** and email 1 says
"expires in 5 days" in six languages — so every hour of delay makes that claim an
hour optimistic. Three hours is 2.5% of the window instead of 5%, and the
open-checkout condition, not the length of the delay, is what catches the
in-checkout cohort.

**Why not the other sanctioned option.** The analysis also offers "send email 1
immediately without the code and introduce the code in email 2". It is cheaper to
build and catches *every* same-day buyer rather than a three-hour slice — but the
sign-up form now promises *"Ja, ik wil 10% korting op mijn eerste bestelling"*, so
an email 1 that does not mention the code contradicts the promise the customer
just accepted. That is a complaint, not a saving.

### 2 · Connect and the other B2B storefronts

Connect is **28.7% of Placed Order events** in this account, and those buyers must
never receive a consumer discount ladder. Every split now also asks whether the
profile signed up on a store whose name contains `connect.` — measured, not
assumed: Completed Signup carries exactly one usable property, `store`, and every
Connect storefront in the account matches (`connect.helloprint.nl`, `.co.uk`,
`.be`, `.es`, `connect.fr.helloprint.be`).

**This routes rather than excludes.** A Connect sign-up now goes to the no-code
branch, so no discount can leak, but it would still receive four consumer emails.
Full exclusion belongs on the flow's **trigger filter**, which is not reachable
from the API — see the constraint below. Not urgent: the Completed Signup metric
is one day old, has 75 events, and every one is `drukzo.nl`.

### 3 · The timing, and why the copy is still true in every country

The three hours were taken out of the **email 1 → email 2** interval (1 day → 21
hours) rather than added to the front of the sequence. That matters: pushing every
later email three hours late would have put email 4 — *"Last day for your 10%"* —
three hours **past** the expiry it announces.

| Email | Lands at | Claims | True? |
|---|---|---|---|
| WEL-1 | T+3h | "expires in 5 days" | 3h optimistic — 4d21h actually remain |
| WEL-2 | T+1.00d | "4 days left" | exact |
| WEL-3 | T+3.00d | "2 days left" | exact |
| WEL-4 | T+5.00d | "Last day" | lands within validity |

Verified by `scripts/render_check_welcome.py`, which renders all 14 messages in
all nine locales and checks each one's day claim against its own send offset — so
a future retiming cannot silently falsify a countdown in six languages.

### What could not be done, and what it costs to finish

**A flow's `definition` is not patchable.** `PATCH /flows/{id}` accepts `status`
and nothing else, and rejects `definition` outright. Individual **actions** are
patchable, so a delay's value and a split's conditions can both be changed in
place — which is how all of the above was applied without rebuilding. What cannot
be done is **adding an action**, or setting the flow's `trigger_filter` or
`profile_filter`. Two consequences:

1. **Full Connect exclusion** needs the trigger filter: one field in the Klaviyo
   UI (`store` **not-contains** `connect.` — the operator is `not-contains`,
   verified against the API), or a flow rebuild.
2. **The 10% holdout cannot be built here at all**, and the analysis calls it the
   one change that is not optional. There is no random-split action type in the
   flow API, and a census of all 29 flows in this account found only
   `send-email`, `time-delay`, `conditional-split`, `send-sms`, `send-whatsapp`,
   `send-internal-alert` and `update-profile`. It needs either Klaviyo's own
   experiment feature in the UI, or a random bucket written onto the profile by
   the data team, which a conditional split could then read.

### Unchanged, and endorsed by the analysis

The 10% itself and the €25 cap stay: at a 32.5% gross margin a 10% code needs a
+44% relative lift, which the analysis calls *"right at the ceiling — defensible
only because it is an acquisition cost, not a retention one."* The two-branch
split on Placed Order, the countdown mechanic and the fixed-hour delays are all
endorsed. The analysis also notes that newsletter-signup codes produce the
weakest retaining cohort in the dataset (−4.3pp), so this flow should be judged on
**first-order incrementality alone** and not expected to produce downstream
loyalty.

### Still open

- **The coupon's expiry semantics.** Email 4 lands exactly five days after
  sign-up. If the coupon expires at *end of day* five it is fine; if it expires
  exactly 120 hours after issue, the "last day" email arrives as the code dies.
  This pre-dates the retiming and needs a one-line answer from the commerce
  system.
- **"API" and "print stores"** are named in the analysis's exclusion list, but no
  `store` value observed in this account identifies them. The Connect pattern is
  built; the other two need their identifiers before a filter can be written.

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

---

## Templates attached — 2026-08-31

All 14 flow messages now carry a template. Flow `TEhf2p`, still `draft`.

**Klaviyo clones on attach.** Pointing a flow message at a saved library
template makes a private copy owned by that message. The 8 imported
templates are the masters; the 14 copies are what actually sends. Editing a
master does **not** update the copies — a content fix means re-attaching, or
editing all copies. Mapping is in `data/klaviyo-flow-welcome-messages.json`.

Verified by render, not by assumption:

- `Tejd65` (imported master, WEL-2B) rendered against `nl-NL` → Dutch, and
  against `de-DE` → German. Different locales produce different output, so the
  nine-branch `{% if person.locale %}` switches survived Klaviyo's importer.
  The importer does rewrite the HTML — CSS pretty-printed, `#ffffff` → `#fff`,
  entities to characters, attributes reordered and self-closed — all cosmetic.
- `WeqrBR` (live copy of WEL-1, discount version) rendered against `fr-FR` →
  French, with all four discount surfaces present (promo bar, HELLO10 code box,
  preheader, grid subtitle) and `Se désabonner`. So cloning preserves the
  switches too.

### Found during the render checks — not yet fixed

1. ~~**The 5-day expiry is an unverified factual claim.**~~ **RESOLVED 2026-08-31 — see the bottom of this document.** `wc.expires5`
   ("Valid only 5 days") plus "Expires in 5 days" on every product tile, plus
   the WEL-4 subject "Last day for your 10%". That asserts HELLO10 expires 5
   days after signup, in 9 languages, several times per email. If the coupon is
   not actually configured to expire, this is a false limited-time claim
   (UCPD Annex I point 7) — the same issue that stopped the 14-day version.
   **Confirm HELLO10's real terms before this flow goes live.**
2. **Review count disagrees between emails.** welcome-01 says 33,000 reviews;
   welcome-03 says 34,000. Consistent inside each email, contradictory across
   the sequence a recipient receives 3 days apart. Should come from one number.
3. **Prices are not localised.** Tiles render `€39.96` in French; it should be
   `39,96 €`. `i18n.decimal()` exists and is used for review scores, but tile
   prices are emitted as literal text and never pass through it. Affects
   fr, de, es, it, nl.
4. **Product names stay English.** The French email shows "Classic Business
   Cards", "Standard Posters", "Roller Banners". Allowlisted in
   `check_translations.py` as `SAMPLE_PRODUCTS`, so the audit passes, but it is
   still English body copy in a French email.
5. **Trustpilot link is the Irish domain.** `ie.trustpilot.com` in the French
   render; should be the market's own Trustpilot domain.
6. **Market-URL fallback is visible.** Three of four French tiles link to
   `/en-gb/...`. Known: 36 of 108 path × market pairs do not resolve.
7. `<html lang="en">` on every locale.

Subject lines and preview text remain English-only across all 14 messages —
they live on the flow message, not the template, and Django in a subject line
is still unverified.

---

## The six fixes — 2026-08-31

### 1. Trustpilot count is one number, written per language
Welcome 01 said 33,000 and Welcome 03 said 34,000. The live Trustpilot total is
**34,394**, so both are now "34,000+" and the "+" carries the "at least" the old
"more than" wording carried. Written the way each language writes it:
`34,000+` / `34.000+` / `34 000+` (French, with a NON-BREAKING space so a client
cannot wrap "34" and "000+" onto separate lines). Six keys × six languages,
plus `review.score`, which stays driven off `rv.review_total()` rather than
frozen. `i18n.thousands` was switched from U+202F to U+00A0 for the same reason:
U+202F has no glyph in several Outlook and Android fallback fonts.

### 2. Prices and product names come from the market's own feed
New `data/catalog-welcome-tiles.json` + `scripts/_lib/catalog.py`. Every tile's
name, price, currency, quantity and link is the market's own catalog entry.

- **Currency is per market, not assumed.** GB is GBP; everyone else EUR.
- **Money is written per language**: `£43.49`, `€ 46,62` (nl, it), `31,99 €`
  (fr, de, es).
- **Quantity comes from the market, the unit word from the language.** Belgium's
  flyer minimum is 500 where the Netherlands' is 1,000. The feed's unit is only
  ever plural, which produced "1 units" for a roll-up banner, and it left an
  Italian reader with English "units" — so the number is the market's and the
  word is ours: "1 stuk", "1.000 pezzi".
- **The fallback keeps the CURRENCY, not the language.** Falling gaps through to
  GB showed a Spanish reader "21,99 GBP", which is not payable in Spain. Gaps
  fall to IE instead — English name, euro price, working link.

Gaps, checked rather than assumed: **Italy has no catalog items at all** (no
`biglietti`, no `striscioni`), and Spain has no standard business card or
roll-up banner. Those six tiles fall back and `catalog.fell_back()` lists them
at build time. **Belgium's catalog mixes languages** — flyers and roll-ups are
French, cards and posters Dutch — so two of four tiles carry the other national
language whichever Belgian locale reads them. Kept as-is: the price and market
are right, and substituting the NL or FR item would show a price the Belgian
checkout does not charge.

### 3. Trustpilot links are per language
`ie.trustpilot.com` was hardcoded in 24 places, so a French reader was sent to
Ireland. Now `reviews.read_url` over the same language-keyed map the
review-request links already used. Every subdomain was checked by DNS with a
deliberate control (`zz.trustpilot.com` has no DNS; all nine country hosts do).
The preview default was also Irish for every language; it now follows the locale
being previewed.

### 4. Market URLs come from the feeds, verified over HTTP
`market-urls.json` only recorded whether `/{market}/{path}` resolved, which
assumes one slug everywhere. It is not one slug: the Dutch flyer page is
`/nl-nl/standaardflyers`, the French `/fr-fr/flyersdigital`, the Belgian
`/fr-be/flyersclassiques`. A new `urls` map holds the market's real localised
URL, taken from the catalog feed for products and from each market's own home
page for the company pages, and **all 72 verified 200** by
`scripts/build_market_urls_from_feeds.py`.

Gaps went from nine paths across up to six markets each, down to two paths in
Italy only. Three are genuine absences, established by listing each market's own
links rather than guessing: Italy has no all-products and no sustainability
page, and Spain has no request-a-quote page — only `mis-presupuestos`, the
reader's own saved quotes, which is the wrong page, so it is left to fall back.

### 5. `<html lang>` is the reader's locale
Was `lang="en"` in all nine languages, in 13 full documents and 174 previews.
Not cosmetic: screen readers take their pronunciation from it, so a Dutch email
was read aloud in an English accent.

### 6. Subject lines and preview text

**Preview text is fixed by REMOVING it.** Every template already carries a
hidden preheader div that is locale-switched and translated. The flow message
also carried an English `preview_text`, so a Dutch reader got the English field
followed by the translated div. The field is now empty on all 14 messages and
the translated div does the job it exists for.

**Subject lines could not be done with Django.** Measured, not assumed:

| test | result |
|---|---|
| 96-char `{% if person.locale %}` switch | stored verbatim — Django **is** accepted |
| 255 plain characters | stored |
| 500 plain characters | **400** "An invalid field type was passed in" |
| the real 747-char nine-branch switch | **400** |

`subject_line` caps at 255 characters. A nine-locale chain is 560–747, and a
six-language `|slice` version spends 274 on the conditions alone. Two languages
plus English is the most that fits, which is not a localisation.

So subjects use **Klaviyo's own Translations feature**, which this account
already runs on dozens of RFB templates and messages. Verified before the other
thirteen were touched: a collection exposes four value blocks (subject,
preview_text, from_label, template body), and writing subject translations left
the body block's 47,972-character source untouched with every body translation
empty. An empty translation falls back to the source, so the template's Django
switches keep control of the body. The two mechanisms do not collide.

Five of the seven subjects reuse an existing translated headline rather than
being translated a second time; only `subj.wel1` and `subj.wel4` are new. All
are unescaped — `we&rsquo;ll` would have reached the inbox as those literal
characters.

### Also fixed: nested locale switches
Welcome 04's `<h1>` was **1,952 characters with four nested switches**, because
`render()` replaced English with its switch directly and a later, shorter string
("Send it over") matched inside the en-IE and en-GB branches of a longer one
("Send it over, we'll handle it"). Longest-first ordering does not prevent that,
it causes it. `render()` now substitutes an opaque token first and expands every
token at the end. The h1 is 641 characters and welcome-04 is 3KB smaller.

### ~~THE TEMPLATES IN KLAVIYO ARE NOW STALE~~ — resolved, see below

Every fix above is in the repo. The 8 templates imported into Klaviyo earlier
today, and the 14 per-message copies cloned from them, still carry the OLD body
— the live copy of WEL-4 still links a Dutch reader to `/en-gb/quote` where the
repo now has `/nl-nl/offerte-aanvragen`. The 8 files in `klaviyo-templates/` must
be re-imported and re-attached (attaching re-clones) before any of items 2, 3, 4
or 5 reaches a reader. The subject and preview-text fixes in item 6 are on the
flow message, not the template, and are already live in the draft.

---

## Getting a change live is now one command — 2026-08-31

`scripts/push_templates.py`. No hand-importing, no clicking, no re-attaching.

```bash
python3 scripts/push_templates.py
```

It needs `KLAVIYO_PRIVATE_KEY` in `.env` (gitignored, alongside the Trustpilot
and Contentful credentials) with the **Templates** and **Flows** scopes. The key
is read from the file and never printed.

### What it does, and why it has to work this way

Attaching a saved template to a flow message makes a **private copy** owned by
that message, and the copy is what sends. The first attempt patched those copies
directly, so nothing would need re-attaching. **Every one returned 404** —
`Template with id 'WeqrBR' does not exist`. A per-message copy is not addressable
on `/api/templates/{id}`, even though `template-render` renders it happily. It is
readable and not writable.

What works, measured: push the **master**, then re-attach the message to it.
Re-attaching mints a fresh copy from the master's current content. WEL-1 went
from copy `WeqrBR` to `UtFxSQ`, and the new copy carried the new tiles,
`34.000+`, `nl.trustpilot.com` and `lang="nl-NL"` where the old one carried none
of them. Subject line and preview text survive untouched.

So: **push 8 masters → re-attach 14 messages → 14 fresh copies.** Both phases are
automatic. **Copy ids change on every run**, which is why the script writes them
back into `data/klaviyo-flow-welcome-messages.json` rather than anyone tracking
them by hand.

### Verification is semantic, not byte-for-byte

Klaviyo rewrites HTML on save — pretty-prints CSS, `#ffffff` → `#fff`,
`&middot;` → the character, reorders and self-closes attributes. A byte compare
would fail on every push and prove nothing. Each push is instead verified by
reading the template back and checking the locale-switch count, that every switch
is closed, the unsubscribe count, and a **canary** string present only in the new
version. A canary must contain no HTML entity, because Klaviyo converts those.
Welcome 02 matched none of the first five canaries, so its push was being
verified on switch counts alone; the localised company-page URLs were added to
cover it.

### Two API details worth keeping

- **Revisions differ by endpoint.** `/templates` accepts `2024-10-15`, but
  `flow-actions` on that revision has no `definition` field at all and 400s
  listing what it does have. `definition` appears at `2025-10-15`.
- **These endpoints throttle bursts.** A plain loop hits 429; the script retries
  with a backoff and paces itself.

### First run, 2026-08-31

8 masters pushed and verified, 14 copies re-cloned, subjects kept, preview text
empty on all 14. Then all 14 live copies rendered in nl-NL and fr-FR: **28 clean
renders** — no raw Django, correct `html lang`, no Irish Trustpilot link, no
`/en-ie/` link, unsubscribe present in every one. Flow tree unchanged at 28
actions and 27 links with nothing dangling.

**So the flow is now serving every fix in this document.** A promo-code change
from here is: edit the source, run the builder, run this script.

### The overview doc regenerates too

`scripts/refresh_overview.py`. The overview's preview panel renders a snapshot of
each finished email held in a `const PREVIEWS = {...}` object, so every builder
change left it quietly wrong while still looking finished — it was still showing
"33,000+ reviews" hours after that was fixed everywhere else.

Two wrong attempts before the right artifact, both worth recording:

- **Not the live Klaviyo block.** It carries all nine locales as `{% if %}`
  switches. Embedding it doubled the file to 1.8MB and would have shown readers
  literal `{% if person.locale == 'en-IE' %}` text in the preview panel.
- **Not `-proposed.html` as it sits on disk.** English and Django-free, which is
  right, but its images are base64 data URIs — which is why those files are
  30KB–650KB against a 3–21KB snapshot.

The right artifact is the English preview with its data URIs swapped for hosted
CDN URLs, matched by content hash against `assets/`.

**Deriving the key→file mapping at run time was also wrong.** By CSS class prefix
it looked clean and resolved all 29 — but prefix `w2` matches both `welcome-02`
and `welcome-02-nocode`, so glob order decided, and welcome-02 and welcome-03
came out pointing at the no-discount build. Every old snapshot contains the green
promo bar, so all four welcome keys are the discount version. The mapping is now
written out explicitly and the prefix is asserted on each run, so a renamed class
fails loudly instead of putting the wrong email under a heading.

RFB's twelve originals are the "before" half of the comparison and are left
byte-for-byte alone. Thirteen `33,000` references remain in them, correctly —
that is what RFB built.

---

## Conversion copy on the has-not-ordered branch — 2026-08-31

Subjects and preview text on the four has-not-ordered emails now name the
discount and count it down, and the pressure **builds** rather than starting at
maximum:

| | subject | preview text |
|---|---|---|
| day 0 | Welcome to Helloprint, and your 10% code | Your 10% code is inside, and you have 5 days to use it. |
| day 1 | Your 10% is waiting, and 4 days left to use it | Printed closer to you by a certified B Corp. Your 10% has 4 days left. |
| day 3 | Only 2 days left on your 10% | Rated 4.5 from 34,000+ reviews. Only 2 days left to use your 10%. |
| day 5 | Last day for your 10% | Artwork or just an idea, we take it from there. Last day for your 10%. |

Day 0 names the offer without a countdown — opening the relationship with a
deadline is pressure, not persuasion. Day 1 adds the countdown, day 3 promotes it
to the whole subject, day 5 is the final call. All six languages.

**The countdown figures are not invented.** Each email's BODY already carried a
day-accurate countdown — welcome-01 "Expires in 5 days", 02 "Expires in 4 days",
03 "2 days left", 04 "Last day!" — matching the 0/1/3/5 cadence. The subjects
reuse those exact figures, so a subject cannot contradict the email it opens.

**No coupon code in this copy, deliberately.** "HELLO10" in four preheaders across
six languages would be 24 more places to edit when the code changes. The literal
code stays in one place, the code box in welcome-01. This copy says "your 10%".

### The has-ordered branch had to be protected first

welcome-02, 03 and 04 shared ONE preheader between both branches — only
welcome-01 replaced its own in the no-discount variant. Making the shared one
count down the discount would have given someone who had just ordered an inbox
snippet pushing an offer they cannot use, which is precisely what the B branch
exists to avoid. So each of those three now keeps its former neutral preheader as
`pre_ordered`, and the variant swaps it in. Verified after the push: no discount
or urgency wording in any B-branch subject or preview text.

The per-token map also had to become per-email. It was one shared list, so every
`@@PRE@@` resolved to `wc.pre_nocode` — welcome-01's line about "the prints most
businesses start with". Right for 01, wrong for the other three.

### Two API details found doing this

- **The translations endpoint is BETA and needs a `.pre` revision.** `2025-10-15`
  says "before the earliest available, use a date after 2026-04-15"; `2026-04-15`
  and `2026-07-15` say "no valid revisions found for method"; `2026-10-15` says
  "unable to specify a future revision date". The one that works is
  **`2026-07-15.pre`**. Flow actions and templates still use `2025-10-15`.
- **Re-attaching with the message's CURRENT copy id is a no-op** — it does not
  re-clone. Only pointing at the master mints a fresh copy. Useful when changing
  a subject without wanting new copy ids.

### ~~Still unverified, and now more prominent~~ — resolved, see below

The 5-day expiry is asserted in the **subject line of three of the four** emails
and in all four preview texts. It was already in every body with a day-accurate
countdown, so this amplifies an existing claim rather than introducing one — but
if HELLO10 is not actually configured to expire five days after signup, this is
now the most visible thing in the inbox. **Confirm the coupon's real terms.** If
the window is different, the figures live in one place per email
(`welcome-0N/expires`, `flow-welcome/subj.wel*`, `welcome-0N/pre`) and one edit
plus `push_templates.py` changes all of it.

---

## Test-phase BCC — 2026-08-31

All 14 messages blind-copy `behavioral-email-tests@helloprint.com`. Verified from
the API: 14 of 14, no cc on any of them.

It is set in `scripts/push_templates.py` as `TEST_BCC`, not by hand in the UI.
Re-attaching rewrites the whole message object, so a bcc typed into Klaviyo would
be silently dropped by the next push — the push has to own it or it does not
survive.

**REMOVE BEFORE GO-LIVE.** A bcc on a live flow copies every customer's email to
an internal mailbox, which is a data-minimisation problem rather than just noise.
Set `TEST_BCC = None` and re-run the push to clear all fourteen.

Note the spelling: the address is **behavioral** (US), while everything else in
this repo is *behavioural* (UK). That is what was asked for, but a BCC to an
address that does not exist fails quietly, so it is worth one test send to
confirm the mailbox receives.

---

## The code, and the redesigned code block — 2026-08-31

**`HELLO-8DS2-10`** replaces `HELLO10`. Same string in every market, one use per
customer enforced in the commerce system, so the email does not claim it.

**It is defined once**, in `scripts/_lib/offers.py`, and reaches the templates
through an `@@CODE@@` sentinel. It is deliberately NOT in the translation store:
a code is identical in every language, so putting it there would have meant six
copies per email and a 24-place edit on the next rename. Changing the code is now
one line plus `push_templates.py`.

The guards moved with it. `build_order_02_low`, `build_order_03_high` and
`build_order_03_low` each asserted the literal string `"HELLO10"` must not appear
in their body. A guard naming a retired code protects nothing, so all three now
assert on `offers.WELCOME_CODE`, as do `translate_welcome.DISCOUNT_WORDS`,
`collect_templates`'s paste audit and `make-nodiscount`.

### Welcome 01's hero, rebuilt on the post-purchase email 5 pattern

| | before | after |
|---|---|---|
| eyebrow | – | `10% OFF YOUR FIRST ORDER`, green caps, letterspaced |
| code | inline pill, code inside a sentence | labelled card: `YOUR CODE` / 26px letterspaced value / grey note line |
| card | transparent, 8px radius, 13px text | `#212121`, 2px dashed `#9fdbb8`, 12px radius, 400px max-width |
| under CTA | – | `Use it at checkout on anything in the range.` |

**The CTA stays white, not green.** Post-purchase 05 uses a green pill because
nothing green sits near it. In welcome-01 the green USP speech balloon sits
directly beneath the button, and two greens stacked was the thing this layout was
built to avoid. Everything else from that block is adopted.

**The eyebrow and the CTA note sit OUTSIDE the code card**, so the no-discount
variant had to strip all three. Stripping only the card left "10% OFF YOUR FIRST
ORDER" as the first line of an email with no offer in it. Verified after the
push: no code, no eyebrow, no note and no "YOUR CODE" label in any B-branch
email.

### The code now rides the green banner in emails 2, 3 and 4

Has-not-ordered only — the banner is what the no-discount variant strips, so this
cannot reach the ordered branch:

```
WEL-2  Je 10% staat nog klaar HELLO-8DS2-10 · Verloopt over 4 dagen
WEL-3  Je 10% staat nog klaar HELLO-8DS2-10 · Nog 2 dagen
WEL-4  Je 10% welkomstkorting HELLO-8DS2-10 · Laatste dag!
```

Email 1's banner does NOT repeat it — the code has a 26px card of its own three
lines below, and saying it twice in one screen reads like a mistake.

The code is a plain literal in the banner rather than part of the translated
string, for the same reason as above: one place per file, not six.

---

## Blue links in Gmail, and the timing change — 2026-08-31

### Why two links rendered Gmail blue

Not a Klaviyo problem — a CSS specificity one, and it affected **every call to
action in the programme**, 77 anchors across all 33 blocks.

Gmail's own stylesheet colours links with `a:link`, specificity **0-1-1**. A rule
like `.hp-w1-cta{background:#fff;color:#191919;padding:15px 34px}` is **0-1-0**,
so Gmail wins on `color` while everything else in the same rule still applies —
the white pill renders correctly and the label inside it comes out blue. That is
exactly what the screenshot showed.

The proof sits in the same email: `.hp-w1-helplinks a` is 0-1-1, ties with
Gmail's rule, wins on document order, and renders green — while `.hp-w1-cta` a
few lines above it does not. Same stylesheet, same client, one character of
specificity between them.

**Fix:** `scripts/fix_link_specificity.py` prefixed the element onto all 34
affected rules — `.hp-w1-cta` → `a.hp-w1-cta` — which is 0-1-1 and behaves like
the descendant rule that already worked. No markup changed, so nothing can shift
in layout, and it lives in the source CSS so a rebuild keeps it. Every one of the
53 classes was first verified to appear **only** on `<a>` elements; prefixing a
selector whose class also sat on a div would have silently dropped that div's
styling. Re-ran the detector afterwards: **0 anchors still vulnerable.**

Worth noting this was worse than cosmetic on the green pills: white text repainted
Gmail blue on `#008539` is close to unreadable, and that is most of the CTAs in
the abandoned-order, category and winback emails.

### First email now sends immediately

The entry delay went from 1 hour to 0 (`116031814`). Flow tree re-checked
afterwards: 28 actions, no dangling links.

**This reverses the reason the delay was there.** It was set to 1 hour precisely
because signup happens inside the checkout, so many people order within minutes —
the delay let the split catch them and send the no-discount version. Sending
immediately means someone who is mid-checkout gets a 10% code they can apply to
the order they are already placing.

That is only a problem if the discount is meant to *win* an order rather than
reward a signup. Paired with putting "10% off your first order" on the signup
form, it is the opposite of a leak: it is the deal being honoured promptly, and
the immediate send is what makes that promise credible. Recorded here because the
two decisions only make sense together — reinstating the delay while the form
advertises the discount would break the promise.

---

## Offer conditions in the email — 2026-08-31

Six conditions to carry: max 25 off, one per customer, 5-day expiry, no stacking,
not on bespoke quotes, products only excluding services and delivery.

**Bottom: the full terms.** A `hp-wN-terms` block in the footer of all four
has-not-ordered emails, above the company legal line, six languages. Stripped by
the no-discount variant — terms that name a discount have no business in an email
that carries none, and the build check caught it when they first survived.

**Top: one addition, the cap.** The note under the code went from

    10% off your first order · expires in 5 days
    10% off your first order, up to £25 · expires in 5 days

This is the one place I did not keep to "as little as possible at the top", and
the reason is narrow: a **cap is the single condition a reader can be materially
misled by**. "10% off" next to a €600 basket implies €60. Disclosing that only in
footer small print is the textbook misleading-omission shape under the UCPD.
Everything else — stacking, bespoke quotes, services and delivery — genuinely can
live at the bottom, because none of them changes what the headline number appears
to be worth. Remove it if legal disagrees; it is one key, `welcome-01/code_line`.

**The cap is per MARKET, not per language.** £25 in GB, €25 everywhere else, and
written the way each language writes money: `£25`, `€25`, `€ 25`, `25 €`. That
needed a new mechanism — `i18n.tr` grew `fills_loc`, keyed on locale rather than
language, because en-GB and en-IE share every word of English while one is GBP
and the other EUR. A language-keyed fill wrote sterling into the Irish branch.

Verified live: `en-GB` renders `up to £25`, `en-IE` renders `up to €25`, and the
ordered branch carries no terms block and no "10%" at all.

**The green banner in emails 2-4 does NOT repeat the cap.** It already carries
the offer, the code and the countdown; a fourth clause would not fit on one line
on mobile. The terms at the foot of those same emails state it.

---

## The offer terms are confirmed — 2026-08-31

Sebastiaan confirmed both figures against the coupon as created in the commerce
system:

| | |
|---|---|
| Code | `HELLO-8DS2-10`, same in every market |
| Discount | 10% |
| Cap | **25** in the market's own currency (GBP in GB, EUR elsewhere) |
| Validity | **5 days** from signup |
| Redemption | one use per customer, enforced in the commerce system |

**This closes the one blocker that had been open all day.** It was not a
formality: "expires in 5 days" is asserted in three subject lines, four preview
texts, four email bodies, the terms block and now the signup form, and "up to
25" sits next to the discount claim itself. Had the coupon not actually been
time-limited and capped, every one of those would have been a false limited-time
claim under UCPD Annex I point 7 — which is why the first version of this
programme refused to write a 14-day expiry that nobody had verified.

Both numbers are single-sourced in `scripts/_lib/offers.py` as `WELCOME_CAP` and
`WELCOME_DAYS`. If the coupon is ever reconfigured, change them there and re-run
the builders plus `push_templates.py`; nothing else needs touching.

### What is still open before this flow can be turned on

Nothing about the offer. What remains:

1. **The custom `locale` profile property must be unset.** It shadows the native
   field, and 51 of 82 profiles carry both. Until the data team removes it, a
   reader's language is decided by the wrong field — and the native locale is the
   thing the whole programme was rebuilt around. Requested; not done.
2. **Remove the test BCC.** `TEST_BCC = None` in `push_templates.py` and re-run.
   A bcc on a live flow copies every customer email to an internal mailbox.
3. ~~Decide what `store` means for the trigger.~~ **Settled 2026-08-31.**
   `drukzo.nl` and `drukzo.be` are the LEGACY names for Helloprint in NL and
   nl-BE. The front end was rebranded to Helloprint in November 2025; the back
   end still emits the old store. Same brand, same customers, so no trigger
   filter and no per-brand flows are needed. Not a risk, and not to be raised
   again.
4. **A native speaker has still read none of the translations** — including the
   two subject lines, the four preview texts and the terms block, all of which I
   wrote today.
5. The signup form copy needs implementing on the website, with the GB form
   showing GBP25 rather than EUR25.

Item 1 is the one that can still put the wrong LANGUAGE in front of someone. 2
is a privacy obligation before go-live. 4 is now in progress - see below. 5 is
outside Klaviyo.

---

## Translations out for review — 2026-08-31

`scripts/translations_csv.py` exports the strings for the translation team and
reads their edits back.

```bash
python3 scripts/translations_csv.py export              # welcome, 107 strings
python3 scripts/translations_csv.py export --all        # whole programme, 511
python3 scripts/translations_csv.py import FILE.csv --dry-run
python3 scripts/translations_csv.py import FILE.csv
```

One row per string, one column per language, plus `scope` and `key` which are the
string's identity and how the import finds it again, and a `where` column so a
translator who cannot see the template knows what they are editing.

### What the import refuses, and why each one is a real risk

- **A lost token.** `@@CAP@@` becomes the discount cap in the market's own
  currency at build time. A translator who translates or drops it silently
  removes the cap from that language - the one condition a reader can be
  materially misled by. Refused.
- **A bare `&`.** Entities like `&middot;` are markup. A stray ampersand breaks
  the HTML rather than showing as text. Refused.
- **An empty cell.** Refused, rather than shipping a blank line.
- **A lost non-breaking space.** French groups thousands with U+00A0 - "34 000+".
  It is invisible in a spreadsheet, so a translator retyping the number uses a
  normal space and the number can then wrap across two lines. Repaired
  automatically, and reported.
- **Formula injection.** A cell starting `= + - @` is read as a formula by Sheets
  and Excel. Guarded on export, stripped on import.

Nothing is written unless every row passes, so one bad cell cannot leave the
store half-updated. Tested five ways before use: an unedited round trip changes
0 of 107 strings, a legitimate edit is picked up, a deleted token is refused, a
lost French space is repaired, and no dry run touches the file.


---

## Translation sheet linked — 2026-08-31

https://docs.google.com/spreadsheets/d/13Z2nfCpZbEU-qWmGxdslWzzaY2_le976aWExfX97Zko/edit

Linked from the Translations fact box in the overview's Welcome Flow section.

**One thing to be aware of.** `behavioural-email-overview.html` sits at the root
of a PUBLIC GitHub repo and is served by GitHub Pages, and the sheet is shared
with "anyone with the link". So the overview now hands that link to anyone who
finds the page. The contents are marketing copy in six languages, not customer
data, so the exposure is low - but it is a public page pointing at an internal
working document, and if the sheet is later reused for anything less harmless
that inherits the same exposure. Two ways to close it if you would rather:
restrict the sheet to named people in the Helloprint workspace, or keep the link
in this repo and out of the published page.
