# Versions

| Version | Where | What it is |
| --- | --- | --- |
| **v0** | git tag `ug-v0` · `site/v0.html` · [artifact](https://claude.ai/code/artifact/511855d0-486a-477c-8400-ff36d05e5494) | The first surface: compare desk, pool board, per-head rentals, weekend planner, Hustle Mode, plug-ins, Flutterwave sandbox, the Crest, the particle map. Frozen. |
| **v1** | `site/index.html` (current) · [artifact](https://claude.ai/code/artifact/e8a24b54-8907-4526-87c0-e8e170eb7907) | The app shell and the Virtual Stage: two doors, the sixty-second Handshake, paid intents that fill a stage, a driver's Comfort Map and funded-offer feed, empty legs, Me, a bottom tab bar, a manifest, and the panel's quick wins folded in. Twenty-three towns on the map, local apps recognised per town. v1.1 adds Deliver as the fourth verb with the flip line; Book on UG with the trip rail so nobody leaves the site; the Atlas of every way to move (air, bus, water, rail, Signature cars, stays) with truthful states, and those modes in the compare desk; buses on the corridor and agent accounts learned from SafariShare; the Install section with a QR code; and the opening animation. |
| **v1.2** | `server/` + `site/` (current) | **Real.** A Node backend with SQLite: OTP accounts, stages, intents, offers, a double-entry ledger, bookings, Pulse, Flutterwave verify and webhooks, tests, Docker, GitHub Actions for the image and for Pages. The site detects the API and goes live; the sandbox remains the fallback. PWA with a service worker and icons. Kisoro and every major park on the map with the GTA-style terrain labels. v1.3 adds **teleport** (hover or tap a town and every desk moves there), **six languages** with honest confidence, and **Foresight**: seasonal produce, venue rhythms and events forecast a week ahead by place and vehicle class, drivers promise to be there, the gap is visible, amber rings on the map, produce hauling in Deliver, and the same forecast from the server. |
| **v2** | planned | The backend and the licence: ledger, webhooks, regulatory gate, two launch corridors, the mobile diet, four-tab shell. See `roadmap.md` and `stress-test.md`. |

Rules: a version is frozen by tag and copy before the next begins. The artifact link for v0
stays as it was; v1 has its own. The brand, tokens and the Crest are shared across versions so
the site, the app and the platform read as one thing.
