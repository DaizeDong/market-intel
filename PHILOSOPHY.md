# Design Philosophy — Root-cause design, not incremental patching

> **设计理念 —— 从根本进行设计，而非小修小补**

This is the organizing principle of market-intel. Every feature, every guardrail, every refactor in
this repo exists because of the six principles below. They are not after-the-fact rationalizations —
they are the lens that produced each decision, and the test every future change must pass.

> 这是 market-intel 的统领原则。本仓库里的每个功能、每道护栏、每次重构，都源于下面六条。它们不是事后
> 总结的漂亮话，而是**催生了每个决定的透镜**，也是未来每次改动都必须通过的检验。

**The one-sentence version:** when something is wrong, we change the assumption underneath it, not
the symptom on top of it. A patch leaves the bad default in place; fixing the framing changes every
decision that follows.

> **一句话：** 出了问题，我们改的是它底下的假设，而不是它表面的症状。补丁让错误的默认值继续存在；
> 改框架则会改变其后的每一个决定。

---

## P1 — Fix the framing, not the symptom · 改框架，不改症状

- **The patch:** the tool survey came back paid-API-biased, so… add a few free tools to the list.
- **The root:** ask *why* it was biased. The barrier-route taxonomy itself was wrong — it treated
  browser-automation as a last-resort footnote. So we **reclassified all four barrier routes** and
  promoted route ④ (act-like-human browser) to a first-class option preferred over paid APIs.
- **Why it matters:** the patch would have left the wrong default ("reach for a paid API") in place.
  Fixing the framing changed how *every* domain selects a source, forever.

> - **补丁：** 调研结果偏向付费 API，那就……往清单里加几个免费工具。
> - **根本：** 追问它*为什么*偏。是"信息壁垒路线"这个分类本身错了——它把浏览器自动化当成最后兜底的脚注。
>   于是我们**重构了全部四条壁垒路线**，把路线④（模拟人浏览器）提升为优先于付费 API 的一等公民。
> - **为何重要：** 补丁会让"优先掏钱买 API"这个错误默认值留着；改框架则永久改变了每个方向的选源逻辑。

## P2 — Mechanisms, not intentions · 机制，而非意图

- **The patch:** write "remember to verify every repo" and "remember to refresh quarterly" in the
  docs, and hope it happens.
- **The root:** encode the right behavior as an **enforced, fail-closed mechanism** — a CONSTITUTION
  injected as hard constraints, a deterministic gate (`verify_matrix.py`) with final veto, branch +
  PR isolation. Correct behavior is *structural*, not voluntary.
- **Why it matters:** intentions decay, docs get skipped, and an LLM forgets between runs. A gate
  does not. You cannot rely on anyone — including the model, including future-you — to "remember."

> - **补丁：** 在文档里写"记得核实每个仓库""记得每季度刷新"，然后指望它发生。
> - **根本：** 把正确行为编码成**强制的、fail-closed 的机制**——注入为硬约束的宪法、有最终否决权的确定性
>   闸门（`verify_matrix.py`）、分支+PR 隔离。正确行为是*结构性*的，不靠自觉。
> - **为何重要：** 意图会衰减、文档会被跳过、LLM 跨运行会遗忘。闸门不会。不能指望任何人——包括模型、
>   包括未来的你——去"记得"。

## P3 — Monotonic evolution against default decay · 对抗默认腐化的单调进化

- **The patch:** set up an auto-updater and trust it stays good.
- **The root:** recognize that **the default trajectory of any auto-updater is decay** — hallucinated
  entries, silent deletions, drifting quality. So design it so the system can *only move forward*:
  guardrails only accumulate (never relax), coverage can't drop past a threshold, time only advances,
  methodology is preserved, and every change must prove improve-or-hold before it can land.
- **Why it matters:** "evolves automatically" is the easy promise; "cannot silently degrade" is the
  hard guarantee — and the only one worth making.

> - **补丁：** 搭个自动更新，然后相信它会一直好。
> - **根本：** 认清**任何自动更新的默认走向都是腐化**——幻觉条目、静默删除、质量漂移。于是设计成系统
>   *只能向前*：护栏只增不减、覆盖度不得跌破阈值、时间只前进、方法论被保留、每次改动落地前必须证明
>   "变好或持平"。
> - **为何重要：** "自动进化"是容易的承诺；"不会静默退化"才是难的保证——也是唯一值得做的保证。

