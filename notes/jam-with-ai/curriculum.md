# The Mother of AI project — curriculum map

Jam With AI's flagship series. The framing: a build-first, learn-by-doing path where each phase
ships a complete working system rather than a notebook demo. Their stated positioning is that
most tutorials jump straight to vector search, while companies that actually ship start from
search fundamentals and layer AI on top.

> **Provenance:** the 6-phase outline is *(secondhand)*, assembled from search snippets of the
> Week 0 post. The Phase 1 detail below is first-hand — read directly from the cloned course
> repo at commit `424a0eb`.

---

## The six phases *(secondhand)*

| Phase | Focus | Shipped outcome |
|---|---|---|
| **1** | **RAG Systems: Zero to Hero** | A personal AI research assistant. Ingest 1000+ papers, chunk, embed, hybrid search, LLM answer generation, monitoring |
| **2** | **AI Agents + Tool Use + Monitoring** | Decision-making agents with memory, planning and tools — multi-step reasoning past static RAG |
| **3** | **Recommendation Systems** | Real-time content-based / hybrid multi-stage recommenders: ranking, personalization, feedback loops, metrics |
| **4** | **MLOps + LLMOps** | CI/CD, evaluation harnesses, fine-tuning, prompt versioning, data pipelines, security, testing |
| **5** | **Full App Integration + Cloud Deployment** | Containerization, API orchestration, front-end, AWS/GCP deploy, IaC, cost optimization |
| **6** | **Monitoring + Alerting Mastery** | Systems that "never go silent" |

The through-line across phases: *production* means the operational concerns (observability,
cost, evaluation, failure handling) are treated as first-class curriculum, not an appendix.

---

## Phase 1 in detail — the arXiv Paper Curator

Seven weeks, each with a git tag (`week1.0` … `week7.0`) so you can check out the exact state of
the codebase at that point in the course. Each week also has a Jupyter notebook under
`notebooks/weekN/` and a paired newsletter post.

### Week 1 — Infrastructure foundation

Stand up the whole backbone before writing a line of AI code. Docker Compose brings up FastAPI
(8000), PostgreSQL 16 (5432), OpenSearch 2.19 + Dashboards (9200/5601), Apache Airflow 3.0
(8080), and Ollama (11434). Health-check endpoints and code-quality tooling from day one.

The teaching move here: infrastructure first means every later week has somewhere to land. By
Week 7 `compose.yml` runs **13 services** — the RAG stack plus a full self-hosted Langfuse
deployment (ClickHouse, MinIO, its own Postgres and Redis).

### Week 2 — Data ingestion pipeline

arXiv API client with rate limiting and retry logic; scientific PDF parsing via **Docling**;
Airflow DAGs for automated daily ingestion; metadata into Postgres. A `MetadataFetcher`
orchestrates the pipeline (`src/services/metadata_fetcher.py`), and the DAG is decomposed into
`fetching` / `indexing` / `reporting` / `setup` modules rather than one monolithic file
(`airflow/dags/arxiv_ingestion/`).

### Week 3 — Keyword search first

**The load-bearing week, pedagogically.** BM25 over OpenSearch: index mappings, Query DSL,
filters, boosting, relevance scoring, precision/recall analytics. No vectors yet — deliberately.

The argument is that if you can't get keyword retrieval right, adding embeddings only hides the
problem behind an opaque similarity score.

### Week 4 — Chunking & hybrid search

Section-based chunking; production embeddings via **Jina AI** (1024-dim, v3) with fallback
strategies; hybrid retrieval fusing BM25 with vector search via **RRF**; one unified endpoint
serving all search modes so they can be compared head-to-head.

### Week 5 — Complete RAG pipeline

The LLM layer. **Ollama** running `llama3.2:1b` locally for full data privacy; a system prompt
tuned for academic papers; streaming responses over Server-Sent Events; dual endpoints
(`/api/v1/ask` and `/api/v1/stream`); a Gradio UI on 7861. The README claims an 80% prompt
reduction yielding roughly 6x speedup — an explicit lesson that prompt size is a latency budget.

### Week 6 — Production monitoring & caching

**Langfuse** for end-to-end tracing, **Redis** for exact-match caching with TTL management,
dashboards for latency and cost. README cites 150–400x speedup on cache hits.

> ⚠️ Some third-party summaries describe Week 6 as "setting up evals." The upstream repo says
> monitoring and caching. The repo is authoritative; those pages are stale.

### Week 7 — Agentic RAG with LangGraph + Telegram

The current head of the course. A **LangGraph** state machine replaces the linear pipeline:
guardrails for domain validation, LLM-based document grading, adaptive query rewriting with
retry, and out-of-scope early exit. Plus a Telegram bot for mobile access, and exposed reasoning
steps so the agent's decision path is visible to the user.

See [`production-rag-playbook.md`](production-rag-playbook.md) for how this is actually built.

---

## The stack, in one place

**Serving** FastAPI · Gradio · Telegram bot
**Retrieval** OpenSearch 2.19 (BM25 + kNN + native RRF pipeline) · Jina v3 embeddings
**Generation** Ollama (`llama3.2:1b`) · LangGraph · LangChain
**Data** PostgreSQL 16 · Apache Airflow 3.0 · Docling
**Ops** Langfuse (self-hosted: ClickHouse + MinIO + Postgres + Redis) · Redis cache · Docker Compose
**Tooling** Python 3.12 · `uv` · pytest · pre-commit

Notable: everything runs locally. No hosted LLM API is required to complete the course — a
deliberate choice for privacy and for keeping the cost of learning at zero.

---

## What's worth stealing from the course design

- **Weeks are git tags.** Learners check out `week3.0` and get exactly that state. The teaching
  artifact and the code artifact are the same object.
- **Sequenced so each week is useless-until-integrated.** Chunking (W4) is pointless without the
  index (W3), which is pointless without ingestion (W2). Nothing is a detached tutorial.
- **Ops introduced before the fancy part.** Monitoring (W6) lands *before* agents (W7), so when
  the agent starts making nondeterministic decisions there's already tracing to see them with.
  Most curricula do this in the opposite order.
- **The unglamorous foundation gets top billing.** BM25 gets a full week and the strongest
  rhetorical framing in the README. That is the course's actual thesis.
