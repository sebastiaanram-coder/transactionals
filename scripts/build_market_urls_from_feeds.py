#!/usr/bin/env python3
"""
Fill data/market-urls.json from the local feeds, then verify every URL.

WHY THIS EXISTS. market-urls.json only ever recorded WHETHER /{market}/{path}
resolved, which assumes the slug is identical in every market. It is not: the
Dutch flyer page is /nl-nl/standaardflyers, the French one is
/fr-fr/flyersdigital, and the Belgian one is /fr-be/flyersclassiques. Because the
same slug was assumed, nine paths fell back to en-GB in up to six markets each -
so a French reader was sent to an English page that did exist instead of the
French page that also existed.

The catalog feed already holds the real localised URL for every product in every
market. This reads it, HTTP-verifies each one, and writes an explicit
path -> locale -> url map that market_url_verified prefers over slug-guessing.

BELGIUM KEEPS THE FEED'S OWN MARKET SEGMENT. BE-standardflyers is
/fr-be/flyersclassiques and BE-businesscardsstandard is
/nl-be/standaardvisitekaartjes - one Belgian catalog carrying both languages.
Rewriting the segment to match the reader's language would invent a URL
(/nl-be/flyersclassiques) that has never been verified and probably 404s, so the
feed's URL is used as-is and a Dutch-speaking Belgian may land on a French page
for two of the four products. That is a catalog gap, recorded in the snapshot's
"gaps", not something this script should paper over.

Run: python3 scripts/build_market_urls_from_feeds.py
"""
import json, io, os, sys, urllib.request, urllib.error, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "_lib"))
import catalog as cat          # noqa: E402
import subcategories as sc     # noqa: E402

MU = os.path.join(ROOT, "data", "market-urls.json")

# the path an email links to (the en-IE slug) -> the catalog product key
FROM_CATALOG = {"standardflyers": "standardflyers",
                "standardbusinesscards": "businesscardsstandard",
                "posters": "posters",
                "budgetrollupbanners": "rollupbannersv2"}

# THE COMPANY PAGES, whose slugs are localised too and are in no feed.
#
# These are not products, so the catalog does not know them. They were found by
# reading each market's own home page for its links and then probing the
# candidates; only a slug that answered 200 is here, and the script re-verifies
# every one on each run. Any market absent below has no such page AT ALL, which
# was checked by listing that market's company-page links rather than assumed:
#
#   all-products    it-IT has no "tutti i prodotti" page
#   sustainability  it-IT has no sustainability page (prodotti-eco is a product
#                   category, not the company page this link means)
#   quote           es-ES has only mis-presupuestos, which is the reader's OWN
#                   saved quotes, not a request form - the wrong page, so it is
#                   left to fall back rather than linked. en-US does have one,
#                   but as a CONTACT FORM WITH A QUERY STRING
#                   (new2contactform?type=inquiry) rather than a /quote slug,
#                   which is why probing /quote, /request-quote and /get-a-quote
#                   all 404'd. Supplied and verified 200 on 2026-09-03.
CONTENT_SLUGS = {
    # The US roll-up page is "rollerbanners"; budgetrollupbanners 404s
    # there. Verified 2026-09-03.
    "budgetrollupbanners": {"en-US": "rollerbanners"},
    "our-promises": {
        "en-IE": "our-promises", "en-GB": "our-promises", "en-US": "our-promises",
        "nl-NL": "onze-beloftes", "nl-BE": "onze-beloftes",
        "fr-FR": "nos-promesses", "fr-BE": "nos-promesses",
        "de-DE": "unsere-versprechen", "es-ES": "nuestras-promesas",
        "it-IT": "le-nostre-promesse"},
    "all-products": {
        "en-IE": "all-products", "en-GB": "all-products", "en-US": "all-products",
        "nl-NL": "alle-producten", "nl-BE": "alle-producten",
        "fr-FR": "tous-nos-produits", "fr-BE": "tous-nos-produits",
        "de-DE": "alle-produkte", "es-ES": "todos-los-productos"},
    "about-us": {
        "en-IE": "about-us", "en-GB": "about-us", "en-US": "about-us",
        "nl-NL": "over-ons", "nl-BE": "over-ons",
        "fr-FR": "a-propos-de-nous", "fr-BE": "a-propos-de-nous",
        "de-DE": "uber-uns", "es-ES": "sobre-nosotros",
        "it-IT": "chi-siamo"},
    "sustainability": {
        "en-IE": "sustainability", "en-GB": "sustainability", "en-US": "sustainability",
        "nl-NL": "duurzaamheid", "nl-BE": "duurzaamheid",
        "fr-FR": "durabilite", "fr-BE": "durabilite",
        "de-DE": "nachhaltigkeit", "es-ES": "sostenibilidad"},
    # The artwork-check promise page. Six markets have their own; fr-FR, fr-BE
    # and es-ES have no equivalent, so they point at that market's OWN
    # our-promises page instead of an English one - same language, and the
    # artwork-check promise is stated there. es-ES has /soluciones-diseno, which
    # resolves but is a design-SERVICES page, not the promise, so it is not used.
    "always-a-perfect-design": {
        "en-IE": "always-a-perfect-design", "en-GB": "always-a-perfect-design",
        "en-US": "always-a-perfect-design",
        "nl-NL": "altijd-een-perfect-ontwerp", "nl-BE": "altijd-een-perfect-ontwerp",
        "de-DE": "immer-ein-perfektes-design", "it-IT": "un-design-sempre-perfetto",
        "fr-FR": "nos-promesses", "fr-BE": "nos-promesses",
        "es-ES": "nuestras-promesas"},
    "quote": {
        "en-IE": "request-a-quote", "en-GB": "quote",
        "en-US": "new2contactform?type=inquiry",
        "nl-NL": "offerte-aanvragen", "nl-BE": "offerte-aanvragen",
        "fr-FR": "quote", "fr-BE": "quote",
        "de-DE": "angebot-anfragen", "it-IT": "richiedi-un-preventivo"},
}

