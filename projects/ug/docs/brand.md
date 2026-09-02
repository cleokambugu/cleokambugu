# UG brand

## Name

**UG.** Two letters, the country code, what people already type. Pronounced "you-gee". Never
"U.G." with stops, never spelled out.

## Catchphrase

**Ride. Pool. Rent. Deliver.**

Four verbs, four full stops, always in this order: the daily habit first (Ride), the social
saving second (Pool), the aspiration third (Rent), and the parcel last (Deliver), because the
flip side of a ride is a thing that needs to move. Written with full stops as a line and with
middle dots when it runs inline. It sits beside the logo in the nav and is the hero headline.

**The flip.** Every verb has a demand-side reading that the hero shows beneath the highlighted
word: Find a ride. Share the ride. Rent the ride. Send the thing. The verbs are what UG does;
the flip is what the customer came for.

Explore is a section and a feature, not part of the catchphrase; when it is listed, it comes
after: "Ride. Pool. Rent. Deliver. Explore the weekend."

## Positioning line

**Look the part. Pay the smart price.**

The line under the catchphrase. It names the tension the customer lives with, and takes their
side. Secondary lines used in
sections: "Arrive properly." (Rent), "Share the seat, split the fuel." (Pool), "The Pearl,
priced honestly." (Explore), "For people running three lives." (Hustle Mode).

## Voice

Direct, Kampala-literate, unembarrassed about money. Uses the words people use: boda, matatu,
stage, special hire, rolex, kwanjula. Never explains those words to Ugandans. Never says
"seamless", "premium", or "experience". Prices are always shown; where they are estimates, the
provenance is on the card, not in a footnote.

## Mark: the Crest

Three feathers rising from a pearl. Files in [`brand/`](../brand/): `crest.svg` (the mark),
`wordmark.svg` (crest + UG + catchphrase), `app-icon.svg` (dark tile for the phone).

Why a crest:

- **It is the crested crane's crest**, the bird on the flag, redrawn as three strokes in the
  flag's black, yellow and red. Nobody in Uganda needs it explained.
- **Three feathers are the three moving verbs.** Ride, Pool, Rent, in that order, left to
  right. The middle feather is the tallest and yellow: Pool is the one UG owns. **The pearl
  is Deliver**: the thing that travels, the parcel in the boot. Four verbs, one mark.
- **A crest is what old money has.** The customer wants to look the part; UG hands them a
  crest to wear. The joke is gentle and the customer is in on it.
- **The pearl** is the Pearl of Africa, and a wheel, and a coin. It sits where the feathers
  meet, so the mark reads as movement fanning out from one point on the map.

Construction: a 64-unit square; three round-capped strokes of 7.5 units from the pearl at
(32, 48); the outer feathers curve out to (12.5, 17) and (51.5, 17), the middle rises to
(32, 8.5). The first feather and the pearl take `currentColor`, so the mark holds on any
ground: cream on night, ink on noon, and the yellow and red never change. Minimum size 20 px;
below that use the pearl alone.

The wordmark sets UG in Unbounded 900 beside the crest; the catchphrase in IBM Plex Mono
follows at 70% ink. The app icon puts the crest on a near-black tile with a faint diagonal
sheen and UG beneath, so it sits comfortably beside the other apps it compares.

Partner marks on the compare screen are UG's own stylised renderings: each operator's name and
colour drawn in one consistent hand (a helmet for SafeBoda, a horse for Faras, since faras
means horse). They are placeholders for the operators' official logo files, which production
must use under each partner's brand guidelines.

## Palette

Dark-first because the reference (the Antigravity landing page) and the use case (a phone at
night outside a function) both are. A full light theme exists and is the OS-follows default in
daylight.

