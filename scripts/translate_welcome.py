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
import subcategories as sc
import klaviyo_assets as ka
import catalog as cat
import offers

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
    # The offer conditions. Shared, because all four has-not-ordered emails
    # carry the same ones, and stripped by the variant for the ordered branch.
    ("wc.terms",
     "Offer terms: 10% off your first order, up to @@CAP@@ maximum discount. "
     "One use per customer. The code expires 5 days after you sign up. It cannot "
     "be combined with other codes, is not valid on bespoke quotes, and applies "
     "to products only, excluding services and delivery."),
]

errs = []

# ---------------------------------------------------------------- go-live fixes
#
# Three defects the hand-written Welcome files carried that no generated email
# has, because these four never went through a builder. All three are invisible
# in a browser preview and all three break a real send.


def link_assets(html, live):
    """Swap embedded base64 images for the sentinel URL the other emails use.

    A data: URI is right for the PREVIEW - it makes the file self-contained, and
    every generated email does the same. It is wrong for the send: Gmail and
    Outlook do not render data: images at all, and the bytes pushed these four
    emails to 220-451KB against Gmail's ~102KB clipping threshold, so the images
    were broken AND the email was truncated.

    Matched by CONTENT HASH against assets/, not by position or filename, so a
    reordered or renamed image cannot silently pair with the wrong file.
    """
    if not live:
        return html
    import base64, hashlib, re as _re
    have = {}
    for root, _, files in os.walk(os.path.join(ROOT, "assets")):
        for fn in files:
            fp = os.path.join(root, fn)
            have[hashlib.sha1(open(fp, "rb").read()).hexdigest()] = fn

    def one(m):
        raw = base64.b64decode(m.group(2))
        name = have.get(hashlib.sha1(raw).hexdigest())
        if not name:
            errs.append("an embedded %s image (%d bytes) is not in assets/, so it "
                        "has no file to link to" % (m.group(1), len(raw)))
            return m.group(0)
        return 'src="%s"' % ka.url(name)

    return _re.sub(r'src="data:image/(\w+);base64,([^"]+)"', one, html)


def real_unsubscribe(html, live, tr):
    """Give the unsubscribe link somewhere to go.

    The LABEL was translated into nine locales and the HREF was left as "#". A
    dead unsubscribe link is not a cosmetic problem: it is legally required, and
    Klaviyo will not let the template send without one. Every generated email
    emits {% unsubscribe %}; these four never did.
    """
    if not live:
        return html
    # MATCH THE LINK, NOT ITS LABEL. The string substitutions run before this,
    # so by now the label is already a nine-way switch and looking for the
    # English word finds nothing. This is the second time the order of these
    # passes has bitten: the check caught it, the code did not.
    dead = re.findall(r'<a href="#">.*?</a>', html, re.S)
    if len(dead) != 1:
        errs.append("expected exactly one dead unsubscribe link to replace, "
                    "found %d" % len(dead))
        return html
    # The switch goes OUTSIDE the tag: see i18n.per_locale for why.
    return html.replace(
        dead[0],
        i18n.per_locale("{%% unsubscribe '%s' %%}", "_shared",
                        "foot.unsub", "Unsubscribe", True), 1)


# Paths these four emails link to. market_url_verified raises on anything not in
# data/market-urls.json rather than emitting an unverified link.
WC_PATHS = ["", "all-products", "cs", "about-us", "sustainability",
            "our-promises", "contact", "quote", "budgetrollupbanners",
            "posters", "standardbusinesscards", "standardflyers"]


# --------------------------------------------------------------- product tiles
#
# The four tiles in Welcome 01 were the last hardcoded thing in these emails: an
# English name, an Irish euro price written with an English decimal point, an
# English quantity, and a link to /en-ie/. All four of those are per market in
# the catalog feed, so all four now come from it. See _lib/catalog.py.

# which tile is which, recognised by the slug in its (still Irish) href
TILE_PRODUCT = [("standardflyers", "standardflyers"),
                ("standardbusinesscards", "businesscardsstandard"),
                ("budgetrollupbanners", "rollupbannersv2"),
                # LAST, and not "posters": "posters" is a substring of nothing
                # here but "standardflyers" would match before it if the order
                # were reversed for a slug like "posterflyers". Matching the
                # longest slugs first keeps this from depending on luck.
                ("posters", "posters")]

TILE_EMAILS = ("welcome-01",)

# locales whose preview cannot be derived from a language preview
PREVIEW_LOCALES = ("en-US",)

TILE_RE = re.compile(r'(<a class="hp-w1-tile" href=")([^"]*)(">)(.*?)(</a>)', re.S)


