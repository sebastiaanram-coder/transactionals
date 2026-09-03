#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add (or rewrite) the Translation review section of the overview doc.

WHY THIS EXISTS. The doc embeds the ENGLISH render of every email and has no
locale switcher, so a translation-only change could not move it at all - the
reviewable artefact was a CSV nobody outside the repo sees. Translators need the
opposite of a rendered email anyway: the strings, side by side with the English,
in the order they appear, with a note of where each one sits and which bits must
survive editing untouched.

WHAT IT CHECKS WHILE RENDERING. Every translation is compared against its
English for the things a reviewer cannot see but an email breaks on:

  @@CAP@@ and {n}   replaced at build time with the discount cap and a quantity.
                    Translated or dropped, that market silently loses them.
  &middot; &rsquo;  markup, not text. A retyped line easily turns "&" into a
                    bare ampersand, which breaks the HTML.
  <em>              the emphasis has to survive in pairs.
  the NBSP          French groups thousands with U+00A0. It is invisible in a
                    spreadsheet and a normal space lets the number wrap.

A row that fails any of those is flagged in the table rather than left for the
render check to find later.

Idempotent: the section lives between two markers and is replaced wholesale.

  python3 scripts/refresh_overview_translations.py
"""
import html as H
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
DOC = os.path.join(ROOT, "behavioural-email-overview.html")
STORE = os.path.join(ROOT, "data", "translations.json")
BEGIN, END = "<!--TRX:BEGIN-->", "<!--TRX:END-->"

from translations_csv import EMAIL_NAME, WHERE, LANGS, VARIANTS   # noqa: E402

LANG_NAME = {"nl": "Nederlands", "fr": "Français", "de": "Deutsch",
             "es": "Español", "it": "Italiano", "en-US": "English (US)",
             "sv": "Svenska (draft)"}
REVIEW = [l for l in LANGS if l != "en"] + list(VARIANTS)

# the order flows are presented in, and which scopes belong to each
GROUPS = [
 ("BEH-1 Welcome", ["flow-welcome", "welcome-01", "welcome-02", "welcome-03",
                    "welcome-04"]),
 ("BEH-1b Account created", ["account-01"]),
 ("BEH-2 Browse Abandonment", ["flow-browse", "browse-01", "browse-02",
                               "browse-03"]),
 ("BEH-3 Abandoned Order", ["flow-order", "order-01", "order-02-high",
                            "order-02-low", "order-03-high", "order-03-low"]),
 ("BEH-4 Post-Purchase", ["post-01-review", "post-02-reminder", "post-04-expert",
                          "post-05-offer", "post-06-lastday"]),
 ("BEH-5 Customer Winback", ["winback-01-high", "winback-01-low",
                             "winback-02-high", "winback-02-low",
                             "winback-03-high"]),
 ("Product category names", ["clothing-textiles", "commercial-print",
                             "corporate-gifts", "labels-packaging",
                             "signage-outdoor", "stationery"]),
 ("Shared across flows", ["_shared"]),
]
NBSP = " "


def issues(en, tr, lang):
    """What a reviewer cannot see but the email breaks on. [] when clean."""
    out = []
    if not (tr or "").strip():
        return ["not translated"]
    for pat, what in ((r"@@[A-Z]+@@", "token"), (r"\{\w+\}", "placeholder")):
        a, b = sorted(re.findall(pat, en)), sorted(re.findall(pat, tr))
        if a != b:
            out.append("%s: %s vs %s" % (what, b or "none", a or "none"))
    if (en.count("<em>"), en.count("</em>")) != (tr.count("<em>"), tr.count("</em>")):
        out.append("&lt;em&gt; not matched")
    if re.search(r"&(?![a-z]+;|#\d+;)", tr):
        out.append("bare &amp;")
    if lang == "fr" and re.search(r"\d \d{3}", tr):
        out.append("normal space in a number, needs NBSP")
    return out


def esc(t):
    """Show the string as the translator must keep it: entities stay visible."""
    return H.escape(t or "", quote=False).replace(NBSP, "<span class=nb>&#9251;</span>")


def build(d):
    rows_total = flagged = 0
    parts = [BEGIN,
      '<div class="wrap"><section id="translations">',
      '<h2 class="secttl">Translation review</h2>',
      '<p class="trx-lede">Every string in the programme, beside its English '
      'source. Pick a language and read down: this is what the emails actually '
      'say, in the order the reader meets it. <b>Bold</b> markers such as '
      '<code>@@CAP@@</code>, <code>{n}</code> and <code>&amp;middot;</code> are '
      'replaced or rendered at build time and must survive editing exactly as '
      'they are. <span class=nb>&#9251;</span> marks a non-breaking space.</p>',
      '<div class="trx-bar"><label for="trxlang">Language</label> '
      '<select id="trxlang">']
    for l in REVIEW:
        parts.append('<option value="%s"%s>%s</option>'
                     % (l, ' selected' if l == "nl" else '', LANG_NAME[l]))
    parts.append('</select> <span class="trx-count muted"></span></div>')

    for title, scopes in GROUPS:
        blocks = []
        for sc in scopes:
            node = d.get(sc) or {}
            keys = [k for k in node
                    if isinstance(node[k], dict) and "en" in node[k]]
            if not keys:
                continue
            trs = ['<h3>%s</h3>' % H.escape(EMAIL_NAME.get(sc, sc)),
                   '<table class="trx"><thead><tr><th>Where</th><th>English</th>'
                   '<th class="trx-t">Translation</th><th>Keep exactly</th>'
                   '</tr></thead><tbody>']
            for k in keys:
                e = node[k]
                en = e["en"]
                keep = sorted(set(re.findall(r"@@[A-Z]+@@", en))
                              | set(re.findall(r"&[a-z]+;", en))
                              | set(re.findall(r"\{\w+\}", en)))
                cells = []
                for l in REVIEW:
                    bad = issues(en, e.get(l, ""), l)
                    # AN ABSENT VARIANT IS NOT A DEFECT. A blank en-US means
                    # "use the English" and a blank sv means "not written yet";
                    # counting either as a problem made the headline read 425
                    # and told the reader nothing. Only integrity failures on a
                    # string that HAS a value are flagged.
                    blank_variant = l in VARIANTS and not e.get(l)
                    flagged += bool(bad) and not blank_variant
                    warn = ('<div class="trx-warn">%s</div>' % "; ".join(bad)
                            if bad and not blank_variant else "")
                    if e.get(l):
                        body = esc(e[l])
                    elif l == "sv":
                        # Swedish covers the Welcome flow only so far, and a gap
                        # is a gap - not a deliberate fall-through to English.
                        body = ('<span class="trx-none">not translated yet'
                                '</span>')
                    elif l in VARIANTS:
                        body = ('<span class="muted">&mdash; uses the English'
                                '</span>')
                    else:
                        body = '<span class="trx-none">not translated</span>'

                    cells.append('<td class="trx-v" data-l="%s">%s%s</td>'
                                 % (l, body, warn))
                rows_total += 1
                trs.append('<tr><td class="trx-w"><code>%s</code><br>'
                           '<span class="muted">%s</span></td>'
                           '<td class="trx-en">%s</td>%s'
                           '<td class="trx-k">%s</td></tr>'
                           % (H.escape(k), H.escape(WHERE.get(k, "")),
                              esc(en), "".join(cells),
                              " ".join('<code>%s</code>' % H.escape(x)
                                       for x in keep) or
                              '<span class="muted">&mdash;</span>'))
            trs.append('</tbody></table>')
            blocks.append("\n".join(trs))
        if blocks:
            parts.append('<h2 class="trx-flow">%s</h2>' % H.escape(title))
            parts += blocks

    parts += ['</section></div>', STYLE, SCRIPT, END]
    return "\n".join(parts), rows_total, flagged


STYLE = """<style>
#translations .trx-lede{font-size:14px;line-height:22px;color:var(--ink2);
  max-width:78ch;margin:0 0 18px}
