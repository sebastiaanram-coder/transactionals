"""
Serve the Contentful category snapshot to the email builders.

Reads data/subcategories.json, written by scripts/fetch_subcategories.py. No
network, no credentials, so every preview rebuilds from a clean checkout.

THE EMAIL LOCALE IS NOT THE CONTENTFUL LOCALE. person.locale is "nl-NL" and
"it-IT"; Contentful calls those "nl" and "it". Belgium keeps both halves in both
systems because it is genuinely two languages in one market. LOCALE_MAP is the
translation, and it is the only place that mapping should live.

ONLY THE NAME AND THE URL VARY BY LOCALE. The surrounding copy is ours and can be
machine-translated like the rest of the email, so it appears once in the template
rather than eight times. Duplicating a whole section per locale would have cost
about 40KB against Gmail's 102KB clipping threshold; this costs about 4KB.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data", "subcategories.json")

# what the order event says -> what Contentful calls it
LOCALE_MAP = {"en-IE": "en-IE", "en-GB": "en-GB", "nl-NL": "nl", "nl-BE": "nl-BE",
              "fr-FR": "fr-FR", "fr-BE": "fr-BE", "es-ES": "es-ES", "it-IT": "it",
              # DACH, added once the numbers were looked at: 17,063 Brand Label
              # orders and EUR332k of gross profit in the twelve months to
              # 2026-09-01, which is MORE ORDERS THAN ITALY and about the same
              # gross profit - and Italy had a full translation while German had
              # nothing. Scandics was measured at the same time and left out:
              # 3,075 orders and EUR46k does not pay for a language.
              "de-DE": "de-DE"}
FALLBACK = "en-GB"
# THE PROFILE, NOT THE EVENT. A list-triggered flow has no event, so this used
# to fall through to English for every reader. See i18n.LOCALE_EXPR, which is the
# canonical definition; this is kept in step with it.
LOCALE_EXPR = "person.locale"


def _load():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"fetched": None, "subcategories": {}, "emails": {}}


_D = _load()


def fetched():
    return _D.get("fetched")


def emails():
    return _D.get("emails") or {}


def key_for(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def sub(name):
    return (_D.get("subcategories") or {}).get(key_for(name))


def field(name, cf_locale, which):
    """name or url for one Contentful locale, falling back to English."""
    s = sub(name) or {}
    by = s.get("by_locale") or {}
    row = by.get(cf_locale) or by.get(FALLBACK) or {}
    return row.get(which)


def has(name, cf_locale, which):
    """Whether this locale has its OWN value, with no fallback.

    field() resolves to English when a locale is missing, which is right for
    rendering and useless for checking - a build check written on field() can
    never fail, because there is always something to return. Anything asking "is
    this locale actually covered" has to come through here.
    """
    row = ((sub(name) or {}).get("by_locale") or {}).get(cf_locale) or {}
    return bool(row.get(which))


def image(name, w=560, h=560):
    """The category's searchImage, padded on white to the ratio asked for.

    fit=pad rather than fill: these are product shots on a light ground, so
    padding is invisible, whereas cropping a square to landscape would cut the
    top off a tall product like a roll-up banner.

    These are Contentful assets, so unlike 95% of the product feed's images they
    honour resize parameters - which is what makes a category tile lighter than a
    product tile rather than heavier."""
    s = sub(name) or {}
    u = s.get("image")
    if not u:
        return None
    return ("%s?fm=jpg&fl=progressive&fit=pad&bg=rgb:ffffff&w=%d&h=%d&q=80"
            % (u, w, h))


def locale_switch(name, which, esc=lambda x: x):
    """A Django conditional picking this field for the reader's locale.

    Only the name and the URL need this. Emitted in the order of LOCALE_MAP so
    the output is stable between builds."""
    out = ""
    for i, (email_loc, cf_loc) in enumerate(LOCALE_MAP.items()):
        v = field(name, cf_loc, which)
        if v is None:
            continue
        kw = "if" if not out else "elif"
        out += '{%% %s %s == "%s" %%}%s' % (kw, LOCALE_EXPR, email_loc, esc(v))
    fb = field(name, FALLBACK, which)
    return out + "{%% else %%}%s{%% endif %%}" % esc(fb or "")


def preview_field(name, which, locale=None):
    """What the preview shows, in the locale being previewed.

    Defaulting to en-IE is what made every translated preview show English
    product names under translated headings: the copy around the tile was
    translated and the tile itself was not.
    """
    # LOCALE_MAP, not the raw locale: the store keys Dutch as "nl" and Italian
    # as "it", so passing "nl-NL" straight through missed every record and fell
    # back to English, which is exactly the bug this argument exists to fix.
    loc = LOCALE_MAP.get(locale or "en-IE", locale or "en-IE")
    return (field(name, loc, which) or field(name, "en-IE", which)
            or field(name, FALLBACK, which) or "")


def market_path(cf_locale):
    return (_D.get("market_path") or {}).get(cf_locale)


def market_url(path, live, esc=lambda x: x):
    """A helloprint.com URL with the right market segment, per locale.

    Every email in this programme still hardcodes /en-ie/ for its home and
    help-centre links, which is on the go-live list. This is the fix, and new
    emails should use it rather than adding to that debt.
    """
    if not live:
        return "https://www.helloprint.com/%s/%s" % (market_path("en-IE"), path)
    out = ""
    for email_loc, cf_loc in LOCALE_MAP.items():
        seg = market_path(cf_loc)
        if not seg:
            continue
        kw = "if" if not out else "elif"
        out += ("{%% %s %s == '%s' %%}%s"
                % (kw, LOCALE_EXPR, email_loc,
                   esc("https://www.helloprint.com/%s/%s" % (seg, path))))
    return out + ("{%% else %%}%s{%% endif %%}"
                  % esc("https://www.helloprint.com/%s/%s" % (market_path("en-GB"), path)))


def landing(slug):
    """The snapshot key of the page the header and both buttons go to, if the
    email has one. See LANDINGS in scripts/fetch_subcategories.py for why this is
    not just the first tile."""
    return (emails().get(slug) or {}).get("landing")


def missing():
    """Any (subcategory, locale) with no name or no URL, for the build check."""
    out = []
    for k, v in (_D.get("subcategories") or {}).items():
        for el, cl in LOCALE_MAP.items():
            row = (v.get("by_locale") or {}).get(cl)
            if not row or not row.get("name") or not row.get("url"):
                out.append((k, cl))
    return out

# ---- verified market URLs -------------------------------------------------
# ROOT is already the repo root; deriving it again with one dirname too few
# pointed this at scripts/data/ and every lookup raised.
_MU_CACHE = os.path.join(ROOT, "data", "market-urls.json")
try:
    with open(_MU_CACHE, encoding="utf-8") as _f:
        _MU = json.load(_f)
except FileNotFoundError:
    _MU = {"paths": {}, "not_found": []}

MU_FALLBACK = "en-GB"


def market_url_verified(path, live, esc=lambda x: x):
    """Like market_url, but only switches to markets where the URL RESOLVES.

    market_url swaps the market segment and keeps the path, which assumes the
    slug is the same everywhere. It is not: /en-ie/about-us is a page and
    /nl-nl/about-us is a 404, and six of nine markets 404 on
    /en-ie/standardbusinesscards. Emitting those would put a dead link in a
    customer's inbox, which is worse than the Irish link it replaced.

    A locale with no working URL for this path falls back to en-GB rather than to
    the market home page: the right page in the wrong language beats the wrong
    page in the right language, and it can never 404.

    Refresh the data with scripts/fetch_market_urls.py.
    """
    good = (_MU.get("paths") or {}).get(path)
    if good is None:
        raise KeyError(
            "%r is not in data/market-urls.json, so no locale has been verified "
            "for it. Add it to PATHS in scripts/fetch_market_urls.py and re-run "
            "rather than shipping an unverified link." % path)

    # THE FEED'S OWN URL WINS. "paths" only records whether /{market}/{path}
    # resolved, which assumes one slug for every market. It is not one slug:
    # the Dutch flyer page is /nl-nl/standaardflyers and the French one is
    # /fr-fr/flyersdigital, so the same-slug test failed for both and sent each
    # reader to en-GB. "urls" holds the market's real localised URL out of the
    # catalog feed, HTTP-verified by scripts/build_market_urls_from_feeds.py.
    exact = (_MU.get("urls") or {}).get(path) or {}

    def for_locale(email_loc):
        if email_loc in exact:
            return exact[email_loc]
        seg = market_path(LOCALE_MAP[email_loc])
        if seg and email_loc in good:
            return "https://www.helloprint.com/%s/%s" % (seg, path)
        return None

    fb = (exact.get(MU_FALLBACK)
          or "https://www.helloprint.com/%s/%s"
          % (market_path(LOCALE_MAP[MU_FALLBACK]), path))
    if not live:
        return exact.get("en-IE") or (
            "https://www.helloprint.com/%s/%s" % (market_path("en-IE"), path))
    out = ""
    for email_loc in LOCALE_MAP:
        if not market_path(LOCALE_MAP[email_loc]):
            continue
        out += "{%% %s %s == '%s' %%}%s" % (
            "if" if not out else "elif", LOCALE_EXPR, email_loc,
            esc(for_locale(email_loc) or fb))
    return out + "{%% else %%}%s{%% endif %%}" % esc(fb)


def market_url_gaps(paths):
    """Which (path, locale) pairs fall back, so a builder can report them."""
    good = _MU.get("paths") or {}
    exact = _MU.get("urls") or {}
    return [(p, l) for p in paths for l in LOCALE_MAP
            if p in good and l not in good[p] and l not in (exact.get(p) or {})]
