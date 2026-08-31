"""
Serve cached Trustpilot reviews to the email builders.

Reads data/trustpilot-reviews.json, which scripts/fetch_reviews.py writes. No
network, no credentials - so every preview rebuilds from a clean checkout.

THE RULE THAT SHAPES ALL OF THIS: A REVIEW IS NEVER TRANSLATED.

A Dutch reader gets a review a Dutch customer actually wrote, or they get the
placeholder. Running a French customer's words through a translator and showing
them to a Dutch reader under "Verified Trustpilot review" produces a quote that
nobody ever said - a fabricated record with a real person's name on it. Same for
letting Klaviyo's Smart Translations rewrite an English review into Spanish.

That has a consequence for the Klaviyo build, and it is the one open question
worth resolving before these emails send: the review block must be EXCLUDED from
Smart Translations. If translation runs over it, every non-source-language
version becomes an invented quote. Two ways to avoid it and neither is verified
yet - see the note in build_category_nudge.py.

The language branch is emitted as a Django conditional on the locale, the same
mechanism the product tiles already use and which is render-verified:

    {% if person.locale == "nl-NL" %} <a real Dutch review>
    {% elif person.locale == "nl-BE" %} <a real Dutch review>
    ...
    {% else %} <the placeholder, visibly marked>
    {% endif %}

So a language with no suitable review shows a placeholder rather than someone
else's words.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE)) if os.path.basename(HERE) == "_lib" else HERE
CACHE = os.path.join(os.path.dirname(os.path.dirname(HERE)), "data",
                     "trustpilot-reviews.json")

# The locale prefix the email branches on. event.Locale is "nl-NL", "fr-BE" and
# so on, so the first two characters are the language - which is what a review
# is written in. Note this is deliberately NOT the market slice used for the
# catalogue: fr-BE and nl-BE are one market but two languages, and a Belgian
# reading in Dutch should get a Dutch review.
# KEPT FOR REFERENCE, NO LONGER USED IN A CONDITIONAL. The review block used to
# branch on this, and `|slice` inside an {% if %} comparison has never been
# rendered in this account: if it does not evaluate, every locale falls through to
# {% else %} and every email shows the placeholder instead of a review. That is a
# silent failure, so the switch moved to exact matches on event.Locale, which is
# what every other switch in these templates uses and has been rendered.
LANG_EXPR = 'person.locale|slice:":2"'  # unverified in an {% if %}; do not branch on it

# The reader's locale comes from the PROFILE, not the event: a list-triggered
# flow has no event, so event.Locale silently served English. Kept in step with
# i18n.LOCALE_EXPR, which is the canonical definition.
LOCALE_EXPR = "person.locale"


def _load():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"fetched": None, "reviews": {}, "languages": []}


_DATA = _load()


def fetched():
    return _DATA.get("fetched")


def languages():
    return _DATA.get("languages") or []


def get(category_slug, language):
    """The cached review for this category and language, or None."""
    return (_DATA.get("reviews") or {}).get("%s|%s" % (category_slug, language))


def available(category_slug):
    """Languages that have a real review for this category."""
    return [l for l in languages() if get(category_slug, l)]


def attribution(r, outof="out of 5 on Trustpilot"):
    """The line under the quote. Star count and author are part of showing a
    review honestly, so they are not optional.

    The NAME is never translated and neither is the quote. Only the "out of 5 on
    Trustpilot" scaffolding is, which the caller passes in.
    """
    who = r["author"]
    if r.get("author_location"):
        who += ", " + r["author_location"]
    return "%s &middot; %d %s" % (who, r["stars"], outof)


def score():
    """The live TrustScore, as a dated snapshot in the cache.

    Refresh with `python3 scripts/fetch_reviews.py --score-only`, which touches
    these two numbers and nothing else."""
    return _DATA.get("score")


def review_total():
    return _DATA.get("review_total")


def score_fetched():
    return _DATA.get("score_fetched")


# WHERE A REVIEW GETS WRITTEN, per language rather than per country.
#
# Trustpilot serves its review form in the language of the subdomain, and there
# are eight locales but only six languages. Belgium is the reason this is keyed on
# language: be.trustpilot.com has to pick one of Dutch or French, and whichever it
# picks is wrong for half of Belgium. nl and fr both get a form they can read.
#
# NO PER-STAR LINKS. The obvious design is a row of five stars each linking to
# ?stars=N. It does not work: loading /evaluate/helloprint.com?stars=4 leaves all
# five radios unchecked, so a reader who clicks four stars lands on a blank form.
# One button, and it says what it does.
TP_BY_LANG = {"en-IE": "ie", "en-GB": "uk", "nl": "nl", "nl-BE": "nl",
              "fr-FR": "fr", "fr-BE": "fr", "es-ES": "es", "it": "it",
              # Added with the German market. Without it write_url falls through
              # to its "uk" default, so a German reader would have been sent to
              # uk.trustpilot.com to review a German order. de.trustpilot.com
              # returns 200.
              "de-DE": "de"}
TP_URL = "https://%s.trustpilot.com/evaluate/helloprint.com"


def write_url(cf_locale):
    return TP_URL % TP_BY_LANG.get(cf_locale, "uk")


def count():
    return len(_DATA.get("reviews") or {})


def quote_switch(pool, tr, locale=None, live=False, byline_en="verified Trustpilot review"):
    """One review as (quote, byline), in the reader's own language.

    WHY THIS EXISTS. Three of the abandoned-order emails carried a hardcoded
    English quote, so a Dutch or German reader was shown an English stranger
    vouching for us. Translating that quote would have been worse: it would put
    words in a named person's mouth that they never said. The quote is SWAPPED
    for one a customer in that language actually wrote.

    In live mode both halves come back as one exact-match switch on
    person.locale, English in the {% else %}, matching every other switch in
    these templates.
    """
    by = tr("rev.by", byline_en)

    def pair(lang):
        r = get(pool, lang)
        return None if not r else ("&ldquo;%s&rdquo;" % r["text"],
                                   "%s &middot; %s" % (r["author"], by))

    if not live:
        p = pair(LOCALE_LANG_LOCAL.get(locale or "en-GB", "en"))
        return p or pair("en") or ("", by)

    qs, bs = "", ""
    for loc in LOCALES_LOCAL:
        p = pair(LOCALE_LANG_LOCAL[loc])
        if not p:
            continue
        kw = "if" if not qs else "elif"
        qs += "{%% %s %s == '%s' %%}%s" % (kw, LOCALE_EXPR, loc, p[0])
        bs += "{%% %s %s == '%s' %%}%s" % (kw, LOCALE_EXPR, loc, p[1])
    en = pair("en")
    if not qs or not en:
        return (en[0] if en else "", en[1] if en else by)
    return (qs + "{%% else %%}%s{%% endif %%}" % en[0],
            bs + "{%% else %%}%s{%% endif %%}" % en[1])


# kept local so reviews.py does not import i18n and create a cycle
LOCALE_LANG_LOCAL = {"en-IE": "en", "en-GB": "en", "nl-NL": "nl", "nl-BE": "nl",
                     "fr-FR": "fr", "fr-BE": "fr", "de-DE": "de", "es-ES": "es",
                     "it-IT": "it"}
LOCALES_LOCAL = list(LOCALE_LANG_LOCAL)
