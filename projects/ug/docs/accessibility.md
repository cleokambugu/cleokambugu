# Accessibility

Different bodies, same app. UG's accessibility thinking follows the same rule as its language
justice: nobody should have to adapt themselves to the product.

## Settings, in the product

An Accessibility sheet opens from the welcome screen and from Me:

| Setting | What it does |
| --- | --- |
| Larger text | Scales the whole page up (zoom 1.18) |
| High contrast | Raises secondary text, lines and borders toward full ink; borders thicken |
| Reduce motion | No opening animation, no drifting particles, near-zero transitions everywhere |
| Underline links | Links are underlined, never colour alone |

Choices persist on the device and are seeded from the system: `prefers-reduced-motion` turns
Reduce motion on by default, `prefers-contrast: more` turns High contrast on. The welcome
screen's 3D language ring collapses to a flat grouped list under reduced motion, and every
overlay honours the `hidden` attribute so nothing invisible traps a pointer or focus.

## Built in, not settings

- **Keyboard end to end.** Every control is a real button, select or link; focus is visible
  (a yellow outline); the language ring turns with the arrow keys and chooses with Enter; modals
  close with their close button and by clicking the backdrop.
- **Screen readers.** Landmarks, `aria-label`s on icon buttons, `aria-live` on the stages, the
  trip pill and the greeting, `role="dialog"` with `aria-modal` on every sheet, `role="switch"`
  with `aria-checked` on the accessibility toggles, a text alternative for the particle map.
- **Voice.** The microphone button drives the app by speech ("compare Ntinda to Downtown",
  "take a seat to Jinja"), and the Cephable plug-in brings switch, face and voice control for
  people who navigate that way.
- **Language.** Thirty-plus languages with honest confidence labels are themselves an
  accessibility feature; `dir="rtl"` is applied for Arabic.
- **Reduced-motion media queries** already guard the ticker, dock pulse, reveals and hero
  animations even before the setting is touched.

## Known gaps (v2 work)

- Colour contrast of some secondary text on glass surfaces has not been audited against WCAG AA
  in both themes; the High contrast setting is the stopgap.
- The particle map is decorative for screen-reader users; town pins are buttons, but the heat
  layers (Pulse, Foresight) need a table alternative.
- No haptics; no captions for Tazama audio yet (the showreel's sound cut has captions).
- Translations of the accessibility sheet itself ship in the next dictionary round.