def _locale_switch(value_for, live, locale=None):
    """value_for(locale) -> text. One locale's value, or a nine-branch switch.

    Collapses to a bare string when every locale agrees, which is common for the
    English pair and saves the KB that nine identical branches would cost.
    """
    if not live:
        return value_for(locale or i18n.FALLBACK_LOCALE)
    vals = [(loc, value_for(loc)) for loc in i18n.LOCALES]
    if len({v for _, v in vals}) == 1:
        return vals[0][1]
    out = ""
    for i, (loc, v) in enumerate(vals):
        out += "{%% %s %s == '%s' %%}%s" % (
            "if" if i == 0 else "elif", i18n.LOCALE_EXPR, loc, v)
    return out + "{%% else %%}%s{%% endif %%}" % value_for(i18n.FALLBACK_LOCALE)


def catalog_tiles(html, slug, live, locale=None):
    """Name, quantity, price and link for each tile, from the market's feed.

    RUNS AFTER market_links, NOT BEFORE. market_links rewrites every
    https://www.helloprint.com/en-ie/<slug> it can see, and the en-IE branch of
    a switch emitted here still contains exactly that. Running first meant
    market_links reached inside these switches and nested a second one in each -
    the same overlap that once turned all 30 links into home-page switches. By
    running afterwards and matching on the tile's own markup instead of on its
    URL, there is nothing left for either pass to re-scan.
    """
    # Only Welcome 01 has a product grid. The other three have no tiles, so
    # running here at all would report four missing ones for each of them.
    if slug not in TILE_EMAILS:
        return html

    seen = []

    def one(m):
        open_a, href, close_a, body, end = m.groups()
        product = next((p for slug, p in TILE_PRODUCT if slug in href), None)
        if product is None:
            errs.append("a product tile links to %r, which matches no known "
                        "product, so its figures were left in English" % href[:70])
            return m.group(0)
        seen.append(product)

        def price_pair(loc):
            it = cat.item(product, loc)
            lang = i18n.LOCALE_LANG[loc]
            was = cat.money(it["price"], it["currency"], lang)
            now = cat.money(cat.discounted(it["price"]), it["currency"], lang)
            return ('<s class="hp-w1-tiwas">%s</s>&nbsp;'
                    '<span class="hp-w1-tinow">%s</span>' % (was, now))

        name = _locale_switch(lambda l: cat.item(product, l)["title"], live, locale)
        qty = _locale_switch(
            lambda l: cat.qty_label(l, product, i18n.LOCALE_LANG[l]), live, locale)
        price = _locale_switch(price_pair, live, locale)
        url = _locale_switch(lambda l: cat.item(product, l)["url"], live, locale)

        body = re.sub(r'(<span class="hp-w1-tiname">)[^<]*(</span>)',
                      lambda x: x.group(1) + name + x.group(2), body, count=1)
        body = re.sub(r'(<span class="hp-w1-tiqty">).*?(</span>)',
                      lambda x: x.group(1) + qty + x.group(2), body, count=1, flags=re.S)
        body = re.sub(r'(<span class="hp-w1-tiprice">).*?(</span></span>)',
                      lambda x: x.group(1) + price + "</span>", body, count=1, flags=re.S)
        # The alt text too. Outlook blocks images by default, so for a good
        # number of readers the alt IS the product name they see.
        body = re.sub(r'( alt=")[^"]*(")',
                      lambda x: x.group(1) + name + x.group(2), body, count=1)
        return open_a + url + close_a + body + end

    out = TILE_RE.sub(one, html)
    want = [p for _, p in TILE_PRODUCT]
    if sorted(seen) != sorted(want):
        errs.append("%s: expected the four product tiles %s, matched %s"
                    % (slug, sorted(want), sorted(seen)))
    return out


def html_lang(html, live, locale=None):
    """Set <html lang> to the reader's locale instead of a hardcoded "en"."""
    want = '<html lang="%s">' % i18n.html_lang(live, locale)
    out, n = re.subn(r'<html lang="[^"]*">', lambda _: want, html, count=1)
    if not n:
        errs.append("no <html lang> attribute to set")
    return out


# Only these two carry a Trustpilot block. Welcome 02 and 04 have none, so
# demanding a link in all four reported eight failures that were not faults.
TP_EMAILS = ("welcome-01", "welcome-03")


