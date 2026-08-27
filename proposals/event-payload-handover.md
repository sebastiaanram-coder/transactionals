# Klaviyo event payloads: what the behavioural flows need

**For:** whoever owns the Klaviyo event payloads on presta and on v4 / Helloprint One.
**From:** Sebastiaan Ram, behavioural email programme.
**Date:** 27 August 2026.
**Status:** three asks, and two fixes on our own side. Two of the asks block
emails that are otherwise finished.

---

## 1. Why this document exists

Twenty-four behavioural emails are built and ready. Nine of them can only be sent
in Ireland, and five of them cannot be routed to the right customer, because of
fields that are missing from the events that trigger them.

Nothing here is a design question. The emails exist, the copy exists, the
translations exist. These are data fields.

The same pass also turned up a live defect on our own side, in the product links
of the six abandoned-order emails. It is written up here rather than kept
separate, because the honest fix is for us to stop asking the event for something
the catalogue already has.

---

## 2. The one rule that drives all of it

**A flow can only read the event that triggered it.**

Plus the customer profile and our product catalogue. That is the whole
vocabulary. If a field is not in the triggering event, the flow cannot see it,
cannot branch on it and cannot print it. There is no way to look sideways at
another event from inside a running flow.

So each flow depends on exactly one event:

| Flow | Triggered by | Emails |
|---|---|---|
| Post-Purchase, including the 5 category nudges | `Placed Order` | 10 |
| Abandoned order | `Started Checkout` | 6 |
| Browse abandonment | `Viewed Product` | 3 |
| Winback | a segment, no event | 5 |

`Ordered Product` triggers none of them. It is measured below for completeness
because it was the first candidate for the category split, but it has the same
gap as `Placed Order` and switching would not help.

---

## 3. There are two kinds of category. Only one belongs in the event

This distinction is the thing most likely to cause a wrong fix, so it is worth
being explicit.

**Internal, feed categories.** Always English, three levels, e.g.

```json
["Commercial Print", "All Stationery", "Notepads"]
```

These decide **which** email a customer gets. They must be in the event. They
must stay English: a flow condition compares against a fixed string, so a
translated value would need eight variants per branch and would break the moment
a translation is edited. Verified English on fr-FR, nl-BE, es-ES and it-IT
events.

**Website, Contentful categories.** Translated per market. These fill the email
with product names and links. They live in our own snapshot
(`data/subcategories.json`), keyed to the internal categories in
`scripts/fetch_subcategories.py`. **Nothing is needed from you for these.**

### The shape to keep

`Categories` is a flat array of three-element groups, one group per order line.
A two-line order looks like this:

```json
["Commercial Print", "All Stationery", "Bookmarks",
 "Photo products",   "Greeting cards", "Cards"]
```

Please keep all three levels and keep the grouping. The first level routes the
five nudges today. The second level is what a planned sixth nudge for Stationery
would route on: Stationery is worth €1.24M of gross profit a year but is a
*sub*category of Commercial Print, so it is invisible at level one.

---

## 4. What is there today

Measured on the 100 most recent events of each type, 27 August 2026. Reproduce
with the Klaviyo MCP `get_events`, or see §7.

Stack is inferred: `event_source: "presta"` means presta;
`ctMessageId` or `store` means v4 / Helloprint One; a small remainder had
neither and is shown as unattributed.

### `Placed Order` — powers Post-Purchase, 10 emails
n=100: presta 87, v4 13.

| Field | Overall | presta | v4 | Needed for |
|---|---|---|---|---|
| `Locale` | **100/100** | 87/87 | 13/13 | translating all 10 emails |
| `Categories` | **61/100** | 61/87 (70%) | **0/13** | choosing which of the 5 category nudges |
| `Items` | 13/100 | 0/87 | 13/13 | not used by these emails |

### `Ordered Product` — powers nothing, measured for completeness
n=100: presta 84, v4 16.

| Field | Overall | presta | v4 |
|---|---|---|---|
| `Locale` | 100/100 | 84/84 | 16/16 |
| `Categories` | 65/100 | 65/84 (77%) | **0/16** |
| `ProductID` | 11/100 | 0/84 | 11/16 |

### `Started Checkout` — powers abandoned order, 6 emails
n=100: presta 96, unattributed 4.

| Field | Overall | Needed for |
|---|---|---|
| `CheckoutURL` | **100/100** | the link back to the basket |
| `Items` | **100/100** | the basket contents |
| `Categories` | 75/100 | copy angle only, not routing |
| `Locale` | **0/100** | translating |

`Items` entries, measured across all 150 item lines in the 100 events:

| Item field | Lines | Note |
|---|---|---|
| `Brand`, `Quantity`, `ItemPrice`, `RowTotal` | 150/150 | |
| `ProductID` | **145/150** | see ask 3 |
| `ProductName`, `ProductSlugLocale`, `SKU` | 145/150 | |
| `ImageURL` | 142/150 | |
| `Categories` | 116/150 | per line, not used for routing |
| `ProductURL` | **8/150** | see below |

### `Viewed Product` — powers browse abandonment, 3 emails
n=100: presta 88, unattributed 12.

