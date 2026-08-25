# Trustpilot reviews in the behavioural emails

## Setting it up

The key lives in your shell, never in this repo:

```
export TRUSTPILOT_API_KEY='...'
```

Do not paste it into a chat, a commit, or a file here. If it leaks, rotate it in
the Trustpilot developer portal rather than trying to scrub it.

Then, in order:

```
python3 scripts/_lib/trustpilot.py            # connectivity check
python3 scripts/fetch_reviews.py --inventory  # what tags exist?
python3 scripts/fetch_reviews.py              # refresh the cache
python3 scripts/build_category_nudge.py       # rebuild the emails
```

## Run `--inventory` first, because the tags cannot be guessed

The Trustpilot API has **no endpoint listing tag groups or values**. Tags appear
only inside review objects, so the only way to learn how the account tags reviews
is to fetch a sample and look. `--inventory` does that and prints the groups and
values with counts.

`TAG_MAP` in `scripts/fetch_reviews.py` currently holds a **guess** at the value
names. Replace it with the real ones and set `TAG_GROUP` to the group they live
in. Until then the fetcher matches little or nothing — which is the safe
direction to fail in, because it means placeholders rather than wrong quotes.

Worth checking on that first run: whether the category tagging sits on
**service** reviews or **product** reviews. This client reads service reviews,
which is what was asked for. Product reviews are a different endpoint
(`/v1/product-reviews/...`); if the tags live there, the client needs a second
method. Small change, but it changes the plan.

## The rule everything else follows

**A review is never translated.**

A Dutch reader gets a review a Dutch customer wrote, or a placeholder. Putting a
French customer's words through a translator and showing them under their own
name in Dutch produces a quote that person never gave — a fabricated record with
a real name on it. Same for letting Smart Translations rewrite an English review
into Spanish.

So the block is a per-language conditional on `event.Locale`, the same mechanism
the product tiles use and which is render-verified:

```
{% if event.Locale|slice:":2" == "nl" %}   a real Dutch review
{% elif event.Locale|slice:":2" == "fr" %} a real French review
{% else %}                                 the visible placeholder
{% endif %}
```

Note this is the **language** slice (`:2`), not the market slice (`3:5`) the
catalogue uses. `fr-BE` and `nl-BE` are one market but two languages, and a
Belgian reading in Dutch should get a Dutch review.

Reviews are stored and rendered **verbatim**. One too long for the block is
skipped at fetch time, never trimmed, because editing a customer's words
misrepresents them. Author and star count travel with the quote.

## The open question, and it blocks sending

**The review block has to be excluded from Smart Translations.**

Everything else in these emails is meant to be translated. Reviews are the
exception, and if a translation pass runs over them, every non-source language
ends up with an invented quote carrying a real person's name.

How Klaviyo lets a region opt out is not yet verified. Two things to try:

1. Whether Klaviyo honours a do-not-translate marker on a block or element.
2. Whether the per-language conditional survives a translation pass intact — it
   may be cleaner to keep reviews out of the translated template entirely and
   inject them as a universal block per language.

Until one is settled: send in the source language only, or leave the
placeholders in.

## Trustpilot's own rules, as they affect this

- **Do not incentivise reviews.** The day-18 review request carries no offer, and
  the discount emails sit far from it in the sequence.
- **Do not invite selectively.** Choosing which *published* review to quote in an
  ad is normal; choosing who gets *asked* is not.
- **Show reviews as written**, attributed, with the rating.

## The manual fallback

`scripts/README-trustpilot.md` documents a browser-based extraction route with
`scripts/trustpilot-extract.js`, from before the API was wired up. `curl` gets
HTTP 403 from trustpilot.com but a real browser engine loads it, so that route
still works when no key is available, or for eyeballing a locale's reviews
before trusting a fetch. It cannot filter by tag, which is why it is the
fallback rather than the plan.

That page also verified, on 24 Aug 2026, the account-wide figures the emails
quote: **score 4.5, 34,288 reviews**. Worth re-checking when the API is first
run, since the API returns them too and the site's own about-us page was already
stale at 4.4 / 31,000+.

## Why there is a cache

`data/trustpilot-reviews.json` is committed and dated. The builders read only
that, so anyone can check out this repo with no key and no network and rebuild
every preview. Refreshing is deliberate, the same shape as the Welcome price
snapshot — so a stale review shows up in review rather than in an inbox.
