# Plug-ins and integrations

UG exposes a small plug-in registry (`PLUGINS` in `site/index.html`). Each plug-in is an
adapter: a name, a role, a default endpoint, a link-out, and a set of hooks that appear on
pool trips, weekend plans and the day plan once the plug-in is switched on. Endpoints and keys
are stored in the browser (`localStorage`, key `ug:plug:<id>`) until UG has accounts, and the
"Forget" button clears them.

None of the four partner sites was reachable from the build session (egress proxy), so every
adapter below is a link-out with a configurable endpoint and URL parameters, not a verified
API call. What each product does is stated from general knowledge and the user's brief, and
should be checked against the product's current documentation before wiring phase 1.

| Plug-in | Role in UG | Default endpoint | Hooks | What phase 1 must wire |
| --- | --- | --- | --- | --- |
| **Felt** (felt.com) | Maps. A pool trip or weekend plan becomes a shared web map: route, stops, fuel and toll markers, the lodge. | `https://felt.com/` | "Map on Felt" on every trip; "Map the weekend" on the itinerary. | Felt's API to create a map and add layers/pins from UG's route data; a share link back into the trip chat. |
| **Infrared City** (platform.infrared.city/workflows) | Workflows. Run an urban-climate workflow (heat, wind, shade) along the route by hour so legs move out of the worst sun. | `https://platform.infrared.city/workflows` | "Route comfort" on the itinerary; "Check the day's heat" in Hustle Mode. | The workflow API: submit the route geometry and departure times, read back comfort scores per leg, re-order the day. |
| **Tazama** (the user's own product; Live per the profile README) | Entertainment. The road-trip playlist and a watch room for the back seats, sized to the trip's length. | `http://127.0.0.1:5178` (local dev build), production `https://tazama-watch.xulaye.chatgpt.site/` | "Tazama playlist" on every trip with the trip's minutes; "Watch room for the drive" on the itinerary. | UG passes `?source=ug&trip=…&minutes=…`; Tazama should read those and open a room. Rights and source rules stay Tazama's. |
| **Cephable** (cephable.com/downloads) | Automation and hands-free control. Voice, face and switch input for UG, plus automations that act on the user's behalf. | `https://cephable.com/downloads/` | "Hands-free today" in Hustle Mode; "Automate Friday seat". | Cephable's device/SDK integration for input; UG-side automation rules ("take my Friday seat when it opens", "top up under UGX 20,000") run on UG's backend and are only triggered through Cephable. |

## Lit up in v1

The cards became features. Each is honest about what runs here and what the partner adds.

| Plug-in | What runs in the prototype | What the partner adds when connected |
| --- | --- | --- |
| **Tazama** | The **dock**: an in-transit entertainment system in the corner of every screen, the New York cab screen done properly. The first tap on the site starts the drive: a generative mix synthesised in the browser (WebAudio, 96 bpm, warm chords) with a live visualiser, and a **UG Bulletin** that rotates fuel, tolls, permits and the stages filling now. Pause, next mix, and the dock stays out of the way. | Tazama's catalogue and watch rooms replace the sandbox mix; an accepted offer opens a watch room sized to the trip. |
| **Pulse** (UG's own, exported to **Felt**) | UG reads paid seats per town against drivers' comfort maps and ranks hotspots: for a driver, where funded demand exceeds cars; for a rider, which stages leave first. **Point me there** rotates the 3D map to the town and opens its card; the map carries a breathing heat layer (yellow for demand, red for a gap). | **Export Pulse layer** copies the layer as GeoJSON (points per town with demand, drivers near, seats open, gap; corridor lines with stage fill and seat price) for a Felt map, so the demand map is a shared, live, collaborative layer rather than a Google Maps pin. |
| **Cephable** | **Hands-free**: the mic button in the nav and in Me listens through the browser's speech engine. Commands: "compare Ntinda to Downtown Kampala", "take a seat to Jinja", "my offers", "where is the demand", "night mode", "start the music", "next mix", "help". Replies are spoken back. | Cephable's face, head and switch controls for people who cannot use a touchscreen, and automations that act on rules ("take my Friday seat when it opens"). |
| **Clarifom** | **Say what happened**: spoken or typed feedback after a trip, with tags, logged on the device. Also the voice behind commands. | Routing of feedback into tickets and ratings. Vendor named in the brief; not verified online. |
| **Infrared City** | A comfort hint on every stage card by departure hour (a modelled sun index: hot leg, cool departure, night with a lit pickup). | The workflow replaces the model: heat, wind and shade along the corridor by hour. |

## Rules

- A plug-in is off by default. Nothing about a trip leaves UG until the user switches the
  plug-in on, and the card says so.
- Keys are optional and are only sent to the configured endpoint if that endpoint is an API,
  never to the link-out page.
- Hooks are links with URL context; they never fire on their own.
- A plug-in that is on and whose endpoint is unreachable shows "Connected" in this prototype
  because it does not probe the endpoint. Phase 1 should add a health check and show
  "unreachable" honestly.

## Adding a plug-in

Add an entry to `PLUGINS` with `id`, `name`, `role`, `colour`, `url`, `endpoint`, `blurb`,
`hooks` (labels), `mark` (a 40×40 SVG), and `open(ctx)` (builds the outbound URL from trip
context). Then call `hookLink(id, label, ctx)` wherever the hook should appear.
