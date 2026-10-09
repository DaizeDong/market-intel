# Design Philosophy, Root-cause design, not incremental patching

> **设计理念, 从根本进行设计，而非小修小补**

The seven principles below govern source selection, delegation, evidence and maintenance.
They favor correcting the assumptions that cause repeated failures, with explicit checks for
the resulting behavior. A proposed feature must follow these principles or revise the affected
principle explicitly.

The initial design followed a 12-subagent tool survey and a five-subagent adversarial review.
That review rejected a second full-stack research engine because it would duplicate existing
workflows and conflict with their triggers. It confirmed the reconnect requirement for
`claude mcp add` and led to citation verification, source tiers and counter-evidence requirements.

> 以下七条原则指导选源、委托、证据和维护。重复出现的问题应检查其前提，并用明确的检查约束修改后的行为。
> 最初的设计经过 12 子任务工具调研和 5 子任务对抗评审，放弃了重复建设完整调研引擎的方案，
> 确认了 `claude mcp add` 的重连要求，并加入引用回验、源等级和反方检索要求。

---

## P1, Fix the framing, not the symptom · 改框架，不改症状

The initial survey favored paid APIs because its route taxonomy treated browser
automation as a last resort. The correction applied to all four barrier routes:
route ④ became a first-class option, preferred over paid APIs when it provides the
required data. Changing the selection rule addresses the bias across domains;
adding a few free tools to an otherwise unchanged list would not.

> 最初的调研偏向付费 API，原因是路线分类把浏览器自动化当作最后备选。
> 修正覆盖全部四条路线：路线 ④ 成为正式选项，能满足数据需求时优先于付费 API。
> 修改选源规则可以影响各个方向，而仅增加几个免费工具会保留原来的选择偏差。

## P2, Mechanisms, not intentions · 机制，而非意图

Encode required behavior in explicit constraints and fail-closed checks:
inject CONSTITUTION into each refresh, give `verify_matrix.py` final veto, and
isolate changes on a branch for review. Instructions to remember verification
or quarterly review are insufficient without these controls. Keep each check's
coverage explicit; a documented intention is not evidence of enforcement.

> 必要行为应落实为明确约束和失败时阻断的检查：每次刷新注入 CONSTITUTION，
> 由 `verify_matrix.py` 保留最终否决权，在分支上隔离修改并接受审查。
> 仅提醒核验或季度复核不足以执行规则；每项检查须说明实际覆盖范围。

## P3, Monotonic evolution against default decay · 对抗默认腐化的单调进化

Updates must control fabricated entries, silent deletions and quality drift.
Preserve declared guardrails, coverage thresholds, evidence dates and methodology,
and require checks and review before landing. The scheduled updater is retired;
the same constraints apply to manually initiated refreshes.

These controls detect specified regressions. Semantic improvement, complete
coverage and current provider readiness require separate evidence.

> 更新应防范编造条目、静默删除和质量漂移。保留已声明的护栏、覆盖阈值、
> 证据日期和方法要求，落地前通过检查与审查。定时更新已退役，手动刷新仍须遵守。
> 这些控制检测已定义的退化；语义质量提升、完整覆盖和当前服务可用性须另行举证。

## P4, Facts over recall, evidence over assertion · 实测胜于记忆，证据胜于断言

Source claims require direct evidence, such as `gh api` responses and official
pricing pages, checked independently of the editor. The model cannot substitute
recall or a plausible assertion for that evidence. A remembered star count can
look credible while being wrong; unverified values must remain visibly unverified.

> 来源论断需要 `gh api` 响应、官方定价页等直接证据，由编辑者之外的核验者检查。
> 模型记忆或听起来合理的断言不能替代证据。未经核验的值必须保留未核验标记。

## P5, Delegate the depth, own the seam · 委托深度，守住接缝

The skill owns commercial-source triage, installation guidance and research
quality requirements. Retrieval, verification and synthesis are delegated to
existing `deep-research` and `research-lit` workflows. This division limits duplicate
maintenance and trigger conflicts as the underlying tools change.

> 本 skill 负责商业来源分诊、安装指引和调研质量要求。检索、验证和综合委托给
> 已有的 `deep-research` 与 `research-lit` 流程，以减少重复维护和触发冲突。

### P5 hard limit · 接缝硬边界(2026-06-17 added against drift)

P5 守护"委托深度,守住接缝",但 v0.17-v0.21 这一连串往 `tools/` 加了 ~2000 行刷新基础设施
(discover.py / feedback-bump.py / verify_matrix.py / l0_verify.py / workflow_helpers.md /
2 个 workflow scripts),而 SKILL.md (真正的接缝) ~270 行。**量级倒置 7x**。

seam-drift fork 判 "PASS-but-fragile": 接缝守住了,但代码量级是漂移信号。为防未来安静越界,
立这条 hard limit:

