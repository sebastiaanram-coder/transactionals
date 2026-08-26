# Customer Winback — proposal

A proposal. Nothing built. Replaces four emails in four days with a flow that
knows who it is writing to.

---

## 1. Why day 90 / 91 / 92 / 93 is wrong, and what the data says instead

Four emails inside four days, ninety days after somebody stopped ordering. It
treats a three-month silence as an emergency that needs resolving by Thursday.

### The measurement

159 buyers, sampled from Klaviyo profiles created between April and August 2026,
read from `predictive_analytics`. Two caveats up front, because they shape
everything below:

- **Klaviyo only holds 4½ months of history.** The oldest profile in the account
  is 8 April 2026. So `historic_number_of_orders` is truncated: a customer with one
  order in Klaviyo may have ten years behind them in presta. **Frequency is
  advisory. Order value is not** — one order gives you a reliable AOV.
- **The sample still contains Connect.** Resellers are in here, and they are the
  accounts with 200 to 2,560 orders. Where it matters below, the top frequency
  decile is excluded.

### What the customer base actually looks like

| Orders | n | Median AOV | Median value | Median gap between orders |
|---|---|---|---|---|
| 1 | 50 | €58 | €53 | — |
| 2–3 | 18 | €71 | €163 | **180 days** |
| 4–9 | 21 | €92 | €558 | **91 days** |
| 10–49 | 33 | €115 | €2,092 | **64 days** |
| 50+ | 37 | €105 | €31,046 | 13 days |

**The last column is the argument.** A single 90-day trigger is:

- **far too early** for the occasional buyer, whose own rhythm is 180 days — at day
  90 they are halfway through a normal gap, not lapsed
- **about right** for the 4–9 order customer at 91 days
- **late** for the regular at 64 days, who has already missed a cycle

One trigger cannot be correct for all three. That is the case for splitting, and
it is a stronger case than "high value people deserve nicer emails".

### And value concentrates, once resellers are out

Excluding the top frequency decile (≥208 orders):

| Threshold | Share of customers | Share of value |
|---|---|---|
| AOV ≥ €150 | 24% | **49%** |
| AOV ≥ €100 | 43% | 81% |
| Orders ≥ 2 | 61% | **98%** |

A clean Pareto split at €150 AOV. Note that **with resellers left in, this inverts**
— AOV ≥150 looked like 22% of customers holding only 12% of value, because a
€20-AOV account placing 87 orders outweighs everything. Any threshold set on the
unfiltered base would have been backwards.

---

## 2. The proposal

### Trigger

`Placed Order` + 90 days, no order since. Connect excluded. As specified.

### First split: is ninety days actually late for this person?

Before anything else, a conditional split on `average_days_between_orders`.

- **Gap > 120 days** → they are mid-cycle, not lapsed. **Hold until day 180.** For
  the 2–3 order customer whose rhythm is 180 days, day 90 is not a winback, it is
  an interruption.
- **Gap ≤ 120 days, or unknown** → start now.

This costs one split and it is the single most valuable thing in the flow.

### Second split: value

On `average_order_value`, at **€150**. It is the Pareto point, and AOV is the axis
that survives having only 4½ months of history. Frequency would be the textbook M/F
combination and it is not trustworthy yet — revisit once Klaviyo has a year.

### The two branches

**High value — AOV ≥ €150 · 24% of customers, half the value · 3 emails**

| Day | Email | Lever |
|---|---|---|
| 90 | A print expert, by name, offering to look at what they last spent and where it could go further | None |
| 111 | What changed since they last printed — new formats, faster turnarounds, prices that moved | None |
| 140 | 15%, with a real deadline | Money |

**Low value — AOV < €150 · 2 emails**

| Day | Email | Lever |
|---|---|---|
| 90 | What changed, and the code | 15% |
| 120 | Last call on the code | Money |

Fewer emails to the people worth less, and no human time spent where the order
value cannot carry it.

### Why the intervals widen

21 and 29 days on the high branch, 30 on the low one. The longer somebody has been
gone, the less a fast follow-up helps — the four-days-in-a-row schedule assumes the
opposite. Total span is 50 to 70 days rather than four.

---

## 3. The commercial idea, and the storyline

**Products, not a changelog.** The first version of this led on "what changed since
you last printed", laid out as a then-and-now comparison. That was the wrong
instinct — it is how software announces itself, and this is a print business selling
products. It also depended on somebody supplying three checkable changes, which
nobody had.

**What replaces it: things to come back to.** A grid of four recommended products,
image and name, no prices. It says nothing that has to be verified and it puts the
range in front of somebody who has stopped looking at it.

- **High value** still opens with a person at day 90 — that part worked. The grid
  arrives at day 111 with no offer attached, and again at day 140 with the code.
- **Low value** gets the grid and the code together at day 90, and a two-tile
  version on the day-120 last call so the code has something to be spent on.

**No prices on the tiles**, following the category nudge. A browse invitation
reading "from €300.11 for 100 units" argues against itself, and the whole bug class
behind "for 500.0 unités" disappears when there is no number to format.

---

## 4. Where the products come from, and what needs checking

**Klaviyo's recommendation engine**, via `{% catalog person %}` in the custom HTML
block. Three things about that, and the first is the one that matters.

**It names no product ids, which is what makes it safer than the tiles this
programme removed.** The category nudge was deliberately rebuilt without
`{% catalog %}` because a lookup on a missing id returns HTTP 400 and *the whole
email fails to send* — and 10 of 144 market-product pairs were missing. A
recommendation block asks for n items and gets whatever exists, so there is no id to
miss. **That reasoning needs one test render to confirm before this is switched on.**
I could not run it: the template-create endpoint rejects the nested payload through
this tooling.

**Rows are cut with `|slice`, not `divisibleby`.** `|slice` is verified to work in
this account; `divisibleby` is not. The build fails if `divisibleby` appears.

**Category-scoped recommendations are not available.** Every catalogue category
returns an empty `external_id`, so they all share one compound id — "more of what
they bought" cannot be expressed. Whatever the engine returns is what it returns,
and if that turns out to be poorly targeted, the fallback is the same Contentful
subcategory tiles the category nudge uses, which are already verified.

**And the recommended images inherit a known problem.** The feed's images are still
1200px PNGs on IE and NL, up to 1.65 MB each. A four-tile grid of those is a heavy
email in exactly the two markets that were not fixed.

---

## 5. What has to be true before this can be built

1. **One test render of the recommendation block**, to confirm `{% catalog person %}`
   works in a custom HTML block and that it degrades safely when the engine has
   nothing to recommend. This is the only unverified thing in the flow.
2. **15% needs a coupon**, and the same expiry problem as everything else: presta
   v3 cannot expire per customer, Talon.one can.
3. **The high-value email needs a named sender with a monitored inbox**, same
   dependency as day 45.
4. **Connect exclusion** on the trigger, same filter as the rest.

---

## 6. What I am least sure about

**The €150 threshold rests on 95 customers** after reseller exclusion, from 4½
months of a new Klaviyo account. It is the right shape and roughly the right place;
it is not a number to defend to two decimals. Re-derive it from presta's full
history if that is available, and revisit once Klaviyo has a year.

**The 120-day hold is a judgement, not a finding.** It sits between the 91-day and
180-day medians because that is where the two populations separate, but the right
number depends on how much the occasional buyer's 180 days is real seasonality
versus noise on 18 customers.
