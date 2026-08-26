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

Not "we miss you". That is a sentence about us.

**"Here is what changed since you last printed."** It is the only story in this
programme that gets better the longer someone has been away, and at 90 to 180 days
it is genuinely true: the range has moved, lead times have moved, prices have
moved. It gives the email a reason to exist that is not an apology or a discount.

- **High value** gets it as a person: *what you spent last time, and what I would
  do differently now.* An expert reading their own history back to them is worth
  more than 15% to somebody whose jobs are €150 and up.
- **Low value** gets it as a page: three things that are new, and a code.

### One conflict to design around

**Post-Purchase ends at day 73 with a 10% offer.** A winback discount at day 90 is
17 days behind a discount that just failed. So:

- the high branch leads with a person and holds money back to day 140, by which
  point the earlier offer is 67 days old
- the low branch's code is **15%, not 10%** — a repeat of the same number three
  weeks later reads as a resend, and 15% at 90+ days is a defensible step on the
  ladder: welcome 10, post-purchase 10, winback 15, abandoned order 25 capped

---

## 4. The design template

New, and deliberately unlike the four templates already in the programme.

**A "then and now" strip.** Two or three rows, each one line of what has changed
since they last ordered, with the change stated as a fact rather than a boast — a
format that is new, a lead time that is shorter, a price that came down. Left
column what it was, right column what it is now.

It is the only layout in the programme that carries a comparison, which is what
makes it feel like news rather than marketing. On mobile the two columns stack into
before/after pairs.

The high-value email 1 does not use it at all: that one is John's letter template
from day 45, which already exists and is the right shape for a person writing.

---

## 5. What has to be true before this can be built

1. **The "then and now" content has to be real.** Three concrete changes, checkable.
   If nothing has changed in the last six months the template is a lie and the
   storyline collapses. This needs someone from product or category to supply them,
   and they will need refreshing quarterly.
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
