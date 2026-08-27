"""
House style rules that every email has to pass, in one place.

WHY THIS EXISTS. The jargon list was copied into eight builders, which means eight
places to update and eight chances to miss one. The em dash rule arrived after
fourteen of them had already shipped one. Rules that apply to every email belong
somewhere every builder can call.

WHAT COUNTS AS VISIBLE. Not the stylesheet, not the HTML comments, not the Django
tags - a reader sees rendered text and alt attributes, and nothing else. Checking
raw markup instead is how a previous check tripped on "gsm" inside a URL and then
inside a template tag.
"""
import re

# NO EM DASHES IN EMAIL COPY. They read as machine-written, and they let a sentence
# run twice as long as it should because there is always room for one more clause.
# The fix is almost always a full stop.
DASHES = ("—", "&mdash;", "–", "&ndash;")

# Trade language a customer should not have to know. House style forbids it in
# anything a reader sees.
JARGON = ("bleed", "dpi", "cmyk", "safe area", "pre-flight", "gsm")


def visible(html):
    """The text a reader actually sees, plus alt text, lowercased."""
    body = html.split("</style>", 1)[1] if "</style>" in html else html
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    alts = " ".join(re.findall(r'alt="([^"]*)"', body))
    txt = re.sub(r"\{%.*?%\}", " ", re.sub(r"<[^>]+>", " ", body), flags=re.S)
    txt = re.sub(r"\{\{.*?\}\}", " ", txt, flags=re.S)
    return re.sub(r"\s+", " ", txt + " " + alts).strip().lower()


def violations(html, label=""):
    """Every house-style breach in one email, as a list of sentences."""
    vis = visible(html)
    out = []
    for d in DASHES:
        if d in vis:
            # show the offending sentence, because "there is an em dash somewhere"
            # is not enough to act on
            i = vis.index(d)
            out.append("%san em dash: …%s…"
                       % (label and label + ": ", vis[max(0, i - 45):i + 45]))
            break
    for j in JARGON:
        if j in vis:
            out.append("%sjargon, which house style forbids: %s"
                       % (label and label + ": ", j))
    return out
