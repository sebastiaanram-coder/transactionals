#!/usr/bin/env python3
"""
Lay the Klaviyo templates out in one folder, named as they must be named there.

WHY THIS EXISTS. The template HTML has to be pasted into Klaviyo by hand. The
MCP tool takes the HTML as a JSON string parameter, which means an assistant
does not copy it, it re-types it with JSON escaping applied - 46KB of quoted
Django and CSS per file, where one wrong character lands silently in an inbox.
Pasting is the safe path, so this makes pasting as close to mechanical as it can
be: one folder, one file per template, and the filename IS the name to type.

It also refuses to hand over a file that is not a complete block, because the
point of failure is now a human copy and the cheapest place to catch a bad one
is before it is pasted rather than after it has sent.

KLAVIYO DOES HAVE EMAIL FOLDERS, in the UI: Templates -> Create -> New email
folder. The API does not expose them - it offers name, editor_type, html and
timestamps, and the tagging endpoints cover campaigns, flows, lists and segments
but not templates - which is not the same thing as the product lacking them, and
an earlier version of this comment said the wrong one.

So: put these eight in a folder called "BEH-1 Welcome". The "BEH-1 " prefix in
each NAME stays anyway, because a flow message picker shows the template name
without its folder, and that is where picking the wrong one costs something.

The same menu offers "Import email template", which takes an HTML file. If it
accepts these directly then nothing needs pasting at all, and this folder is the
set of files to hand it.
"""
import io, json, os, re, shutil, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))
import offers

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "proposals")
OUT = os.path.join(ROOT, "klaviyo-templates")

# (source block, Klaviyo template name, which flow messages use it)
TEMPLATES = [
    ("welcome-01-klaviyo.html", "BEH-1 WEL-1 Welcome + 10%",
     ["WEL-1 Welcome · day 0 (3h)"]),
    ("welcome-01-nocode-klaviyo.html", "BEH-1 WEL-1B Welcome, no discount",
     ["WEL-1B Welcome · ord@S1"]),
    ("welcome-02-klaviyo.html", "BEH-1 WEL-2 Behind the print",
     ["WEL-2 Behind the print · day 1"]),
    ("welcome-02-nocode-klaviyo.html", "BEH-1 WEL-2B Behind the print, no discount",
     ["WEL-2B Behind the print · ord@S1", "WEL-2B Behind the print · ord@S2"]),
    ("welcome-03-klaviyo.html", "BEH-1 WEL-3 Rated excellent",
     ["WEL-3 Rated excellent · day 3"]),
    ("welcome-03-nocode-klaviyo.html", "BEH-1 WEL-3B Rated excellent, no discount",
     ["WEL-3B Rated excellent · ord@S1", "WEL-3B Rated excellent · ord@S2",
      "WEL-3B Rated excellent · ord@S3"]),
    ("welcome-04-klaviyo.html", "BEH-1 WEL-4 Send it over",
     ["WEL-4 Send it over · day 5"]),
    ("welcome-04-nocode-klaviyo.html", "BEH-1 WEL-4B Send it over, no discount",
     ["WEL-4B Send it over · ord@S1", "WEL-4B Send it over · ord@S2",
      "WEL-4B Send it over · ord@S3", "WEL-4B Send it over · ord@S4"]),
]

GMAIL_CLIP_KB = 102
OK_HOSTS = ("https://d3k81ch9hvuctc.cloudfront.net/",
            "https://contentful.helloprint.com/",
            "https://images.ctfassets.net/")


def audit(name, html):
    """Everything that must be true before a human pastes this into Klaviyo."""
    out = []
    if not html.lstrip().lower().startswith("<!doctype html>"):
        out.append("does not start with <!DOCTYPE html>, so it may be truncated")
    if not html.rstrip().lower().endswith("</html>"):
        out.append("does not end with </html>, so it is truncated")
    kb = len(html.encode("utf-8")) // 1024
    if kb > GMAIL_CLIP_KB:
        out.append("%d KB, over Gmail's ~%d KB clip" % (kb, GMAIL_CLIP_KB))
    if "REPLACE-WITH-KLAVIYO-ASSET" in html:
        out.append("still carries an unresolved sentinel asset URL")
    if "data:image" in html:
        out.append("embeds a base64 image, which Gmail and Outlook will not render")
    if 'href="#"' in html:
        out.append('has a dead href="#" link')
    n_if = len(re.findall(r"\{%\s*if\s", re.sub(r"<!--.*?-->", "", html, flags=re.S)))
    n_end = len(re.findall(r"\{%\s*endif\s*%\}", re.sub(r"<!--.*?-->", "", html, flags=re.S)))
    if n_if != n_end:
        out.append("%d {%% if %%} against %d {%% endif %%}" % (n_if, n_end))
    if re.search(r"\{%\s*\w+\s+'[^']*\{%", html):
        out.append("nests a locale switch inside a tag argument, which 400s the render")
    n_unsub = html.count("{% unsubscribe")
    if n_unsub == 0:
        out.append("has no {% unsubscribe %} tag")
    for m in re.finditer(r'src="(https?://[^"]+)"', html):
        if not m.group(1).startswith(OK_HOSTS):
            out.append("loads an image from %s, which is not a host we control"
                       % m.group(1)[:56])
            break
    # the no-discount variants must not mention the offer
    if "no discount" in name:
        for w in ("10%", offers.WELCOME_CODE):
            if w in html:
                out.append("is a no-discount variant but still says %r" % w)
    return out


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    errs, rows, manifest = [], [], []
    for src, name, messages in TEMPLATES:
        p = os.path.join(SRC, src)
        if not os.path.exists(p):
            errs.append("%s is missing, so %r cannot be built" % (src, name))
            continue
        html = io.open(p, encoding="utf-8").read()
        for e in audit(name, html):
            errs.append("%s %s" % (name, e))
        dst = os.path.join(OUT, name + ".html")
        shutil.copy2(p, dst)
        rows.append((name, len(html.encode("utf-8")) // 1024, len(messages)))
        manifest.append({"template": name, "file": name + ".html",
                         "source": src, "flow_messages": messages})

    print("%-46s %5s  %s" % ("PASTE AS THIS NAME", "SIZE", "USED BY"))
    for name, kb, n in rows:
        print("%-46s %4dKB  %d message%s" % (name, kb, n, "" if n == 1 else "s"))
    print("\n%d templates -> %s/  (%d flow messages covered)"
          % (len(rows), os.path.relpath(OUT, ROOT), sum(r[2] for r in rows)))

    with open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump({"flow": "BEH-1 Welcome · Completed Signup",
                   "flow_id": "TEhf2p", "editor_type": "CODE",
                   "klaviyo_folder": "BEH-1 Welcome",
                   "how_to_load": (
                       "Templates -> Create -> New email folder, name it "
                       "'BEH-1 Welcome'. Then Create -> Import email template "
                       "for each .html in here. If import will not take them, "
                       "Create -> New template -> code editor and paste."),
                   "templates": manifest}, f, ensure_ascii=False, indent=1)

    if errs:
        print()
        for e in errs:
            print("  FAIL  " + e)
        raise SystemExit(1)
    print("Every file is a complete block and safe to paste.")


if __name__ == "__main__":
    main()