#translations .trx-bar{position:sticky;top:0;z-index:5;background:var(--surf);
  border:1px solid var(--bd);border-radius:8px;padding:10px 14px;margin:0 0 22px;
  display:flex;gap:10px;align-items:center;font-size:13px}
#translations .trx-bar select{font:inherit;padding:4px 8px;border:1px solid
  var(--bd);border-radius:6px;background:#fff}
#translations h2.trx-flow{font-size:16px;font-weight:700;margin:34px 0 10px;
  padding-bottom:6px;border-bottom:2px solid var(--bd)}
#translations h3{font-size:13px;font-weight:600;color:var(--ink3);
  text-transform:uppercase;letter-spacing:.04em;margin:22px 0 6px}
table.trx{width:100%;border-collapse:collapse;table-layout:fixed}
table.trx th:nth-child(1),table.trx td:nth-child(1){width:16%}
table.trx th:nth-child(2),table.trx td:nth-child(2){width:35%}
table.trx th.trx-t{width:35%}
table.trx th:last-child,table.trx td.trx-k{width:14%}
table.trx td{font-size:13px;line-height:20px}
table.trx td.trx-en{color:var(--ink)}
table.trx td.trx-w code{font-size:11px;color:var(--ink2)}
table.trx td.trx-k code{font-size:11px;background:#f1f1f1;padding:1px 4px;
  border-radius:3px;font-weight:700}
