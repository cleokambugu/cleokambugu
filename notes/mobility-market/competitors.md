# Competitor and reference review

## Sixt (sixt.com) — *(snippet)*; the site itself was blocked

What the search results establish:

- Sixt SE is a mobility group with four product lines sold as verbs: **rent** (car rental),
  **share** (car-sharing with no fixed drop-off, Germany and the Netherlands), **ride**
  (ride-hailing, taxi and limousine worldwide), and **plus** (a car subscription at a fixed
  monthly price). The app store listing is literally titled "SIXT rent. share. ride. plus."
- One app and one account manage all four; users can pick a specific car before the rental and
  unlock it from the app.
- A loyalty layer, SIXT ONE, with member rates, points, and skip-the-counter. A promotion in
  August 2026 offered double status points.
- Bookings can be changed (dates, times, location) up to the start of the rental.

What could not be verified: the homepage layout, the booking widget's exact fields, colours.
Sixt's long-standing orange-and-black identity is general knowledge, not observed here.

**Transferable lesson used in UG:** sell verbs, not categories; one form feeds all of them;
show the change-anytime promise in the booking strip; add a membership tier that changes the
price rather than only adding perks.

## Pool (poolapp.io) — *(snippet)*; blocked

The Pool Carpool site describes "a social ridesharing app" that began as an effort to improve
inter-city transport in the Kitchener–Waterloo region:

- accounts verified by phone number;
- search trips by source and destination; drivers post offers, riders search and filter;
- a trip details screen for managing a trip;
- a built-in two-way rating system and a trip chat;
- pitched as replacing scrolling through Facebook carpool groups;
- iOS and Android.

Nothing was found on how Pool sets or splits the fare. The neighbouring apps in the results
(POOLit: "pay what you want" and gender filters for professionals; Pooly: "no fares, no
strangers"; Pool Ride: route-based smart matching) show the field's spread from social to
transactional.

**Transferable lesson used in UG:** phone verification, trip chat, two-way ratings, and
"circles" (the social layer that replaces the WhatsApp group). UG adds what Pool does not
show: a published cost-split formula, so the seat price is arithmetic rather than a
negotiation.

## SafariShare (safarishare.com) — *(snippet)*; blocked

A Ugandan site that compares and books bus tickets and shared rides across operators and
lets a user reserve a seat days ahead. Closest local analogue to UG Pool's intercity
inventory; a natural partner or acquisition rather than a rival.

## Tinka (tinkataxi.com) — *(snippet)*; blocked

A Kampala ride app that markets itself as the cheapest and publishes "vs" pages against Bolt,
Uber, and Yango. Claims from those pages: fares rounded down to the nearest UGX 500, first
500 m free, operating in Kampala, Wakiso, Entebbe, Mukono, Jinja and Mbarara, "10,000+ monthly
riders" on its press page. Its comparison pages are marketing; the numbers on them were not
seen.

## Faras, SafeBoda, Uber, Bolt, Yango — *(snippet)*

See `uganda-fares.md`. Faras (Kenya, Tanzania, Uganda, Ethiopia, Sudan) charges drivers 10%
and offers boda and car hire with a wallet, live tracking and in-app SOS. SafeBoda charges
around 15%. Bolt 15–20%. Kampala's Lord Mayor has said all bodas should operate under digital
platforms; researchers at The Conversation report drivers under pressure to speed and gaining
little formal protection from platform work.

## The Antigravity landing page — *read first-hand from a public clone*

`Emmancipated/antigravity-landingpage-clone` (Vite, React 19, Three r0.181,
@react-three/fiber). What it actually does:

- `src/hooks/useThreeScene.ts`: a plain Three.js scene, perspective camera at z=50, a
  transparent antialiased renderer with `setPixelRatio(min(dpr, 2))`, resize handling, and
  cleanup. Nothing exotic.
- A large commented-out component, `OrbitalRingLast`, holds the interesting recipe: an
  `InstancedMesh` of small planes with a canvas-drawn soft texture and additive blending,
  distributed in an annulus; per-particle phase and speed; a global "breath" scale; a ripple
  wave by distance from centre; each particle drifting on sine curves; the whole group
  lerping toward the unprojected pointer position with a velocity "trail" term; a slow
  rotation and tilt.
- `src/hooks/useScrollInertia.ts`: adds `scrollSpeed × 0.25` to a y-offset on scroll, decays
  it by 10% per frame, and applies it as a translateY so content overshoots and settles.
- The hero is white 96–144 px text over the particle field, with pill buttons and a bouncing
  scroll cue.

Search results describe Google Antigravity itself as an agentic IDE from Google (Gemini 3)
whose landing page has the floating, pointer-reactive 3D look; nothing from Google was fetched.

**Transferable lesson used in UG:** particles with a canvas sprite, per-particle phase, breath
and ripple; pointer drift and scroll inertia applied to a group's rotation; a UMD Three build
(r128 is the last on cdnjs) so a single HTML file needs no bundler. UG swaps the abstract
ring for a point-in-polygon fill of Uganda's outline, so the effect carries information
(landmarks, the lake) rather than only mood.

## Flutterwave inline checkout — *read first-hand from the official SDK*

`Flutterwave/React-v3`, `src/types.ts`: the `FlutterWaveProps` contract (public_key, tx_ref,
amount, currency, payment_options, redirect_url, customer {email, phone_number, name},
customizations {title, description, logo}, meta, subaccounts, callback, onclose) and the
`FlutterWaveResponse` shape (amount, currency, customer, tx_ref, flw_ref, status,
transaction_id). `src/script.ts` pins the script at `https://checkout.flutterwave.com/v3.js`.

From snippets only: Uganda mobile money supports MTN and Airtel in UGX; the payment option
key is `mobilemoneyuganda`; Flutterwave received a Bank of Uganda PSO licence in 2024.
