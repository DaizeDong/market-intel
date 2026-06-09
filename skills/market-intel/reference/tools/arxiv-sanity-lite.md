# Tool: karpathy/arxiv-sanity-lite

- **Domain(s):** frontier-research (also: none)
- **Barrier route:** ③ (self-host OSS) · **Source tier:** L4 (personal recommender over arXiv) · **Ready MCP:** no — self-hosted web app; query its DB/HTTP yourself or wrap a thin MCP
- **Cost:** **free** — self-host, no key. [github.com/karpathy/arxiv-sanity-lite, gh-api 2026-06]
- **Repo / Provider:** github.com/karpathy/arxiv-sanity-lite — `karpathy/arxiv-sanity-lite` (**1.6k★**, gh-api 2026-06; MIT). ⚠ **D-STALE: last push 2023-06 (~3yr, >18mo)** — not archived, still self-hosts and runs, but unmaintained.
- **Top pick for its domain:** no

## What it does / when to pick it
A self-hostable "tame your arXiv firehose" app: it ingests arXiv papers, builds tf-idf features, and **recommends papers similar to ones you've tagged/liked** (SVM over your library), with search and per-tag ranking. **Decision rule:** pick it only if you want a **persistent, personalized recommender you run yourself** over a chosen arXiv slice — e.g. a standing scout for one sub-field. For one-shot recent-paper queries it's overkill; use the **arXiv API + HF Daily Papers** ① (free, no setup). For citation-graph neighborhood exploration use **Connected Papers / ResearchRabbit**; for deep synthesis delegate to **`research-lit`**.

## Install
```
git clone https://github.com/karpathy/arxiv-sanity-lite
cd arxiv-sanity-lite
pip install -r requirements.txt
python arxiv_daemon.py    # fetch papers for your categories
python compute.py         # build features
python serve.py           # local Flask app
```
Pure self-host (Flask + SQLite). No MCP transport — query its endpoints/DB directly or wrap a thin MCP. See `reference/install-guide.md` (Python prereqs, route ③) and `reference/volatile/pricing-install.md` → frontier-research. ⚠ Because it's stale (2023), expect to patch pinned dependency versions to install on a current Python.

## Auth / keys
None — fully local, no API key. It pulls from the public arXiv API (be polite, ~1 req/3s). (No secret-hygiene concern.)

## Usage — call examples
- Configure the arXiv categories you track in the daemon config (e.g. `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `stat.ML`).
- Run `arxiv_daemon.py` → `compute.py` → `serve.py`, open the local UI, tag a few seed papers, then read the **"recommend"** ranking for similar new papers.
- Programmatic: hit the Flask routes or read the SQLite DB it builds, rather than the UI.

## General experience & gotchas (踩坑)
- **Stale repo (push 2023-06).** The shard flags it **D-STALE** explicitly. It still self-hosts free, but you'll likely fix dependency pins and small breakages; nobody is upstreaming fixes. Budget setup time.
- **You run the infra.** Unlike the no-setup arXiv API, this is a daemon + feature-compute + web server you maintain — only worth it for a *standing* personalized scout, not a single query.
- **Recommendations are tf-idf/SVM over your tags — L4 personal signal, not significance.** It surfaces *similar* papers, not *important* ones. Verify significance via **Semantic Scholar** citation velocity / **OpenReview** scores, per the shard.
- **Coverage is only what your daemon fetched** (your configured categories + window) — it won't know about a paper outside that slice. It also inherits arXiv's scope (no biomed venues; use **paper-search-mcp** for those).
- Politeness: the daemon hits the arXiv API — respect the ~1 req/3s limit or you'll get throttled.

## Failure signals & fallback
Failure = install breaks on old pins, the daemon returns empty (category/window misconfig or arXiv throttle), or recs are noisy on a thin tag set. Fall back to the zero-setup route: **arXiv API + HF Daily Papers** ① for recent papers, **Semantic Scholar** for citation signal, **Connected Papers / ResearchRabbit** for graph neighborhood, and **`research-lit`** for synthesis.

## Last verified: 2026-06
