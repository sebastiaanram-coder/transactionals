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

TAGS NEED OAUTH. Verified, not assumed: the PUBLIC review endpoint returns no
tags field at all - 500 reviews scanned, zero tags, and "tags" is simply absent
from the response. The PRIVATE endpoint returns them:

  GET /v1/private/business-units/{id}/reviews    Bearer token
      Same filters, plus a "tags" array on each review.

The token comes from client_credentials, which needs only the key and the
secret - no business user password, despite that being a possibility in the
docs:

  POST /v1/oauth/oauth-business-users-for-applications/accesstoken
       Authorization: Basic base64(key:secret)
       grant_type=client_credentials
       -> access_token, expires_in 360000 (100 hours)

WHAT THE TAGS ACTUALLY LOOK LIKE. One group, "generic", holding the whole
category path and the product slug together, e.g. a flyers review carries
"Commercial Print", "All Flyers", "Flyers" and "standardflyers". So matching on
the top-level category name is exact, and matching on a product slug is possible
if a finer cut is ever wanted. About 58% of reviews carry tags at all.

SERVICE REVIEWS, NOT PRODUCT REVIEWS. Product reviews live on a different
endpoint (/v1/product-reviews/...). Seb asked for service reviews for now.
"""
import base64, json, os, sys, urllib.error, urllib.parse, urllib.request

BASE = "https://api.trustpilot.com/v1"
ENV_KEY = "TRUSTPILOT_API_KEY"
ENV_SECRET = "TRUSTPILOT_API_SECRET"
UA = "helloprint-behavioural-email/1.0 (+internal tooling)"
TIMEOUT = 30


class TrustpilotError(RuntimeError):
    pass


def _secret():
    return os.environ.get(ENV_SECRET, "").strip() or _from_dotenv(ENV_SECRET)


def _from_dotenv(name=None):
    """Read the key from a gitignored .env at the repo root, if present.

    This exists because a shell export does not survive between tool calls, so
    an agent driving this needs the value to live somewhere it can read on each
    run. .env is in .gitignore; the value is never printed or copied elsewhere."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, ".env")
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(name or ENV_KEY):
                    _, _, v = line.partition("=")
                    return v.strip().strip("'\"")
    except FileNotFoundError:
        pass
    return ""


def api_key():
    k = os.environ.get(ENV_KEY, "").strip() or _from_dotenv(ENV_KEY)
    if not k:
        raise TrustpilotError(
            "%s is not set. Export it in your shell first:\n"
            "    export %s='your-key'\n"
            "or put it in a gitignored .env at the repo root:\n"
            "    %s=your-key\n"
            "Get one from the Trustpilot developer portal."
            % (ENV_KEY, ENV_KEY, ENV_KEY))
    return k


def _get(path, **params):
    """GET with the key in the query string, as the API expects.

    The key is stripped from anything this function reports, so a traceback or
    an error message can never carry it into a log or a terminal history."""
    params = {k: v for k, v in params.items() if v is not None}
    params["apikey"] = api_key()
    url = "%s%s?%s" % (BASE, path, urllib.parse.urlencode(params))
    # A real User-Agent and an explicit Accept. Without them the default
    # "Python-urllib/3.x" gets a 403 with a CloudFront HTML page - the request
    # never reaches the API, so it looks like an auth failure and is not one.
    # The key also goes in a header as well as the query string, because the API
    # accepts either and the header is the one that survives a redirect.
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json",
        "apikey": params["apikey"],
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:400]
        hint = ""
        if e.code == 403 and "<HTML" in body.upper():
            hint = ("\n\nThis is an HTML block page, not a JSON auth error, so the "
                    "request was rejected before it reached the API. Usually a "
                    "blocked User-Agent or IP rather than a bad key.")
        elif e.code in (401, 403):
            hint = "\n\nCheck the key is a Trustpilot API key and is still active."
        raise TrustpilotError("HTTP %s on %s\n%s%s" % (e.code, _safe(url), body, hint))
    except urllib.error.URLError as e:
        raise TrustpilotError("could not reach %s: %s" % (_safe(url), e.reason))


def _safe(url):
    """The same URL with the key removed, safe to show a human."""
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parts.query)
    q = [(k, "***" if k == "apikey" else v) for k, v in q]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))


def access_token():
    """A bearer token for the private endpoints, via client_credentials.

    Fetched fresh each run rather than cached to disk - it is one cheap call, and
    a token sitting in a file is one more secret to look after."""
    sec = _secret()
    if not sec:
        raise TrustpilotError(
            "%s is not set, and the private endpoints need it. Add it to .env "
            "next to the key." % ENV_SECRET)
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    auth = base64.b64encode(("%s:%s" % (api_key(), sec)).encode()).decode()
    req = urllib.request.Request(
        BASE + "/oauth/oauth-business-users-for-applications/accesstoken",
        data=body,
        headers={"Authorization": "Basic " + auth,
                 "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise TrustpilotError(
            "token exchange failed: HTTP %s %s\nIf this is 400 or 401, the app may "
            "not have the Client Credentials grant enabled - the Password grant "
            "would additionally need a business user username and password."
            % (e.code, e.read().decode("utf-8", "replace")[:200]))
    t = d.get("access_token")
    if not t:
        raise TrustpilotError("token exchange returned no access_token")
    return t


def _bearer_get(token, path, **params):
    params = {k: v for k, v in params.items() if v is not None}
    url = "%s%s?%s" % (BASE, path, urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token, "Accept": "application/json",
        "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise TrustpilotError("HTTP %s on %s\n%s"
                              % (e.code, url, e.read().decode("utf-8", "replace")[:300]))


def private_reviews(token, business_unit_id, language=None, stars=None,
                    pages=1, per_page=100, order="createdat.desc"):
    """Service reviews WITH their tags. Newest first."""
    for page in range(1, pages + 1):
        d = _bearer_get(token, "/private/business-units/%s/reviews" % business_unit_id,
                        language=language, stars=stars, page=page,
                        perPage=per_page, orderBy=order)
        batch = d.get("reviews") or []
        for r in batch:
            yield r
        if len(batch) < per_page:
            return


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
        # numberOfReviews is a plain int here, not the object the docs imply
        n = meta.get("numberOfReviews")
        if isinstance(n, dict):
            n = n.get("total")
        sc = meta.get("score")
        sc = sc.get("trustScore") if isinstance(sc, dict) else sc
        print("business unit: %s  (%s, %s reviews, score %s)"
              % (bu, meta.get("identifyingName"), n, sc))
    except TrustpilotError as e:
        print("FAILED: %s" % e); raise SystemExit(1)