def trustpilot_link(html, slug, live, locale=None):
    """The "read the reviews" link per language, not hardcoded to Ireland.

    Trustpilot serves its review page in the subdomain's language, so this uses
    the same language-keyed map as the review-request link in the post-purchase
    emails - see reviews.TP_BY_LANG. It was ie.trustpilot.com in every locale,
    which put an Irish page in front of a French reader.
    """
    if slug not in TP_EMAILS:
        return html
    want = rv.url_switch(rv.read_url, sc.LOCALE_MAP, i18n.LOCALE_EXPR,
                         live, locale)
    out, n = re.subn(r'https://[a-z]{2}\.trustpilot\.com/review/helloprint\.com',
                     lambda _: want, html)
    if not n:
        errs.append("%s: no Trustpilot review link to localise" % slug)
    return out


# THE DISCOUNT CAP IS FILLED PER LOCALE, NOT PER LANGUAGE. en-GB and en-IE share
# every word of English but one market is GBP and the other EUR, so a fill keyed
# on language writes the wrong currency into one of them. i18n.tr grew fills_loc
# for exactly this.
def _cap(locale):
    lang = i18n.LOCALE_LANG[locale]
    cur = cat.item("standardflyers", locale)["currency"]
    return cat.money(offers.WELCOME_CAP, cur, lang, whole=True)


CAP_FILL = {"@@CAP@@": _cap}


def offer_code(html):
    """Put the welcome code in, from the one place it is defined.

    NOT A TRANSLATED STRING. A code is the same in every market, so putting it in
    the store would have meant six copies per email and 24 places to edit on a
    rename. It is a sentinel in the source instead, filled from
    offers.WELCOME_CODE - so the code lives in exactly one file.
    """
    if "@@CODE@@" not in html:
        return html
    return html.replace("@@CODE@@", offers.WELCOME_CODE)


def market_links(html, live):
    """Point each link at the reader's own market, where that URL exists.

    /en-ie/ was hardcoded 6-10 times per email, so a Dutch or German reader was
    sent to the Irish site. Swapping the market segment blindly would be worse:
    the slugs are localised too, so /nl-nl/about-us is a 404 and six of nine
    markets 404 on /en-ie/standardbusinesscards. Only verified URLs are switched;
    the rest fall back to en-GB, which always resolves.
    """
    if not live:
        return html

    # ONE REGEX PASS, NOT A LOOP OF str.replace.
    #
    # Replacing longest-path-first looks like it handles the overlap and does
    # not. The bare home path makes `old` "https://www.helloprint.com/en-ie/",
    # which is a PREFIX of every other link - and of the en-IE branch of every
    # switch already emitted. So the last iteration reached back into finished
    # switches and nested a home switch inside each one. All 30 links across the
    # four emails came out pointing at the home page with the path stranded
    # outside the conditional.
    #
    # A single pass cannot do that: each match is replaced once and the
    # replacement is never re-scanned.
    import re as _re

    def one(m):
        path = m.group(1)
        if path not in WC_PATHS:
            errs.append("%r is linked but not in WC_PATHS, so no locale has been "
                        "verified for it" % path)
            return m.group(0)
        return sc.market_url_verified(path, True)

    return _re.sub(r"https://www\.helloprint\.com/en-ie/([a-z0-9-]*)", one, html)

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


# Keys that exist ONLY to be swapped into a no-discount variant, so their
# English is deliberately not in the source file. Without this exclusion the main
# substitution loop hunts for `pre_ordered` in the file, fails to find it, and
# reports six failures per email for a key that is working correctly.
VARIANT_ONLY_KEYS = {"pre_ordered"}


def strings_for(slug):
    """Every (key, English) this email substitutes, from the translation file."""
    d = i18n.data()
    keys = [(k, (d.get(slug) or {})[k]["en"])
            for k in sorted((d.get(slug) or {}))
            if k not in VARIANT_ONLY_KEYS]
    return keys + [(k, e) for k, e in SHARED_IN_FILE]



# --------------------------------------------------- the all-inclusive-price USP
#
# "Every price includes delivery and VAT" IS TRUE IN THE US ONLY. Sebastiaan
# confirmed it is a US proposition: elsewhere prices exclude VAT and delivery,
# which _shared/px.exvat_note has been saying in the other emails all along. So
# the claim was not just off-brand outside the US, the two lines contradicted
# each other.
#
# WHY THIS IS NOT A TEXT SWAP. The USP strip is a filmstrip of THREE items
# animated by hpw1usp, whose keyframes step translateX to -100% and then -200%.
# Drop an item and leave the animation alone and the third step scrolls to blank.
# Outlook, which ignores transform, gets a separate static bar showing item one -
# so the claim appears TWICE in the markup and both have to go.
#
# The strip is therefore emitted twice, once per shape, behind a locale switch:
# three items on hpw1usp for en-US, two on hpw1usp2 for everyone else. Duplicated
# markup costs about 1KB stored and nothing rendered, and it keeps each shape's
# animation self-contained rather than making one keyframe serve both.
USP_MSO_RE = re.compile(r'<div class="hp-w1-usp-mso">(.*?)</div>', re.S)

