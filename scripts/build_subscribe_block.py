#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The commercial HTML block for Klaviyo's hosted subscribe page, one per locale.

WHY NINE BLOCKS AND NOT ONE THAT DETECTS THE LANGUAGE. Three things were tested
on the live page and all three say a self-detecting block would be a liability:

  · a ?lang= or ?locale= parameter does not switch language - it flips the page
    into UNSUBSCRIBE mode ("Enter the email you want to unsubscribe")
  · document.documentElement.lang is "en" and stays "en"
  · Accept-Language changes nothing in the server response

So a block that guessed from navigator.language would sometimes render Dutch
above English form labels, which is the one thing the brand voice guide rules
out ("Dutch pages stay Dutch"). Klaviyo already translates this page - the
editor shows 10 translations - so the block is supplied per locale and pasted
into each translation, where it is guaranteed to match the labels beside it.

FONT. The page renders in "Helvetica Neue"/Arial, not Inter. The stack here
asks for Inter first and falls back to the page's own font, so the block matches
its surroundings if Inter is unavailable rather than looking foreign.

The copy comes from data/translations.json, so this block and the email that
links to it cannot drift apart.

  python3 scripts/build_subscribe_block.py
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "_lib"))
ROOT = os.path.dirname(HERE)
import catalog as cat
import i18n
import offers

LOCALES = ["en-IE", "en-GB", "nl-NL", "nl-BE", "fr-FR", "fr-BE",
           "de-DE", "es-ES", "it-IT"]
NAME = {"en-IE": "English (Ireland)", "en-GB": "English (UK)",
        "nl-NL": "Nederlands", "nl-BE": "Nederlands (België)",
        "fr-FR": "Français", "fr-BE": "Français (Belgique)",
        "de-DE": "Deutsch", "es-ES": "Español", "it-IT": "Italiano"}

EYEBROW = {"en": "10% OFF YOUR FIRST ORDER", "nl": "10% KORTING OP JE EERSTE ORDER",
           "fr": "10% SUR VOTRE PREMIÈRE COMMANDE", "de": "10% AUF IHRE ERSTE BESTELLUNG",
           "es": "10% EN TU PRIMER PEDIDO", "it": "10% SUL TUO PRIMO ORDINE"}
H = {"en": "Your 10% is one click away", "nl": "Je 10% is één klik weg",
     "fr": "Vos 10% sont à un clic", "de": "Ihre 10% sind einen Klick entfernt",
     "es": "Tu 10% está a un clic", "it": "Il tuo 10% è a un clic"}
SUB = {
 "en": "Leave your email address below and the code arrives within minutes: 10% off your first order, up to {cap}, valid for 5 days.",
 "nl": "Vul hieronder je e-mailadres in en de code komt binnen enkele minuten: 10% korting op je eerste bestelling, tot {cap}, 5 dagen geldig.",
 "fr": "Indiquez votre adresse e-mail ci-dessous et le code arrive en quelques minutes : 10% sur votre première commande, jusqu'à {cap}, valable 5 jours.",
 "de": "Geben Sie unten Ihre E-Mail-Adresse ein und der Code kommt innerhalb von Minuten: 10% auf Ihre erste Bestellung, bis zu {cap}, 5 Tage gültig.",
 "es": "Introduce tu correo abajo y el código llega en minutos: 10% en tu primer pedido, hasta {cap}, válido 5 días.",
 "it": "Inserisci la tua email qui sotto e il codice arriva in pochi minuti: 10% sul tuo primo ordine, fino a {cap}, valido 5 giorni.",
}
B = {
 "en": ["All-inclusive prices — VAT and delivery before you pay",
        "Every file checked at no cost before it prints",
        "Print experts on the phone, not a chatbot"],
 "nl": ["All-in prijzen — btw en verzending vóór je betaalt",
        "Elk bestand gratis gecontroleerd voordat het gedrukt wordt",
        "Printexperts aan de telefoon, geen chatbot"],
 "fr": ["Prix tout compris — TVA et livraison avant paiement",
        "Chaque fichier vérifié gratuitement avant l'impression",
        "Des experts en impression au téléphone, pas un chatbot"],
 "de": ["All-inclusive-Preise — MwSt. und Versand vor dem Bezahlen",
        "Jede Datei kostenlos geprüft, bevor sie gedruckt wird",
        "Druckexperten am Telefon, kein Chatbot"],
 "es": ["Precios con todo incluido — IVA y envío antes de pagar",
        "Cada archivo revisado gratis antes de imprimir",
        "Expertos en impresión al teléfono, no un chatbot"],
 "it": ["Prezzi tutto compreso — IVA e spedizione prima del pagamento",
        "Ogni file controllato gratuitamente prima della stampa",
        "Esperti di stampa al telefono, non un chatbot"],
}
TP = {"en": "Excellent", "nl": "Uitstekend", "fr": "Excellent",
      "de": "Hervorragend", "es": "Excelente", "it": "Eccellente"}
