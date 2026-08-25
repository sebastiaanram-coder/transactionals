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

    {% if event.Locale|slice:":2" == "nl" %} <a real Dutch review>
    {% elif event.Locale|slice:":2" == "fr" %} <a real French review>
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
LANG_EXPR = 'event.Locale|slice:":2"'


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


def attribution(r):
    """The line under the quote. Star count and author are part of showing a
    review honestly, so they are not optional."""
    who = r["author"]
    if r.get("author_location"):
        who += ", " + r["author_location"]
    return "%s &middot; %d out of 5 on Trustpilot" % (who, r["stars"])


def count():
    return len(_DATA.get("reviews") or {})
