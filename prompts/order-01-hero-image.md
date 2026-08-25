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

## Option A — poster

> Hyper-realistic studio photograph of a single large-format printed poster leaning against a
> seamless matte charcoal wall in a professional print studio.
>
> The poster is portrait, printed on heavy uncoated matte stock with visible fine paper grain and
> a slightly soft, natural edge. Its design is minimal and premium: a deep charcoal-black
> background, hex `#191919`, carrying one line of large, confident, tightly-tracked sans-serif
> type in warm off-white, reading exactly: **Left something behind?** Nothing else is printed on
> the poster — no other words, no logo, no watermark, no border, no decorative marks, no QR code.
>
> Lighting: soft directional studio light from the upper left, raking across the paper so the
> grain and the faint relief of the ink are both visible. A soft natural shadow falls to the
> lower right. The print looks freshly made: crisp trimmed edges, no curl, no dust, no
> fingerprints.
>
> Composition: the poster occupies the lower two thirds of the frame, slightly right of centre,
> at a shallow three-quarter angle so one cut edge catches the light and the thickness of the
> stock is readable. Shallow depth of field, critically sharp on the type, falling off softly
> into the background.
>
> Background and fade: the upper third of the image must resolve to a completely flat, solid
> `#191919` — no gradient banding, no vignette, no visible objects, no light spill, nothing but
> clean empty dark. The transition from that solid dark area down into the lit scene must be
> smooth and even across the entire width of the frame, with no hotspot in the middle.
>
> Colour: neutral, very slightly cool. No orange-and-teal grade, no warm filter, no colour cast
> on the white of the paper. Photographic and physical — not a 3D render, not an illustration, no
> CGI sheen, no glow.
>
> Aspect ratio 4:3, landscape.

## Option B — card

Same as above, with the product paragraph replaced by:

> The subject is a single premium printed card, roughly A6, held upright in a simple matte black
> card stand on a dark surface. The card is printed on heavy soft-touch uncoated stock, deep
> charcoal `#191919`, with one line of tightly-tracked sans-serif type in warm off-white reading
> exactly: **We noticed you left something.** Nothing else is printed on it. The card's edge
> shows the thickness and the slightly raw texture of the cut stock. A second, identical card
> lies flat and slightly out of focus behind the stand, adding depth without competing.

---

## Two things worth deciding before generating

**1. The logo is better composited than generated.** Image models mangle wordmarks — the letters
come back nearly right, which is worse than absent. Leave it off the printed piece and I will
composite the real `helloprint-wordmark` onto the poster afterwards, in register and at the right
size, or we leave it off entirely and let the masthead above carry the brand.

**2. This bakes English into an image.** The whole rebuild exists because RFB put text in
pictures, and although this is different — the email's own headline stays live HTML text and the
picture is a visual device — a baked line still means one generation per language. Fine for the
IE and GB pilot. Ten markets means ten images, and an English poster sitting in the Dutch email
would look careless rather than clever.

If that is a problem, the fix is a product shot with no legible words at all: the same poster,
same lighting, photographed at an angle where the type reads as type but not as a sentence. It
loses the joke and keeps the craft.
