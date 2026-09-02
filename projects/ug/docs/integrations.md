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
