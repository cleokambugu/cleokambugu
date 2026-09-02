# UG v1: the Virtual Stage

Version 0 (tag `ug-v0`, `site/v0.html`) proved the surface: compare, pool, rent, explore, pay.
Version 1 reorganises everything around one question: **how does a person, in a few taps, start
receiving business as a driver, or start getting moved as a rider, on the distances and places
they are comfortable with?**

The answer borrows the oldest logistics idea in Uganda and gives it a ledger.

## The trick: a stage that fills before the car exists

At a matatu stage the vehicle waits until it is full, then leaves. Everyone in Kampala already
understands that. Ride-hailing threw it away in favour of one car per request; carpool apps
(BlaBlaCar, Pool) made drivers post trips and hope. UG flips it:

1. **Riders queue money, not requests.** A rider says where, roughly when, and pays the seat
   into escrow. That is an *intent*: "Jinja, Friday, leaving 17:00 to 19:00, UGX 21,000." No car
   exists yet.
2. **Drivers declare a comfort map, not trips.** Home base, a radius, the corridors they would
   drive, the days and hours, the car. "Ntinda. 15 km around home any weekday. Kampala–Jinja
   Fridays and Sundays. Airport any night. RAV4, four seats." They never post a trip.
3. **The stage fills itself.** When enough intents line up on a corridor inside a driver's comfort
   map, UG manufactures the trip and offers it to the driver *with the money already in it*:
   "UGX 84,000 is waiting for a 17:30 Jinja run on Friday. Accept?" One tap. The riders get a
   car, a plate, and a face.
4. **Depart when full, or at the cut-off.** Every virtual stage has a fill bar and a cut-off time.
   Full early, leave early. Not full at cut-off, UG tops the car up from the empty-leg pool or
   refunds the seats. Nobody waits at a real stage in the sun.

This is demand-first, pre-paid, corridor-based pooling. Via and Swvl run fixed routes with
their own fleets; inDrive lets riders bid per trip; BlaBlaCar lets drivers post. Nothing in the
market pools *paid* demand first and then hands a full, funded car to a private driver who
only said where they are comfortable going. That is the invention, and it is the reason a
driver can be earning within minutes of signing up: the first offer can arrive before
verification is finished, and it can only be *accepted* once verification clears.

## Four mechanisms

| Mechanism | What it is | Why it matters |
| --- | --- | --- |
| **Comfort Map** | A driver's declared operating envelope: base, radius, corridors, hours, vehicle, and hard no's (no night, no boda passengers, no upcountry). Editable in one screen; drawn on the map. | Drivers get only offers they would say yes to. Acceptance rates go up; the offer feed is quiet and valuable. |
| **Virtual Stage** | A corridor-and-window bucket where paid intents accumulate: fill bar, cut-off, price per seat, who is in it (by circle). | Riders see it filling, invite friends to fill it faster (the seat price falls as the car fills), and know the departure rule. |
| **Empty Legs** | Every rental with driver, special hire and pool has a return. The return's seats go on sale at 40% the moment the outbound is booked. | Turns dead kilometres into revenue for the driver and cheap seats for riders. Nobody does this for cars in Uganda. |
| **Vouch** | A driver becomes bookable inside a circle when two members vouch; UG's document check unlocks all circles. Riders vouch for riders the same way. | Trust ladders instead of a single gate. Supply starts in the circles where trust already exists, which is also where the demand is. |

## The Handshake: sixty seconds to open for business

Three screens, no more. Every field has a default or can be skipped and completed later.

**Everyone:** phone number, one-time code, first name, a photo (optional). Role chips: *I need
rides*, *I drive*, *I have a car to rent out*, any combination.

**Drivers:** the Comfort Map screen. Tap the corridors you would drive (chips on the map),
drag the radius, pick days and hours, choose the vehicle from a list or type the plate. Snap
the plate and the permit. Done: the offer feed is live, marked "offers arrive now, accept
after verification, usually within a day".

**Riders:** home and the two places you go most, plus the circles you belong to (employer,
alumni, church, school run). Done: the Virtual Stages near you appear with fill bars.

**Car owners:** plate, class, photos, per-day price suggested from the fleet table, with driver
or self-drive, the circles allowed to book. Done: the car appears in Rent and its empty legs
are sold automatically.

## Site, app, experience, platform: one thing

- **One shell.** The web site *is* the app. A persistent bottom bar on the phone (Stage, Ride,
  Rent, Explore, Me); the same sections as a scrolling page on a desktop. Same code, same
  data, same state.
- **Installable.** A web app manifest and an "Install UG" prompt; the app icon is the Crest.
- **Continuity.** Sign in on the site, the phone shows the same stage. A QR code on the desktop
  hands the current screen to the phone.
- **One design system.** Tokens, type, glass, motion and the Crest are shared; the critics'
  panel reviews the same file the customer uses.
- **Plug-ins ride along.** Felt, Infrared City, Tazama and Cephable stay adapters on the same
  shell; a stage's departure opens a Tazama watch room; a comfort map can be exported to Felt.

## What v1 ships in the prototype

- The two doors on the hero ("I need to get somewhere" / "I drive or have a car") and the
  Handshake as an in-page wizard with simulated OTP.
- A live Virtual Stage board with fill bars, cut-offs, and seat prices that fall as cars fill.
- A driver dashboard with a Comfort Map (corridor chips, radius, hours) and an offer feed with
  offers that arrive and can be accepted or declined.
- Empty legs shown on rentals and pool trips.
- Vouch counts on driver cards.
- The v0 sections (compare, pool, rent, explore, hustle, plug-ins, partners) kept, reorganised
  under the app shell, with a bottom bar on small screens.
- A web app manifest and install prompt in the repo (the Artifact sandbox ignores them).

## What v1 does not ship

A backend. Everything is local to the browser. The stress-test report lists what the sharks
and maestros say must exist before a shilling of real money moves.
