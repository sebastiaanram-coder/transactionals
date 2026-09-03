#!/usr/bin/env python3
"""
Verify, per market, which helloprint.com paths actually exist.

WHY THIS FILE EXISTS. Every email in the programme hardcodes /en-ie/ for its
home, help-centre and product links. The obvious fix is to swap the market
segment and keep the path - which is what subcategories.market_url does - and for
most paths that produces a 404, because the slugs are localised too.

Measured, not assumed: /en-ie/about-us is fine, /nl-nl/about-us is a 404.
/en-ie/standardbusinesscards is fine, and six of the nine markets 404 on it. An
Irish link in a Dutch email is wrong; a 404 in a customer's inbox is worse.

So the switch is built from what actually resolves. A locale that 404s falls back
to en-GB for the same path, which always works and is at least English, rather
than to the market home page, which would be the right market and the wrong page.

Refresh with:  python3 scripts/fetch_market_urls.py
It only writes if every request completed, so a flaky network cannot silently
turn a working URL into a fallback.
"""
import json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
import subcategories as sc

OUT = os.path.join(ROOT, "data", "market-urls.json")

# Every path any email links to, without its market segment. Adding an email
# means adding its paths here and re-running.
PATHS = ["", "all-products", "cs", "about-us", "sustainability", "our-promises",
         "contact", "quote", "budgetrollupbanners", "posters",
         "standardbusinesscards", "standardflyers"]

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"}


def status(url):
    req = urllib.request.Request(url, headers=UA, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:                                  # network, DNS, TLS
        return str(e)


def main():
    markets = {loc: sc.market_path(cf) for loc, cf in sc.LOCALE_MAP.items()}
    ok, bad, errors = {}, [], 0
    for path in PATHS:
        ok[path] = []
        row = ""
        for loc, seg in markets.items():
            code = status("https://www.helloprint.com/%s/%s" % (seg, path))
            if code == 200:
                ok[path].append(loc)
                row += " ok "
            elif isinstance(code, int):
                bad.append((path, loc, code))
                row += "%3d" % code
            else:
                errors += 1
                row += " ER"
        print("  %-24s %s" % (path or "<home>", row))

    if errors:
        raise SystemExit("\n%d request(s) failed outright. Nothing written: a "
                         "flaky run must not turn a working URL into a fallback."
                         % errors)

    # THIS SCRIPT PREDATES THE FEED-DERIVED "urls" BLOCK AND WOULD DROP IT.
    # market-urls.json now also carries path -> locale -> the market's real
    # localised URL, written by build_market_urls_from_feeds.py. Rewriting the
    # file from scratch here silently regresses every one of those links back to
    # same-slug guessing, which is what put French readers on English pages.
    # Refuse rather than destroy; use the feed builder, which merges.
    if os.path.exists(OUT):
        existing = json.loads(open(OUT, encoding="utf-8").read())
        if existing.get("urls"):
            raise SystemExit(
                "REFUSING TO WRITE. %s already holds a feed-derived 'urls' block "
                "(%d paths) that this script does not know how to produce, so "
                "writing would drop it. Use scripts/build_market_urls_from_feeds.py, "
                "which merges into the same file." % (
                    os.path.relpath(OUT, ROOT), len(existing["urls"])))

    io_out = {"fetched": sys.argv[1] if len(sys.argv) > 1 else None,
              "markets": markets, "paths": ok,
              "not_found": [{"path": p, "locale": l, "status": c} for p, l, c in bad]}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(io_out, f, ensure_ascii=False, indent=1)
    print("\n  %d path-locale pairs resolve, %d do not -> %s"
          % (sum(len(v) for v in ok.values()), len(bad),
             os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main()
