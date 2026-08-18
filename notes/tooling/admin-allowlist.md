# Admin runbook — allowlist media & model hosts (network policy)

For the environment owner. This is host-path #3 from
[`media-and-egress.md`](media-and-egress.md): once you allow the right hosts, the
tools in [`tools/transcribe/`](../../tools/transcribe/) run end to end with no
hand-holding — fetch a video's captions or audio, and download the ASR model
automatically.

> This is a **configuration change you make in the claude.ai UI**, not something a
> session can do to itself. A running session can't widen its own network policy;
> that's the whole point of the control. Source: the official docs, fetched
> 2026-08 —
> [Configure cloud environments → Network access](https://code.claude.com/docs/en/cloud-environments#network-access).

## The four network-access levels

Every cloud environment has exactly one level (from the docs, verbatim intent):

| Level | What it allows |
|---|---|
| **None** | No outbound network through the session |
| **Trusted** (default) | Allowlisted defaults only: package registries (PyPI, npm, …), GitHub, cloud SDKs |
| **Full** | **Any** domain |
| **Custom** | Your own allowlist, optionally plus the Trusted defaults |

The current sandbox is on **Trusted** — which is exactly why PyPI works (so the
tools install) but YouTube and Hugging Face are blocked (so media and model
weights don't arrive).

## Two ways to fix it

### Option A — quickest: set the environment to **Full**

Unblocks everything (YouTube, Hugging Face, and anything else) with zero host
maintenance. The trade-off is the broadest egress surface. Fine for a personal
learning environment; think twice for anything handling sensitive code.

### Option B — tightest: **Custom** with a precise allowlist

Keeps everything locked down except the hosts you name. Recommended if you care
about egress. Use the lists below.

## Steps (either option)

1. Go to **[claude.ai/code](https://claude.ai/code)**.
2. Open the **environment selector** (the cloud button above the message box).
   Hover the environment you want to change and click the **settings gear**
   (or **Add cloud environment** for a new one). Org-shared environments are
   edited at **[claude.ai/admin-settings](https://claude.ai/admin-settings) →
   Cloud environments**.
3. In the dialog, set the **Network access** selector:
   - For Option A: choose **Full**. Done.
   - For Option B: choose **Custom**, then in **Allowed domains** enter one host
     per line (lists below). A leading `*.` matches every subdomain. Tick
     **"Also include default list of common package managers"** so PyPI/npm/etc.
     keep working (you need this — the tools install from PyPI).
4. Save. New sessions in that environment pick up the policy. (Changing allowed
   hosts also re-runs the environment's setup script on next start.)

> Note: allowlists are **per environment** — there's no org-wide list pushed to
> everyone. Edit the specific environment your sessions use (or the org default).

## Allowed-domains lists (for Option B)

### To download the ASR model (Hugging Face) — optional

```
huggingface.co
*.huggingface.co
*.hf.co
```

`faster-whisper` pulls model weights from Hugging Face via `huggingface_hub`. The
API lives on `huggingface.co` and the weight blobs come from its CDN subdomains,
so the wildcards matter. After the model is cached once, you can drop these again
and run offline via `WHISPER_MODEL_DIR`.

> **You may not need this at all.** A model can also be provisioned from
> `raw.githubusercontent.com` (already on the Trusted list) with
> `SRC=mirror tools/transcribe/provision_model.sh` — no allowlisting required.
> Allowlist Hugging Face only if you want the **official** Systran model rather
> than a community mirror (see the provenance note in `provision_model.sh`).
> Allowlisting for **media** (below) is the part that actually needs doing.

### To fetch video captions / audio from YouTube (yt-dlp)

```
*.youtube.com
youtubei.googleapis.com
*.googlevideo.com
*.ytimg.com
```

- `*.youtube.com` — the page and caption endpoints
- `youtubei.googleapis.com` — YouTube's internal API that yt-dlp calls
- `*.googlevideo.com` — the actual audio/video byte CDN (**required** for `--mode audio`; not needed for `--mode subs` if captions come from youtube.com)
- `*.ytimg.com` — thumbnails (optional)

> Streaming-CDN hostnames can shift over time. If a fetch fails on a host not
> listed here, read the failing host out of the yt-dlp error and add it — or fall
> back to Option A (**Full**). Other sites (Vimeo, podcasts, university lecture
> hosts) need their own hosts added similarly; yt-dlp supports many.

## After allowlisting — the unattended flow

```bash
pip install -r tools/transcribe/requirements.txt

# Fast path: captions only, no video, no ASR
python tools/transcribe/learn.py youtube "https://www.youtube.com/watch?v=VIDEO_ID" --mode subs
python tools/transcribe/learn.py ingest "downloads/<the>.en.vtt"

# Or: no captions available -> audio -> Whisper (model auto-downloads once HF is allowed)
python tools/transcribe/learn.py youtube "https://www.youtube.com/watch?v=VIDEO_ID" --mode audio
python tools/transcribe/learn.py transcribe "downloads/<the>.mp3"
```

## What this repo will not do

Write code to bypass a **blocked** host — tunneling, proxy-hopping, disabling TLS
verification. The egress proxy is a security control and its own README says to
report blocked hosts, not route around them. Allowlisting (above) is the correct,
supported lever, and it's yours to pull as the admin.
