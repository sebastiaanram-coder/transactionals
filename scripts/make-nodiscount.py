#!/usr/bin/env python3
"""
Generate the no-discount variant of a Welcome email from the discount version.

The two versions differ in a handful of places only, so keeping a second copy
by hand would drift. This derives one from the other, which means there is a
single file to edit when the design changes.

Usage: python3 scripts/make-nodiscount.py proposals/welcome-01-proposed.html
"""
import re, sys, os

def strip_discount(s):
    # 1. promo bar carries a brand line instead of the offer
    s = re.sub(r'(<div class="hp-w1-promo">)\s*Your 10% welcome discount\s*<span class="hp-w1-ends">.*?</span>\s*',
               r'\1\n      Print made simple, by people who have your back ',
               s, count=1, flags=re.S)
    # 2. hero subline loses the code sentence
    s = s.replace(' Your 10% code is ready whenever you are.', '')
    # 3. the code chip goes entirely, with its trailing break
    s = re.sub(r'\s*<div class="hp-w1-code">.*?</div><br>', '', s, count=1, flags=re.S)
    # 4. grid subline stops promising a checkout discount
    s = s.replace('Pick one and your 10% comes off at checkout.',
                  'Where most businesses start.')
    # 5. each tile keeps the catalogue price only, with no strike and no
    #    second figure beside it
    s = re.sub(r'<span class="hp-w1-tiprice"><s class="hp-w1-tiwas">(&euro;[\d.,]+)</s>'
               r'&nbsp;<span class="hp-w1-tinow">&euro;[\d.,]+</span></span>',
               r'<span class="hp-w1-tiprice">\1</span>', s)
    # 6. the price reclaims the brand green now that nothing competes with it,
    #    and the two-figure rules are dead weight
    s = s.replace('.hp-w1-tiprice{display:block;font-size:17px;line-height:22px;font-weight:800;color:#191919;}',
                  '.hp-w1-tiprice{display:block;font-size:17px;line-height:22px;font-weight:800;color:#008539;}')
    s = re.sub(r'\n\.hp-w1-tiwas\{[^}]*\}\n\.hp-w1-tinow\{[^}]*\}', '', s, count=1)
    # 7. this reader has already bought, so "first order" is wrong
    s = s.replace('Start your first order', 'See what we print')
    # 8. preheader
    s = s.replace('Your 10% code is inside, and the prints most businesses start with.',
                  'The prints most businesses start with, and a team to help you spec them.')
    s = s.replace('<title>Welcome 01 proposed</title>', '<title>Welcome 01 proposed (no discount)</title>')
    return s

if __name__ == '__main__':
    src = sys.argv[1]
    out = src.replace('-proposed.html', '-proposed-nodiscount.html')
    s = open(src, encoding='utf-8').read()
    t = strip_discount(s)
    open(out, 'w', encoding='utf-8').write(t)
    left = len(re.findall(r'10%|HELLO10', t))
    print(f"wrote {out}")
    print(f"  discount references remaining: {left}")
