# Jam With AI — study notes

Notes distilled from **[Jam With AI](https://www.youtube.com/@jam-with-ai)**, an AI/ML education
project by **Shirin Khosravi Jam** and **Shantanu Ladhwe**. They publish across YouTube, a
Substack newsletter, and open-source course repositories, with an explicitly build-first,
"no toy demos" stance on teaching production AI systems.

| Note | Contents |
|---|---|
| [`curriculum.md`](curriculum.md) | The Mother of AI project — its 6 phases, and the 7-week Phase 1 syllabus in detail |
| [`production-rag-playbook.md`](production-rag-playbook.md) | 14 transferable engineering patterns pulled from the course source code |

---

## How these notes were made — read this first

**I did not watch the videos.** Two independent reasons, both worth stating plainly:

1. I have no audio or video capability — I cannot watch or listen to a video under any
   circumstances.
2. In this environment `youtube.com`, `jamwithai.dev`, and `jamwithai.substack.com` are all
   **blocked by the network egress proxy**, so even the pages' text was out of reach.

What I did instead was go to the primary source that *was* reachable: the project's public
GitHub repository, **[`jamwithai/production-agentic-rag-course`](https://github.com/jamwithai/production-agentic-rag-course)**
(also mirrored as `jamwithai/arxiv-paper-curator`). Public GitHub repos can be cloned
anonymously through this session's git proxy.

So the provenance splits cleanly:

| Source | Trust | What came from it |
|---|---|---|
| **Course repo, cloned and read directly** (`README.md`, `src/`, `airflow/`, `compose.yml`, `tests/`) | First-hand. Verifiable — every claim carries a file path. | Essentially all of `production-rag-playbook.md`, and the week-by-week detail in `curriculum.md` |
| **Web search snippets** (Substack post titles/summaries, the project's site copy) | Secondhand. Indexed summaries, not the articles themselves. | The 6-phase roadmap outline, author background, publishing platforms |

Anything sourced from search snippets is marked *(secondhand)* at the point of use. Where a
third-party page contradicted the upstream repo, the repo wins and the conflict is flagged.

Commit `424a0eb` is the version of the course repo these notes describe (README badge:
"Week 7 Advanced Features").

## Source links

- Channel: <https://www.youtube.com/@jam-with-ai> — also listed as
  <https://www.youtube.com/channel/UCqbneebdpn4ytLZG9EklhNg>
- Site: <https://www.jamwithai.dev/> · Courses: <https://learn.jamwithai.dev/>
- Newsletter: <https://jamwithai.substack.com/>
- GitHub org: <https://github.com/jamwithai>
- Course repo: <https://github.com/jamwithai/production-agentic-rag-course>

### Newsletter posts referenced by the course README

Each week of the course pairs with a written deep-dive. Titles and URLs below are taken from
the repo's own week-to-blog table, so the mapping is first-hand even though the articles
themselves were unreachable.

| Week | Post |
|---|---|
| 0 | [The Mother of AI project](https://jamwithai.substack.com/p/the-mother-of-ai-project) |
| 1 | [The Infrastructure That Powers RAG Systems](https://jamwithai.substack.com/p/the-infrastructure-that-powers-rag) |
| 2 | [Building Data Ingestion Pipelines for RAG](https://jamwithai.substack.com/p/bringing-your-rag-system-to-life) |
| 3 | [The Search Foundation Every RAG System Needs](https://jamwithai.substack.com/p/the-search-foundation-every-rag-system) |
| 4 | [The Chunking Strategy That Makes Hybrid Search Work](https://jamwithai.substack.com/p/chunking-strategies-and-hybrid-rag) |
| 5 | [The Complete RAG System](https://jamwithai.substack.com/p/the-complete-rag-system) |
| 6 | [Production-ready RAG: Monitoring & Caching](https://jamwithai.substack.com/p/production-ready-rag-monitoring-and) |
| 7 | [Agentic RAG with LangGraph and Telegram](https://jamwithai.substack.com/p/agentic-rag-with-langgraph-and-telegram) |

Other posts surfaced in search *(secondhand — titles only)*: "How to Start with AI Engineering
in end of 2025", "The Advanced AI/ML Engineering Path", "Data Science Roadmap 2026",
"The 2026 Roadmap: Production AI/ML Systems", "How to become AI/ML Engineer v2025".
