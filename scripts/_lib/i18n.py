"""
Translations, held in data/translations.json and switched inside the HTML.

WHY IN THE HTML AND NOT KLAVIYO'S TRANSLATIONS. One universal block per email
carrying every language means one thing to edit when copy changes, it is version
controlled here, and nothing has to be relinked when a template is copied into a
flow message - which is the failure that made the inherited flows unmaintainable.

WHY A FLAT NINE-WAY SWITCH ON event.Locale, and not a language prefix. A prefix
test would be half the size:

    {% if event.Locale|slice:":2" == 'nl' %}

but `|slice` inside an `{% if %}` comparison has never been rendered in this
account, whereas an exact-match elif chain on event.Locale is what every template
here already uses and an 83-branch chain has been rendered successfully. The
translation programme is not the place to introduce an unverified mechanism. The
duplication is free: Klaviyo renders before it sends, so exactly one branch
reaches the reader.

Prose is chosen by LANGUAGE, links and product names by MARKET, and both are
resolved per locale, so a Flemish or Belgian-French exception is a one-line
override rather than a restructure.

ENGLISH IS THE SOURCE AND THE FILE KNOWS IT. Every entry carries its "en" value.
The builder passes the English string it is about to render and check_source
refuses to run if the two have drifted, so editing English copy without revisiting
its translations fails the build instead of silently shipping a stale sentence.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PATH = os.path.join(ROOT, "data", "translations.json")

SOURCE = "en"
LANGS = ["en", "nl", "fr", "de", "es", "it"]

# Klaviyo locale -> which language's prose it reads. Two markets share a language
# and differ only in their links, which is the whole reason prose and links are
# resolved separately.
LOCALE_LANG = {"en-IE": "en", "en-GB": "en",
               "nl-NL": "nl", "nl-BE": "nl",
               "fr-FR": "fr", "fr-BE": "fr",
               "de-DE": "de", "es-ES": "es", "it-IT": "it"}
LOCALES = list(LOCALE_LANG)
FALLBACK_LOCALE = "en-GB"

_D = None


def data():
    global _D
    if _D is None:
        with open(PATH, encoding="utf-8") as f:
            _D = json.load(f)
    return _D


def _entry(email, key):
    d = data()
    for scope in (email, "_shared"):
        e = (d.get(scope) or {}).get(key)
        if e is not None:
            return e
    return None


def get(email, key, locale, english=None):
    """The string for one locale.

    Resolution order: an exact per-locale override, then the locale's language,
    then English. A per-locale override is how a Flemish or Belgian-French
    exception gets in without giving those markets their own everything.
    """
    e = _entry(email, key)
    if e is None:
        return english
    if locale in e:
        return e[locale]
    lang = LOCALE_LANG.get(locale, SOURCE)
    return e.get(lang) or e.get(SOURCE) or english


def missing(email, key):
    """Languages with no translation for this key."""
    e = _entry(email, key)
    if e is None:
        return list(LANGS)
    return [l for l in LANGS if not (e.get(l) or "").strip()]


def source_drift(email, key, english):
    """Whether the English in the file differs from the English being rendered.

    Returns the stored English when it has drifted, else None. This is what stops
    an edit to the source copy from leaving five languages quietly out of date.
    """
    e = _entry(email, key)
    if e is None:
        return None
    stored = (e.get(SOURCE) or "").strip()
    if stored and english is not None and stored != english.strip():
        return stored
    return None


def keys_for(email):
    d = data()
    return sorted((d.get(email) or {}).keys())


def shared_keys():
    return sorted((data().get("_shared") or {}).keys())


# ---------------------------------------------------------------- the switch
#
# Lives here rather than in a builder because there are ten builders and one
# correct way to emit this. Two of them had already been written by hand and both
# had leaks: a helper pinned to one locale, and a call site that never received
# the translator at all.
MISSING, DRIFT = [], []


def translator(scope, live, locale=None):
    """tr(key, english, escape=None) -> one locale's text, or a nine-way switch.

    NINE BRANCHES AND NO `or`, and {% else %} is always English. Grouping locales
    that share a translation would halve the size, but `or` inside an {% if %} has
    never been rendered in this account and neither has `|slice`; an exact-match
    elif chain has, including an 83-branch one. Using the last locale as the else
    would serve Italian to any locale we do not know about.

    ESCAPE AFTER TRANSLATING, never before: passing esc(english) in makes the
    drift check compare an escaped string against the raw one on file, and it
    cannot be done afterwards because by then the string is a Django switch.
    """
    def tr(key, english, escape=None):
        e = escape or (lambda x: x)
        miss = missing(scope, key)
        if miss:
            MISSING.append((scope, key, miss))
        drifted = source_drift(scope, key, english)
        if drifted:
            DRIFT.append((scope, key, english, drifted))
        if not live:
            return e(get(scope, key, locale or "en-GB", english))
        texts = [(loc, e(get(scope, key, loc, english))) for loc in LOCALES]
        if len({t for _, t in texts}) == 1:
            return texts[0][1]
        out = ""
        for i, (loc, txt) in enumerate(texts):
            out += "{%% %s event.Locale == '%s' %%}%s" % (
                "if" if i == 0 else "elif", loc, txt)
        return out + "{%% else %%}%s{%% endif %%}" % e(
            get(scope, key, FALLBACK_LOCALE, english))
    return tr


def report(errs, warns=None):
    """Drift is an error, missing translations are a count. Call from a builder."""
    seen = set()
    for scope, key, now, stored in DRIFT:
        if (scope, key) in seen:
            continue
        seen.add((scope, key))
        errs.append("%s: English for %r changed since it was translated. Now %r, "
                    "translated from %r. Update data/translations.json."
                    % (scope, key, now[:48], stored[:48]))
    need = {}
    for scope, key, miss in MISSING:
        need.setdefault(scope, set()).add(key)
    return {k: sorted(v) for k, v in need.items()}


def leaks(path, lang, phrases):
    """English found in a non-English preview means a call site is unwired.

    Visible text only: the first version of this read the raw file and reported a
    phrase that turned out to be a CSS comment, in every file.
    """
    import housestyle
    if lang == SOURCE:
        return []
    txt = housestyle.visible(open(path, encoding="utf-8").read())
    return [p for p in phrases if p.lower() in txt]
