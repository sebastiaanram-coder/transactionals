"""
Trustpilot API client - just enough of it to pull tagged service reviews.

CREDENTIALS NEVER TOUCH THIS REPO. The key is read from the environment and is
never printed, logged, or written to the cache. Set it in your shell:

    export TRUSTPILOT_API_KEY='...'

Do not paste it into a chat, a commit, or a file here. If it does end up
somewhere it should not, rotate it in the Trustpilot developer portal rather
than trying to scrub it.

WHAT THE API GIVES US, confirmed against developers.trustpilot.com:

  GET /v1/business-units/search?query={domain}
      API key auth. Finds the business unit id for a domain.

  GET /v1/business-units/{id}/reviews
      API key auth. Service reviews. Parameters we use:
        stars      filter by rating
        language   filter by review language - this is the whole reason the
                   per-language plan works
        tagGroup   filter by tag group
        tagValue   filter by tag value
        perPage    up to 100
        page
        orderBy    createdat.desc

  Each review carries: id, stars, title, text, language, createdAt,
  experiencedAt, consumer.displayName, consumer.displayLocation, companyReply,
  and tags as [{"group": ..., "value": ...}].

THERE IS NO ENDPOINT LISTING THE AVAILABLE TAG GROUPS OR VALUES. Tags only
appear inside review objects, so the inventory has to be discovered by fetching
reviews and looking at what comes back. fetch_reviews.py does that and prints
it, which is how the tag-to-category mapping gets filled in.

SERVICE REVIEWS, NOT PRODUCT REVIEWS. Product reviews live on a different
endpoint (/v1/product-reviews/...). Seb asked for service reviews for now.
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

BASE = "https://api.trustpilot.com/v1"
ENV_KEY = "TRUSTPILOT_API_KEY"
TIMEOUT = 30


class TrustpilotError(RuntimeError):
    pass


def api_key():
    k = os.environ.get(ENV_KEY, "").strip()
    if not k:
        raise TrustpilotError(
            "%s is not set. Export it in your shell first:\n"
            "    export %s='your-key'\n"
            "Get one from the Trustpilot developer portal. Do not put it in a "
            "file in this repo." % (ENV_KEY, ENV_KEY))
    return k


def _get(path, **params):
    """GET with the key in the query string, as the API expects.

    The key is stripped from anything this function reports, so a traceback or
    an error message can never carry it into a log or a terminal history."""
    params = {k: v for k, v in params.items() if v is not None}
    params["apikey"] = api_key()
    url = "%s%s?%s" % (BASE, path, urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:400]
        raise TrustpilotError("HTTP %s on %s\n%s" % (e.code, _safe(url), body))
    except urllib.error.URLError as e:
        raise TrustpilotError("could not reach %s: %s" % (_safe(url), e.reason))


def _safe(url):
    """The same URL with the key removed, safe to show a human."""
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parts.query)
    q = [(k, "***" if k == "apikey" else v) for k, v in q]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))


def find_business_unit(domain):
    """The business unit id for a domain, e.g. 'helloprint.com'."""
    d = _get("/business-units/search", query=domain)
    units = d.get("businessUnits") or []
    if not units:
        raise TrustpilotError("no business unit matched %r" % domain)
    for u in units:  # prefer an exact identifying-name match over a fuzzy one
        if (u.get("identifyingName") or "").lower() == domain.lower():
            return u["id"], u
    return units[0]["id"], units[0]


def reviews(business_unit_id, language=None, stars=None, tag_group=None,
            tag_value=None, pages=1, per_page=100, order="createdat.desc"):
    """Service reviews, newest first. Yields review dicts."""
    for page in range(1, pages + 1):
        d = _get("/business-units/%s/reviews" % business_unit_id,
                 language=language, stars=stars, tagGroup=tag_group,
                 tagValue=tag_value, page=page, perPage=per_page, orderBy=order)
        batch = d.get("reviews") or []
        for r in batch:
            yield r
        if len(batch) < per_page:
            return


def tag_inventory(review_iter):
    """Group -> value -> count, built from whatever reviews we were given.

    This exists because the API has no endpoint for it. Run it over a broad
    fetch to find out what the tagging actually looks like before mapping tags
    onto our category slugs."""
    inv = {}
    for r in review_iter:
        for t in (r.get("tags") or []):
            g = t.get("group") or "(no group)"
            v = t.get("value") or "(no value)"
            inv.setdefault(g, {}).setdefault(v, 0)
            inv[g][v] += 1
    return inv


def normalise(r):
    """The subset we store, with attribution intact.

    Trustpilot's terms require reviews to be shown as written and attributed, so
    the text is kept verbatim - selection happens by choosing a short review,
    never by trimming a long one - and the author, rating and date come along
    with it."""
    c = r.get("consumer") or {}
    return {
        "id": r.get("id"),
        "stars": r.get("stars"),
        "title": (r.get("title") or "").strip(),
        "text": " ".join((r.get("text") or "").split()),
        "language": (r.get("language") or "").lower(),
        "created_at": r.get("createdAt"),
        "author": (c.get("displayName") or "").strip(),
        "author_location": (c.get("displayLocation") or "").strip(),
        "tags": [{"group": t.get("group"), "value": t.get("value")}
                 for t in (r.get("tags") or [])],
    }


if __name__ == "__main__":
    # a connectivity check that prints nothing sensitive
    try:
        bu, meta = find_business_unit(sys.argv[1] if len(sys.argv) > 1 else "helloprint.com")
        print("business unit: %s  (%s, %s reviews, score %s)" % (
            bu, meta.get("identifyingName"),
            (meta.get("numberOfReviews") or {}).get("total"),
            (meta.get("score") or {}).get("trustScore")))
    except TrustpilotError as e:
        print("FAILED: %s" % e); raise SystemExit(1)
