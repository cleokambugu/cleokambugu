# CLAUDE.md

Personal knowledge repository for Cleo Kambugu. This is the GitHub *profile* repo
(`cleokambugu/cleokambugu`), so it has one public-facing surface and one working surface.

## Layout

| Path | What it is |
|---|---|
| `README.md` | **Renders publicly on the GitHub profile page.** Any edit here is an outward-facing change — propose it, don't merge it unasked. |
| `notes/<topic>/` | Distilled study notes, one directory per source or subject. |

## Rules for writing notes

1. **Primary sources first.** If a course, talk, or channel has an open-source repo, clone
   and read the code before trusting any summary of it. Code is ground truth; marketing copy
   and search snippets are not.
2. **Mark provenance explicitly.** Every note states what was read first-hand versus what came
   from search snippets or secondhand write-ups. Never let a secondhand summary read as if it
   were direct observation.
3. **Cite locations.** Reference concrete `path/to/file.py` anchors or URLs so a claim can be
   re-checked later. A pattern with no anchor is an opinion.
4. **Prefer the transferable lesson.** Record *why* a design holds up in production, not just
   which API was called. Notes should stay useful after the library version moves.
5. **Flag contradictions rather than silently picking a side.** When a third-party page and the
   upstream repo disagree, say so and note which one is authoritative.

## Environment notes (Claude Code web sessions)

Outbound network runs through a policy-enforcing egress proxy. Known state as of 2026-08:

- **Blocked:** `youtube.com`, `jamwithai.dev`, `*.substack.com`, `wikipedia.org`, and most
  general web hosts. Direct `curl` fails, and so does `WebFetch`.
- **Available:** `WebSearch` (titles, links, snippets), and anonymous `git clone` of **public**
  GitHub repos through the git proxy — including repos outside the session's attached scope.

Practical consequence: when a resource is blocked, look for its public GitHub repo and clone
that instead of giving up. That path produced all of `notes/jam-with-ai/`. Do not attempt to
route around the proxy — report blocked hosts instead.

## Tooling notes

- Writing files with `cat <<'EOF'` heredocs is blocked by the auto-mode classifier in this
  environment. Use the `Write` tool for file creation instead.