# MATCH THE WHOLE TRACK, NOT THE FIRST ITEM. A non-greedy (.*?)</div> stops at
# item one's own closing tag, so the rebuilt track was inserted and items two and
# three were left dangling outside it - two items in the strip and two loose
# copies below it. The track holds nothing but item divs, so say so.
USP_TRACK_RE = re.compile(
    r'<div class="hp-w1-usp-track">\s*'
    r'((?:<div class="hp-w1-usp-item">.*?</div>\s*)+)'
    r'</div>', re.S)
USP_ITEM_RE = re.compile(r'<div class="hp-w1-usp-item">.*?</div>', re.S)
US_LOCALE = "en-US"


def _usp_items(html):
    """The strip's items, or None if the markup is not the shape we expect."""
    m = USP_TRACK_RE.search(html)
    if not m:
        return None, None
    items = USP_ITEM_RE.findall(m.group(1))
    return m, items


def _inner(item):
    return re.sub(r'^<div class="hp-w1-usp-item">|</div>$', "", item)


def usp_strip(html, slug, live, locale=None):
    """Show the price-inclusive USP to en-US only, and fix the animation."""
    if slug != "welcome-01":
        return html
    m, items = _usp_items(html)
    if not items or len(items) != 3:
        errs.append("welcome-01: expected a 3-item USP track, found %s"
                    % (len(items) if items else "no track"))
        return html

    three = '<div class="hp-w1-usp-track">' + "".join(items) + "</div>"
    two = ('<div class="hp-w1-usp-track hp-w1-usp-track2">'
           + "".join(items[1:]) + "</div>")
    mso_us = '<div class="hp-w1-usp-mso">%s</div>' % _inner(items[0])
    mso_rest = '<div class="hp-w1-usp-mso">%s</div>' % _inner(items[1])

    if not live:
        if (locale or i18n.FALLBACK_LOCALE) == US_LOCALE:
            return html
        html = USP_MSO_RE.sub(lambda _m: mso_rest, html, count=1)
        return USP_TRACK_RE.sub(lambda _m: two, html, count=1)

    sw = "{%% if %s == '%s' %%}%s{%% else %%}%s{%% endif %%}"
    html = USP_MSO_RE.sub(
        lambda _m: sw % (i18n.LOCALE_EXPR, US_LOCALE, mso_us, mso_rest),
        html, count=1)
    html = USP_TRACK_RE.sub(
        lambda _m: sw % (i18n.LOCALE_EXPR, US_LOCALE, three, two),
        html, count=1)
    return html

def render(html, slug, locale=None, live=False):
    """Swap each English string for one locale's text, or for a nine-way switch.

    LONGEST FIRST. "Your 10% welcome discount" contains no other string here, but
    "Chat with us" sits inside nothing while "Do you need help?" could. Replacing
    short strings first lets a later substitution match inside text that has
    already been translated, which produces a sentence half in each language.
    """
    tr = i18n.translator(slug, live, locale)
    pairs = sorted(strings_for(slug), key=lambda kv: -len(kv[1]))

    # TWO PASSES, VIA A TOKEN. Replacing English straight with its switch lets a
    # LATER, SHORTER string match inside a switch already emitted. welcome-04's
    # headline is "Send it over, we'll handle it" and step one of its timeline is
    # "Send it over", so the short one was found inside the en-IE and en-GB
    # branches of the long one and a whole nine-branch switch was nested inside
    # each. The h1 came out 1,952 characters with four nested {% if %} in it. It
    # rendered correctly - the inner switch resolves to the same locale - so this
    # was invisible, just 1.5KB of waste against Gmail's clipping threshold.
    #
    # Longest-first ordering does not prevent it; it CAUSES it, because the long
    # string is the one that becomes a switch first. Substituting an opaque token
    # first and expanding every token at the end does prevent it: by the time the
    # short string is looked for, the long one's text is a token, not prose.
    subs = []
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
        token = "\x00T%d\x00" % len(subs)
        subs.append((token, key, eng))
        html = html.replace(eng, token)
    for token, key, eng in subs:
        html = html.replace(token, tr(key, eng, fills_loc=CAP_FILL))
    if "\x00" in html:
        errs.append("%s: a substitution token survived into the output" % slug)
    if "@@CAP@@" in html:
        errs.append("%s: @@CAP@@ survived - the cap was never filled" % slug)
    html = swap_reviews(html, slug, tr, locale, live)
    html = real_unsubscribe(html, live, tr)
    html = market_links(html, live)
    html = catalog_tiles(html, slug, live, locale)
    html = offer_code(html)
    html = trustpilot_link(html, slug, live, locale)
    html = usp_strip(html, slug, live, locale)
    html = html_lang(html, live, locale)
    return link_assets(html, live)