```
P5 hard limit:
1. 任何 tools/<X>.py 或 scripts/<X>.py 只能在 REFRESH (月扫/周扫/手动 refresh) 时运行,
   不能被 SKILL.md Step 1-5 (用户查询路径) 加载/调用。
2. 用户研究查询时,fan-out 主路径 SHOULD 是 deep-research / research-lit;
   直接 Agent tool fan-out 仅当连了具体商业 MCP 时才用。
3. EVAL gate (若实施) 仅作为 refresh 期的 benchmark,不在 user-query 时运行。
4. shard-as-view compiler (若实施) 仅做 markdown 渲染,不做 retrieval。
5. 添加任何 user-query 路径上的新代码 → 必须 explicit revise this principle in PHILOSOPHY.md,
   或拒绝改动。**never quietly violated.**
```

判 P5 是否被违反的命令: 一行 grep, `grep -E "(import|load|from|require).*(discover|feedback-bump|l0_verify|verify_matrix|workflow_helpers)" SKILL.md`。
任何命中都是 P5 违反。每次 refresh sweep cleanup pass 跑一次。

### P5 amendment, config-side post-sweep automation (2026-06-17)

`market-intel-config/scripts/config-bridge.py` is **allowed** to represent user identity
(open signup pages, capture keys, configure tools) under these conditions:

1. It runs in the **companion-config repo**, not the skill repo. The skill seam is
   unchanged.
2. **No silent batch identity actions.** Every tool that requires user identity
   (signup / OAuth / key paste) **MUST** get explicit per-tool `y/N` consent in the
   running session before any browser open or key capture.
3. Tools that need NO user identity (public no-key MCPs: HN, GDELT, arXiv, etc.)
   MAY be auto-configured without prompt, those carry no identity risk.
4. **No auto-accept of paid plans.** Anything that incurs cost stays in
   `pending_registrations.md` with a manual flag.
5. All identity actions logged to `metrics/config-bridge.audit.jsonl` (when, what tool,
   what action taken, user-consent y/N).

This amendment widens P5 by one specific case (post-sweep config-bridge in the
**companion repo**) without softening the skill-repo limit. The grep check above is
unchanged: SKILL.md still must never import refresh-side scripts.


## P6, Honest boundaries, no silent degradation · 诚实的边界，拒绝静默退化

Report coverage gaps, known gate blind spots and fallback routes explicitly.
When a specialized source is unavailable, identify the replacement and its evidence
limits beside the affected claim. An apparently complete report that omits a
required dimension prevents the reader from assessing the conclusion.

> 明确报告覆盖缺口、检查器的已知盲区和备选路线。专业来源不可用时，在受影响的结论旁
> 标明替代来源及其证据限制；缺少必要维度的报告不能表现为完整结论。

---

## P7, Load budget is a design constraint · 加载预算是设计约束

`SKILL.md` is loaded on every invocation; references are loaded only when needed.
Keep required rules and their checks in SKILL, and put detailed procedures, rationale
and failure examples in the relevant reference. Avoid duplicating the same prose.

Earlier review found the complete secret-handling procedure in both SKILL and
`install-guide.md`, and one configuration-suggestion template in three files.
These copies increase loading cost and can diverge during maintenance.

Before moving a passage, check both conditions:

1. SKILL remains correct and actionable without loading the reference.
2. Removing the passage leaves the rule enforceable. Otherwise keep the necessary
   rule or procedure in the main workflow.

An incident or gotcha collection that only explains existing rules belongs in a
reference; preserve any cited IDs when moving it. A small skill may appropriately
keep all its content together. Keep essential failure-prevention invariants and
troubleshooting branches beside the step where they are needed. Measure the text
loaded per run before splitting or merging files.

The pinned Style kit's `style/tools/load_budget.py` measures always-loaded lines
and cross-file prose overlap using word shingles. Code, tables and links are
excluded from the overlap calculation. It blocks threshold violations, but compares
SKILL against references only; reference-to-reference duplication needs human review.


---

## The generative test · 生成式检验

Every future change to this skill, a new domain, a new tool, a new guardrail, must pass one test:

> **"Does this fix the framing, or just patch a symptom?"**

If it only patches a symptom, find the assumption underneath and fix that instead. Add tactics only
*after* the framing is right. This document outranks any individual feature; when a proposed change
conflicts with a principle here, the principle wins (or the principle is explicitly, deliberately
revised, never quietly violated).

> 本 skill 未来的每次改动,新方向、新工具、新护栏,都必须通过一个检验：
>
> **"这是在改框架，还是只在打补丁？"**
>
> 如果只是打补丁，去找它底下的假设、改那个。框架对了*之后*再加战术。本文件的优先级高于任何单个功能；
> 当某个改动与这里的原则冲突时，原则胜出（或者显式、审慎地修订原则,绝不悄悄违反）。
