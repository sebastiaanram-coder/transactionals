# -*- coding: utf-8 -*-
"""
The document shell every Klaviyo email needs, and the <html lang> in it.

WHY THIS EXISTS. The Welcome templates are full HTML documents and carry a
nine-way locale switch in <html lang>. The browse and abandoned-order blocks
were emitted as a bare <div class="hp-b1-root"> with its own <style>, so the
template Klaviyo stored - and therefore the message it sends - had no <html>
element and no lang attribute at all.

That is the same defect that was fixed on Welcome, for the same reasons: screen
readers take their pronunciation rules from lang, so a Dutch email was read
aloud in an English accent, and Gmail and Outlook use it when deciding whether
to offer to translate the message. A block with no lang is not better than
lang="en"; the client just guesses instead.

WHY IT WRAPS AT THE WRITE SITE, not inside the builders' KLAVIYO_DOC strings.
Those are %-format templates and the lang switch is Django - `{% if ... %}` -
which carries bare % signs. Embedding it in a format string would need every %
doubled, and one missed pair is a ValueError at build time or, worse, a mangled
switch in the shipped HTML. Formatting first and wrapping after cannot have that
bug.

THE DOC COMMENT MOVES INSIDE. Each block opens with a generated-by comment. A
comment before <!DOCTYPE html> is legal but puts a stray node ahead of the
doctype, and Welcome puts its comment after <body>, so this matches that: the
leading comment is lifted out and re-emitted directly after the body tag.

AND IT IS WRAPPED IN {% comment %}, WHICH IS NOT COSMETIC. *** Django parses
inside HTML comments. *** <!-- --> hides text from a browser; it hides nothing
from the template engine. Those generated headers document the bindings by
QUOTING them - "{% catalog %}", "{% with %} is not supported", "{% if ... 'GBP' %}"
- and Klaviyo executed every one of those examples. A bare {% catalog %} has no
id, {% with %} does not exist in Klaviyo's dialect, and either one fails the
WHOLE render with 400 "Unable to render given template with provided context".

Five of the nine BEH-2/BEH-3 templates failed to render for exactly this reason
and nothing else: browse 1, 2, 3 and both low-value order emails. Each was
correct HTML with correct Django in its body, and each would have sent nothing.
Confirmed by stripping only the comment, which made all five render.

{% comment %} is the right neutraliser rather than {% verbatim %} because it does
not parse its contents AND drops them from the output, so the header stays
readable in Klaviyo's code editor while 1.0-1.9 KB per email stops being sent to
the recipient. That margin is worth having: Gmail clips a message at about 102 KB
and the largest of these is 81 KB.

Any OTHER comment carrying template syntax is wrapped in {% verbatim %} instead,
which also stops execution but keeps the bytes - a mid-body comment may be an
Outlook conditional comment, and those have to survive into the output.
"""
import re

import darkmode
import i18n

# Same body attributes as the Welcome documents. The page background shows in the
# gutter either side of the 600px block, so it is not decoration.
BODY = 'style="margin:0;padding:0;background:#f8f8f8;"'

_LEAD_COMMENT = re.compile(r"\A\s*(<!--.*?-->)\s*", re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _has_template_syntax(text):
    return "{%" in text or "{{" in text


def _guard_body_comments(block):
    """{% verbatim %} any remaining comment that quotes template syntax.

    Keeps the bytes, unlike {% comment %}, because a mid-body comment can be an
    Outlook conditional comment (<!--[if mso]>) that must reach the client.
    """
    def sub(m):
        c = m.group(0)
        if not _has_template_syntax(c) or "{% verbatim %}" in c:
            return c
        return "{%% verbatim %%}%s{%% endverbatim %%}" % c
    return _COMMENT.sub(sub, block)


def shell(block, live=True, locale=None, title="Helloprint"):
    """Wrap one scoped block in a full document. Idempotent.

    THE TITLE IS ALWAYS THE BRAND, never the build label. `title` is kept in the
    signature because the builders pass one and it reads as documentation, but
    the document that reaches a customer said "Abandoned order 03 low" - the
    only English string left in an otherwise fully Dutch email, since the doc
    comment it belongs with is inside {% comment %} and never renders. It is not
    shown in the body, but it is what a screen reader announces and what a
    "view in browser" tab shows.
    """
    title = "Helloprint"
    if "<html" in block[:2000]:
        return block                      # already a document, leave it alone
    lead = ""
    m = _LEAD_COMMENT.match(block)
    if m:
        # {% comment %}, not a bare <!-- -->: Django executes what is inside an
        # HTML comment, and these headers quote {% catalog %} and {% with %} as
        # documentation. See the module docstring.
        lead = "{%% comment %%}\n%s\n{%% endcomment %%}\n" % m.group(1)
        block = block[m.end():]
    block = _guard_body_comments(block)
    # Dark mode is hardened HERE, for every email at once - see darkmode.py.
    # Gmail rewrites colours that come from CSS, which turned the black masthead
    # light grey and would have put transparent feed packshots on a dark panel.
    block, _counts = darkmode.harden(block)
    return ('<!DOCTYPE html>\n<html lang="%s">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '%s'
            '<title>%s</title>\n</head>\n<body %s>\n%s%s\n</body>\n</html>\n'
            % (i18n.html_lang(live, locale), darkmode.metas(), title, BODY,
               lead, block.rstrip()))