# The edits are expressed as regexes over the BUILT block, because these files
# are string-substituted rather than templated: by the time a live block exists
# its locale switches are already resolved, so there is no slot left to target.
VARIANT_EDITS = {
    # welcome-01 is the discount email, so it names the offer in FOUR places, not
    # one. A first pass removed only the dashed code box and left the promo bar,
    # the preheader and a section subtitle all still promising 10%. The check at
    # the bottom of this file exists because of that.
    "welcome-01": [
        # the code card, switches and all. It is a block now, not an
        # inline pill, so there is no trailing <br> to match any more.
        (r'<div class="hp-w1-code">.*?</div>\s*', ""),
        # THE EYEBROW AND THE CTA NOTE SIT OUTSIDE THE CARD. Stripping only the
        # card left "10% OFF YOUR FIRST ORDER" as the first line of an email
        # with no offer in it, and "Use it at checkout" under the button.
        (r'<span class="hp-w1-eyebrow">.*?</span>\s*', ""),
        (r'<span class="hp-w1-ctanote">.*?</span>\s*', ""),
        # the green promo bar above the logo
        (r'<div class="hp-w1-promo">.*?</div>', ""),
        # the preheader, which is what shows in the inbox list
        (r'(<div class="hp-w1-pre">)(.*?)(</div>)', r"\1@@PRE@@\3"),
        # "Pick one and your 10% comes off at checkout."
        (r'(<p class="hp-w1-sectsub">)(.*?)(</p>)', r"\1@@SECTSUB@@\3"),
        # "Start your first order" is wrong for someone who just ordered
        (r'(<a class="hp-w1-cta" href="[^"]*">)(.*?)(</a>)', r"\1@@CTA@@\3"),
        # THE OFFER TERMS. They name the discount, the cap and the expiry, so
        # they have no business in an email that carries no offer.
        (r'<div class="hp-w1-terms">.*?</div>\s*', ""),
        # THE PRODUCT TILES WERE STILL PRICED AS IF THE CODE APPLIED. Each of the
        # four tiles carried the list price struck through beside the discounted
        # one - <s>EUR 39.96</s> EUR 35.96 - and a countdown under it, in an
        # email with no code anywhere in it. Forty was/now pairs and four
        # countdowns, in nine locales.
        #
        # WHY IT SURVIVED EVERY CHECK. scripts/make-nodiscount.py has rules for
        # exactly this, written against the English source where a tile price is
        # one literal. By the time the variant is built the price is a
        # nine-branch locale switch, so those regexes matched nothing - and the
        # nocode guard below looked for "10%", the code and a few class names,
        # none of which appear in a struck-out price.
        #
        # THE STRIKE TAG GOES WITH IT. Keeping the <s> wrapper would have left
        # the surviving price line-through, which reads as "no longer available"
        # rather than "this is the price".
        (r'<s class="hp-w1-tiwas">(.*?)</s>&nbsp;'
         r'<span class="hp-w1-tinow">.*?</span>', r"\1"),
        (r'<span class="hp-w1-tiexp">(?:(?!</span>).)*</span>', ""),
        # the price reclaims the brand green now that nothing competes with it
        (r'\.hp-w1-tiprice\{display:block;font-size:17px;line-height:22px;'
         r'font-weight:800;color:#191919;\}',
         ".hp-w1-tiprice{display:block;font-size:17px;line-height:22px;"
         "font-weight:800;color:#008539;}"),
    ],
    "welcome-02": [
        # the countdown bar
        # MATCH THE BAR ONLY. This used to be
        #   <div class="hp-w2-promo">.*?</div>\s*</div>  ->  </div>
        # and the non-greedy run still reached past the bar's own close, taking
        # the masthead, the hero image, the H1, the call to action and the speech
        # balloon with it and leaving three orphaned </div> tags. The variant
        # looked plausible in a byte count and was a broken email.
        (r'<div class="hp-w2-promo">.*?</div>', ""),
        # ALSO REPLACE THE PREHEADER. This email shares one preheader
        # between both branches, and the has-not-ordered version now
        # counts down the discount. Left alone, someone who had just
        # ordered would get an inbox snippet pushing an offer they
        # cannot use - the exact thing this variant exists to avoid.
        (r'(<div class="hp-w2-pre">)(.*?)(</div>)', r"\1@@PRE@@\3"),
        # the offer terms, for the same reason as the promo bar above
        (r'<div class="hp-w2-terms">.*?</div>\s*', ""),
    ],
    # In 03 and 04 the discount is ONLY the green bar. Everything else stands on
    # its own: 03 is three real Trustpilot reviews and a 4.5 rating, 04 is John
    # and the print expert team with the how-it-works steps. An earlier version
    # of this build dropped both emails from the ordered path on the grounds that
    # they "were" the discount reminder. They are not. Strip the bar and each is
    # still a complete email.
    "welcome-03": [
        (r'<div class="hp-w3-promo">.*?</div>', ""),
        # ALSO REPLACE THE PREHEADER. This email shares one preheader
        # between both branches, and the has-not-ordered version now
        # counts down the discount. Left alone, someone who had just
        # ordered would get an inbox snippet pushing an offer they
        # cannot use - the exact thing this variant exists to avoid.
        (r'(<div class="hp-w3-pre">)(.*?)(</div>)', r"\1@@PRE@@\3"),
        # the offer terms, for the same reason as the promo bar above
        (r'<div class="hp-w3-terms">.*?</div>\s*', ""),
    ],
    "welcome-04": [
        (r'<div class="hp-w4-promo">.*?</div>', ""),
        # ALSO REPLACE THE PREHEADER. This email shares one preheader
        # between both branches, and the has-not-ordered version now
        # counts down the discount. Left alone, someone who had just
        # ordered would get an inbox snippet pushing an offer they
        # cannot use - the exact thing this variant exists to avoid.
        (r'(<div class="hp-w4-pre">)(.*?)(</div>)', r"\1@@PRE@@\3"),
        # the offer terms, for the same reason as the promo bar above
        (r'<div class="hp-w4-terms">.*?</div>\s*', ""),
    ],
}


