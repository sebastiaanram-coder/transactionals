# -*- coding: utf-8 -*-
"""
Make the emails survive a mail client's dark mode.

THE SYMPTOM, seen on Gmail for iOS in dark mode: the black masthead came out
light grey, with the wordmark sitting in it as a black rectangle. Nothing was
wrong with the email. Gmail's dark mode REWRITES COLOURS THAT COME FROM CSS -
it inverts what it decides is a light-on-dark or dark-on-light pair - and the
masthead's #191919 lives in a `<style>` rule on a <div>. The wordmark kept its
black because that black is part of the PNG, not part of the CSS, which is
exactly why it ended up as a black box on a lightened band.

The same rewrite is what makes a transparent packshot look broken. Feed images
are PNGs with no background, and they were sitting on cells coloured #f8f8f8 and
#ffffff from CSS classes. Invert those to near-black and the product is floating
on a dark panel it was never cut out for.

WHAT ACTUALLY SURVIVES, and this is the whole technique:

  1. `bgcolor` is an HTML ATTRIBUTE, not CSS. Gmail's inverter leaves it alone.
     So every colour that matters is stated twice - once as bgcolor for the
     client, once in CSS for everything else.
  2. `background-color` INLINE on the <img> itself travels with the image, so a
     transparent PNG keeps a white card behind it whatever happens to its
     container.
  3. `<meta name="color-scheme" content="light">` tells Apple Mail and Outlook
     that this message only has a light design, and they stop auto-inverting.
     Gmail ignores it; 1 and 2 are what cover Gmail.
  4. `[data-ogsc]` / `[data-ogsb]` are the attributes the Gmail app adds to
     elements whose colour it changed, so a rule keyed on them can put the
     intended colour back. Support varies by Gmail version, which is why it is
     the backstop here and not the primary fix.

WHY THIS IS A POST-PROCESS and not nine edits. It is the same shape as
scripts/fix_link_specificity.py: one rule, applied to every built body, so the
nine emails cannot drift apart and a tenth gets it for free. Each builder keeps
its own markup; this only hardens what they produced.
"""
import re

INK = "#191919"       # the masthead
CARD = "#ffffff"      # anything a transparent image sits on
TILE_BG = "#f8f8f8"   # the packshot cell

_METAS = ('<meta name="color-scheme" content="light">\n'
          '<meta name="supported-color-schemes" content="light">\n')


def metas():
    """The two <head> tags. Kept here so doc.shell and this module agree."""
    return _METAS


def _masthead(html):
    """The <div> masthead becomes a table whose colour is a bgcolor attribute."""
    pat = re.compile(
        r'<div class="(hp-[a-z0-9]+)-logobar">(.*?)</div>', re.S)

    def sub(m):
        cls, inner = m.group(1), m.group(2)
        # THE CLASS GOES ON THE CELL, not the table. The existing rule is
        # `.hp-x-logobar{background:#191919;padding:12px 24px 10px;}` and
        # padding on a <table> is not reliably honoured by Outlook, so moving
        # the class up would quietly lose the masthead's padding in exactly the
        # client that needs the table wrapper in the first place.
        return (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0"'
            ' width="100%%" bgcolor="%(ink)s" style="background-color:%(ink)s;">'
            '<tr><td align="center" bgcolor="%(ink)s" class="%(cls)s-logobar"'
            ' style="background-color:%(ink)s;">%(inner)s</td></tr></table>'
            % {"ink": INK, "cls": cls, "inner": inner})
    return pat.subn(sub, html)


def _image_backgrounds(html):
    """Give every image that can be transparent its own white card.

    Catalog packshots come straight from the feed and are PNGs with no
    background. `background-color` inline on the <img> is the one place a client
    will not take it away, and it is square on purpose: a rounded corner on the
    image would show the inverted container through the corner, which is the
    artefact this is removing.
    """
    n = 0
    out = []
    pos = 0
    for m in re.finditer(r"<img\b[^>]*>", html):
        tag = m.group(0)
        transparent = ("featured_image" in tag or "catalog_item" in tag
                       or "-ellipse" in tag or "wordmark-dark" in tag)
        if not transparent or "background-color" in tag:
            continue
        add = "background-color:%s;" % CARD
        if 'style="' in tag:
            new = tag.replace('style="', 'style="%s' % add, 1)
        else:
            new = tag[:-1].rstrip() + ' style="%s">' % add
        out.append((m.start(), m.end(), new))
        n += 1
    for s, e, new in reversed(out):
        html = html[:s] + new + html[e:]
    return html, n


def _cells(html):
    """Restate the panel colours the images sit on, where the client will keep them.

    td and div take a `bgcolor` attribute. An <a> does not - the tile cards are
    anchors - so those get the colour inline instead, which is the next most
    durable place. Counting is of ACTUAL changes: an earlier version returned
    subn's match count, which reported 18 hardened cells on an email where it
    had changed two, because the anchors matched and were then skipped.
    """
    n = 0
    for cls, colour in (("pimgcell", TILE_BG), ("tile", CARD), ("shell", CARD)):
        pat = re.compile(r'<(td|div|a)([^>]*?)class="(hp-[a-z0-9]+)-%s"' % cls)

        def sub(m):
            nonlocal n
            tag, rest, pre = m.group(1), m.group(2), m.group(3)
            if "bgcolor" in rest or "background-color" in rest:
                return m.group(0)
            n += 1
            if tag == "a":
                return ('<a%s style="background-color:%s;" class="%s-%s"'
                        % (rest.rstrip() or "", colour, pre, cls))
            return ('<%s%s bgcolor="%s" class="%s-%s"'
                    % (tag, rest.rstrip() or "", colour, pre, cls))
        html = pat.sub(sub, html)
    return html, n


def _ogsc(html):
    """Backstop: put the masthead colour back if the Gmail app recolours it."""
    rules = []
    for pre in sorted(set(re.findall(r"class=\"(hp-[a-z0-9]+)-logobar\"", html))):
        rules.append("[data-ogsc] .%s-logobar,[data-ogsb] .%s-logobar"
                     "{background:%s !important;background-color:%s !important;}"
                     % (pre, pre, INK, INK))
    if not rules:
        return html, 0
    block = "\n" + "\n".join(rules) + "\n"
    i = html.rfind("</style>")
    if i < 0:
        return html, 0
    return html[:i] + block + html[i:], len(rules)


def harden(html):
    """All of it, in one call. Returns (html, counts) so a builder can report."""
    html, mast = _masthead(html)
    html, imgs = _image_backgrounds(html)
    html, cells = _cells(html)
    html, ogsc = _ogsc(html)
    return html, {"masthead": mast, "images": imgs, "cells": cells, "ogsc": ogsc}
