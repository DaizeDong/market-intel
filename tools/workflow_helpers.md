# Discovery prompt helpers

Use these rules when preparing a refresh discovery request. The canonical task
and candidate schema are in
[refresh-protocol.md](../skills/market-intel/reference/refresh-protocol.md).
The shared model interface is described in [CONFIG.md](../CONFIG.md#model-adapter).

## Shared prompt content

A discovery request should name the commercial domain, required capabilities,
current catalog comparison, permitted sources and output schema. Keep common
instructions together so every request follows the same evidence rules. Model
routing and any provider-specific caching remain the installed interface's concern.

Every candidate has one barrier route:

| Route | How the data is obtained |
|---|---|
| ① | Official API |
| ② | Resale or proxy aggregator |
| ③ | Self-hosted scraper |
| ④ | Browser automation |

An MCP server is an interface to one of these routes. Record its availability
separately with `has_ready_mcp`; it does not create another barrier route.

Discovery may inspect registries, repository activity, communities, official
release and pricing pages, and the public feeds described in the protocol. Attach
a fetched source URL to every volatile capability, price or activity claim.
Unverified claims remain WATCH candidates. Use ADD or REPLACE only with the
comparison evidence and fields required by the candidate schema.

Resolve the full consumer checkout before assigning reads. The relevant public
inputs are the source index, selected domain shard, discovery instructions and
MCP ecosystem shard. Include the Chinese discovery guide when that source scope
applies. Do not read runtime inventories as public documentation.

## Call the configured agent interface

The caller constructs the domain assignment and passes it to installed `llmcall`:

```python
from llmcall import call

prompt = "Discover candidate data sources for the assigned domain using the provided schema and evidence rules."
result = call(prompt, mode="agent")
if not result:
    raise RuntimeError("Discovery agent failed; inspect private provider diagnostics")
```

Provide the actual assignment and public reference paths in the prompt. Validate
the returned candidate structure against the refresh protocol before synthesis.
An import failure requires the model-adapter setup in CONFIG.md. An execution
failure is a coverage gap, not an empty successful discovery result.

Inherit the installed routing, model, timeout, retries and fallback policy. Do not
wrap it in another immediate-retry or provider-selection loop. Preserve completed
observations when another domain fails, and report attempted, completed and failed
domains separately.

Raw responses, rejected candidates, watchlists and research notes are DATA. Keep
those in the verified PRIVATE versioned companion through the existing DATA
resolver and writer. The public repository contains only the reusable instructions
and generator-owned synthetic examples.