#translations .trx-lede code{font-size:11px;background:#f1f1f1;padding:1px 4px;
  border-radius:3px}
.trx-none{color:#92400e;font-style:italic}
.trx-warn{margin-top:4px;font-size:11px;line-height:15px;color:#92400e;
  background:#fff8e1;border-left:2px solid var(--amber);padding:3px 6px}
.nb{color:#8a9197;font-weight:700}
table.trx td.trx-v{display:none}
table.trx td.trx-v.on{display:table-cell}
@media (max-width:900px){table.trx,table.trx tbody,table.trx tr,
  table.trx td{display:block;width:auto}
  table.trx thead{display:none}
  table.trx tr{border-bottom:1px solid var(--bd);padding:8px 0}
  table.trx td{border:0;padding:2px 0}}
</style>"""

SCRIPT = """<script>
(function(){
  var sel = document.getElementById('trxlang');
  if (!sel) return;
  var count = document.querySelector('#translations .trx-count');
  function show(l){
    document.querySelectorAll('#translations td.trx-v').forEach(function(td){
      td.classList.toggle('on', td.dataset.l === l);
    });
    var n = document.querySelectorAll(
      '#translations td.trx-v.on .trx-warn, #translations td.trx-v.on .trx-none'
    ).length;
    count.textContent = n ? n + ' string(s) need attention' : 'no issues flagged';
    count.style.color = n ? '#92400e' : '';
  }
  sel.addEventListener('change', function(){ show(sel.value); });
  show(sel.value);
})();
</script>"""


def main():
    d = json.loads(io.open(STORE, encoding="utf-8").read())
    sec, n, flagged = build(d)
    s = io.open(DOC, encoding="utf-8").read()
    before = len(s)
    if BEGIN in s:
        i, j = s.index(BEGIN), s.index(END) + len(END)
        s = s[:i] + sec + s[j:]
        how = "replaced"
    else:
        # before the footer, which is the last thing in the body
        anchor = '<div class="foot">'
        assert s.count(anchor) == 1, "footer anchor is not unique"
        s = s.replace(anchor, sec + "\n" + anchor, 1)
        how = "inserted"
    io.open(DOC, "w", encoding="utf-8").write(s)
    print("%s the Translation review section: %d strings, %d flagged"
          % (how, n, flagged))
    print("languages: %s" % ", ".join(LANG_NAME[l] for l in REVIEW))
    print("doc %d KB -> %d KB" % (before / 1024, len(s) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
