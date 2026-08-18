# Production RAG & agentic patterns

Fourteen patterns read directly out of
[`jamwithai/production-agentic-rag-course`](https://github.com/jamwithai/production-agentic-rag-course)
at commit `424a0eb`. Every one carries a file path so it can be re-checked.

Paths below are relative to that repo's root.

---

## Retrieval

### 1. Keyword search is the foundation; vectors are the enhancement

The course's central claim, and it's structural rather than rhetorical — BM25 gets its own week
before embeddings appear at all. `QueryBuilder` (`src/services/opensearch/query_builder.py`)
does real keyword engineering rather than treating text search as a fallback:

```python
self.fields = ["chunk_text^3", "title^2", "abstract^1"]   # chunk-level search
self.fields = ["title^3", "abstract^2", "authors^1"]      # paper-level search

{"multi_match": {
    "query": self.query, "fields": self.fields,
    "type": "best_fields", "operator": "or",
    "fuzziness": "AUTO", "prefix_length": 2,
}}
```

Field boosting, `best_fields`, typo tolerance with a 2-char prefix guard. **Why it matters:**
embeddings quietly fail on exact identifiers, names, and rare jargon — precisely the tokens
users search for. A weak keyword layer makes that invisible, because cosine similarity always
returns *something*.

### 2. Hybrid fusion via the engine's native RRF pipeline

Rather than fetching two result sets and hand-rolling score normalization, they register an
OpenSearch **search pipeline** with `phase_results_processors` and let the engine do Reciprocal
Rank Fusion (`src/services/opensearch/client.py`, `_create_rrf_pipeline`).

RRF fuses on *rank*, not score — which sidesteps the fact that BM25 scores and cosine
similarities are not on comparable scales and never will be. Normalizing them by hand is a
recurring source of subtly bad retrieval.

One unified `search()` degrades gracefully:

```python
if not query_embedding or not use_hybrid:
    # BM25 only
```

Same endpoint, three modes (BM25 / vector / hybrid) — so the modes can be A/B'd on identical
inputs instead of argued about.

### 3. Index config is a tuning surface

`src/services/opensearch/index_config_hybrid.py`:

```python
"index.knn": True,
"index.knn.space_type": "cosinesimil",
"dimension": 1024,                 # Jina v3
"engine": "nmslib",
"ef_construction": 512,            # higher = better recall, slower indexing
"m": 16,                           # bi-directional links per node
```

Plus a custom text analyzer — `standard` tokenizer with `lowercase`, `stop`, `snowball` filters.
The HNSW parameters carry inline comments explaining the recall/latency trade-off. **Lesson:**
these are product decisions, not defaults to inherit silently.

### 4. Section-aware chunking with size bands

`src/services/indexing/text_chunker.py` — the most portable single idea in the repo. Instead of
one fixed window over the document, chunk by *document structure*, then repair the outliers:

| Section length | Treatment |
|---|---|
| 100–800 words | Becomes one chunk as-is |
| < 100 words | Combined with adjacent sections |
| > 800 words | Split by word-window: 600 words, 100-word overlap |
| No sections detected | Fall back to pure word-window chunking |

```python
def __init__(self, chunk_size=600, overlap_size=100, min_chunk_size=100):
    if overlap_size >= chunk_size:
        raise ValueError("Overlap size must be less than chunk size")
```

Two details worth copying: **every chunk carries the paper's title and abstract**, so a chunk
retrieved in isolation still has orienting context; and section-based chunking is wrapped in
`try/except` that falls back to word-based chunking, because real PDFs defeat structure
extraction constantly.

---

## Agent design

### 5. Agentic RAG is a state graph, not a bigger prompt

`src/services/agents/agentic_rag.py` builds an explicit LangGraph `StateGraph`:

```
START → guardrail ─┬→ out_of_scope → END
                   └→ retrieve → tool_retrieve → grade_documents ─┬→ generate_answer → END
                                                                  └→ rewrite_query → retrieve
```

Control flow lives in code with named nodes and typed edges — inspectable, unit-testable, and
renderable (`get_graph_mermaid()`, `get_graph_ascii()`, `get_graph_visualization()`). The
alternative — one mega-prompt asking a model to decide everything — cannot be debugged, traced
per step, or tested node by node.

### 6. Guardrail as a *scored* gate, not a boolean

`src/services/agents/nodes/guardrail_node.py` scores every incoming query 0–100 for domain fit,
then compares against a configurable threshold (default `60`):

```python
return "continue" if score >= threshold else "out_of_scope"
```

The prompt hands the model a calibrated rubric rather than a yes/no:

```
80-100: Clearly about CS/AI/ML research
60-79:  Potentially research-related but unclear
40-59:  Borderline or ambiguous
0-39:   NOT about research papers
```

**Why a score beats a boolean:** policy becomes a number you can tune per environment, per user
tier, or in response to observed false-positive rates — without touching the prompt and
re-validating the model's behaviour. It also gives you something to threshold-sweep offline.

Out-of-scope queries terminate early with an honest "outside my domain" answer. This is
hallucination prevention at the routing layer, which is far cheaper and more reliable than
trying to instruct it away at generation time.

### 7. Self-correcting retrieval loop, explicitly bounded

Retrieved documents are graded for relevance by an LLM
(`nodes/grade_documents_node.py`). Irrelevant → route to `rewrite_query`, which reformulates and
retries retrieval. The loop is bounded in config:

```python
max_retrieval_attempts: int = 2
```

The pattern to steal is the pairing: **a retry loop and its bound are defined together.** An
unbounded agentic loop is a production incident with a latency bill attached.

### 8. Structured outputs at every decision point

No free-text parsing anywhere. Each decision node binds a Pydantic schema
(`src/services/agents/models.py`):

```python
class GuardrailScoring(BaseModel):
    score: int = Field(ge=0, le=100)
    reason: str

class GradeDocuments(BaseModel):
    binary_score: Literal["yes", "no"]
    reasoning: str = ""
```

invoked via `llm.with_structured_output(GuardrailScoring)`. The `ge=0, le=100` constraint means a
malformed score is a validation error at the boundary, not a mystery downstream. Note that every
schema also carries a `reason`/`reasoning` field — the model must state *why*, which is both a
quality nudge and a debugging artifact.

### 9. Temperature is a per-node decision

- Guardrail scoring → `temperature=0.0`
- Document grading → `temperature=0.0`
- Query rewriting → `temperature=0.3`

Judgment nodes are deterministic; the one genuinely generative node gets a little freedom. A
single global temperature is a smell.

### 10. Every LLM call has a deterministic fallback

The most valuable production lesson in the repo. **Every** node wraps its model call and
degrades rather than propagating failure:

| Node | Fallback when the LLM call fails |
|---|---|
| Guardrail | Conservative score of `50` with the error as the reason |
| Document grading | Heuristic — `len(context.strip()) > 50` |
| Query rewriting | Simple keyword expansion (`+ "research paper arxiv machine learning"`) |
| Answer generation | Apologetic error message returned as the answer, span marked `level="ERROR"` |
| Retrieve | Guarded tool invocation with its own degradation path |

(`out_of_scope` is the one node with no `try/except` — it makes no model call, returning a
canned `AIMessage`. The rule is precisely "every LLM call", not "every node".)

```python
except Exception as e:
    logger.error(f"LLM grading failed: {e}, falling back to heuristic")
    is_relevant = len(context.strip()) > 50
```

The graph always reaches a terminal state. A flaky model provider degrades answer quality; it
does not take down the endpoint. Note also that the fallback records *itself* in the reasoning
field (`"Fallback heuristic (LLM failed): ..."`), so degraded responses are identifiable in
traces afterwards rather than silently indistinguishable from healthy ones.

### 11. Dependency injection via typed runtime context

Nodes are plain async functions taking `(state, runtime)` — clients arrive through
`Runtime[Context]` (`src/services/agents/context.py`), not closures:

```python
workflow = StateGraph(AgentState, context_schema=Context)
workflow.add_node("guardrail", ainvoke_guardrail_step)   # bare function reference
```

```python
llm = runtime.context.ollama_client.get_langchain_model(...)
```

The repo's own comment: *"Lightweight nodes as pure functions... no closures needed!"* The payoff
is visible in `tests/unit/services/agents/test_nodes.py` — nodes are testable in isolation with a
mock context, no graph construction required. Typed state (`AgentState` as a `TypedDict` with an
`add_messages` reducer, `state.py`) means what flows between nodes is declared, not implied.

---

## Operations

### 12. Observability designed in, never bolted on

Every node opens a Langfuse span with structured input, output, metadata, and
`execution_time_ms` (`src/services/langfuse/`). Three details that make this production-grade
rather than decorative:

**Tracing failures never break the request.** Every span operation is individually wrapped:

```python
try:
    span = runtime.context.langfuse_tracer.create_span(...)
except Exception as e:
    logger.warning(f"Failed to create span for guardrail validation: {e}")
```

Monitoring is strictly best-effort. An observability outage must not become a product outage.

**Errors are traced as first-class outcomes**, not just logged:

```python
trace.update(output={"error": str(e)}, level="ERROR")
trace.end()
self.langfuse_tracer.flush()
```

**Context propagation is automatic.** `CallbackHandler()` inherits the current span context from
`start_as_current_span`, so nested LangChain calls attach to the right trace without threading a
trace object through every call site.

### 13. Reasoning transparency as a product feature

`_extract_reasoning_steps()` returns the agent's decision path to the caller:

```
Validated query scope (score: 85/100)
Retrieved documents (2 attempt(s))
Graded documents (3 relevant)
Rewritten query for better results
Generated answer from context
```

The API response carries `reasoning_steps`, `retrieval_attempts`, `rewritten_query`, and
`guardrail_score` alongside the answer. Users get to see *why*; engineers get a bug report
attached to every response. Same data, two audiences.

### 14. Cache keys must cover everything that changes the answer

`src/services/cache/client.py` hashes the full parameter set, not the query string:

```python
key_data = {
    "query": request.query,
    "model": request.model,
    "top_k": request.top_k,
    "use_hybrid": request.use_hybrid,
    "categories": sorted(request.categories) if request.categories else [],
}
key_string = json.dumps(key_data, sort_keys=True)
key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
```

`sort_keys=True` and `sorted(categories)` make the key canonical, so semantically identical
requests hit the same entry regardless of field ordering. Keying on the query alone would serve a
`top_k=3` BM25 answer to a `top_k=10` hybrid request — a class of bug that is very hard to
notice, because the response looks perfectly plausible.

Cache errors are swallowed and return `None`, so Redis being down means slow, not broken:

```python
except Exception as e:
    logger.error(f"Error checking cache: {e}")
    return None
```

---

## The meta-lesson

Sequence the operational concerns *before* the impressive ones. Infrastructure lands in Week 1,
search in Week 3, tracing and caching in Week 6 — and only then, in Week 7, do agents start
making nondeterministic decisions. By the time the system can surprise you, you already have the
instruments to see what it did.

The recurring shape across all fourteen patterns is the same: **decide explicitly, bound the
loop, type the boundary, and always have a fallback.** That is what separates a RAG demo from a
RAG system.
