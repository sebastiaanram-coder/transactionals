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

1. **The 5-day expiry is an unverified factual claim.** `wc.expires5`
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
