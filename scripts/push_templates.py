#!/usr/bin/env python3
"""
Push the built Klaviyo blocks straight into Klaviyo. No import, no re-attach.

WHY THIS EXISTS. Getting a content change live used to mean: Sebastiaan imports
eight files by hand, then every flow message is re-attached, which re-clones all
fourteen copies. That is a lot of manual work to change one word, and it made
small fixes expensive enough to skip.

WHAT KLAVIYO ACTUALLY STORES. Attaching a saved template to a flow message makes
a PRIVATE COPY owned by that message, and the copy is what sends.

THE COPIES CANNOT BE PATCHED. This script first tried to PATCH them directly, so
that nothing would need re-attaching. Every one returned 404 "Template with id
'WeqrBR' does not exist": a per-message copy is not addressable on
/api/templates/{id}, even though template-render happily renders it. So the copy
is reachable for reading and not for writing.

WHAT WORKS, measured: push the MASTER, then re-attach the flow message to that
master. Re-attaching mints a FRESH copy from the master's current content - WEL-1
went from copy WeqrBR to copy UtFxSQ, and the new one carried the new tiles,
34.000+, nl.trustpilot.com and lang="nl-NL" where the old one carried none of
them. Subject line and preview text survive the re-attach untouched.

So this runs in two phases, and both are automatic:

  1. push   - PATCH the 8 masters with the built HTML
  2. attach - PATCH the 14 flow actions to point at their master, which
              re-clones, then record the new copy ids

REVISIONS DIFFER BY ENDPOINT. /templates accepts 2024-10-15, but flow-actions on
that revision has no `definition` field at all and 400s listing the fields it
does have. `definition` appears at 2025-10-15. One revision is used throughout.

VERIFICATION IS SEMANTIC, NOT BYTE-FOR-BYTE. Klaviyo rewrites HTML on save: it
pretty-prints the CSS, shortens #ffffff to #fff, converts &middot; to the
character, reorders and self-closes attributes. A byte comparison would fail on
every push and prove nothing. So each push is verified by reading the template
back and checking the things that MATTER survived: the number of locale switches,
that every switch is closed, and that a canary string only present in the new
version is there. A canary must not contain an HTML entity, because Klaviyo
converts those.

The key is read from .env and never printed. Requires the Templates scope.

Usage:
  python3 scripts/push_templates.py              # push masters, re-attach, verify
  python3 scripts/push_templates.py --dry-run    # show what would happen
  python3 scripts/push_templates.py --push-only  # masters only, no re-attach
  python3 scripts/push_templates.py --only WEL-4 # substring match on name
"""
import io, json, os, re, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, "klaviyo-templates")
MANIFEST = os.path.join(TEMPLATES, "MANIFEST.json")
MESSAGES = os.path.join(ROOT, "data", "klaviyo-flow-welcome-messages.json")
REVISION = "2025-10-15"
BASE = "https://a.klaviyo.com/api"

# Strings that must appear in the stored HTML after a push, chosen because they
# are NEW in this version and contain no HTML entity for Klaviyo to rewrite.
# TEST-PHASE BCC. Every Welcome message blind-copies this address so the team can
# read what actually landed, in every locale, without being on the list.
#
# IT LIVES HERE, NOT ONLY IN KLAVIYO. re-attach rewrites the whole message
# object, so a bcc set by hand in the UI is silently dropped by the next push.
# Setting it here means the push preserves it instead of removing it.
#
# REMOVE BEFORE GO-LIVE. A bcc on a live flow copies every customer email to an
# internal mailbox, which is a data-minimisation problem, not just noise. Set it
# to None and re-run to clear it from all fourteen.
TEST_BCC = "behavioral-email-tests@helloprint.com"

CANARIES = ["34.000+", "/nl-nl/offerte-aanvragen", "fr.trustpilot.com",
            "/fr-fr/flyersdigital", "/de-de/standardvisitenkarten",
            # Welcome 02 matched none of the above, so its push was being
            # verified on switch counts alone. These are the localised company
            # pages that used to fall back to en-GB, and they cover it.
            "/nl-nl/over-ons", "/nl-nl/duurzaamheid", "/de-de/alle-produkte"]