| Field | Overall | Needed for |
|---|---|---|
| `ProductID` | **100/100** | catalogue lookup |
| `Categories` | **100/100** | copy angle |
| `ProductName` | **100/100** | fallback label |
| `Locale` | **0/100** | translating |

---

## 5. The asks

### Ask 1 — `Locale` on `Started Checkout` and `Viewed Product`
**Blocks 9 of 24 emails from leaving Ireland.**

It is absent from both events entirely, 0 of 100 each. Those nine emails
therefore carry hardcoded `/en-ie/` links and no locale conditionals at all,
against 24 conditionals in a Post-Purchase email that does have `Locale`. They
can run in Ireland and nowhere else.

- **Field:** `Locale`
- **Format:** the same values `Placed Order` already sends, exactly:
  `en-IE, en-GB, nl-NL, nl-BE, fr-FR, fr-BE, es-ES, it-IT`
- **Done when:** 100% of both events carry one of those eight values.

### Ask 2 — `Categories` on `Placed Order` from v4, and on the missing presta share
**Blocks the 5 category nudges from being routed.**

Without it the flow cannot tell whether somebody bought signage or stationery, so
every one of those customers falls to the default branch or drops out.

- **Field:** `Categories`, on `Placed Order`
- **Format:** flat array of three-element groups per order line, English, as §3
- **v4 today:** 0 of 13. The `Items[]` on those events carry no category field of
  any kind either, so it cannot be derived in the template as a fallback.
- **presta today:** 61 of 87. The missing 30% needs a cause; it is not obviously
  one shop or one market.
- **Done when:** ≥99% of `Placed Order` on both stacks carries it.

### Ask 3 — `ProductID` on every `Started Checkout` item line
**Small, but it can blank a whole email rather than degrade it.**

`ProductID` is on 145 of 150 item lines. The five that lack it matter more than
5 lines suggests: the abandoned-order emails open a catalogue lookup per line,
and in this account a catalogue lookup on a missing or empty id fails the
**entire** render, not just that row. One bad line can cost the whole email.

We are adding a guard on our side so a missing id skips its row instead of
killing the send (see below), so this is not a blocker. It is still worth closing.

- **Field:** `ProductID` on each entry of `Items[]`, on `Started Checkout`
- **Done when:** 100% of item lines carry a non-empty id.

### Not an ask: two fixes on our own side

Neither of these is an ask of you. They are recorded because they were found in
the same pass and they change what we need from the event.

**`ProductURL` is not something we should be asking for.** Six abandoned-order
emails print `{{ it.ProductURL }}`, and that field is on only **8 of 150** item
lines, so the product link in the basket table is empty for about 95% of rows
today. That is our bug, not yours. The templates already open
`{% catalog it.ProductID %}` for the product image, so the fix is to take the
link from the catalogue in the same block rather than from the event. **Do not
add `ProductURL` on our behalf** — we would rather read one source than two.

**A guard around the catalogue lookup**, so a line with no `ProductID` skips its
row instead of failing the render. See ask 3.

---

## 6. A note on the v4 numbers

v4 was 13% of `Placed Order` in this sample, and **9 of those 13 were test
orders** (`PlaywrightTest…`, `luukjansenhp+guest…`). Real v4 volume today is
therefore smaller than 13%.

That is an argument for fixing it now rather than later. It is cheap while the
stack is small and it becomes a silent, growing failure as the migration
proceeds: the flow will keep running and keep picking the wrong branch for an
increasing share of customers, with nothing in the reporting to say so.

---

## 7. How to reproduce these numbers

Metric ids in this account: `Placed Order TuC7Z7`, `Ordered Product XGuVCG`,
`Started Checkout T3uGk6`, `Viewed Product WX8EsF`.

Pull the 100 most recent events of a metric with `fields[event]=event_properties`
and count how many carry each field. Classify the stack on `event_source`
versus `ctMessageId`/`store`.

**Caveat.** These are the 100 most recent events per type at one moment. The
direction is solid and was consistent across two independent samples on the same
day; the exact percentages are indicative, and the presta/v4 mix will move as the
migration proceeds. Anyone acting on this should re-measure over a longer window
before quoting a figure externally.

---

## 8. Appendix: what each email reads from its event

Extracted from the built Klaviyo templates in `proposals/*-klaviyo.html`, so this
is what the HTML actually references rather than what anyone intended.

| Emails | Reads from the event |
|---|---|
| 5 category nudges | `Locale` — plus `Categories` in the flow's conditional split, not in the HTML |
| post-01, post-02 | `Locale` |
| post-04, post-05, post-06 | `Locale` |
| 5 winback | `Locale`; three also use Klaviyo's `{% catalog person %}` recommendation engine, which needs no event data |
| 6 abandoned order | `CheckoutURL`, `Items[ProductID, ProductName, Quantity, RowTotal]`, and `Items[ProductURL]` which is 5% populated and being removed from the templates see below |
| 3 browse | `ProductID`; browse-01 also `Categories` |

The winback flow reads nothing from any event and is not affected by anything in
this document.