| Token | Night | Noon | Role |
| --- | --- | --- | --- |
| ground | `#0F0C0A` | `#F3EEE3` | page; warm near-black, murram-dust paper |
| surface | `#1E1915` | `#FFFDF8` | cards and panels |
| ink | `#F4ECDD` | `#17120E` | text |
| yellow | `#F2C200` | `#E0B300` | the accent: best price, primary action, active tab |
| red | `#D2202F` | `#B8161F` | UG's own products on a list, landmark nodes, alerts |
| crane | `#94A8B6` | `#4E6B7C` | the lake, secondary badges, circles |

Semantic colours (good `#3DBB7A`, warn `#F2A900`, bad `#E5484D`) are separate from the accent.

## Type

- **Display: Unbounded** (900 for the headline, 700 for section heads, 500 for card titles). A
  wide, geometric face that reads like a number plate from across a car park.
- **Body: Albert Sans.** Quiet, humanist, works at 13 px on a price card.
- **Data: IBM Plex Mono** with tabular numerals for every price, distance and time. The meter
  look is deliberate: money in this app is always in the monospace face.
- **Labels are Albert Sans**, semibold, 11–13 px: eyebrows, chips, badges, map labels, the tab
  bar, the footer headings. v0 set these in uppercase mono and they read as retro; v1 moved every
  label to the body face so only figures carry the meter look. Map labels are glass pills in
  the body face, bolder for the big towns, muted for parks.

Scale: hero 44–96 px fluid, section heads 28–46 px fluid, body 16 px, card body 13–14 px,
labels 11–12 px uppercase with 0.1 em tracking.

## Glass

Glass is used only where a surface floats over something: the nav over the page, the booking
strip over the tail of the particle map, the landmark card over the map, the checkout sheet
over the page, the wallet. It is one token class: 64% surface over a blur, a hairline border
at 14% ink, a one-pixel inner highlight. Panels that sit in the page flow stay solid, so text
never fights a background.

## Motion

Choreography on load, once, in the manner of a product launch page: each verb rises out of a
blur one after another (0.2 s, 0.5 s, 0.8 s; 1.15 s each on an expo-out curve), a single light
sweep crosses the letters, the positioning line and buttons follow, the map dollies in from a
tilted pose while the landmark pins pop in sequence. After the intro the yellow highlight moves
Ride → Pool → Rent every 3.8 s; hovering a word holds it. The nav tagline echoes the headline
only once the headline has scrolled away. Sections pick up the same easing when they reveal.

One orchestrated moment: the particle map of Uganda in the hero breathes, ripples, drifts with
the pointer, tilts with scroll velocity, and can be dragged. Landmark pins project from 3D to
HTML so they stay crisp and clickable. Everything else is quiet: prices roll up like a meter
when a comparison recomputes, fleet cards tilt a few degrees on hover, sections fade in from a
visible resting state. `prefers-reduced-motion` turns all of it off and leaves the map static.

## The opening

The app and the site open the same way, once per session, three and a half seconds, skippable,
off under reduced motion: Uganda assembles from scattered particles (land in cream and yellow,
lakes in crane), fourteen vehicles dash the corridors from Kampala to the towns and back with
lit trails in the flag colours, U flies in from the left and G from the right and lock with a
flash of yellow, then Ride. Pool. Rent. Deliver. appear beneath. The hero is already running
underneath when the overlay dissolves, so the map the opening drew is the map you land on.

## Staying on UG

A partner's name and colour appear on a quote, and the primary action is always "Book on UG":
the trip rail in the nav shows placed, driver and plate, arriving, on trip, done. The partner
link is a quiet secondary. The product rule: nobody is sent away to finish what they started.

## The verbs, as UI

Ride, Pool, Rent, Deliver and Explore live in one booking strip under the hero, as tabs in that order.
That strip is the Sixt pattern (rent, share, ride, plus) rebuilt: the tab changes the button's verb ("Show prices", "Find a
seat", "See the fleet", "Price the weekend") and routes the same pick-up, destination, date
and time to the matching section. One form, four outcomes.
