# Slack message: locale on the Klaviyo profile

Slack formatting (`*bold*`, backticks, plain URLs) so it renders on paste.

---

Hi team, one change to the Klaviyo profile data, and it *replaces* the earlier
ask for `Locale` on `Started Checkout` and `Viewed Product` — that one is
withdrawn, this is smaller and covers more.

*What we need*

1. Write the *native* Klaviyo profile field `locale` — the first-class field, set
via `attributes.locale`. Not a custom property.
2. *In the same pass, `unset` the custom property also called `locale`.*

Format: `en-IE, en-GB, nl-NL, nl-BE, fr-FR, fr-BE, de-DE, es-ES, it-IT`
(`de-DE` is new — DACH is in the programme now).

When: at registration *and* refreshed on every order. It has to be maintained,
not set once — someone who signs up on nl-NL and then only ever buys on fr-BE
would otherwise keep getting Dutch.

*Why both halves, and why the same pass*

A custom property named `locale` *shadows* the native field. We verified this
with a preview send yesterday against a profile deliberately set to native
`nl-NL` with a custom `properties.locale` of `it-IT` — the email rendered
*Italian*. With the custom property unset and native unchanged, the same
template rendered *Dutch*.

Of 82 real profiles created on 31 August, *51 carried both fields*, and one
already disagreed with itself: native `fr-FR` against custom `en-GB`. So if
native gets written first and the custom one lingers, the backfill has *no effect
on exactly the profiles that already look correct* — and nothing errors, so it
looks like it worked.

*Two practical notes*

• Use `unset`, not an empty string. An empty value is still a value and still
shadows the native field:
```
PATCH /api/profiles/{id}
{ "data": { "type": "profile", "id": "...",
    "attributes": { "locale": "nl-NL" },
    "meta": { "patch_properties": { "unset": "locale" } } } }
```
• Three systems currently write these fields and they disagree about which.
Registration path A writes both; registration path B writes only the custom one;
the order/customer sync writes only native. All three want to write native only.

*Where we are today*: native 80% populated, custom 70%, 12% have neither.
The 12% fall through to English, which is correct and needs no fix.

*Why it matters now*: all 24 behavioural emails read `person.locale` for their
language. If the custom property is still shadowing native when they go live,
those readers get whatever the stale custom value says.

Full detail, including the measurements and how to reproduce them, is in Ask 1
here: `proposals/event-payload-handover.md`

Happy to jump on a call if it's easier.

---

## Candidate channels

I could not find where the original handover went, so pick one:

- *#group-customer-data-flows* — closest by purpose, created by Michael Heerkens
- *#group-data-catman* — has a stated data-request form:
  https://forms.gle/9E6GAbo1cLz9xG6y5 — if requests are meant to go through that
  form, this message is the form's content rather than a channel post
- *#data-analytics*

## One inconsistency worth resolving separately

Your 25 August message in #fr-growth told Sarah that "Klaviyo Smart Translations
then renders the matching language per email". That is no longer how it works:
every email carries all nine locales in one universal HTML block and switches on
`person.locale`, precisely so Smart Translations never runs over a Trustpilot
review and invents a quote. Worth correcting if anyone is planning against it.