def variant(html, slug, tr):
    """Strip the discount from a built live block. Every edit must land."""
    edits = VARIANT_EDITS.get(slug)
    if not edits:
        return None
    for pattern, repl in edits:
        new, n = re.subn(pattern, repl, html, flags=re.S)
        if not n:
            errs.append("%s variant: %r matched nothing, so the discount was "
                        "not removed" % (slug, pattern[:54]))
            continue
        html = new
    for token, key, english in VARIANT_TOKENS.get(slug, ()):
        if token not in html:
            errs.append("%s variant: %s was never inserted, so %s is unused"
                        % (slug, token, key))
            continue
        html = html.replace(token, tr(key, english))
    left = re.findall(r"@@[A-Z]+@@", html)
    if left:
        errs.append("%s variant: %s survived into the output"
                    % (slug, sorted(set(left))))
    return html


# WHICH NEUTRAL STRING EACH TOKEN RESOLVES TO, per email.
#
# This used to be one shared list, so every email's @@PRE@@ resolved to
# wc.pre_nocode - which is welcome-01's line about "the prints most businesses
# start with". Correct for 01 and wrong for the other three, which now each keep
# their own former preheader as `pre_ordered`.
VARIANT_TOKENS = {
    "welcome-01": (
        ("@@CTA@@", "cta.browse_range", "Browse the full range"),
        ("@@PRE@@", "wc.pre_nocode",
         "The prints most businesses start with, and the people behind them."),
        ("@@SECTSUB@@", "wc.sectsub_nocode",
         "Pick one and see what it comes to."),
    ),
    "welcome-02": (("@@PRE@@", "pre_ordered",
                    "Printed closer to you, a B Corp certification, and over "
                    "10,000 products."),),
    "welcome-03": (("@@PRE@@", "pre_ordered",
                    "Rated 4.5 on Trustpilot from 34,000+ reviews. Here is what "
                    "a few of them say."),),
    "welcome-04": (("@@PRE@@", "pre_ordered",
                    "Artwork or just an idea. Send either and John&rsquo;s team "
                    "takes it from there."),),
}


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
    # A LOCALE VARIANT NEEDS ITS OWN PREVIEW TOO.
    #
    # The loop above is per LANGUAGE, and en-US is not a language - it reads
    # English prose with per-locale overrides. So no US preview was ever written
    # and the overview had no US button, even though the US email differs in
    # three visible ways: dollars, /en-us/ links, and "includes shipping" where
    # the others claim VAT. Proofreading it needs the locale, not the language.
    for _loc in PREVIEW_LOCALES:
        io.open(os.path.join(OUT, "%s-%s-proposed.html" % (slug, _loc)), "w",
                encoding="utf-8").write(render(english, slug, _loc))

    _live = render(english, slug, None, True)
    io.open(os.path.join(OUT, slug + "-klaviyo.html"), "w",
            encoding="utf-8").write(_live)
    _var = variant(_live, slug, i18n.translator(slug, True))
    _extra = ""
    if _var:
        io.open(os.path.join(OUT, slug + "-nocode-klaviyo.html"), "w",
                encoding="utf-8").write(_var)
        _extra = " + 1 no-discount variant"
    print("  %-12s -> %d language previews + 1 Klaviyo block%s"
          % (slug, len(i18n.LANGS) - 1, _extra))

