# Presence: designing for more than the screen

A note in the brief: *humans have eight senses*. It is a better provocation than it first looks,
because almost every product decision in software is made about one of them.

Here is the honest audit of what UG reaches, what it could reach, and where the idea stops being
useful and starts being decoration.

## The eight, and what a mobility app can actually do with each

**1 · Sight.** Everything, obviously — but the specific decision is what the eye is asked to do
*first*. On the compare desk the answer is: find the money. So the money is the largest object in
the row, in tabular figures at a fixed measure, so the column aligns down the page and the eye can
run it like a fare board. The type is set expanded and heavy in the display face for the same
reason a coach destination board is: it is read from an angle, in a hurry, in bad light.

**2 · Hearing.** Two channels, and they are different. The score is generative and sits under
everything; the voice carries meaning and must be a person (`showreel/voice/CASTING.md` explains
why no model can do it). The bulletin in the dock is the third: a radio register, because that is
what a Ugandan car actually sounds like.

**3 · Touch.** A phone can speak to the hand and almost no product uses it for anything but
alerts. UG has five patterns, and each means one thing:

| | | |
|---|---|---|
| `tick` | something you did registered | 10 ms |
| `fill` | a seat went in, the price moved | two short, rising |
| `land` | a driver, a plate, a real thing | one firm |
| `done` | money moved, and it worked | short-long |
| `stop` | something needs you | two firm, spaced |

Small enough to learn without being taught. Off under reduced motion, off when the accessibility
panel says so, and silently absent on iOS, which does not implement the Vibration API — so nothing
depends on it. It is `haptic()` in `site/index.html`.

**4 · Balance (vestibular).** The sense that motion sickness lives in, and the reason
`prefers-reduced-motion` is not a nicety. Everything that moves in UG can be turned off, and the
opening film has a wall-clock stop so a throttled tab cannot leave the page swimming. In the reel,
the camera moves are eased rather than linear because a linear push feels like being dragged.

**5 · Proprioception.** Where your body is, which on a phone means where your thumb is. The reason
the mobile comparison row stacks — logo and name, then the price, then the action full width — is
that the action belongs in the bottom third where the thumb rests, and the price belongs above it
where the eye already is. The tab bar and the dock sit above the safe-area inset for the same
reason.

**6 · Interoception.** The least discussed and, for this product, the most important: the felt
sense of your own state. Anxiety, mostly. *Will the price change? How long am I standing here?
Where did my money go? Is this driver safe?*

Almost everything UG is actually for lives in this sense. The provenance label on every fare, the
greyed row that says why it cannot serve you, the trip rail with real timestamps, the receipt for
every shilling, the Quality section refusing to publish a number it has not earned — none of those
are visual features. They are interoceptive ones. They change how it feels to be a person with
somewhere to be and not enough money.

**7 and 8 · Taste and smell.** A screen cannot deliver either, and pretending otherwise is where
this framework turns into a poster. The only honest move is to *evoke* rather than claim, and to
do it sparingly: the rolex money in the weekend budget, the Nile at sunset in the Jinja blurb. Two
mentions in the whole product. A third would be twee.

## The rule this gives us

**Reach a sense only where that sense is the right instrument.** Haptics for confirmation, because
the hand is faster than the eye. Voice for warmth, because a person's voice is the only thing that
carries it. Silence and stillness as defaults, because the most common accessibility request in
this market is *less*, not more.

The failure mode is a product that buzzes, chimes and animates to prove it is sophisticated. That
is not presence. Presence is a person putting the price where you were already looking, telling
you the truth about it, and then getting out of the way.
