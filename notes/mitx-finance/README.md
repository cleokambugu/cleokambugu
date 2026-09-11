# MITx Finance MicroMasters — study notes

Notes distilled from the **MITx MicroMasters® Program in Finance**, MIT Sloan's
graduate-level finance sequence delivered through MITx Online / edX. The
program shares most of its content with MIT's residential Master of Finance
courses.

| Note | Contents |
|---|---|
| [`curriculum.md`](curriculum.md) | The six courses, their topics, prerequisites and ordering |
| [`engineering-lessons.md`](engineering-lessons.md) | What survived contact with an implementation — the transferable results |

The curriculum was turned into working code rather than prose alone: a
zero-dependency engine in [`tools/finance/`](../../tools/finance/) and five
agent skills in [`.claude/skills/`](../../.claude/skills/).

---

## How these notes were made — read this first

**MIT's own hosts were unreachable from this sandbox.** Every canonical source
for this program sits behind the network egress proxy:

| Host | What it holds | Status |
|---|---|---|
| `ocw.mit.edu` | OpenCourseWare lecture notes for the residential courses | **Blocked** |
| `web.mit.edu` | Prof. Jiang Wang's own 15.415 syllabus PDF | **Blocked** |
| `mitxonline.mit.edu` | Official course pages | **Blocked** |
| `learn.mit.edu` | MIT Learn course/program pages | **Blocked** |
| `micromasters.mit.edu` | Program overview | **Blocked** |
| `courses.edx.org` | Official 15.435x and 15.455x syllabus PDFs | **Blocked** |

Confirmed by both `WebFetch` (`EGRESS_BLOCKED`) and direct `curl`
(`CONNECT tunnel failed, response 403`). Per [`CLAUDE.md`](../../CLAUDE.md),
blocked hosts are **reported, not bypassed** — the fix is an allowlist change
(see [`notes/tooling/admin-allowlist.md`](../tooling/admin-allowlist.md)), and
a policy change only applies to **newly started** sessions.

So no MIT-authored lecture note, problem set or syllabus PDF was read for
these notes. What *was* reachable was anonymous `git clone` of public GitHub
repos, which is the path that produced the substance here — the same route
that produced [`notes/jam-with-ai/`](../jam-with-ai/).

### Provenance, split three ways

| Source | Trust | What came from it |
|---|---|---|
| **Two learner coursework repos, cloned and read directly** | First-hand *reading* of a **third-party** artifact. Verifiable, but **not MIT-authored** — a student's notes, which can contain student errors. | The detailed topic map for 15.435x and 15.455x in `curriculum.md` |
| **Web search snippets** of MIT-operated pages | Secondhand. Indexed summaries of pages that could not themselves be opened. | Course codes, titles, prerequisites, ordering, instructors, the topic outlines for 15.415.1x/2x and 15.516x |
| **Standard finance results, implemented and numerically verified in-sandbox** | First-hand *evidence*, independent of both above. | Everything in `tools/finance/` and `engineering-lessons.md` |

That third row is the important one. The identities in this curriculum —
put-call parity, the Black-Scholes formula, Macaulay duration, the
mean-variance frontier, DuPont — are long-established public results, not
proprietary MIT content. Rather than restate them on someone's authority, they
were implemented and then **checked against independent routes to the same
number**: closed forms against numerical differentiation, trees against closed
forms, Monte Carlo against both inside its own confidence interval, simulations
against their analytic counterparts. All 74 checks pass
(`python tools/finance/test_finlib.py`). Where this repo asserts a formula is
right, that test suite — not the cheat sheet, and not a search snippet — is
the reason.

Anything sourced from search snippets is marked *(secondhand)* at the point of
use in `curriculum.md`.

### The two repos that were read

Cloned anonymously through the session's git proxy:

| Repo | Commit | What it is |
|---|---|---|
| [`ol-gerd/MIT15.435x`](https://github.com/ol-gerd/MIT15.435x) | `40c9508` (2021-12-17) | A learner's final-exam cheat sheet for 15.435x — ~11k characters of formulas across forwards, swaps, duration/convexity, option strategies, binomial and Black-Scholes pricing, Greeks, delta-gamma hedging, exotics, interest-rate trees, credit risk (Merton), CDS and securitisation. Plus a `BondCalc.xlsm`. |
| [`m-chinmayee/MITx_15.455x_...`](https://github.com/m-chinmayee/MITx_15.455x_Mathematical_Methods_for_Quantitative_Finance) | `09d0a01` (2022-12-13) | A learner's Python coursework for 15.455x: ARMA generation with ACF/PACF (`week3_module2_time_series.py`), Monte Carlo price paths (`week3_recitation_monte_carlo.py`), gambler's ruin (`week3_module4_gamblers_ruin.py`), continuous-time models (`week4_continuous_time_models.py`), plus a topic list in `README.md`. |

**These are student artifacts, not course materials.** They are strong
evidence of *what the courses cover* — the 15.435x sheet even carries the
course support address `mm_fin@mit.edu` — and weak evidence of *what is
correct*. They were used for the first and not the second.

### One contradiction, flagged

Per [`CLAUDE.md`](../../CLAUDE.md) rule 5, rather than silently picking a side:

The 15.435x cheat sheet gives numerical effective duration as
`D_eff = (1/P) · (P_rise − P_fall) / (2Δy)`. Read with "rise/fall" meaning the
*yield* rises or falls, that expression is **negative** for an ordinary bond,
whereas duration is conventionally quoted positive. Read with "rise/fall"
meaning the *price* rises or falls, it is positive and correct.

The second reading is almost certainly what was meant. `fixed_income.effective_duration`
implements the unambiguous yield-based form,
`(P(y−Δy) − P(y+Δy)) / (2·P(y)·Δy)`, documents the ambiguity at the call site,
and the test suite pins it against the analytic modified duration. The
convexity formula on the same sheet is symmetric in the two prices, so the
ambiguity does not arise there.

## What would make these notes better

The gap is MIT-authored primary material — lecture notes, problem sets, the
official syllabi. Two routes, in order of cost:

1. **Allowlist the hosts.** `ocw.mit.edu` alone would open the OpenCourseWare
   editions of the residential courses (15.401/15.415 Finance Theory,
   15.511/15.515 Financial Accounting, 15.437 Options and Futures,
   18.S096 Topics in Mathematics with Applications in Finance). Add
   `web.mit.edu` and `courses.edx.org` for the instructor syllabi. Then start a
   **new** session — a policy change never affects the running one.
2. **Supply lecture video or captions directly.** The committed pipeline at
   [`tools/transcribe/`](../../tools/transcribe/) turns media into study-able
   text without network access (`learn.py ingest` for existing captions,
   `learn.py transcribe` for ASR).

## Source links

- Program: <https://micromasters.mit.edu/fin/overview> · <https://learn.mit.edu/programs/program-v1:MITxT+FIN>
- 15.415.1x Foundations of Modern Finance I — <https://learn.mit.edu/courses/course-v1:MITxT+15.415.1x>
- 15.415.2x Foundations of Modern Finance II — <https://mitxonline.mit.edu/courses/course-v1:MITxT+15.415.2x/>
- 15.435x Derivatives Markets — <https://mitxonline.mit.edu/courses/course-v1:MITxT+15.435x/>
- 15.455x Mathematical Methods for Quantitative Finance — <https://learn.mit.edu/courses/course-v1:MITxT+15.455x>
- MIT OpenCourseWare (residential editions) — <https://ocw.mit.edu/>

All of the above were **blocked** from this session; they are listed so the
claims can be re-checked from an unrestricted network.
