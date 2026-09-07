# Deploying UG

UG is one repository directory (`projects/ug`) with a static site, a Node server that serves
that site and the API from one process, shared data files, and brand assets. No build step, no
npm dependencies: Node 22.13 or later with its built-in SQLite.

## Run it locally in two minutes

```
cd projects/ug/server
npm run export-data      # the site's data block → ../data/*.json (the server reads these)
npm run dev              # sandbox: OTP codes come back to the client, payments confirm without money
# open http://localhost:8787
```

`npm test` runs the ledger, stage and API tests. `npm run icons` regenerates the PNG icons from
the Crest with the bundled Chromium (set `PLAYWRIGHT_MODULE` and `CHROMIUM_PATH` if they are not
on the default paths).

## What "live" means

When the page is served by the server (or `window.UG_API_BASE` in `site/config.js` points at
one), the page detects `/api/health` and switches to **live mode**: accounts, stages, seats,
offers, bookings and Pulse come from the server and are shared by everyone using it. Without a
server the page runs its in-browser sandbox, which is what the Artifact link and GitHub Pages show.

The server itself runs in **sandbox** until `FLW_SECRET_KEY` is set: codes are returned to the
client, payments are confirmed without a processor, documents clear after a minute. With the
Flutterwave keys set it verifies every payment against Flutterwave before a seat is held, checks
the webhook hash, and refuses to hold anything it cannot verify.

## Environment

See `server/.env.example`. The important ones:

| Variable | What |
| --- | --- |
| `PORT`, `UG_DB` | port; SQLite path (mount a volume in Docker) |
| `UG_SANDBOX=1` | force sandbox even with keys |
| `UG_DEMO_SEED=1` | seed six stages and two verified drivers on an empty database |
| `UG_CORS_ORIGIN` | the site's origin in production |
| `FLW_PUBLIC_KEY`, `FLW_SECRET_KEY`, `FLW_WEBHOOK_HASH` | Flutterwave; the webhook URL to register is `/api/webhooks/flutterwave` |
| `SMS_PROVIDER` + keys | `console` (sandbox), `africastalking`, or `generic` (any gateway that takes `{to, message}`) |

## Three ways to put it on the internet

1. **Docker anywhere** (Fly, Render, Railway, a VPS). The image is built by the `UG server`
   workflow on every push to `main` and pushed to `ghcr.io/<owner>/ug`. Run it with a volume at
   `/data` and the environment above. One process, port 8787.
   ```
   docker run -p 8787:8787 -v ug-data:/data -e UG_DEMO_SEED=1 ghcr.io/cleokambugu/ug:latest
   ```
2. **GitHub Pages for the site alone.** The `UG site to GitHub Pages` workflow publishes
   `projects/ug/site` (with `brand/` and `data/`) as a static site. Enable Pages with "GitHub
   Actions" as the source in the repository settings once; every push to `main` that touches the
   site deploys. The static site runs the sandbox unless `site/config.js` sets
   `window.UG_API_BASE = 'https://your-server'` and the server's `UG_CORS_ORIGIN` allows the
   Pages origin.
3. **Both**: Pages for the site, Docker for the API, joined by `config.js`.

## Before real money

The panel's list, unchanged: settle the float question with Bank of Uganda and Flutterwave,
bind per-seat insurance, get the MoWT/TLB written position, register with the PDPO, and put the
Flutterwave inline checkout on the server-generated `tx_ref` (the server already issues one per
intent and per booking; the client sandbox pays before confirming, production must pay *with*
that reference and confirm with the transaction id). Payouts (`Flutterwave.transfer`) are wired
but not scheduled; add the T+1 hold job before enabling them.