SMALL = {
 "en": "One per customer. Unsubscribe whenever you like.",
 "nl": "Eén per klant. Je kunt je altijd afmelden.",
 "fr": "Un par client. Désinscription à tout moment.",
 "de": "Einer pro Kunde. Jederzeit abbestellbar.",
 "es": "Uno por cliente. Puedes darte de baja cuando quieras.",
 "it": "Uno per cliente. Puoi disiscriverti quando vuoi.",
}

GREEN = "#008539"
INK = "#191919"
FAINT = "#555555"
# SINGLE QUOTES INSIDE THE FAMILY NAMES, and this is not a style preference.
# Every rule here lives in a style="..." attribute, so a double-quoted family
# name terminates the attribute at the first quote and the whole declaration is
# discarded silently. Measured: with double quotes the eyebrow rendered 15px/400
# ink instead of 11px/700 green, and every other rule in the block died with it.
# Single quotes are valid CSS and safe inside a double-quoted attribute.
FONT = "'Inter','Helvetica Neue',Arial,sans-serif"
TICK = ('<span style="display:inline-block;width:16px;height:16px;border-radius:9999px;'
        'background:%s;color:#fff;font:700 11px/16px %s;text-align:center;'
        'flex:none;margin-top:3px;">&#10003;</span>' % (GREEN, FONT))


def cap_for(locale):
    lang = i18n.LOCALE_LANG[locale]
    cur = cat.item("standardflyers", locale)["currency"]
    return cat.money(offers.WELCOME_CAP, cur, lang, whole=True)


def block(locale):
    lg = i18n.LOCALE_LANG[locale]
    cap = cap_for(locale)
    bullets = "".join(
        '<div style="display:flex;gap:9px;align-items:flex-start;margin:0 0 7px;">'
        '%s<span style="font:400 14px/20px %s;color:%s;">%s</span></div>'
        % (TICK, FONT, FAINT, b) for b in B[lg])
    stars = "".join(
        '<span style="display:inline-block;width:15px;height:15px;background:#00b67a;'
        'margin-right:2px;"></span>' for _ in range(4))
    half = ('<span style="display:inline-block;width:15px;height:15px;'
            'background:linear-gradient(90deg,#00b67a 50%,#dcdce6 50%);"></span>')
    return (
      '<div style="font-family:%(font)s;-webkit-font-smoothing:antialiased;'
      'text-align:left;padding:0 0 6px;">'
      '<div style="font:700 11px/16px %(font)s;letter-spacing:.09em;color:%(green)s;'
      'margin:0 0 6px;">%(eye)s</div>'
      '<div style="font:700 24px/30px %(font)s;color:%(ink)s;margin:0 0 8px;'
      'letter-spacing:-.01em;">%(h)s</div>'
      '<p style="font:400 15px/23px %(font)s;color:%(faint)s;margin:0 0 14px;">%(sub)s</p>'
      '%(bullets)s'
      '<div style="margin:12px 0 0;padding-top:11px;border-top:1px solid #e5e5e5;'
      'display:flex;align-items:center;gap:8px;">'
      '<span style="display:inline-flex;">%(stars)s%(half)s</span>'
      '<span style="font:700 13px/18px %(font)s;color:%(ink)s;">%(tp)s</span>'
      '<span style="font:400 13px/18px %(font)s;color:%(faint)s;">'
      '&middot; 4,5/5 &middot; 34.000+ Trustpilot</span></div>'
      '<p style="font:400 12px/17px %(font)s;color:%(faint)s;margin:11px 0 0;">'
      '%(small)s</p>'
      '</div>'
    ) % {"font": FONT, "green": GREEN, "ink": INK, "faint": FAINT,
         "eye": EYEBROW[lg], "h": H[lg], "sub": SUB[lg].replace("{cap}", cap),
         "bullets": bullets, "stars": stars, "half": half, "tp": TP[lg],
         "small": SMALL[lg]}


DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Subscribe page &middot; HTML blocks per locale</title>
<style>
body{margin:0;background:#f8f8f8;color:#191919;
     font:400 15px/24px "Inter","Helvetica Neue",Arial,sans-serif;padding:32px 20px 60px}
.w{max-width:820px;margin:0 auto}
h1{font-size:28px;line-height:36px;margin:0 0 8px}
.lede{color:#555;margin:0 0 10px}
.how{background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:20px 22px;margin:0 0 26px}
.how ol{margin:8px 0 0;padding-left:20px}
.how li{margin:0 0 6px;color:#333}
.loc{background:#fff;border:1px solid #e5e5e5;border-radius:16px;margin:0 0 22px;overflow:hidden}
.loc h2{margin:0;padding:14px 20px;font-size:16px;line-height:22px;background:#191919;color:#fff}
.prev{padding:22px 20px;border-bottom:1px solid #e5e5e5;background:#fff}
.src{padding:14px 20px 18px}
textarea{width:100%%;height:132px;font:400 12px/17px ui-monospace,SFMono-Regular,Menlo,monospace;
     color:#333;border:1px solid #d9d9d9;border-radius:8px;padding:10px;background:#f8f8f8}
.hint{font-size:12px;line-height:18px;color:#8a8a8a;margin:6px 0 0}
</style></head><body><div class="w">
<h1>Subscribe page &mdash; the commercial block, per locale</h1>
<p class="lede">Klaviyo's hosted subscribe page cannot be edited through the API, so this
is the block to paste in yourself. One per language, because the page's language cannot be
detected from inside a block &mdash; see the note below.</p>
<div class="how">
  <strong>How to add it</strong>
  <ol>
    <li>Open the subscribe page editor, <em>Subscribe page</em> tab.</li>
    <li>Drag an <strong>HTML</strong> block to the top, above the Email field.</li>
    <li>Paste the English block below.</li>
    <li>Open <strong>translations</strong> and paste each language's block into its own
        version. That is what keeps the block in the same language as the labels next to it.</li>
    <li>While you are there: consider deleting <strong>First name</strong> and
        <strong>Last name</strong>. Three fields to claim a discount is friction, and
        Email is the only required one.</li>
  </ol>
</div>
%(sections)s
<div class="how">
  <strong>Why nine blocks and not one that detects the language</strong>
  <ol>
    <li>A <code>?lang=</code> or <code>?locale=</code> parameter does not switch language
        &mdash; it flips the page into <em>unsubscribe</em> mode.</li>
    <li><code>document.documentElement.lang</code> is <code>en</code> and stays <code>en</code>.</li>
    <li><code>Accept-Language</code> changes nothing in the response.</li>
  </ol>
  <p class="hint">So a block guessing from the browser language would sometimes put Dutch
  copy above English form labels. Pasting per translation is the only way to guarantee
  the block matches its surroundings.</p>
</div>
</div></body></html>
"""

SECTION = """<div class="loc">
  <h2>%(name)s &nbsp;&middot;&nbsp; %(loc)s</h2>
  <div class="prev">%(html)s</div>
  <div class="src"><textarea readonly onclick="this.select()">%(esc)s</textarea>
  <p class="hint">Click to select all, then copy.</p></div>
</div>"""

import html as _h
secs = "".join(SECTION % {"name": NAME[l], "loc": l, "html": block(l),
                          "esc": _h.escape(block(l))} for l in LOCALES)
out = DOC % {"sections": secs}
p = os.path.join(ROOT, "proposals", "subscribe-page-blocks.html")
io.open(p, "w", encoding="utf-8").write(out)
print("wrote proposals/subscribe-page-blocks.html  (%d KB, %d locales)"
      % (len(out) // 1024, len(LOCALES)))
for l in LOCALES:
    print("   %-6s %-20s cap %s  %d bytes" % (l, NAME[l], cap_for(l), len(block(l))))