MARKET_SEG = {"en-IE": "en-ie", "en-GB": "en-gb", "en-US": "en-us",
              "nl-NL": "nl-nl",
              "nl-BE": "nl-be", "fr-FR": "fr-fr", "fr-BE": "fr-be",
              "de-DE": "de-de", "es-ES": "es-es", "it-IT": "it-it"}

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def alive(url):
    """True when the URL answers 200. HEAD first, GET if HEAD is refused."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method,
                                     headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status == 200, r.status
        except urllib.error.HTTPError as e:
            if e.code == 405 and method == "HEAD":
                continue
            return False, e.code
        except Exception as e:                      # DNS, TLS, timeout
            return False, type(e).__name__
    return False, "no-method"


def main():
    d = json.loads(io.open(MU, encoding="utf-8").read())

    # path -> locale -> url, straight from the feed, before verification
    proposed = {}
    for path, product in FROM_CATALOG.items():
        for loc in cat.MARKET_FOR_LOCALE:
            # THE PATH NAMES A PRODUCT; THE SLOT MAY SHOW ANOTHER ONE. en-US
            # shows booklets where Europe shows a roll-up banner, so
            # cat.item("rollupbannersv2", "en-US") is booklets - and filing that
            # under the "budgetrollupbanners" path would point every US
            # roll-up-banner link at booklets. The tiles take their URL from the
            # catalog directly, so nothing needs this entry; the real US
            # roll-up page is supplied by CONTENT_SLUGS instead.
            if cat.product_for(product, loc) != product:
                continue
            it = cat.item(product, loc)
            if it["fell_back"]:
                continue            # that market genuinely has no such product
            proposed.setdefault(path, {})[loc] = it["url"]

    for path, by_loc in CONTENT_SLUGS.items():
        for loc, slug in by_loc.items():
            proposed.setdefault(path, {})[loc] = (
                "https://www.helloprint.com/%s/%s" % (MARKET_SEG[loc], slug))

    jobs = [(p, l, u) for p, m in proposed.items() for l, u in m.items()]
    print("verifying %d feed URLs over HTTP ..." % len(jobs))

    results = {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(alive, u): (p, l, u) for p, l, u in jobs}
        for f in cf.as_completed(futs):
            p, l, u = futs[f]
            ok, code = f.result()
            results[(p, l)] = (ok, code, u)

    urls, dead = {}, []
    for (p, l), (ok, code, u) in sorted(results.items()):
        if ok:
            urls.setdefault(p, {})[l] = u
        else:
            dead.append((p, l, u, code))

    for p in sorted(proposed):
        got = sorted(urls.get(p, {}))
        print("  %-24s %d/%d verified  %s"
              % (p, len(got), len(proposed[p]), " ".join(got)))
    if dead:
        print("\n  did NOT resolve, so left to fall back:")
        for p, l, u, code in dead:
            print("    %-24s %-7s %s  (%s)" % (p, l, u, code))

    d["urls"] = urls
    d["urls_note"] = ("path -> locale -> the market's real localised URL, taken "
                      "from the catalog feed and HTTP-verified. Preferred over "
                      "the same-slug assumption in 'paths'. Belgium keeps the "
                      "feed's own market segment; see "
                      "data/catalog-welcome-tiles.json gaps.")
    io.open(MU, "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("\nwritten data/market-urls.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
