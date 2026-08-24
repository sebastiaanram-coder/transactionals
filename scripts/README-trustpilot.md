# Pulling Trustpilot reviews for the behavioural emails

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

## For automation

Browser extraction needs a session. To script this per locale on a schedule,
use the **Trustpilot Business API** (`/v1/business-units/{id}/reviews`), which
supports language and stars filters and returns full text. It needs an API key,
so keep it in an env var (`TRUSTPILOT_API_KEY`) and never in the repo.
