# -*- coding: utf-8 -*-
"""
The Klaviyo REST plumbing, in one place: the key, one request, one render.

Extracted from scripts/push_templates.py, which grew these first and is still
the deploy loop for BEH-1. BEH-2 and BEH-3 need exactly the same three things,
and a second copy of a 429-backoff loop is how the two drift apart.

REVISIONS DIFFER BY ENDPOINT, which is why REVISION is a parameter and not a
constant: /templates accepts 2024-10-15, flow-actions needs 2025-10-15 (older
revisions have no `definition` field at all), and /translations is beta and
needs 2026-07-15.pre - 2025-10-15 answers "use a date after 2026-04-15",
2026-04-15 and 2026-07-15 answer "no valid revisions for method", and
2026-10-15 answers "future revision date".

The key is read from file and never returned to a log.
"""
import io, json, os, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = "https://a.klaviyo.com/api"
REVISION = "2025-10-15"
REVISION_BETA = "2026-07-15.pre"


def load_key():
    """The key, and which file it came from. The VALUE never reaches a log."""
    for path in (os.path.join(ROOT, ".env"), os.path.join(ROOT, "..", ".env")):
        try:
            for line in io.open(path, encoding="utf-8"):
                k, sep, v = line.strip().partition("=")
                if sep and k.strip() == "KLAVIYO_PRIVATE_KEY":
                    v = v.strip().strip('"').strip("'")
                    if v and v != "pk_your_key_here":
                        return v, os.path.relpath(path, ROOT)
        except IOError:
            pass
    sys.exit("no KLAVIYO_PRIVATE_KEY in .env - see proposals/klaviyo-flow-welcome.md")


def call(key, method, path, body=None, tries=5, revision=REVISION):
    """One request, retrying a 429. Klaviyo throttles bursts on these endpoints."""
    for attempt in range(tries):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            BASE + path, data=data, method=method,
            headers={"Authorization": "Klaviyo-API-Key %s" % key,
                     "revision": revision, "accept": "application/json",
                     "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")
            if e.code == 429 and attempt < tries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            return e.code, {"error": txt}
    return 0, {"error": "retries exhausted"}


def errors(res):
    """The API's error details as short lines, or [] - for readable failures."""
    txt = res.get("error") or ""
    try:
        return ["%s %s" % (e.get("source", {}).get("pointer", ""),
                           e.get("detail", "")) for e in json.loads(txt)["errors"]]
    except Exception:
        return [txt[:300]] if txt else []


def render(key, tid, locale, context=None):
    """Render a template for one locale. Works on a per-message copy too."""
    person = {"locale": locale, "first_name": "Sebastiaan"}
    st, res = call(key, "POST", "/template-render/",
                   {"data": {"type": "template", "id": tid, "attributes": {
                       "context": dict(context or {}, person=person)}}})
    if st != 200:
        return None, res
    return ((res.get("data") or {}).get("attributes") or {}).get("html"), res
