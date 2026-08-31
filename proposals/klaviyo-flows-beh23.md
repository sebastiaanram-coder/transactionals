# BEH-2 Browse Abandonment and BEH-3 Abandoned Order

Built in Klaviyo 31 August 2026. Both **draft**. Nothing is scheduled and nothing
can send until someone activates them.

| Flow | Klaviyo | Trigger | Emails |
|---|---|---|---|
| BEH-2 Browse Abandonment | [`SLJCa5`](https://www.klaviyo.com/flow/SLJCa5/edit) | Viewed Product `WX8EsF` | 3 |
| BEH-3 Abandoned Order | [`YhfMdM`](https://www.klaviyo.com/flow/YhfMdM/edit) | Started Checkout `T3uGk6` | 6 across two branches |

They replace RFB's `Wzhp2m` (Browse, 5 emails) and `VCVzm6` (Abandoned Cart) plus
`Abandoned Checkout`. **The RFB flows are still there and still draft. Switch them
off, or delete them, before either of these is activated** — otherwise a person
can be in both.

## What to review

Everything is verifiable without sending anything:

    python3 scripts/verify_flows.py          # reads both flows back and walks the tree
    python3 scripts/render_check_flows.py    # renders all 9 emails in every locale

`verify_flows.py` prints the trigger filters, the flow filters, the re-entry
window and the exact path a person takes, read back from Klaviyo rather than from
this document. `render_check_flows.py` renders the per-message copy — the thing
that actually sends — once per market, with a realistic event.

## Structure

    Viewed Product  (WX8EsF, filtered)
      └─ wait 1 hour     → BRW-1   the product, with the three real blockers
          └─ wait 23h    → BRW-2   you do not need the finished artwork yet
              └─ wait 2d → BRW-3   tell us the job and we will price it

    Started Checkout  (T3uGk6, filtered)
      └─ wait 1 hour
          └─ split: sum of $value since flow start >= 150
              ├─ HIGH  ORD-1H +1h · ORD-2H +24h · ORD-3H +72h
              └─ LOW   ORD-1L +1h · ORD-2L +24h · ORD-3L +72h

Three emails per path, not RFB's five. A product view is a weak signal, and this
flow's volume feeds the same sending reputation as everything else.

**The split sits after the 1-hour delay, not at entry.** A conditional split
accepts only a `profile_filter` — every event-side key the API offers is rejected
— so the cart value is read as *sum of Started Checkout `$value` since flow
start*. Evaluated at t=0 that is a boundary case: the triggering event may not yet
be inside its own window, which would read every cart as 0 and send every customer
down the low branch, silently. After a delay it is unambiguous, and BEH-1 already
proved a post-delay split reads flow-start events correctly. Email 1 was due at
+1h anyway, so it costs nothing.

It diverges from "the triggering cart" only if the same person starts checkout
again within the hour, when the sum is both carts. Two 80 carts would read as 160
and take the high branch — which offers a person and holds the discount back, so
the failure mode is a more expensive email, not a margin leak.

## Messages

### BEH-2 Browse Abandonment
| Message | Subject | Template | Master id |
|---|---|---|---|
| `BRW-1 The one you were looking at · +1h` | The print you were looking at | The one you were looking at | `Ru6gHW` |
| `BRW-2 You do not need the artwork yet · +24h` | You do not need the finished artwork yet | You do not need the artwork yet | `S2u4Zb` |
| `BRW-3 Tell us the job, we will price it · +3d` | Need a price you can forward? | Tell us the job, we will price it | `XW9vMR` |

### BEH-3 Abandoned Order
| Message | Subject | Template | Master id |
|---|---|---|---|
| `ORD-1H Basket restored · high · +1h` | Left something behind? | Basket restored, high value | `RiPL3a` |
| `ORD-1L Basket restored · low · +1h` | Left something behind? | Basket restored, low value | `W56mVY` |
| `ORD-2H Print expert · high · +24h` | Want a print expert to look at it first? | Print expert, high value | `YpU3HG` |
| `ORD-2L 10 percent off · low · +24h` | 10% off, for the next 72 hours | 10 percent off, low value | `RLAhWZ` |
| `ORD-3H Expert plus 10 percent · high · +72h` | Still happy to go through this with you | Expert plus 10 percent, high value | `SiY6ee` |
| `ORD-3L 25 percent capped · low · +72h` | 25% off, for the next 24 hours | 25 percent capped, low value | `R4VYYY` |

Subjects and preview texts are set in **nine locales** through Klaviyo
Translations, from `data/translations.json` (scopes `flow-browse`, `flow-order`).
A subject line cannot carry the nine-way Django switch the bodies use: the field
caps at 255 characters, measured, and a nine-locale chain is 560 to 747.

Both `ORD-1H` and `ORD-1L` use the same subject and preview. The email differs;
the promise in the inbox does not.

## Which markets each flow may fire in, and why they differ

`{% catalog %}` **hard-fails**: an id that is not in the feed returns 400 and the
whole email fails to render, not just that block. So a market is allowed in only
if every id its email can look up exists. Verified by fetching each id on
31 August 2026.

**BEH-2 allows IE, GB, NL, BE, FR, DE.** browse-01's cross-sell builds ids it was
never given — `event.ProductID|slice:":3"|add:"<slug>"` — so all nine slugs it can
reach must exist per market.

| Market | Coverage of the nine cross-sell slugs |
|---|---|
| IE GB NL BE FR DE | all nine present → **allowed** |
| ES | missing `canvafoldedleaflets`, `businesscardsstandard`, `rollupbannersv2` |
| SE | missing `canvafoldedleaflets`, `rollupbannersv2`, `letterheads` |
| IT | **no catalog feed at all** |

**This supersedes the proposal's "IE- or GB- only"**, which was written before the
other feeds were checked. That restriction would have aimed these flows at the two
markets the programme is *not* launching in: Ireland is 1.5 per cent of Started
Checkout events, and NL — where BEH-1 just went live — is 14 per cent.

**BEH-3 allows en-IE, en-GB, nl-NL, nl-BE, fr-FR, fr-BE, de-DE, es-ES.** It
constructs nothing: every lookup is `it.ProductID`, an item the customer just
configured, so it exists by construction. It needs only a feed to exist and a
locale the email is built for. Excluded: `it-IT`, because Italy has no feed
(`IT-flyerseco`, `IT-flyera5`, `IT-standardflyers` and `IT-adesivi` all 404), and
`en-US`, which is **5.1 per cent of Started Checkout events** with no US feed and
no en-US branch in any template — a US reader would be shown the en-GB fallback in
pounds.

## Hosts, measured over 800 production Started Checkout events

| Host | Share |
|---|---|
| `www.helloprint.com` | 85.0 per cent |
| `connect.helloprint.{nl,fr,be,es,co.uk,it}` | 14.3 per cent |
| `v4.staging.helloprint.dev` | 0.6 per cent |

Both flows filter on the host. Connect is the B2B storefront and those buyers must
not get consumer lifecycle mail. Staging is why the host filter cannot be dropped
in favour of the locale filter: a staging URL carries a real locale segment
(`v4.staging.helloprint.dev/it-it/checkout/details`), so only the host separates
it. **Staging writing into the production Klaviyo account is a separate problem
and should be fixed at source.**

## Flow filters, re-checked before every send

| BEH-2 | BEH-3 |
|---|---|
| no `Added to Cart` since entering | — (this flow is *for* people with a basket) |
| no `Placed Order` since entering | no `Placed Order` since entering |
| no `Ticket Created` in the last 7 days | no `Ticket Created` in the last 7 days |

`Added to Cart` hands a browser over to BEH-3 cleanly: they are no longer
browsing, they have a basket, and BEH-3 is the flow that can show it.

The ticket filter is Klaviyo's own recommendation — someone mid-conversation with
support should not receive "you left something behind". There is no "ticket is
open" signal in the account, only `Ticket Created`, so 7 days is the implementable
approximation rather than the literal condition.

Re-entry: **14 days** for BEH-2 (print is a considered purchase). **30 days** for
BEH-3, and that one is a commercial control: the low branch reaches 25 per cent
off within 72 hours of a single abandoned checkout, which is a discoverable
pattern — configure something cheap, abandon it, wait three days. Monthly
re-entry still serves a genuine repeat abandoner while capping the loop at twelve
times a year.

## Klaviyo's filter logic is the reverse of the usual convention

Documented here because it is the single easiest way to break these flows:

    conditions INSIDE one condition_group are combined with OR
    condition_groups are combined with AND

Getting it backwards is harmful in both directions. Six markets as six *groups*
and the flow never fires. Two exclusions in one *group* and the filter becomes
"has not ordered OR has not added to cart", which is true of nearly everybody —
so the flow would mail people who had already bought. Every group in
`scripts/create_flows.py` is commented with which it is.

## Django parses inside HTML comments

Five of the nine templates — browse 1, 2, 3 and both low-value order emails —
failed to render, and would have sent **nothing**. Each was correct HTML with
correct Django in its body.

The cause: every generated template opens with a header comment that documents
the bindings by *quoting* them — a bare `catalog` tag, "`with` is not supported",
an example locale switch. `<!-- -->` hides text from a browser and hides nothing
from the template engine, so Klaviyo executed those examples. A `catalog` tag with
no id, and a `with` tag that does not exist in Klaviyo's dialect, each fail the
whole render.

Fixed centrally in `scripts/_lib/doc.py`: the header is wrapped in a Django
`comment` block, which does not parse its contents and drops them from the output
— so the documentation stays readable in Klaviyo's code editor and 1.0 to 1.9 KB
per email stops being sent to the recipient. Any other comment carrying template
syntax is wrapped in `verbatim` instead, which keeps the bytes, because a mid-body
comment may be an Outlook conditional comment that has to survive.

The same class of bug is latent in BEH-1 and the post-purchase templates. They
happen to render because their headers quote nothing executable. Worth applying
`doc.shell` there too.

## The nine emails also gained an `html lang`

All nine shipped as a bare `<div>` with its own `<style>` and no `<html>` element
at all, so the message had no `lang` attribute. That is the same defect that was
fixed on BEH-1, and it is not cosmetic: screen readers take their pronunciation
rules from `lang`, so a Dutch email was read aloud in an English accent, and
Gmail and Outlook use it when deciding whether to offer to translate. They are now
full documents with the same nine-way locale switch BEH-1 uses.

## Deploying a content change

No manual import, and nothing to re-attach by hand:

    python3 scripts/build_browse_01.py        # or whichever builder changed
    python3 scripts/push_flows.py             # pushes masters, re-clones, verifies
    python3 scripts/render_check_flows.py

Attaching a saved template to a flow message makes a **private copy** owned by
that message, and the copy is what sends. A copy **cannot** be patched —
`/api/templates/{id}` returns 404 for it — so the master is pushed and the message
re-attached, which mints a fresh copy. Copy ids therefore change on every push,
which is why they are recorded in `data/klaviyo-flow-*-messages.json` rather than
remembered.

Subject or preview text changed? `python3 scripts/push_flow_subjects.py`. It reads
`data/translations.json`, sets the English source on the message and the nine
locales through Translations, and **fails rather than shipping** if a subject's
stated percentage or deadline disagrees with `scripts/_lib/offers.py`.

## Open, and needing someone else

1. **Neither discount code exists.** `CART-5H9N-10` (10 per cent, 72h) and `CART-9M4T-25`
   (25 per cent capped at 25, 24h) must be created in the commerce system before
   BEH-3 leaves draft. They are named to the programme convention rather than the
   old `BASKET10` / `BASKET25` placeholders, and they live in one place,
   `scripts/_lib/offers.py`. `CART-5H9N-10` is deliberately shared by ORD-2L and
   ORD-3H: same depth, same expiry, so two codes would be two things to create for
   no gain. The cost is that a report grouped *by coupon* cannot separate those two
   messages.
2. **The expiries have to be real.** 72 hours on the 10 per cent, 24 on the 25.
   Each is stated in a subject line, a preview text and the body. If the code
   outlives the sentence, the next deadline is not believed. Same limitation
   already flagged for the winback and post-purchase flows.
3. **ORD-3L at 25 per cent becomes the deepest discount in the programme**
   (Welcome 10, Winback 15). The cap and the 30-day re-entry are the controls;
   whether 25 is the right number is a commercial call, not an engineering one.
4. **Feed images are far too heavy.** Packshots come straight from the feed at
   300 KB to 6.5 MB, `?w=` is ignored by `storage.googleapis.com`, and Klaviyo's
   `thumbnail.src` is byte-identical to `full.src`. A sensible email thumbnail is
   30 to 60 KB. On mobile data the packshot may simply not appear — and in
   browse-01 the packshot *is* the email. Needs a feed change (a roughly 600x600
   q80 JPEG), not an email change.
5. **ES joins BEH-2** as soon as `canvafoldedleaflets`, `businesscardsstandard` and
   `rollupbannersv2` are in the Spanish feed. Three ids, then one line in
   `BROWSE_MARKETS`.
6. **A `catalog` tag in a subject line is untested.** Both browse subjects use the
   static fallback rather than the dynamic product title, because a subject cannot
   be rendered through the API. One live test send settles it.
7. **`TEST_BCC` is on all nine messages** (`behavioral-email-tests@helloprint.com`),
   same as BEH-1. **Remove before go-live**: a bcc on a live flow copies every
   customer email to an internal mailbox, which is a data-minimisation problem, not
   just noise. Set `TEST_BCC = None` in `scripts/create_flows.py` and re-run
   `push_flows.py`.
8. **Translations need a native-speaker pass.** `translations-browse-order.csv`,
   174 strings, same format and round-trip guarantees as the welcome sheet.
9. **Gmail clips at about 102 KB.** `ORD-3H` is 81 KB and `BRW-1` is 76 KB — under
   the limit, but not by much, and the feed-image fix would not help since images
   are fetched rather than embedded. Worth watching if either grows.
10. **UTM tracking is off** (`add_tracking_params: false`) and Smart Sending is on,
    matching BEH-1. Confirm that is what reporting expects.
