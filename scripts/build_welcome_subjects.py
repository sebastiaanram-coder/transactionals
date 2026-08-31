#!/usr/bin/env python3
"""
Build the per-locale subject line for each Welcome flow message.

WHY NOT A DJANGO SWITCH, WHICH IS HOW EVERY OTHER STRING IS LOCALISED.
Measured against the live API, not assumed:

  - Django IS accepted in subject_line. A 96-character
    {% if person.locale == 'nl-NL' %}...{% endif %} stored verbatim.
  - subject_line is capped at 255 characters. 255 plain characters stored; 500
    returned 400 "An invalid field type was passed in", and so did the real
    747-character nine-branch switch.

A nine-locale exact-match chain is 560-747 characters, so it cannot fit. Nor can
a six-language one: the {% elif person.locale|slice:':2' == 'xx' %} conditions
alone come to 274 characters before any subject text. Two languages plus English
is the most that fits, which is not a localisation.

So the subject uses Klaviyo's own Translations feature, which is built for
exactly this and which THIS ACCOUNT ALREADY USES - RFB set it up on dozens of
templates, flow messages and campaign variations. Verified on WEL-1 before the
rest were touched: the collection exposes four value blocks (subject,
preview_text, from_label, and the template body), and writing subject
translations left the body block's 47,972-character source untouched with every
body translation empty. An empty translation falls back to the source, so the
template's own nine-branch Django switches stay in charge of the body. The two
mechanisms do not collide.

PREVIEW TEXT IS NOT SET HERE, AND THAT IS THE FIX. Each template already carries
a hidden preheader div that is locale-switched and translated. The flow message
ALSO carried an English preview_text, so the reader got the English field
followed by the translated div. Clearing the field leaves the translated div as
the preheader, which is what it is for.

NO HTML ENTITIES. welcome-04's headline is stored as "we&rsquo;ll" because it
goes into HTML. A subject line is plain text and would show the entity, so
everything here is unescaped.

Writes proposals/welcome-flow-subjects.json - the payloads, not the API calls.
"""
import html, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_lib"))
import i18n   # noqa: E402

# flow message name -> (scope, key). Five of the seven subjects are already a
# translated headline, so they are reused rather than translated twice: a second
# copy is a second thing to keep in step.
# Klaviyo translation locale -> which language's text it gets. Klaviyo's locale
# set is not ours: it uses bare "nl"/"fr"/"de"/"es"/"it" plus "en-GB", "en-IE",
# "nl-BE", "fr-BE". These are the codes the account's existing collections use.
KLAVIYO_LOCALE_LANG = {"en-GB": "en", "en-IE": "en", "nl": "nl", "nl-BE": "nl",
                       "fr": "fr", "fr-BE": "fr", "de": "de", "es": "es",
                       "it": "it"}

# flow message id -> (name, scope, key). Five of the seven subjects are already a
# translated headline, so they are reused rather than translated twice.
SUBJECTS = {
    "WC7XqJ": ("WEL-1 Welcome · day 0 (1h)",       "flow-welcome", "subj.wel1"),
    "T3gcpL": ("WEL-1B Welcome · ord@S1",          "welcome-01", "h1"),
    "SWCW4n": ("WEL-2 Behind the print · day 1",   "welcome-02", "h1"),
    "VZ6UN7": ("WEL-2B Behind the print · ord@S1", "welcome-02", "h1"),
    "TzDYEZ": ("WEL-2B Behind the print · ord@S2", "welcome-02", "h1"),
    "XCghBN": ("WEL-3 Rated excellent · day 3",    "_shared", "wc.waiting"),
    "YjUAzP": ("WEL-3B Rated excellent · ord@S1",  "welcome-03", "h1"),
    "Tv2JjB": ("WEL-3B Rated excellent · ord@S2",  "welcome-03", "h1"),
    "VPQq7j": ("WEL-3B Rated excellent · ord@S3",  "welcome-03", "h1"),
    "XxD3gq": ("WEL-4 Send it over · day 5",       "flow-welcome", "subj.wel4"),
    "Yfhker": ("WEL-4B Send it over · ord@S1",     "welcome-04", "h1"),
    "RBXAtJ": ("WEL-4B Send it over · ord@S2",     "welcome-04", "h1"),
    "SMnrmA": ("WEL-4B Send it over · ord@S3",     "welcome-04", "h1"),
    "SamnJX": ("WEL-4B Send it over · ord@S4",     "welcome-04", "h1"),
}

def text(scope, key, lang):
    v = ((i18n.data().get(scope) or {}).get(key) or {}).get(lang)
    if v is None:
        raise KeyError("%s/%s has no %s" % (scope, key, lang))
    return html.unescape(v)


def main():
    out, errs = {}, []
    for msg_id, (name, scope, key) in SUBJECTS.items():
        tr = {}
        for kloc, lang in KLAVIYO_LOCALE_LANG.items():
            v = text(scope, key, lang)
            if "&" in v and ";" in v:
                errs.append("%s/%s: entity survived: %s" % (name, kloc, v))
            if len(v) > 150:
                errs.append("%s/%s: %d characters is too long for a subject"
                            % (name, kloc, len(v)))
            tr[kloc] = v
        out[msg_id] = {"name": name, "scope": scope, "key": key,
                       "source": text(scope, key, "en"), "translations": tr}

    print("%-8s %-36s %s" % ("msg", "flow message", "English source"))
    for mid, d in out.items():
        print("%-8s %-36s %s" % (mid, d["name"], d["source"]))
    print()
    print("one message in full, %s:" % list(out)[0])
    for k, v in out[list(out)[0]]["translations"].items():
        print("   %-6s %s" % (k, v))

    if errs:
        print("\nPROBLEMS:")
        for e in errs:
            print("  " + e)
        return 1

    p = os.path.join(ROOT, "proposals", "welcome-flow-subjects.json")
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("\nwritten proposals/welcome-flow-subjects.json  (%d messages)" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
