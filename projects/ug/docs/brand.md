# UG brand

## Name

**UG.** Two letters, the country code, what people already type. Pronounced "you-gee". Never
"U.G." with stops, never spelled out. The four verbs follow it in this order, always with
middle dots when written on one line: **Rent · Pool · Ride · Explore.**

## Line

**Look the part. Pay the smart price.**

It names the tension the customer lives with, and takes their side. Secondary lines used in
sections: "Arrive properly." (Rent), "Share the seat, split the fuel." (Pool), "The Pearl,
priced honestly." (Explore), "For people running three lives." (Hustle Mode).

## Voice

Direct, Kampala-literate, unembarrassed about money. Uses the words people use: boda, matatu,
stage, special hire, rolex, kwanjula. Never explains those words to Ugandans. Never says
"seamless", "premium", or "experience". Prices are always shown; where they are estimates, the
provenance is on the card, not in a footnote.

## Mark

A vertical three-band tile in the flag's black, yellow, and red with the crane reduced to a
white circle ringed in red. The word UG sits beside it in the display face. The mark is the
only place the flag colours appear as a flag; everywhere else they are used as a palette.

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
- **Data: IBM Plex Mono** with tabular numerals for every price, distance, time, and tag. The
  meter look is deliberate: money in this app is always in the monospace face.

Scale: hero 44–96 px fluid, section heads 28–46 px fluid, body 16 px, card body 13–14 px,
labels 11–12 px uppercase with 0.1 em tracking.

## Motion

One orchestrated moment: the particle map of Uganda in the hero breathes, ripples, drifts with
the pointer, tilts with scroll velocity, and can be dragged. Landmark pins project from 3D to
HTML so they stay crisp and clickable. Everything else is quiet: prices roll up like a meter
when a comparison recomputes, fleet cards tilt a few degrees on hover, sections fade in from a
visible resting state. `prefers-reduced-motion` turns all of it off and leaves the map static.

## The four verbs, as UI

They live in one booking strip under the hero, as tabs. That strip is the Sixt pattern
(rent, share, ride, plus) rebuilt: the tab changes the button's verb ("Show prices", "Find a
seat", "See the fleet", "Price the weekend") and routes the same pick-up, destination, date
and time to the matching section. One form, four outcomes.