# ---- nothing English may survive in a translated preview
LEAKS = ["Do you need help?", "Chat with us", "Help Centre",
         "Start your first order", "Read our story", "Read the reviews"]
import glob
for f in sorted(glob.glob(os.path.join(OUT, "welcome-0*-*-proposed.html"))):
    # PARSE THE WHOLE TAG, NOT THE LAST TWO DASHES. rsplit("-", 2) reads
    # "welcome-01-en-US-proposed.html" as language "US", and then every English
    # string in the US preview looked like a leak. The tag is whatever sits
    # between the slug and "-proposed".
    tag = re.match(r"welcome-\d+-(.+)-proposed\.html$",
                   os.path.basename(f)).group(1)
    lg = i18n.LOCALE_LANG.get(tag, tag)
    # An English preview is SUPPOSED to be in English. en-US differs from en in
    # its money, links and tax wording, not its language, so the leak test does
    # not apply to it.
    if lg == i18n.SOURCE:
        continue
    for p in i18n.leaks(f, lg, LEAKS):
        errs.append("%s: English left in the %s preview (%r)"
                    % (os.path.basename(f), tag, p))


# ---- the three go-live defects must not come back --------------------------
#
# Every one of these was invisible in a browser preview and broke a real send,
# which is exactly the class of fault a check has to hold.
GMAIL_CLIP_KB = 102

# ---- the no-discount variants, for readers who ordered before the first email
#
# WHY THESE EXIST. The Welcome flow waits an hour before its first email,
# because signup happens inside checkout and many people order straight after.
# Anyone who has ordered in that hour must not be handed a first-order discount:
# they would either use it on a second order we were not discounting, or read it
# as an offer they just missed. So the flow splits and this is the other side.
#
# ONLY THE DISCOUNT IS REMOVED. Same design, same translations, same images -
# the code line and the countdown bar come out, and welcome-01's call to action
# stops saying "Start your first order" to someone who just did.
#
# Emails 3 and 4 have no variant on purpose: they ARE the discount reminder and
# the last-day nudge. With the discount gone there is no email left, so that path
# ends after two and Post-Purchase picks the customer up from their order.


for _slug in EMAILS:
    _lv = os.path.join(OUT, _slug + "-klaviyo.html")
    if not os.path.exists(_lv):
        continue
    _s = io.open(_lv, encoding="utf-8").read()
    _kb = len(_s.encode("utf-8")) // 1024

    if "data:image" in _s:
        errs.append("%s: still embeds a base64 image. Gmail and Outlook do not "
                    "render data: URIs, so it would arrive blank." % _slug)
    if _kb > GMAIL_CLIP_KB:
        errs.append("%s: %d KB, over Gmail's ~%d KB clip, so the end of the "
                    "email is truncated with a 'View entire message' link"
                    % (_slug, _kb, GMAIL_CLIP_KB))
    # ONE TAG PER LOCALE BRANCH, plus the else: the switch wraps the tag rather
    # than sitting inside its argument, so ten tags are correct and exactly one
    # renders. Expecting one was right for the old form, which did not render at
    # all - the API returned 400 on it.
    _want = len(i18n.LOCALES) + 1
    _got = _s.count("{% unsubscribe")
    if _got != _want:
        errs.append("%s: %d {%% unsubscribe %%} tags, expected %d (one per "
                    "locale branch plus the else). A dead or missing "
                    "unsubscribe link is legally required to work and Klaviyo "
                    "will refuse to send without it." % (_slug, _got, _want))
    if '<a href="#"' in _s:
        errs.append("%s: a link still points at '#'" % _slug)

    # an /en-ie/ URL is only allowed as the en-IE BRANCH of a switch, never as
    # the whole href
    for _m in re.finditer(r'(?:href|src)="(https://www\.helloprint\.com/en-ie/[^"]*)"', _s):
        errs.append("%s: %s is hardcoded to Ireland rather than switched per "
                    "market" % (_slug, _m.group(1)))

    # no sentinel may survive: every asset resolves to a hosted URL now
    if "REPLACE-WITH-KLAVIYO-ASSET" in _s:
        errs.append("%s: still carries an unresolved sentinel asset URL" % _slug)
    # Every image must come from a host we control and intend.
    #   d3k81ch9hvuctc  Klaviyo's own CDN - our uploads and its social icons
    #   contentful      our brand CDN, already public and already localised
    # Anything else is a mistake: the point of this check is that GitHub Pages,
    # a designer's Dropbox or a hotlinked stock URL cannot slip into a send.
    OK_HOSTS = ("https://d3k81ch9hvuctc.cloudfront.net/",
                "https://contentful.helloprint.com/")
    for _m in re.finditer(r'src="(https?://[^"]+)"', _s):
        if not _m.group(1).startswith(OK_HOSTS):
            errs.append("%s: image served from %s, which is not a host we "
                        "control" % (_slug, _m.group(1)[:64]))

    # a preview must stay self-contained and must NOT carry the sentinel
    _pv = os.path.join(OUT, _slug + "-proposed.html")
    _p = io.open(_pv, encoding="utf-8").read()
    if "REPLACE-WITH-KLAVIYO-ASSET" in _p:
        errs.append("%s: the preview leaked a sentinel asset URL, so it will "
                    "show broken images to a proofreader" % _slug)
    if "{% unsubscribe" in _p:
        errs.append("%s: the preview leaked a Django tag" % _slug)

