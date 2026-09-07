# Product and UX critique: UG v0 and the v1 plan

## First 60 seconds

Before a price shows, the phone fetches `v0.html` (134 KB), `three.min.js` r128 (~600 KB, a blocking `<script src>`) and eleven Google Fonts weights (~250 KB): about a megabyte on a bundle. Then the page flashes: everything paints, `classList.add('js')` runs only after Three.js lands, `.js .fx{opacity:0}` hides it again, and the booking strip blurs back in at `--d:1.9s`. On a 360-px screen `#strip` sits under a 52-px `h1`, a 47-word `.lede`, `.hero-stats` and a 420-px `.stage`: the product is a screen and a half down. `#scene` has `touch-action:none` plus `setPointerCapture`, so a thumb landing on the map cannot scroll. `frame()` moves ~5,000 particles every frame and never pauses off-screen. Cut on phones: Three.js, intro delays, `filter:blur`, `backdrop-filter`, eight font weights, the `.ticker`.

## Onboarding: the Handshake as planned

Screen one asks phone, OTP, first name, photo and role chips "any combination". Ask phone and OTP only; the hero door already told you the role, and the name can wait for the first booking. The driver screen is seven tasks: corridors, radius, days, hours, vehicle, plate photo, permit photo. Sixty seconds dies at the permit upload on 4G; that is Uber's fifteen minutes relocated. Default the comfort map from GPS (here, 10 km, weekdays, one corridor) and request documents when the first funded offer arrives: "UGX 84,000 is waiting; snap the permit to accept." Riders should not give home, two places and circles; take the one trip they came for, and let circles arrive by invite link, not a list of employers. Car owners belong in Me. The real cliff is paying a seat into escrow before a car exists, which reads as a scam until the brand is known. First intent: STK push at fill time; prepay from the second.

## Information architecture

Too much. The nav lists seven links plus "Book now", and under 900 px `.nav-links{display:none}` with no menu, so a phone has no navigation at all. Hustle Mode, Plug-ins (asking a consumer for an `#plugEndpoint` and an API key) and Partners are pitch material, not customer surface. Shell: four tabs. **Ride** (strip and compare desk, with a "Today" card replacing Hustle Mode), **Stage** (virtual stages, with "Weekend" destination chips absorbing Explore; brand.md calls it a feature, not a verb), **Rent**, **Me**. A driver switch in Me flips the bar to Offers, Comfort map, Earnings, Me. **Me** holds: phone, MoMo number, wallet and top-up, receipts, saved places, circles and vouches, verification checklist, my cars, plan, language, data-saver toggle, connected apps, privacy and terms, reset.

## Copy and trust

The voice mostly lands: "Meals and rolex money", "kwanjula grade". Slips: "the arbitrage desk" is finance-bro, "Airport lounge-style waiting room" is puffery. Provenance is the right idea badly served: `provKind()` renders a 10-px `.tag.est` whose meaning lives in a `title` tooltip, and `.q-eta{display:none}` under 960 px removes it on every phone. "Best price" is awarded to a `modelled` figure, and Uber's rank rests on "Jan 2020 rates". The copy promises "trip pre-filled", but `m.uber.com/ul/?action=setPickup` carries no coordinates and Bolt's link is a city page. Checkout: `#payPhone` prefilled `0772 000 000`, "Bank of Uganda licensed PSO" printed uncited, and simulated approvals persist in `ug:trips` and bump `#walletBal`. Dark patterns to strip: Boujee `hot` beside Hustler "Current plan" disabled, a fake 184,500 wallet, `badges:['Phone verified']` granted on post, real institutions ("Stanbic circle", "Ministry of Health") as circles, and Privacy and Terms behind `data-soon` while a payment form exists.

## Accessibility and low-end devices

`prefers-reduced-motion` is respected. `role="tab"` on `.verbs` has no keyboard handling or `tabpanel`. `.pin` cards open on `mouseenter` only, and pins move every frame. Neither modal traps or returns focus; `#toast` lacks `role="status"`. `.tag`, `.badge`, `.hook`, `.pin .lbl` and `.field label` are 10–11 px uppercase mono in `--ink-3`, about 4.5:1 on `--surface`: unreadable in Kampala sun on a 720p panel. `color-mix()` fails silently on older WebViews, leaving `.glass` transparent over text. With JS off the selects are empty because `fillRouteSelects()` fills them. No `saveData` gate, and the render loop keeps the GPU warm during checkout.

## Recommendations for v2

1. Drop Three.js on phones: static SVG map; particles only for `hover:hover`, ≥960 px, `saveData` false.
2. Strip first: mobile hero is one line plus `#strip`; no intro delays, no blur.
3. Four-tab shell (Ride, Stage, Rent, Me) with a driver switch; Hustle, plans, plug-ins and partners leave the customer path.
4. Handshake is phone plus OTP; role from the door; documents at the first funded offer.
5. Provenance in words and dates, visible on mobile; "likely cheapest", never "Best price", on a modelled quote.
6. Sandbox honesty: persistent prototype banner, no prefilled identities, nothing fake persisted, no licence claims without a number.
7. Mobile hygiene: fix the scroll trap, add a menu, keyboard tabs, focus traps, 12-px minimum labels, `color-mix` fallbacks.
8. Version the `ug:` localStorage keys, add reset in Me, pause `requestAnimationFrame` off-screen.
