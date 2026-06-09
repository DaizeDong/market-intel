# Tool: Future-House/paper-qa (PaperQA2)

- **Domain(s):** frontier-research (also: none)
- **Barrier route:** ④ self-host (LLM-driven agent over local PDFs) · **Source tier:** L1 · **Ready MCP:** no — Python library, `pip install paper-qa`, call as a lib / CLI
- **Cost:** free & open-source (Apache-2.0); you pay only the LLM + embedding API spend it runs under the hood [github.com/Future-House/paper-qa, fetched 2026-06]
- **Repo / Provider:** github.com/Future-House/paper-qa — `Future-House/paper-qa (8.7k★, gh-api 2026-06)`; active (pushed 2026-06-05, not archived, Apache-2.0)
- **Top pick for its domain:** no (it's the deep full-text layer above the search tools, not the first-line scout)

## What it does / when to pick it
A grounded retrieval-augmented QA agent over **full-text PDFs**: it chunks/embeds a corpus of papers, retrieves the relevant passages, and answers with **inline citations back to the exact source** — designed to minimize hallucinated claims. **Decision rule:** pick it once you already have the right papers (from `arxiv` / `paper-search-mcp` / Semantic Scholar) and need to *read deeply and answer questions with citations* — "what does this set of papers actually say about X", contradiction-checking, evidence extraction. It sits a layer ABOVE raw search. If the job is multi-paper narrative synthesis / a written lit-review, hand off to the **research-lit** skill instead; PaperQA is the engine, research-lit is the workflow.

## Install
`pip install 'paper-qa>=5'` (Python ≥3.11) — pin `>=5` so you land on PaperQA2, not the older v4 line (verified against the repo README 2026-06). It's a **library/CLI, not an MCP** — no `claude mcp add`; you run it (`pqa ask "..."` over a folder of PDFs) or import it. No MCP transport, so no Windows stdio concerns — just a Python env + your PDFs. Cross-link: `reference/volatile/pricing-install.md` → frontier-research (`pip install paper-qa`); L0 mechanics in `reference/install-guide.md`.

## Auth / keys
No account for PaperQA itself. It needs an **LLM + embedding provider key** (default OpenAI via `OPENAI_API_KEY`; configurable to Anthropic / local models). This is a paid LLM key, so secret-hygiene applies: keep it in an env var the **user** sets (`-e KEY=$VAR` / shell export), never echo or commit it — see `reference/install-guide.md` → Secret-handling hygiene. Provide the PDFs locally; for paywalled papers you must supply your own legally-obtained copies.

## Usage — call examples
CLI over a directory of PDFs:
```bash
pqa ask "Does method X outperform Y on long-context benchmarks?" -d ./papers
```
Or as a library: `from paperqa import ask; ask("...")` after pointing it at your document set. It returns a synthesized answer plus a per-claim citation list mapping each statement to the source passage — keep that citation trail; it's the whole point of the tool.

## General experience & gotchas (踩坑)
- **It costs LLM tokens, not an API quota (shard).** "Free & open-source" means the code is free — a deep query over a large corpus can run many embedding + completion calls; watch spend on big PDF sets and pick a cheaper embed model if scaling.
- **Garbage-in on PDFs.** Extraction quality depends on the PDF — scanned/figure-heavy/table-dense papers parse poorly; answers are only as good as the chunked text it could read.
- **It answers from the corpus you give it, not the web.** It will not discover papers — feed it the right set first (`paper-search-mcp` / `arxiv` / Semantic Scholar). Missing-but-relevant work simply won't appear in the answer.
- **Grounding ≠ infallible.** Citations are checkable by design, but verify a load-bearing claim against the cited passage before quoting — that's the feature, use it.
- **First run downloads models / builds an index** and embedding the corpus takes time; reuse the index across questions instead of re-embedding per query.

## Failure signals & fallback
Failure looks like: an auth error (missing/invalid `OPENAI_API_KEY` or chosen provider key); empty / "insufficient context" answers (PDFs didn't parse, or the corpus doesn't actually cover the question — re-collect papers); or runaway cost (corpus too large — narrow it or switch embed model). **Fallbacks:** to *find* the papers first → **paper-search-mcp** (multi-venue) / the **arxiv** MCP; significance ranking → **Semantic Scholar**; for a written multi-paper survey rather than a Q&A engine → delegate to the **research-lit** skill.

## Last verified: 2026-06
