# Pulling Trustpilot reviews — the manual browser route

**This is now the fallback.** The primary path is the API client added later:
`scripts/fetch_reviews.py`, documented in `docs/trustpilot-reviews.md`. It does
what the last section of this file recommended — `/v1/business-units/{id}/reviews`
with language and stars filters, key in `TRUSTPILOT_API_KEY` — and adds tag
filtering, which is what makes per-category reviews possible.

Keep this page for the case where the key is unavailable, or to eyeball what a
locale's reviews look like before trusting a fetch.


`curl` and `fetch` get **HTTP 403** from Trustpilot. A real browser engine loads
the page fine, so use the Claude Code browser tool (or a normal browser console).

## Procedure

1. Open `https://<locale>.trustpilot.com/review/helloprint.com?stars=5&languages=<lang>&sort=recency`
2. Run `trustpilot-extract.js`
3. Take the `shortlist` (5 star, verified, <=130 chars, single line)

The first load may show a transient "Verifying Connection" page; it resolves on
its own. Do not attempt to defeat any challenge that persists.

## Locale map

| Email locale | Trustpilot host | `languages` |
|---|---|---|
| en-IE | `ie.` | `en` |
| en-GB | `uk.` | `en` |
| nl-NL | `nl.` | `nl` |
| de-DE | `de.` | `de` |
| fr-FR / fr-BE | `fr.` | `fr` |
| es-ES | `es.` | `es` |
| it-IT | `it.` | `it` |
| sv-SE | `se.` | `sv` |

Confirmed working: `ie` (en) and `nl` (nl). Others follow the same pattern but
are unverified.

## Live figures (checked 24 Aug 2026)

Score **4.5**, **34,288** reviews — account-wide, not per locale.
Note `helloprint.com/en-ie/about-us` says 4.4 / 31,000+, which is **stale**.
Trustpilot renders 4.5 as four-and-a-half stars.

## For automation — done, see the API client

This section called it correctly: the API supports language and stars filters
and returns full text. `scripts/_lib/trustpilot.py` implements it, plus
`tagGroup` / `tagValue` for the category tagging, and reads the key from
`TRUSTPILOT_API_KEY` exactly as recommended here.