## P4 — Facts over recall, evidence over assertion · 实测胜于记忆，证据胜于断言

- **The patch:** ask the LLM to "be accurate."
- **The root:** the deepest failure mode of an LLM system is *confident fabrication*. So truth must
  come from an **independent deterministic source** (`gh api`, the official pricing page), verified by
  a check the model cannot talk its way past — and the editor is never its own verifier.
- **Why it matters:** a star count recalled from training is plausible and wrong. The whole value of
  a source matrix is that it's *trustworthy*; one fabricated entry poisons that.

> - **补丁：** 叮嘱 LLM "要准确"。
> - **根本：** LLM 系统最深的失效模式是*自信地编造*。所以真相必须来自**独立的确定性来源**（`gh api`、
>   官方定价页），由一个模型无法用话术绕过的检查来核验——且编辑者永远不是自己的核验者。
> - **为何重要：** 凭训练记忆回忆的 star 数，听起来合理却是错的。源矩阵的全部价值在于*可信*；一条编造
>   就毁掉它。

## P5 — Delegate the depth, own the seam · 委托深度，守住接缝

- **The patch:** build a full research engine (yet another deep-research clone).
- **The root:** find the *single irreducible thing only this skill can do* — commercial-source triage
  + install guidance + quality guardrails — and **delegate** retrieval/verification/synthesis to the
  engines that already exist (`deep-research`, `research-lit`). Own the seam, not the depth.
- **Why it matters:** less surface area means less to maintain, less to rot, and no trigger fights.
  Reinventing a capability is how a project accretes liability.

> - **补丁：** 造一个完整的调研引擎（又一个 deep-research 克隆）。
> - **根本：** 找到*这个 skill 唯一无可替代的那件事*——商业源分诊 + 安装引导 + 质量护栏——把检索/验证/
>   合成**委托**给已存在的引擎（`deep-research`、`research-lit`）。守住接缝，而非深度。
> - **为何重要：** 表面积越小，越少维护、越少腐化、越无触发冲突。重造已有能力，是项目累积负债的方式。

## P6 — Honest boundaries, no silent degradation · 诚实的边界，拒绝静默退化

- **The patch:** present fallback web results as if they were first-class data.
- **The root:** surface every limitation explicitly — coverage gaps, the v1 gate's known blind spot,
  a fallback-source flag when a barrier source was unavailable. **Degradation that is visible can be
  fixed; degradation that is hidden compounds.**
- **Why it matters:** a report that looks complete while quietly missing a dimension is worse than one
  that says "this part is uncovered." Honesty is a correctness property, not a courtesy.

> - **补丁：** 把兜底的网页结果当成一等数据呈现。
> - **根本：** 显式暴露每个局限——覆盖缺口、v1 闸门的已知盲区、壁垒源不可用时的兜底标记。**可见的退化
>   能被修复；隐藏的退化会累积。**
> - **为何重要：** 一份看起来完整、实则悄悄缺了一个维度的报告，比一份明说"这部分没覆盖"的更糟。诚实是
>   一种正确性属性，不是礼貌。

---

## P5 hard limit · 接缝硬边界(2026-06-17 added against drift)

P5 守护"委托深度,守住接缝"——但 v0.17-v0.21 这一连串往 `tools/` 加了 ~2000 行刷新基础设施
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

判 P5 是否被违反的命令: 一行 grep —— `grep -E "(import|load|from|require).*(discover|feedback-bump|l0_verify|verify_matrix|workflow_helpers)" SKILL.md`。
任何命中都是 P5 违反。每次 refresh sweep cleanup pass 跑一次。

---

## The generative test · 生成式检验

Every future change to this skill — a new domain, a new tool, a new guardrail — must pass one test:

> **"Does this fix the framing, or just patch a symptom?"**

If it only patches a symptom, find the assumption underneath and fix that instead. Add tactics only
*after* the framing is right. This document outranks any individual feature; when a proposed change
conflicts with a principle here, the principle wins (or the principle is explicitly, deliberately
revised — never quietly violated).

> 本 skill 未来的每次改动——新方向、新工具、新护栏——都必须通过一个检验：
>
> **"这是在改框架，还是只在打补丁？"**
>
> 如果只是打补丁，去找它底下的假设、改那个。框架对了*之后*再加战术。本文件的优先级高于任何单个功能；
> 当某个改动与这里的原则冲突时，原则胜出（或者显式、审慎地修订原则——绝不悄悄违反）。
