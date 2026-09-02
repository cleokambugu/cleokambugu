# Mobility market notes

Study notes gathered while designing UG (`projects/ug/`). Written 2 September 2026 from a
Claude Code web session on the Trusted network policy.

| Note | What it covers |
| --- | --- |
| [`competitors.md`](competitors.md) | Sixt (rent · share · ride · plus), Pool (poolapp.io), SafariShare, Tinka, the Antigravity landing page, Flutterwave's inline checkout. |
| [`uganda-fares.md`](uganda-fares.md) | Everything found on Kampala and intercity fares, commissions, tolls, park fees, rental rates, and the middle-class income band, with dates. |

## Provenance, stated plainly

**Read first-hand (cloned from GitHub and read):**

- `Emmancipated/antigravity-landingpage-clone` — the Three.js hooks and hero component.
- `Flutterwave/React-v3` — `src/types.ts` (the full checkout config contract) and
  `src/script.ts` (the script URL `https://checkout.flutterwave.com/v3.js`).
- `mrdoob/three.js` at tag r128 — `build/three.min.js`, used to test the hero offline.

**Secondhand (WebSearch snippets only; the pages themselves were blocked by the egress proxy):**

- sixt.com, poolapp.io, safarishare.com, tinkataxi.com, developer.flutterwave.com,
  monitor.co.ug, dignited.com, uber.com/ug blog, kee.go.ug, every UWA tariff summary, every
  car-rental price page, the KAS and EPRC middle-class figures.

Anything in these notes that came from a snippet is tagged *(snippet)*. A snippet is a search
engine's summary of a page; it can be stale, truncated, or wrong, and several of the fare
snippets contradict each other (see `uganda-fares.md`). Nothing tagged *(snippet)* should be
quoted as fact without opening the page from a session that can reach it.
