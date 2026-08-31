#!/usr/bin/env python3
"""
Translate the four Welcome emails, which have no builder.

WHY THIS IS A POST-PROCESSOR AND NOT A BUILDER. The other twenty-four emails are
generated, so their copy passes through a translator on the way out. Welcome is
hand-written HTML from before that existed. Rewriting it as a builder would be a
day's work and would risk changing an email that is finished and approved, to gain
nothing a substitution cannot do.

So this reads the English file, swaps each known string for its translation, and
writes the per-language previews and one Klaviyo file carrying every language.

EVERY STRING MUST BE FOUND. A substitution that silently matches nothing leaves
English in a translated email and looks exactly like a translation nobody wrote,
which is the failure this whole programme keeps hitting. If a string is not in the
file, this fails and names it.
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
import i18n
import reviews as rv

OUT = os.path.join(ROOT, "proposals")
EMAILS = ["welcome-01", "welcome-02", "welcome-03", "welcome-04"]

# Strings shared by all four: the footer, the help block, the discount bar.
SHARED_IN_FILE = [
    # The discount bar sits in all four files but its text lives in _shared, so it
    # is not in any email's own key list and was silently skipped: three of the
    # four previews shipped with an English bar over translated copy.
    ("wc.discount", "Your 10% welcome discount"),
    ("wc.waiting", "Your 10% is still waiting"),
    ("wc.expires5", "&nbsp;&middot;&nbsp;Valid only 5 days"),
    ("wc.help", "Do you need help?"),
    ("alt.cs_agents", "Three Helloprint customer service agents"),
    ("help.chat", "Chat with us"),
    ("help.centre", "Help Centre"),
    ("foot.unsub", "Unsubscribe"),
]

errs = []

# A REVIEW IS SWAPPED, NEVER TRANSLATED. welcome-03 shipped three English
# Trustpilot quotes to every locale, so a Dutch reader got three English
# strangers. Running them through a translator instead would be worse: it
# would put words in a named person's mouth that they never said.
#
# Three DIFFERENT category pools, because the cache holds one review per
# category per language and this block shows three at once. Pulling all three
# from one pool would repeat the same quote three times.
REVIEW_POOLS = ["commercial-print", "signage-outdoor", "stationery"]
QUOTE_RE = re.compile(
    r'(<span class="hp-w3-quote">)&ldquo;(.*?)&rdquo;(</span>'
    r'<span class="hp-w3-who">)(.*?)(</span>)', re.S)


def swap_reviews(html, slug, tr, locale=None, live=False):
    """Replace each hardcoded English review with one written in the reader's
    own language."""
    if slug != "welcome-03":
        return html
    byline = tr("rev.by", "verified Trustpilot review")

    def one(lang, i):
        r = rv.get(REVIEW_POOLS[i], lang)
        return r if r else None

    def cell(m, i):
        open_q, _q, mid, _who, close = m.groups()
        if not live:
            r = one(i18n.LOCALE_LANG.get(locale or "en-GB", "en"), i)
            if not r:
                return m.group(0)
            return "%s&ldquo;%s&rdquo;%s%s &middot; %s%s" % (
                open_q, r["text"], mid, r["author"], byline, close)
        # live: one branch per locale, exact match, English in the else
        out = ""
        for n, loc in enumerate(i18n.LOCALES):
            r = one(i18n.LOCALE_LANG[loc], i)
            if not r:
                continue
            out += "{%% %s %s == '%s' %%}&ldquo;%s&rdquo;%s%s &middot; %s" % (
                "if" if not out else "elif", i18n.LOCALE_EXPR, loc,
                r["text"], mid, r["author"], byline)
        if not out:
            return m.group(0)
        en = one("en", i)
        out += "{%% else %%}&ldquo;%s&rdquo;%s%s &middot; %s{%% endif %%}" % (
            en["text"], mid, en["author"], byline)
        return open_q + out + close

    idx = [0]

    def repl(m):
        i = idx[0]
        idx[0] += 1
        return cell(m, i)

    return QUOTE_RE.sub(repl, html)


def strings_for(slug):
    """Every (key, English) this email substitutes, from the translation file."""
    d = i18n.data()
    keys = [(k, (d.get(slug) or {})[k]["en"]) for k in sorted((d.get(slug) or {}))]
    return keys + [(k, e) for k, e in SHARED_IN_FILE]


def render(html, slug, locale=None, live=False):
    """Swap each English string for one locale's text, or for a nine-way switch.

    LONGEST FIRST. "Your 10% welcome discount" contains no other string here, but
    "Chat with us" sits inside nothing while "Do you need help?" could. Replacing
    short strings first lets a later substitution match inside text that has
    already been translated, which produces a sentence half in each language.
    """
    tr = i18n.translator(slug, live, locale)
    pairs = sorted(strings_for(slug), key=lambda kv: -len(kv[1]))
    for key, eng in pairs:
        if eng not in html:
            # a _shared string need not be in every file: welcome-01 has the
            # discount bar, welcome-02 has the waiting one. Only an email's OWN
            # key missing is a real fault.
            if key not in (i18n.data().get(slug) or {}):
                continue
            errs.append("%s: %r is not in the file, so nothing was translated for it"
                        % (slug, eng[:56]))
            continue
        html = html.replace(eng, tr(key, eng))
    return swap_reviews(html, slug, tr, locale, live)


for slug in EMAILS:
    src = os.path.join(OUT, slug + "-proposed.html")
    if not os.path.exists(src):
        errs.append("%s: no English file at %s" % (slug, src))
        continue
    english = io.open(src, encoding="utf-8").read()
    for lg in i18n.LANGS:
        if lg == i18n.SOURCE:
            continue
        loc = next(l for l, x in i18n.LOCALE_LANG.items() if x == lg)
        io.open(os.path.join(OUT, "%s-%s-proposed.html" % (slug, lg)), "w",
                encoding="utf-8").write(render(english, slug, loc))
    io.open(os.path.join(OUT, slug + "-klaviyo.html"), "w",
            encoding="utf-8").write(render(english, slug, None, True))
    print("  %-12s -> 5 language previews + 1 Klaviyo block" % slug)

# ---- nothing English may survive in a translated preview
LEAKS = ["Do you need help?", "Chat with us", "Help Centre",
         "Start your first order", "Read our story", "Read the reviews"]
import glob
for f in sorted(glob.glob(os.path.join(OUT, "welcome-0*-*-proposed.html"))):
    lg = os.path.basename(f).rsplit("-", 2)[1]
    for p in i18n.leaks(f, lg, LEAKS):
        errs.append("%s: English left in the %s preview (%r)"
                    % (os.path.basename(f), lg, p))

need = i18n.report(errs)
if need:
    print("\ntranslations still to write:")
    for s in sorted(need):
        print("  %-14s %s" % (s, ", ".join(need[s])[:80]))
if errs:
    for e in errs:
        print("  FAIL  " + e)
    raise SystemExit(1)
print("all self-checks passed")
