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

---

## Attempt 2: right material, wrong framing

Paper now, portrait, pinned, no floor. The pins sell it and the curled corner sells the
thinness. Four things to change, in order of how much they matter.

1. **The curl clips the first letter.** The lifted corner sits on top of the "L" of "Left", so
   the first character of the message is obscured. Either move the type down and right so it
   clears the curl entirely, or move the curl to the **bottom** right where nothing is printed.
   Bottom-right is better: it keeps the type clean and still shows the sheet is thin.
2. **The poster is too small and too centred.** Roughly a third of the frame width, with large
   empty wall either side. It should fill about **two thirds of the frame width**, still portrait,
   still with both vertical edges visible.
3. **It sits too high.** Its top edge is about a quarter of the way down; it needs to be nearer
   **half**, because the wall above it is the area the live headline sits over. More wall above,
   less wall to the sides.
4. **The poster and the wall are the same value.** They read as one surface with pins in it. Give
   the poster ground a touch more separation — either slightly lighter than the wall, or a faint
   rim of light along one vertical edge so the sheet reads as an object sitting in front of
   something.

Keep: the pins, the curl (relocated), the left-aligned two-line type, the matte finish, the
neutral grade, the absence of any floor.

### Deltas to paste over the Option A prompt

> The poster fills roughly two thirds of the frame width, portrait, both vertical edges visible,
> centred horizontally. Its top edge sits **half way down the frame**, and the bottom of the
> poster runs out of the bottom of the frame.
>
> The **upper half of the image is bare, empty, flat charcoal wall** with nothing in it.
>
> One corner of the sheet lifts a few millimetres away from the wall at the **bottom right**,
> where nothing is printed. The type must not be overlapped or clipped by the lifted corner.
>
> The poster ground is very slightly lighter than the wall behind it, and a faint rim of light
> runs down its left edge, so the sheet reads as a separate object in front of the wall rather
> than part of it.
>
> The type is left-aligned in the upper third of the sheet, set over two lines, with clear margin
> on all sides and no element touching it.

## If you send me the file I can test-fit this one

The wall in attempt 2 is already close to flat and dark, so I can probably extend the top with
`#191919` and make it work as it stands rather than waiting for a perfect generation. That is the
same technique used on every other banner in the programme. Send the PNG or JPEG rather than a
screenshot and I will drop it into the email and show you whether it holds.

---

## Attempt 3: switch to a landscape card

Better on three counts, and the third is the real one.

1. **The aspect agrees with the frame.** A landscape A6 card is about 1.4:1, so it sits inside a
   wide banner instead of fighting it. The portrait poster needed the frame to be taller than the
   email wants to be.
2. **One line fits without wrapping**, and a card with a single line is a finished object. A
   poster with one line at the top and two thirds of empty paper below is a void that has to be
   art-directed around.
3. **A card is addressed to one person; a poster is addressed to a room.** This email goes to
   someone who left a specific basket, and a small card left for them says that. A poster
   announces. That is the argument that decides it, not the geometry.

It also disposes of the rigidity problem for good: a small card leaning or lying on a surface is
normal behaviour, where a large sheet doing the same thing reads as signage.

## Full prompt — landscape card

> Hyper-realistic close-up studio photograph of a single premium printed postcard lying on a
> smooth matte charcoal-black surface, in a dark professional print studio.
>
> The card is **landscape A6, roughly 148 by 105 mm, printed on heavy 400 gsm uncoated soft-touch
> stock**. Its thickness is clearly visible along the near edge — a clean, crisp, freshly guillotined
> edge showing the pale core of the board against the dark printed surface. Fine paper grain is
> visible across the face. The card is deep charcoal, hex `#191919`, very slightly lighter than the
> surface it rests on so its shape reads clearly.
>
> Printed on the card, and nothing else: one line of confident, tightly-tracked sans-serif type in
> warm off-white, **left-aligned**, sitting on the vertical centre line with a generous margin on
> all four sides, reading exactly: **Left something behind?** No second line, no logo, no wordmark,
> no watermark, no border, no rule, no address lines, no stamp box, no QR code, no decorative marks
> of any kind.
>
> Composition: the camera is low and close, almost level with the surface and angled slightly down,
> so the card is seen nearly face-on with just enough perspective to read the thickness of the stock
> and the shadow it casts. The card occupies roughly **two thirds of the frame width** and sits in
> the **lower half of the frame**, centred horizontally. A second identical card lies face-down and
> partly out of frame behind it, softly out of focus, adding depth and showing the edge of the stock
> again.
>
> The **upper half of the image is empty, flat, unlit charcoal darkness** — the surface and
> background receding into shadow, with no objects, no texture detail, no vignette edges, no light
> spill, no gradient banding and no visible horizon line. Clean dark negative space.
>
> Lighting: a single soft directional studio light from the upper left, raking low across the card so
> the paper grain and the faint relief of the ink are both visible, catching the cut edge as a thin
> bright line, and casting one soft natural shadow to the lower right. Freshly printed: no dust, no
> fingerprints, no scuffs, no curl.
>
> Colour: neutral, very slightly cool. No orange-and-teal grade, no warm filter, no colour cast on
> the off-white ink. Shallow depth of field, critically sharp on the type. Photographic and
> physical — not a 3D render, not an illustration, no CGI sheen, no glow, no specular highlights on
> the paper face.
>
> Aspect ratio 4:3, landscape. Highest resolution available.

**Swapping the line** to "We noticed you left something." is a one-word edit to the prompt, but it
is four words longer and text fidelity drops off quickly past about five. Generate the short line
first and only lengthen it once the composition is right.

**The upper half being genuinely flat is still the one thing that matters most.** The live headline
and button sit over it, so texture or banding there shows up behind real type.
