# Category emails: photographic header, and a break in the middle

Built and render-verified for **Commercial Print** only, as agreed. The other four
are untouched apart from picking up the new grid heading.

Preview: `proposals/category-commercial-print-proposed.html`.

The header shape and the headline are both settled — photograph to the top, and
"What are you promoting next?". The five headline options are kept below as a
record of what was considered.

---

## 1. What changed

**A photograph in the header, fading into the ink at both ends.** The wordmark
sits on black, the photograph opens out of that black, and the headline, subtext
and first call to action sit on black underneath it. Three stacked blocks of the
same `#191919`, with a picture apparently embedded in them.

**The fade is baked into the JPEG, not written in CSS.** This matters more than it
sounds. Outlook ignores CSS gradients, so a fade written in CSS is a
hard-edged photograph pasted on a black box for a large slice of the audience.
Instead the image file itself ramps to exactly `#191919` at its first and last
row, so it butts against the blocks above and below with no seam in *every*
client — Outlook included. `scripts/make_newstyle_assets.py` generates it and
fails the build if either end drifts more than 3/255 from the ink, because a
one-off band across a header is exactly the kind of thing nobody notices until
it has been sent.

**A break band between the prose and the tiles.** This is the join you flagged.
The email used to run two paragraphs of prose straight into a grid of pictures,
which read as one long column that changed shape halfway down for no reason. Now
there is a full-bleed band of the same ink as the header, and the email becomes
two halves with separate jobs: read this, then browse this.

**The band carries the customer review**, not product advice. A stranger vouching
for us earns the most prominent spot in the email; a note about artwork does not.
The review is set on the ink with the Trustpilot stars above it, the quote at
20px in white, a short Trustpilot-green keyline, and the name underneath — the
keyline is there because with both simply centred the attribution read as part of
the sentence.

**And *One design, several products* moved to the bottom, on white**, above the
contact block with a hairline over it. It reads as a footnote to the browsing
rather than an interruption of it, which is what it always was.

Nothing was added: the review used to sit below the tiles and the advice used to
sit in the band. They swapped.

**A centred heading before the tiles.** *More in Commercial Print* — "Four more of
the range, in the quantities businesses actually reorder." Everything from the
band down is centred, everything above it is left-aligned prose, so the two halves
look as different as they behave.

**Five of the six pictures are now the new photography.** Both feature rows and
three of the four grid tiles.

---

## 2. The fourth tile: Roller Banners instead of Cards & Invitations

Cards & Invitations had no shot in the set, so it was keeping a yellow packshot on
white beside three art-directed photographs — the worst-looking tile in the email
precisely *because* the other five improved. It is now **Roller Banners**, which
the photography does cover.

What that costs, stated plainly: Cards & Invitations ranks fourth in this category
at **261k** of gross profit and Roller Banners is **175k**, and Roller Banners
belongs to Signage & Outdoor rather than here. So this is 86k of ranking traded
for an email that can go live now and looks like one thing.

It reads straight, at least. Everything else in this email is print that
advertises something, and so is a roller banner.

**Put Cards & Invitations back the moment there is a shot of one.** The
end-of-year case for it has not gone away, and it is the highest-margin PLP in
Commercial Print at 43.2%.

Roller Banners now appears in two emails — here and in Signage & Outdoor. Two
different segments, so no reader sees it twice.

---

## 2a. Where the header and the buttons go

They were wrong. All three — the header photograph, the button in the header and
the button at the bottom — went to `url_of(feature[0])`, the first feature tile.
So every reader of this email was sent to **Booklets**, whatever they had ordered,
from an email whose whole job is to invite a browse.

They now go to the category page, per locale:

| | |
|---|---|
| en-IE / en-GB | `/promotional-printing` |
| nl-NL / nl-BE | `/reclame-drukwerk` |
| fr-FR / fr-BE | `/impression-support-marketing` |
| es-ES | `/impresion-promocional` |
| it-IT | `/stampa-promozionale` |

