# Render test: does `person.locale` evaluate in Klaviyo?

Run 2026-08-31 against the live account (U9YUZK) with the template-render API,
template `VTHUJw` ("ZZ TEMP - person.locale render test"). Rendering does not
send anything and does not modify the template.

## What was tested

| id | expression |
|----|------------|
| T1 | `{% if person.locale == 'nl-NL' %}` — the exact mechanism all 9,537 switch sites use |
| T2 | the full nine-branch elif chain with an English `{% else %}` |
| T3 | `{{ person.locale }}` interpolation |
| T4 | `{% if person.locale\|slice:":2" == 'nl' %}` — previously unverified |
| T5 | `{% if person.locale == 'nl-NL' or person.locale == 'nl-BE' %}` — previously unverified |
| T6 | `{{ person\|lookup:'locale' }}` |

## Results

| context | T1 exact | T2 chain | T3 interp | T4 slice | T5 or |
|---------|----------|----------|-----------|----------|-------|
| `locale: "nl-NL"` | HIT-NL | nl-NL | nl-NL | matched | matched |
| `locale: "de-DE"` | else | **de-DE** | de-DE | no match | no match |
| `locale: "en-US"` (untranslated) | else | **ENGLISH-FALLBACK** | en-US | no match | no match |
| no locale at all | else | **ENGLISH-FALLBACK** | *(empty)* | no match | no match |

**The mechanism works.** Exact matching evaluates, the nine-branch chain selects
the right branch from anywhere in the chain, and — the case that actually
mattered — a profile with **no locale** and a profile with an **untranslated
locale** both fall through to English. Nothing errored on a missing value.

**`|slice` and `or` both work.** Avoided for the whole project as unverified.
They are a choice now, not a constraint: prefix tests would roughly halve every
block, which is worth revisiting if an email nears Gmail's ~102KB clip. The flat
chain is kept for now because it states plainly which locale gets which string,
where a prefix test hides nl-BE and fr-BE.

## Rendered against a REAL PROFILE — the decisive test

The render API takes a context the caller supplies, so it proves the syntax and
nothing about how Klaviyo builds `person` from a profile.
`create_template_preview_send_job` does render against a real profile, so two
preview sends were made to `sebastiaan.ram+klaviyo1@helloprint.com`
(profile `01M1BED36CKDMJEM5QK0PQ5CY5`), with the profile deliberately
misconfigured the first time so the answer could not be ambiguous.

| # | native `locale` | custom `properties.locale` | rendered |
|---|-----------------|----------------------------|----------|
| 1 | `nl-NL` | `it-IT` | **it-IT** |
| 2 | `nl-NL` | *(unset)* | **nl-NL** |

**`person.locale` reads the native profile field — but a custom property of the
same name SHADOWS it.**

That makes retiring the custom `locale` property mandatory rather than tidy, and
it changes the sequencing: it has to be removed in the SAME pass that populates
native, not afterwards. On 2026-08-31, 51 of 82 real profiles created that day
carried both fields, and one of them already disagreed with itself (native
`fr-FR` against custom `en-GB`). If native is written first and the custom
property lingers, the backfill has no effect on exactly the profiles that look
correct, and nothing errors.

Run 2 also re-confirmed every expression against a real profile rather than a
synthetic context: exact match, the nine-branch chain, `|slice` and `or` all
behaved identically.

## What this did NOT settle

The render API takes a **context object supplied by the caller**, not a profile.
So it proves the syntax evaluates; it does not prove that Klaviyo populates
`person.locale` from the NATIVE profile field rather than from a custom property
that happens to share the name.

That matters only while both exist. Once the custom `locale` property is retired
— which is the plan — there is one field and no ambiguity.

Nothing. Both questions are closed: the syntax evaluates, and `person.locale`
resolves to the native field once no custom property shadows it.

## State left behind

- Template `VTHUJw` deleted.
- Test profile `01M1BED36CKDMJEM5QK0PQ5CY5` left at native `locale = nl-NL` with
  no custom `locale` property, which is the intended production shape.
- Two preview emails sit in that inbox. They are previews, not sends: no flow
  ran, no metric was recorded against a customer.
