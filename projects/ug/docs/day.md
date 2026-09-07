# The day

The palette is a clock, not a switch.

## Why

A dark/light toggle asks the wrong question. Nobody wants "dark mode"; they want the screen to stop
shouting at one in the morning, and they want to be able to read a fare at noon in Kampala sun. Those
are two different requests that happen to have been collapsed into one button, and the button is
always in the wrong position when you arrive.

So the page keeps the time instead. It opens in the light the day is actually in, and it moves with
the day while you read.

## The three colours, and where they come from

The flag has three: black for the people of Africa, gold for the sun, red for the blood that runs
through all of us. The sky over Kampala hands them over in this order, every day:

```
black  ──▸  red  ──▸  gold  ──▸  red  ──▸  black
 night      dawn      midday     dusk      night
```

That is **not** the flag's band order and this document does not claim it is. It is the flag's three
colours in the order the sky gives them, which is a different and smaller claim, and a true one.

## Why it can be a fixed table

Uganda is on the equator. Kampala sits at 0°19′N, so the day does not have seasons: the sun is up at
about **06:54** and down at about **18:54**, every day of the year, give or take a quarter of an hour.
Civil twilight at the equator is the shortest on earth — roughly twenty minutes.

Two consequences, and both are load-bearing:

1. **No almanac.** Six anchors and seven segments cover the whole year. A site at 55°N would need a
   sunrise table; this one needs a constant.
2. **The crossings are fast, honestly.** The page changes from a dark ground to a light one at
   sunrise and back at sunset, and nowhere else. That is a real event in the sky, not a compromise —
   and it means the palette never has to drift through the middle, where a dark ground and a light
   ground meet and neither ink can be read on either.

## The anchors

| From | To | Blend | Family |
|---|---|---|---|
| 00:00 | 05:00 | night | dark |
| 05:00 | 06:54 | night → dawn | dark |
| 06:54 | 10:00 | morning → midday | **light** |
| 10:00 | 15:30 | midday | light |
| 15:30 | 18:54 | midday → afternoon | light |
| 18:54 | 21:30 | dusk → night | **dark** |
| 21:30 | 24:00 | night | dark |

Interpolation is smoothstepped and only ever runs *inside* one family. Across a whole minute the
ground moves by at most two values in 255 — far under a just-noticeable difference, which is the
entire point: you never catch it moving.

Night also brings the ink down a step. `--ink` is `#E9DFCF` at two in the morning and `#F4ECDD` was
the old constant; the difference is small and it is the difference between a page and a torch.

## What the weather is allowed to do

Weather bends the light. It does not repaint the brand.

- **Cloud** flattens. In the light family the paper goes toward a colder cream and the gold loses its
  sun; in the dark family the ground comes *up* slightly, because an overcast night over a city is
  brighter than a clear one — the cloud is holding the town's own light down.
- **Rain** cools the ground and the lines toward `--crane`, which is already the brand's grey-blue:
  the crowned crane's own colour, on the flag's crest and in the tokens since v1.

Nothing else moves. **Yellow stays the action, red stays the alert, green stays money you keep** —
the design council fixed those meanings in v1.8 and the weather may not borrow them. The whole dose
is nine numbers in `W` at the top of the pre-paint script; there is no second knob.

Source: [Open-Meteo](https://open-meteo.com) `current`, no key, cached twenty minutes, asked on idle
well after first paint. If the call fails the page keeps its clock and simply has no weather.

> **Not verified against the live endpoint.** This repository's sandbox egress proxy denies
> `api.open-meteo.com` (`connect_rejected`, organisation policy), so the reader is written to the
> documented response shape and exercised against a fixture, never against the service. The first
> person with a network should open the page and confirm the chip fills in.

## Where you can see it

- **The map.** Rain falls on the actual particle map of Uganda, in the scene that is already running —
  no second canvas, no second WebGL context, and it pauses with the map when it scrolls away. Cloud
  is a translucent veil that takes the land's contrast down. Both are off under reduced motion.
- **The chip**, bottom right of the map: the band, the temperature, the condition, the phase.
- **The rail**, in Accessibility. Twenty-four hours of the page's own ground colour, sampled every
  quarter hour, with sunrise, sunset and now marked. It is not a diagram of the flag; it is the
  palette itself, laid out flat. The flag's colours appear in it because the palette is built of them.

## Turning it off

Three states on one control, in Accessibility or on the nav button: **follow the day**, **always
noon**, **always night**. Auto is the default; a deliberate choice is kept and wins for good.
`prefers-contrast: more` and the in-app high-contrast switch both still apply on top, because they
work on the tokens rather than replacing them.

## What holds it up

`site/test/client.test.mjs` §8 walks **every minute of the day against four skies** — clear,
overcast, rain, storm — and checks nine ink/ground pairs against their contrast floors (7:1 for body,
4:5 for the quiet labels). It also asserts the family changes exactly twice a day, at sunrise and
sunset, and that no single minute moves the palette by more than two values in 255.

The first run of that test failed, which is the reason it exists: at one in the morning under heavy
rain the lifted ground took `--ink-3` down to 3.93:1. The three dark phases' quietest ink was raised
until the worst minute of the worst weather passes.

`.build/sample.cjs` runs the same sweep in Node, without a browser, for tuning.