Contentful entry `MRjlkRa7meqiqSY0mSowg`, whose English `searchName` is
*Promotional Products*. It is keyed by entry id rather than by name in
`scripts/fetch_subcategories.py`, because the name is localised and matching on
"Promotional Products" would find nothing in Dutch. All 176 URLs in the snapshot,
this one included, were requested and returned 200.

The tile and feature links are untouched. Those are meant to be specific.

**The other four emails still have this bug** and now say so out loud: the build
prints a `TO DO` line per email naming the tile it currently points at — Banners,
Labels & Stickers, T-shirts, Canvas Tote Bags. Each needs its own category page
before it goes live. If you give me the four URLs I will wire them in one pass.

---

## 2b. Two things the swap uncovered

**The stars picture contradicted the words under it.** The block showed the 4.5
company TrustScore above a line reading *"Beth · 5 out of 5 on Trustpilot"* —
which is that review's own rating. A review card has to show the review's stars,
so it is five now, and the build fails if any selected review is not five stars,
or if the picture and the claim ever drift apart again.

**Trustpilot's stars ship on white.** Dropped onto the ink band they would have
arrived in a white box. The ink version is derived rather than hand-made: a flood
fill inward from the border repaints the gutters and margins and cannot reach the
white stars *inside* the green squares, which is what a blanket white-to-ink
replace would have erased. The build reports what share it repainted (19%) and
fails outside 8–40%, so a future artwork that has no light surround, or one where
the fill leaks into the squares, stops the build rather than shipping.

---

## 3a. The header: photograph to the top — decided

The photograph runs to the very top of the card, carrying the card's own 18px
corners, with the wordmark under it above the eyebrow. The picture speaks before
the brand does.

The alternative — wordmark on ink, then the photograph opening out of that ink and
closing back into it at both ends — was built, compared side by side and rejected.
It has been removed rather than left in the repo: one header, one asset, one code
path, and every check on it reachable.

Three things that came out of building both, worth keeping on the record:

**The fade is baked into the pixels, not written in CSS.** Outlook ignores CSS
gradients, so a fade in CSS is a hard-edged photograph for a large part of the
audience. The image ends in exactly `#191919`, and the build fails if the last row
drifts more than 3/255 from it — or if the *first* row has faded, because there is
nothing above it to blend into and a fade there is a grey wash across the top of
the email.

**The crop had to change with the fade.** The rejected shape wanted its window
pushed 210px down the source, so its bottom fade landed on empty velvet and
whatever the top edge cut through was hidden anyway. Without a top fade that same
window sliced the headline off the flyer behind, so this one starts at 0 and keeps
the whole stack in frame.

**Outlook squares the top corners.** It ignores `border-radius` entirely. That is
already true of the white card itself, so the email stays consistent with itself
there rather than gaining a mismatch.

**One trade, accepted:** with images off, the top of the email is blank until the
wordmark, because the wordmark now sits under the photograph.

---

## 3. Headline: five options

The first version opened *"Running low, or starting the next one?"*, which you were
right to reject. That is a stationery question — it fits somebody whose
letterheads are down to the last box. Everything in this email is print that
advertises something: a campaign, an event, a launch. Nobody runs low on posters.

Option 1 is built and in the preview. Any of the five is a one-line swap.

### 1. Ask what is next — **chosen**
> **PROMOTIONAL PRINT**
> **What are you promoting next?**
> Whatever it is, this is the print that puts it in front of people, and what tends
> to go with what.

Works whatever the occasion, and makes no assumption about whether the last
campaign has run yet. The reason I would ship this one: it is the only option that
cannot be wrong about the reader's situation.

### 2. Reuse the artwork you already have
> **ONE DESIGN, MORE PLACES**
> **You have the design. Put it somewhere else.**
> The artwork from your last job can run as a flyer, a poster, a folded leaflet or
> a banner. Send it once and we will fit it to each size.

The most useful of the five, and the most concrete — it removes the actual reason
people do not order a second format. Catch: the band in the middle of the email
already makes this exact point, so picking this means writing the band again.

### 3. Occasion-led
> **PROMOTIONAL PRINT**
> **Got something coming up?**
> An event, an opening, a new price list. Here is the print that tells people
> about it, in the quantities and timings that fit.

Warmest of the five and the most conversational. Slightly the vaguest.