print("\nGO-LIVE CHECKS on the four live blocks:")
for _slug in EMAILS:
    _lv = os.path.join(OUT, _slug + "-klaviyo.html")
    if os.path.exists(_lv):
        print("  %-12s %3d KB  assets linked, unsubscribe wired, links per market"
              % (_slug, len(io.open(_lv, encoding="utf-8").read().encode("utf-8")) // 1024))

# which market/path pairs could not be localised, so the gap is visible rather
# than quietly absorbed by the en-GB fallback
_gaps = sc.market_url_gaps(WC_PATHS)
if _gaps:
    import collections as _c
    _by = _c.defaultdict(list)
    for _pth, _loc in _gaps:
        _by[_pth].append(_loc)
    print("\n  NOT LOCALISED, falling back to en-GB (the slug 404s in that "
          "market, verified %s):" % (sc._MU.get("fetched") or "?"))
    for _pth in sorted(_by):
        print("    /%-24s %s" % (_pth or "<home>", " ".join(sorted(_by[_pth]))))
    print("    Fix by adding the real localised slug to CONTENT_SLUGS in "
          "scripts/build_market_urls_from_feeds.py and re-running that "
          "one - NOT fetch_market_urls.py, which rewrites the whole "
          "file and drops the feed-derived urls block.")


# ---- NO VARIANT MAY MENTION THE DISCOUNT, ANYWHERE
#
# welcome-01 names the offer in four places: the dashed code box, the green promo
# bar, the preheader that shows in the inbox list, and a section subtitle. A
# first pass removed one of them and the other three still promised 10% off to
# people who had already ordered. Removing "the discount block" is not a single
# edit, so this asserts on the rendered result instead of trusting the edits.
# MARKUP AND VISIBLE TEXT, NOT CSS. An unused ".hp-w1-code{...}" rule is left
# behind by design - deleting stylesheet rules for removed elements would mean
# diffing the CSS too, for no benefit. What matters is that no ELEMENT and no
# WORD remains. This project has tripped on counting class names in a stylesheet
# more than once.
DISCOUNT_WORDS = ["10%", offers.WELCOME_CODE, 'class="hp-w1-code"',
                  'class="hp-w1-eyebrow"', 'class="hp-w1-ctanote"', '-promo">',
                  # A DISCOUNT SHOWS UP AS A NUMBER, NOT ONLY AS A WORD. These
                  # three are how the offer appeared on the product tiles - a
                  # struck-out list price, a discounted price beside it, and a
                  # countdown - none of which contain "10%" or the code, so the
                  # list above passed a variant that was still visibly
                  # discounted.
                  'class="hp-w1-tiwas"', 'class="hp-w1-tinow"',
                  'class="hp-w1-tiexp"']

for _slug in EMAILS:
    _vp = os.path.join(OUT, _slug + "-nocode-klaviyo.html")
    if not os.path.exists(_vp):
        continue
    _v = io.open(_vp, encoding="utf-8").read()
    for _w in DISCOUNT_WORDS:
        if _w in _v:
            _i = _v.index(_w)
            errs.append("%s-nocode still mentions the discount (%r): ...%s..."
                        % (_slug, _w,
                           re.sub(r"\s+", " ", _v[max(0, _i - 70):_i + 40])))

print("\nNO-DISCOUNT VARIANTS: %d built, none mentioning the offer"
      % len([1 for e in EMAILS
             if os.path.exists(os.path.join(OUT, e + "-nocode-klaviyo.html"))]))

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
