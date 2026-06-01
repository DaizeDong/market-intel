# Evolution — toward a fully-automatic, self-improving closed loop

> **自动进化闭环设计 —— 评估结论与分阶段路线**

This document captures the closed-loop design for market-intel's self-update: an honest diagnosis of
where it is today, why it is **not yet** safe to go fully autonomous, and the staged path that gets
there without violating [PHILOSOPHY.md](PHILOSOPHY.md) (P3: monotonic — only improve, never decay).
It is the product of a 5-subagent evaluation (control-theory, feedback, meta-loop, red-team, CI).

> 本文记录 market-intel 自更新的闭环设计：现状诚实诊断、为何**尚不能**安全全自动、以及在不违背
> PHILOSOPHY（P3 单调进化）前提下达成全自动的分阶段路线。源自一次 5-subagent 评估。

---

## 1. Diagnosis — today it is a *half-closed, open-loop* system · 现状诊断

Viewed as a control system, two loops are incomplete:

- **No sensor (open-loop).** After updating the matrix, the system gets **no signal back** about
  whether the update was good — was a newly added source actually useful in a real research run? did
  a price turn out wrong? is a domain quietly rotting? `verify_matrix.py` is a *constraint gate*
  (instantaneous, binary, inward-looking), **not a sensor** of result quality over time. → slow
  degradation is invisible; the next refresh can't learn from the last.
- **Actuator not closed (human relay).** The gate→PR step is strong, but **loop closure is a human
  clicking merge.** No merge → the error signal (stale matrix) is never consumed → PRs pile up while
  the live skill ages. The sensors are strong; the last segment of the actuator is in human hands.

The human-merge step is a **feature, not a bug** (CONSTITUTION C10): it is the only thing catching
the *semantic* degradation the deterministic gate cannot — a wrong REPLACE choice, a hyped/wrapper
tool, a wrong price, a should-it-be-a-new-domain call. The flaw is that it's the *only* closure
channel, so it gates trivial reversible changes (dead-link cleanup) behind the same human relay as
risky ones, causing pile-up.

---

## 2. Honest verdict — do NOT go full-auto yet · 诚实结论：暂不可全自动

The red-team verified a serious integrity gap: **the gate's repo-existence check was nearly hollow
on real data** — 0 `github.com/` URLs in the shards, so existence was only verified for repos that
*happened* to carry a `(NNk★)` annotation; unstarred real repos (e.g. `erithwik/mcp-hn`,
`EnesCinr/twitter-mcp`) were invisible. The deterministic gate is today a **format gate, not a fact
gate** — it catches what breaks Markdown, not what makes the matrix quietly *wrong*.

Worse, the philosophy's own P4 ("the editor is never its own verifier") is **currently violated**:
the same headless LLM both edits and verifies. And P2 ("mechanisms, not intentions") is violated for
C2/C4/C7 — route-downgrade, deletion-needs-evidence, and no-rewrite are enforced only by LLM自觉,
not by the gate.

**Conclusion:** removing the human merge today would amplify silent degradation, not efficiency. The
philosophy *itself* says: fix the framing (make the gate a real fact-gate + add independent
verification + add a feedback sensor) **before** closing the actuator. Full-auto is earned, not
assumed.

### Preconditions before any auto-merge (from the red-team)
- [ ] Gate verifies **every** repo entry's existence (machine-readable mirror block / mandated
      canonical `github.com/owner/repo` URLs) — not the star-annotation side effect. *(v0.5.1: interim
      WARN-tier net for unstarred slugs added; BLOCK-level guarantee still needs the mirror block.)*
- [ ] **Independent cross-model audit** of new/changed entries (editor ≠ verifier) — reuse the
      `citation-audit` / `experiment-audit` pattern (fresh zero-context reviewer vs official sources).
- [ ] **Price-change verification** mechanized (must carry a fetch URL + date or BLOCK).
- [ ] **Deletion needs a machine-checked death-code** + churn ratio >40% → human (mechanize C4/C7).
- [ ] **Route-downgrade detection** (④/③ → ①/② must carry a CHANGELOG reason or BLOCK) (mechanize C2).
- [ ] **Quality-drift time series** live (star drift, freshness aging, added:removed, Discovery-output
      non-zero) — cross-period alerts catch slow rot.
- [x] **fail-closed retry** distinguishing transient network errors from real 404 (v0.5.1).

---

## 3. The staged path to a full closed loop · 全自动闭环分阶段路线

Each stage is independently valuable and strictly adds guardrails (P3-safe). Order matters: sense and
make the gate trustworthy **before** removing the human.