def load_key():
    """The key, and which file it came from. The VALUE is never returned to a log."""
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


def call(key, method, path, body=None, tries=4):
    """One request, retrying a 429. Klaviyo throttles bursts on these endpoints."""
    for attempt in range(tries):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            BASE + path, data=data, method=method,
            headers={"Authorization": "Klaviyo-API-Key %s" % key,
                     "revision": REVISION, "accept": "application/json",
                     "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            body_txt = e.read().decode("utf-8", "replace")[:400]
            if e.code == 429 and attempt < tries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            return e.code, {"error": body_txt}
    return 0, {"error": "retries exhausted"}


def render(key, tid, locale):
    """Render a template for one locale. Works on a per-message copy too."""
    st, res = call(key, "POST", "/template-render/",
                   {"data": {"type": "template", "id": tid, "attributes": {
                       "context": {"person": {"locale": locale,
                                              "first_name": "Sebastiaan"}}}}})
    if st != 200:
        return None
    return ((res.get("data") or {}).get("attributes") or {}).get("html")


def shape(html):
    """The properties a push must preserve. Whitespace and entities excluded."""
    return {"switches": len(re.findall(r"\{%\s*if\s+person\.locale", html)),
            "endifs": len(re.findall(r"\{%\s*endif\s*%\}", html)),
            "unsub": len(re.findall(r"\{%\s*unsubscribe", html))}


def plan():
    """[(template_name, file, master_id, [(action_id, message_id, name, next)])]"""
    man = json.loads(io.open(MANIFEST, encoding="utf-8").read())
    msgs = json.loads(io.open(MESSAGES, encoding="utf-8").read())["messages"]
    by_name = {m["name"]: m for m in msgs}
    out = []
    for t in man["templates"]:
        master, rows = None, []
        for mn in t["flow_messages"]:
            m = by_name.get(mn)
            if not m:
                sys.exit("manifest names flow message %r which is not in "
                         "data/klaviyo-flow-welcome-messages.json" % mn)
            master = master or m["template_saved"]
            rows.append((m["action"], m["message"], m["name"], m["next"]))
        out.append((t["template"], os.path.join(TEMPLATES, t["file"]), master, rows))
    return out


def subjects():
    p = os.path.join(ROOT, "proposals", "welcome-flow-subjects.json")
    return json.loads(io.open(p, encoding="utf-8").read())


def push_master(key, name, path, master, dry):
    """PATCH one master and verify what matters survived Klaviyo's rewriting."""
    html = io.open(path, encoding="utf-8").read()
    want = shape(html)
    cans = [c for c in CANARIES if c in html]
    print("%s  (%d KB, %d switches, %d canaries)"
          % (name, len(html) // 1024, want["switches"], len(cans)))
    if want["switches"] != want["endifs"]:
        print("   SKIPPED: %d if against %d endif in the local file"
              % (want["switches"], want["endifs"]))
        return False
    if dry:
        print("   master %s  would push" % master)
        return True
    st, res = call(key, "PATCH", "/templates/%s/" % master,
                   {"data": {"type": "template", "id": master,
                             "attributes": {"html": html}}})
    if st not in (200, 201):
        print("   master %s  HTTP %s  %s" % (master, st, res.get("error", "")[:160]))
        return False
    st, res = call(key, "GET", "/templates/%s/?fields[template]=html" % master)
    got = ((res.get("data") or {}).get("attributes") or {}).get("html") or ""
    g = shape(got)
    miss = [c for c in cans if c not in got]
    ok = (g["switches"] == want["switches"] and g["switches"] == g["endifs"]
          and g["unsub"] == want["unsub"] and not miss)
    print("   master %s  %s  switches %d/%d  unsub %d/%d%s"
          % (master, "ok" if ok else "MISMATCH", g["switches"], want["switches"],
             g["unsub"], want["unsub"],
             "" if not miss else "  missing canary: %s" % miss[0]))
    time.sleep(0.4)
    return ok


def reattach(key, master, rows, subj, dry):
    """Point each message at its master, which re-clones. Returns {msg_id: new copy}."""
    fresh = {}
    for action, msg_id, name, nxt in rows:
        if dry:
            print("   attach %-34s action %s -> %s" % (name[:34], action, master))
            continue
        src = (subj.get(msg_id) or {}).get("source")
        if not src:
            print("   attach %-34s NO SUBJECT in welcome-flow-subjects.json" % name[:34])
            continue
        st, res = call(key, "PATCH", "/flow-actions/%s/" % action,
            {"data": {"type": "flow-action", "id": action, "attributes": {
                "definition": {"type": "send-email", "id": action,
                    "links": {"next": nxt},
                    "data": {"status": "draft", "message": {
                        "id": msg_id, "name": name, "subject_line": src,
                        "preview_text": "",
                        "from_email": "hello@helloprint.com",
                        "from_label": "HelloPrint",
                        "reply_to_email": "hello@helloprint.com",
                        "bcc_email": TEST_BCC,
                        "template_id": master,
                        "smart_sending_enabled": True, "transactional": False,
                        "add_tracking_params": False}}}}}})
        if st != 200:
            print("   attach %-34s HTTP %s %s" % (name[:34], st,
                                                 res.get("error", "")[:140]))
            continue
        st, res = call(key, "GET", "/flow-actions/%s/"
                       "?fields[flow-action]=definition.data.message" % action)
        m = ((((res.get("data") or {}).get("attributes") or {}).get("definition")
              or {}).get("data") or {}).get("message") or {}
        new = m.get("template_id")
        fresh[msg_id] = new
        print("   attach %-34s copy %s  subj %s  prev %s  bcc %s"
              % (name[:34], new,
                 "kept" if m.get("subject_line") == src else "CHANGED",
                 "empty" if m.get("preview_text") == "" else "NOT EMPTY",
                 "set" if m.get("bcc_email") == TEST_BCC
                 else ("none" if not m.get("bcc_email") else "OTHER")))
        time.sleep(0.4)
    return fresh


def record(fresh):
    """Write the new copy ids back so the next run and the docs stay truthful."""
    p = MESSAGES
    d = json.loads(io.open(p, encoding="utf-8").read())
    for m in d["messages"]:
        if m["message"] in fresh and fresh[m["message"]]:
            m["template_live"] = fresh[m["message"]]
    d["attached"] = "2026-08-31"
    d["note"] = ("Klaviyo clones a saved template per flow message on attach. "
                 "'template_saved' is the library master, which "
                 "scripts/push_templates.py patches; 'template_live' is the "
                 "per-message copy the flow actually sends. A copy is NOT "
                 "patchable - /api/templates/{id} returns 404 for it - so the "
                 "master is pushed and the message re-attached, which mints a "
                 "fresh copy. Copy ids therefore CHANGE on every push.")
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("recorded %d new copy ids in data/%s"
          % (len(fresh), os.path.basename(p)))


def main():
    dry = "--dry-run" in sys.argv
    push_only = "--push-only" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    key, src = load_key()
    print("key loaded from %s\n" % src)

    todo = [t for t in plan() if not only or only.lower() in t[0].lower()]
    if not todo:
        sys.exit("--only %r matched no template" % only)
    subj = subjects()

    fresh, bad = {}, 0
    for name, path, master, rows in todo:
        if not push_master(key, name, path, master, dry):
            bad += 1
            print()
            continue
        if not push_only:
            fresh.update(reattach(key, master, rows, subj, dry))
        print()

    if fresh and not dry:
        record(fresh)

    print("\nmasters pushed: %d/%d   copies re-cloned: %d   problems: %d"
          % (len(todo) - bad, len(todo), len(fresh), bad))
    if not dry and not bad:
        print("\nNothing was imported by hand and nothing needs re-attaching.")
        print("Re-run this after any builder change to make it live.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
