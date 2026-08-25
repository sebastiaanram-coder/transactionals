# Image prompt — Abandoned Order email 1 hero banner

For Gemini / Nano Banana. Two options, poster and card. Generate, then hand me the file and I
crop and fit it.

## What the asset has to do

Replace the foil-business-card banner, which is beautiful but says "premium business cards" to
someone whose basket contains roller banners. This one carries the message instead: a real
printed piece that says the thing the email is saying.

## Technical target

| | |
|---|---|
| Final placement | 600 px wide, about 456 px tall, full bleed at the top of the email |
| Generate at | 4:3 landscape, highest resolution available (1600×1200 or better) |
| Format back | PNG or maximum-quality JPEG, no compression artefacts |
| Ink colour | `#191919` — the email masthead is this exact value, and the seam must be invisible |
| Brand green | `#008539` |
| Top of frame | must end in flat, solid `#191919` for white HTML text to sit over |

The top third being genuinely flat matters more than anything else in the prompt. The headline
and button are real HTML text laid over that area, not part of the picture, so any texture,
vignette or banding up there shows up behind live type.

---

## Attempt 1 and what went wrong

The first generation came back as a thick rigid panel leaning against a wall on a concrete
floor, landscape, with the line centred across its full width. Four problems:

1. **It is a board, not a poster.** Visible thickness, no grain, hard machined edges. It reads as
   foamex signage — a product we sell, but not the one that says "paper".
2. **Leaning on a floor is signage behaviour.** A poster is pinned or taped flat to a wall. The
   lean is most of why it looks rigid.
3. **Landscape.** Wanted portrait.
4. **The type is centred and full-width**, which is how a sign is set, not how a poster is
   designed. A designed poster has intent and generous margins.

One fault was the prompt's rather than the model's: asking for the poster in the lower two thirds
left a lot of dead floor, and floor is the least useful thing in an image that gets cropped to a
wide band.

## The fix: let the composition make the dark space

Rather than asking for a fade painted on top of a scene, frame it so the wall above the poster
**is** the dark area. A portrait poster pinned to a dark wall, top edge about 40% down the frame,
bottom running out of shot: the upper 40% is then bare dark wall — exactly the flat area the
headline needs, present for a real photographic reason instead of painted on.

---

## Option A — portrait poster, pinned to a wall

> Hyper-realistic studio photograph of a single **portrait** printed poster pinned flat against a
> smooth, matte charcoal-black wall in a professional print studio.
>
> The poster is **thin printed paper, not a rigid board**: 170 gsm uncoated matte stock with
> visible fine paper grain, very slightly soft edges, and one corner lifting a few millimetres
> from the wall so the thinness and flexibility of the sheet are unmistakable. A barely
> perceptible natural wave runs across the surface. It is pinned or taped flat — not leaning, not
> standing, not mounted on foam board, not framed, and not resting on a floor. No floor is
> visible anywhere in the image.
>
> The poster's design is minimal and editorial: a deep charcoal-black ground, hex `#191919`,
> slightly darker than the wall behind it so its edges read clearly. One line of confident,
> tightly-tracked sans-serif type in warm off-white, **left-aligned** in the upper third of the
> sheet with a generous margin around it, reading exactly: **Left something behind?** The rest of
> the poster is intentionally empty. Nothing else is printed on it — no second line, no logo, no
> watermark, no border, no rule, no QR code.
>
> Framing: the poster is portrait and both of its vertical edges are visible, so the orientation
> is obvious. Its **top edge sits roughly 40% of the way down the frame**, and the bottom of the
> poster runs out of the bottom of the frame. The poster sits slightly right of centre.
>
> The **upper 40% of the image is bare, empty, unlit charcoal wall** — flat, smooth, even, with no
> objects, no texture detail, no vignette, no light spill and no gradient banding. Clean dark
> negative space above the poster.
>
> Lighting: a single soft directional studio light from the upper left, raking across the paper so
> the grain and the faint relief of the ink are visible, and casting a soft shadow from the
> lifting corner. The wall above falls away into darkness. Freshly printed: crisp trimmed edges,
> no dust, no fingerprints, no curl beyond the one lifted corner.
>
> Colour: neutral, very slightly cool. No orange-and-teal grade, no warm filter, no colour cast on
> the off-white ink. Photographic and physical — not a 3D render, not an illustration, no CGI
> sheen, no glow, no reflections on the paper.
>
> Aspect ratio 4:3, landscape frame containing a portrait poster. Highest resolution available.

## Option B — the card, held

> As above, but the subject is a single premium printed card, roughly A6, **held between the thumb
> and forefinger of one hand** against the same dark wall, so the scale and the flex of the stock
> are obvious. Soft-touch uncoated charcoal stock, one line of warm off-white type reading exactly:
> **We noticed you left something.** The hand is in soft focus; the card and its type are sharp.
> No wrist jewellery, no sleeve branding, no other objects. No floor visible.

Holding it solves the rigidity problem outright: a hand gives the eye a scale reference, and
nobody mistakes a held card for signage.

---

## Two things worth deciding before generating

**1. The logo is better composited than generated.** Image models mangle wordmarks — the letters
come back nearly right, which reads worse than absent. Leave it off the printed piece and I will
composite the real `helloprint-wordmark` on afterwards, in register and at the right size. Or
leave it off entirely and let the masthead above carry the brand.

**2. This bakes English into an image.** The whole rebuild exists because RFB put text in
pictures. This is different — the email's own headline stays live HTML and the picture is a visual
device — but a baked line still means one generation per language. Fine for the IE and GB pilot;
ten markets means ten images, and an English poster in the Dutch email would look careless rather
than clever.

If that is a problem, the fix is a shot with no legible words: the same poster, same lighting,
photographed at an angle where the type reads as type but not as a sentence. Loses the joke,
keeps the craft.

## Banner geometry once we have a keeper

The current banner is 600 x 456 with 126 px of ink headroom baked on. If the wall above the
poster comes back genuinely flat and dark, that headroom becomes unnecessary — I crop straight
into the wall and the flat area is real photography rather than a painted-on band. If it comes
back uneven, I bake the fade as before. Either way the seam with the masthead lands on `#191919`.