### Stage A — Make the gate a *fact* gate (close the integrity gap)
Root fix (P1, not a regex patch): a **machine-readable mirror block** per shard (YAML of
`{repo, stars, route, evidence_id}`) so the gate parses structured data and verifies **all** repos +
prices + routes deterministically. Add the C4 death-code check, C7 churn-ratio block, C2
route-downgrade block, and an **independent cross-model audit gate** (editor ≠ verifier). *Outcome:
the gate catches semantic/fact degradation, not just format.*

### Stage B — Close the measurement loop (add the sensor)
Three feedback signals → drive the next refresh's priorities (not its permissions):
- **Live-run telemetry** (`metrics/live-runs.jsonl`): when market-intel is actually used, append the
  guardrail verdicts it already computes (source `verified/dead/price_mismatch/fallback`, user
  corrections). The highest-value error signal, near-zero collection cost.
- **Drift time series** (`metrics/history.jsonl`): per-domain source counts, freshness, dead-rate,
  free/④ share, added:removed — computed by a deterministic script (P4: not LLM self-report).
- **Gate/discovery ledger**: rejected-candidate & hallucination-rate over time.
Feedback law: a domain's rising dead-rate → top scan priority next run; a source repeatedly flagged
dead in real runs → auto-*nominated* for deletion (still gated); a domain stagnant ≥2 periods →
forced deep Horizon scan. *Feedback changes where effort goes, never what's allowed to land.*

### Stage C — Close the actuator loop (tiered auto-merge, safely)
Move `verify_matrix.py` to **GitHub Actions as a required status check** so the *go/no-go authority
leaves the proposer* (fixes P4 at the infrastructure level — the local script can no longer self-
approve). Then:
- **Tiered autonomy** (deterministic classifier, not LLM self-label):
  - **T0/T1 auto-merge** — dead-link cleanup, star refresh, `last_verified` bump, pure ADD of a
    verified new row. Deterministically checkable + reversible. → CI-green + cooldown → auto-merge.
  - **T2/T3 human** — REPLACE top pick, non-dead deletion, major price change, NEW-DOMAIN/NEW-SKILL,
    SKILL.md/CONSTITUTION edits. Semantic/irreversible. → stays human (label withheld).
- **Safety net:** cooldown window (Discord "auto-merging in N h, reply STOP"), post-merge canary +
  health check, circuit breaker (N anomalies → drop to half-closed), kill-switch file, auto-rollback
  (`git revert`). Anti-pile-up: low-risk auto-merge clears the high-frequency noise so the live skill
  never ages just because a human is away; stale T2/T3 PRs escalate via Discord.

### Stage D — Close the meta loop (the protocol improves itself)
The deepest evolution: an **outer loop** (quarterly) that reviews run history + CHANGELOG +
human-edits + drift, finds protocol failure modes (flapping, stagnation, recurring hallucination,
repeated human edits = an unencoded rule), and proposes改进 to `refresh-protocol.md` /
`verify_matrix.py` / the prompt **itself** — reusing the `meta-optimize` skill's log-driven /
minimal-diff / cross-model-reviewed / PR-only / reversible骨架. Strictly guarded against the
death-spiral:
- **Inner/outer isolation** — inner loop edits data only; meta loop edits rules only (mutually
  exclusive scope guards). Neither can touch its own ceiling.
- **`META-CONSTITUTION.md` immutable core** — gate thresholds may only *tighten*, never loosen
  (STAR_TOL ↓ only, COVER drop ↓ only, checks add-only). Loosening requires explicit human sign-off.
  Tightening can be auto-proposed; loosening cannot.
- **Regression accountability** — each protocol change declares a target metric; if the next inner
  loops don't show improvement, auto-propose a revert.
- **Convergence signal** — Evolution Health Score: human-edit-rate ↓ (protocol is learning), protocol
  change win-rate >0.5, oscillation ≈0, loosening-proposals = 0. Two failed regressions in a row →
  pause meta loop, escalate to human.

---

## 4. Why this *is* the philosophy, not a detour · 这正是设计理念本身

- "Not full-auto yet — fix the gate first" **is P1** (fix the framing — a hollow gate — before adding
  autonomy on top of it).
- The staged order (sense → trust the gate → then remove the human) keeps **P3** (every stage only
  adds guardrails; autonomy is granted only where degradation is deterministically impossible).
- Moving go/no-go to CI so the proposer can't self-approve **is P4** (editor ≠ verifier) at the
  infrastructure level.
- The meta loop's immutable core (rules only tighten) is **P2 + P3 recursed one level up** — no
  automation can edit the ceiling above it, so the "loosen" half of the death spiral is structurally
  cut.

The generative test still governs every step: *does it fix the framing, or just patch a symptom?*
The bare-slug WARN net in v0.5.1 is explicitly an **interim patch**; the framing fix (mirror block) is
Stage A. We name it as a patch rather than pretend it's the cure — that honesty is P6.
