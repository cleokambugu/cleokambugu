# Merging the two builds

Two builds were put side by side: the current one (the virtual stage) and the earlier one. The ask
was to merge them into one better thing. This is what that turned out to mean, and — more usefully —
what it turned out not to mean.

## What the diff actually said

Rather than read 1,464 lines against 4,800 by eye, the two files were compared structurally:
keyframes, CSS classes, element ids, and top-level function names.

```
keyframes present only in the earlier build   0
CSS classes present only in the earlier build 0
functions present only in the earlier build   1   initTheme
element ids present only in the earlier build 4   partners, plugins, statProviders, ticker
```

So the current build is very nearly a superset, and three of those four ids were false alarms:

| earlier id | what happened |
|---|---|
| `partners` | renamed `partnerList` — `renderPartners()` fills it |
| `plugins` | renamed `plugs` — `renderPlugins()` fills it |
| `initTheme` | deliberately replaced by `initDay()`, see [`day.md`](day.md) |
| `statProviders` | the hero stats block it lived in was replaced by the two doors |
| **`ticker`** | **lost** |

## The one real regression

`renderTicker()` was still in the file. Forty lines of `.ticker` CSS were still in the file. The
element they write to was not — it had gone in a markup edit, and nothing said so. The function was
never called from the boot drain, and if it had been it would have thrown on a null.

That is a whole feature that vanished silently, and it is exactly the class of loss a structural
diff finds and reading cannot. The band is back, at the foot of the header, where it leads straight
into the comparison desk it advertises.

It is also the one element on the page that is both a live number and a clock: `.ticker` takes
`--ground-2`, `--line` and `--yellow`, so it moves with the day and the weather along with everything
else. See [`day.md`](day.md).

Two things changed while it was being put back:

- **It speaks the reader's language.** Its six labels are keys now (`ticker.*`), not English written
  into a render function. Site-wide English-literal count went 210 → 206, and CI's ceiling with it.
- **It counts its own board.** The earlier build printed a hardcoded `10` in the hero — "quotes per
  search". That number stopped being true the day Uber left Uganda. The figure is now
  `PROVIDERS.filter(p => p.kind !== 'rent').length`, read off the board that is actually shipping, and
  it sits in the ticker rather than in a hero block the doors replaced.

Guarded by `site/test/client.test.mjs` §12, which asserts (a) no id the JavaScript reaches for is
missing from the markup — the general form of this bug — and (b) the band fills, and follows a
language switch.

## Four promises the current build had stopped making out loud

The earlier build's prose was blunter in four places, and the current build had replaced each with a
description rather than a promise. Descriptions were kept; the promises came back, as one repeated
device — a `.vow` line under each section's paragraph, in the same grid column, ruled in yellow.

| where | the line |
|---|---|
| Compare | We earn a referral or a UG booking. Never a mark-up on the quote you are shown. |
| Pool | Someone in your circle is already driving. No surge, no meter, no awkward cash — the fare is the true cost of the road, divided by the seats. |
| Rent | The price is per head as well as per day, because in Kampala the Prado is a group decision. |
| Hustle | For people running three lives. UG quotes each leg on the cheapest sensible mode, and says where a boda is faster than your dignity is worth. |

All four are keys, translated into Luganda and Swahili, and every reading I am not certain a speaker
would use is listed in that dictionary's `uncertain` array so the correction sheet asks about it. In
the other thirty-nine languages they fall back to English and carry the dotted rule that says so.

The `.vow` sits **inside** the section-head grid rather than beside it: `.sec-head > *:last-child`
became `:nth-child(2)`, and `.sec-head > .vow` takes `grid-column: 8 / -1`. The one grid the design
council fixed in v1.8 still holds; nothing was added outside it.

## What was deliberately *not* merged back

The two builds differ most in atmosphere, and almost all of that difference is work the v1.8 design
council did on purpose. Undoing it would have been a regression wearing a merge's clothes.

| the earlier build | now | why it stays |
|---|---|---|
| Unbounded / Albert Sans / IBM Plex Mono | Archivo + Martian Mono | three display families for one product was the thing the council cut |
| `--shadow: 0 30px 80px rgba(0,0,0,.55)` | contact + cast, `0 1px 1px` / `0 12px 34px` | one enormous drop shadow on every card flattens hierarchy instead of building it |
| `.glass{ blur(18px) saturate(1.4) }` at 64% | `blur(10px)` at 78% | text over the map has to be readable; saturation boost fought the palette |
| `--radius: 6px / 14px` | `5px / 11px / pill / 3px` | four radii used by role, rather than two used everywhere |
| hero stats block, hero CTA pair | the two doors | the doors ask the question the stats only decorated |
| "Secured by Flutterwave · Bank of Uganda licensed PSO" | the prototype note | **this one is not taste.** It is a regulatory claim, and this is a prototype whose own footer says payments run in a sandbox. Dropping it was correct and it is not coming back. |

The dead `.hero-stats`, `.hero-cta` and `.hero-doors` rules are the last trace of the replaced hero.
They are left in place for now and named here so the next person removes them knowingly rather than
wondering what used them.

## Method

`.build/` (gitignored) holds the throwaway tooling: the structural diff, the staged copy of the site
with `THREE_SRC` pointed at the vendored three.js so it renders without a CDN, and
`merge-shots.mjs`, which photographs the fares band at midday, at one in the morning, on a phone,
and in Swahili.