### 4. Format-led
> **SIX WAYS TO SAY IT**
> **Six ways to advertise the same thing**
> A thousand flyers, a poster in the window, a banner behind the stand. One
> message, several places people will meet it.

Makes the range itself the idea, which suits an email that is six tiles. Catch:
the number is load-bearing. If the tile count ever changes the headline lies, so
this one needs a build check that six things are actually shown.

### 5. Momentum
> **PROMOTIONAL PRINT**
> **The last one is out there. What is next?**
> The print businesses come back for when they have something new to advertise,
> and what tends to go well together.

Refers back to their order, which is flattering and specific. Catch: at day 32 the
campaign may not have run yet, and telling somebody their flyers are "out there"
when the box is still unopened reads badly.

### The lines underneath, which also had to change

Two supporting lines were doing the same replenishment thing, and are in the
preview as:

| | Was | Now |
|---|---|---|
| above the feature rows | Popular in Commercial Print / Among the most ordered in this category | **Where most campaigns start** / The two formats businesses order most when they have something to advertise |
| above the grid | More in Commercial Print / in the quantities businesses actually reorder | **More ways to advertise it** / Four more formats, in the quantities businesses actually order |

*Commercial Print* is our own taxonomy word, not a phrase a customer would use, so
it is gone from what the reader sees. The eyebrow says **PROMOTIONAL PRINT**.

---

## 3. Coverage across all five emails

Worth knowing before we do the other four, because it is thinner than Commercial
Print suggests. 21 subcategory tiles across the five emails; the set covers 9.

| Email | Covered | Missing |
|---|---|---|
| **Commercial Print** | **6 of 6** | — (after the Roller Banners swap) |
| **Signage & Outdoor** | 3 of 4 | Beach Flags |
| Labels & Packaging | **0 of 4** | Labels & Stickers, Paper Bags, Labels On Roll, Printed Food Packaging |
| Clothing & Textiles | **0 of 4** | T-shirts, Polo Shirts, Interior Textiles, Caps |
| Corporate Gifts | **0 of 4** | Canvas Tote Bags, Pens, Notebooks, Water Bottles |

Headers are the same story: Commercial Print has a hero, Signage & Outdoor can
have one, and the other three have nothing dark enough to fade.

So the honest sequence is **Commercial Print now, Signage & Outdoor next**, and the
remaining three stay as they are until there is photography for them. Shipping a
half-photographed email is worse than shipping a consistent unphotographed one —
that is the Cards & Invitations problem repeated four tiles at a time.

**If one more batch gets shot, the thirteen above are the list** — the twelve
below plus a greeting card, which buys Cards & Invitations its place back, in that order of
value.

---

## 4. Weight

Seven photographs, 364 KB in total:

| | | |
|---|---|---|
| header | 900 × 630 | 106 KB |
| 2 feature rows | 504 × 378 | 33 KB each |
| 4 grid tiles | 400 × 400 | 33 – 62 KB |

About 1.5× the display size. 2× was indistinguishable in the client and cost
twice the bytes. There is a budget enforced in the build so this cannot creep upward one
photograph at a time. It was 320 KB for six photographs and is 370 KB for seven —
raised by the size of one tile, deliberately, which is the point of having it.

The HTML itself is 33 KB, well inside Gmail's 102 KB clipping threshold. The
photographs do not count toward that.

---

## 5. Two things to decide

1. **Where the photographs are hosted.** They currently point at the published
   copy of this repo, which works today and makes the Klaviyo template render the
   moment it is pasted. That is fine for review and **not** fine for sending — a
   live send should not depend on GitHub Pages. They need to move into Klaviyo's
   asset library before the flow is switched on.
2. **Whether the header photograph should be clickable.** It is, currently, and it
   goes to the same place as the button under it. Easy to remove if a photograph
   that navigates feels wrong.

---

## 6. Still open from before, unchanged by this

- **The review block must be excluded from Smart Translations.** A translation pass
  would put words a named customer never said into their mouth. This is the one
  thing blocking a send.
- The `/en-ie/` home and help-centre links are not yet market-aware. Category
  links already are.
