# Refresh protocol — keep the source matrix current

This skill's value is a curated source matrix. Tools, prices, and barriers in the commercial-data
space move fast (every survey round found acquisitions, price changes, and dead tools within
months). Re-run this protocol periodically to keep `domains/`, `volatile/pricing-install.md`, and
`sources-index.md` accurate.

## Cadence

**v0.17.0 overhaul** — the old "quarterly default" was a v0 residue from when the matrix had
~30 entries. With 155+ tool docs and a `live-runs.jsonl` feedback loop, the default is now
**monthly**. Quarterly is reserved for the broad horizon scan.

- **Weekly** (light pass, Discovery angles ①②④ only — i.e. just discover-new, no full
  re-verify, no shard rewrite): `crypto-defi`, `browser-automation`, `frontier-research`,
  and the new meta-domain `mcp-ecosystem`. These move on a sub-week timescale (patchright →
  camoufox → nodriver reactive-detection turnover happened inside 4 weeks; new MCP releases
  daily). Weekly pass writes to `discovery-state.md` candidate inbox; full Verify & Diff
  defers to the monthly sweep.
- **Monthly** (full sweep): everything else. Was quarterly pre-v0.17.0.
- **Quarterly**: only the **Horizon scan H1-H4** (cross-domain trend / new-territory /
  new-research-angle discovery). Per-domain monthly already catches new tools in known
  domains; horizon-scan is the place to catch new *categories* of work.
- **Opportunistic**: a dead/changed tool encountered in a real run → fix that shard
  immediately, log to `live-runs.jsonl`, do not wait for the cadence.

If `live-runs.jsonl` flags a domain as `hot` in Step -1 of a sweep, that domain's
Discovery budget for the sweep is **doubled** (more angles, more candidates) regardless
of its cadence tier.

## Procedure (full sweep)

每次自动运行分两阶段：**发现阶段（Discovery，找新东西）** + **核实/差分阶段（Verify & Diff，旧条目校验
+ 落库）**。旧版协议只做后者，会停滞——必须先跑发现阶段主动挖掘更前沿的工具，再用准入门槛过滤。

> 发现阶段的完整规则见下方 **「Discovery phase（前沿发现 + 质量筛选）」** 一节。它产出一个
> 「候选池（candidate pool）」，核实/差分阶段只处理通过准入门槛的候选 + 旧条目复检。

-1. **Step -1 — 消费 `metrics/live-runs.jsonl`（必跑，v0.17.0 起）。** 在 Horizon scan 之前,先读
    `metrics/live-runs.jsonl` 自上次 refresh 以来的所有条目（按 `ts` 过滤;首次跑取最近 90 天）,按
    `outcome` 分桶:

    | outcome | 含义 | 该轮的处置 |
    |---|---|---|
    | `dead` | 真实使用中工具死了 | 该工具所在 domain 升级为 **hot**(本轮 Discovery 预算 ×2);该工具该轮必复检,八成进入 C4 墓碑 |
    | `barrier_found` | 命中新付费墙/captcha/反爬 | 该 domain 升级为 hot;启动 D-PRICE / D-TOS / D-CAPTCHA 评估;考察是否到达"第 3 次同档 D-PRICE → 触发 ROADMAP brokerage transport"(P2 触发条件) |
    | `coverage_gap` | 用户问题用现有矩阵答不上 | 该 domain 升级为 hot;Discovery 时显式带"为什么这个 gap 没被现存工具覆盖"角度 |
    | `price_mismatch` | shard 排名/价格与真实不符 | 该工具该轮必复检 + 改 shard,但**该 domain 不一定升 hot**(可能是缓慢漂移) |
    | `verified` | 工具被真实使用且工作 | **cleanup pass 阶段自动把对应 `tools/<slug>.md` 的 `## Last verified` 推进到当月** —— "诚实原则"下,真用过即算复检,STALE 闸门豁免 |
    | `user_correction` (非 null) | 用户人工修正 | 最高权重信号,直接覆盖任何 shard 推断,该条目复检时 quote 用户原话 |

    输出: hot-domains 清单(本轮 Discovery 这些 domain 的角度数 + 候选数翻倍)、必复检 slug 列表、
    cleanup-auto-bump 清单。**此步是后续所有步骤的优先级输入**,不是装饰。

0. **跑 Horizon scan**（全量扫必跑）：按下方 Horizon scan 规则做跨域趋势扫描，找**已有 13 域之外**的新
   territory / 新工具品类 / 新调研角度，产出新角度提案清单（FOLD 项并入下一步；NEW-DOMAIN/NEW-SKILL 进 PR）。
1. **跑发现阶段**：按下方 Discovery phase 规则，对每个域并行盲扫多个发现源，产出候选池
   （每个候选附带：来源、score、对现有首选的「新增/替换/不收录」裁决 + 理由）。
2. **Apply the same quality guardrails** as a normal run (verify each claimed tool exists and the
   price against its official site — do not trust a subagent's recalled pricing).
3. **Incremental edit, don't rewrite**: for each domain, update only changed rows in
   `domains/<domain>.md`; move/refresh price+install lines in `volatile/pricing-install.md`; bump
   that section's `last_verified: YYYY-MM`. Update `sources-index.md` only if a domain's top pick
   changed.
3b. **Keep the L2 per-tool docs + install guide in sync** (added v0.10.0): for every tool **ADDed or
   REPLACEd**, create/update `reference/tools/<slug>.md` (per-tool how-to: install + auth + usage +
   踩坑, each fact gh-api/official-site verified) and add its row to `reference/tools/index.md`. For
   every tool **deleted/tombstoned**, mark its doc `⚠ Avoid (dead)` (never silent-delete) and drop its
   index row. Touch `reference/install-guide.md` only when install *mechanics* change (a new
   prerequisite, an HTTP/stdio transport shift) — per-tool commands live in the tool doc +
   `pricing-install.md`, not the overview. **Also re-verify the swept domain's EXISTING docs (not just
   changed ones) and bump each `## Last verified` only when actually re-checked** — full doctrine in
   **§文档层防腐协议 (R1–R4)** below. The gate enforces this layer: **TOOLS** (index↔doc, BLOCK) +
   **REPO/STAR** verify repos cited inside tool docs (a hallucinated doc repo 404s → BLOCK) +
   **FRESH** rejects future doc dates + **STALE** WARNs docs unchecked >9mo + **DOCCOVER** WARNs a live
   shard repo with no doc (catches lost tracking).
4. **Record the diff** in `CHANGELOG.md` at the repo root (date + per-domain added/removed/changed),
   and bump the plugin `version` in `.claude-plugin/plugin.json`.
5. **Commit + push** to whichever Git remote this matrix repo lives at.

## Discovery phase（前沿发现 + 质量筛选）

发现阶段的目标：**主动发现新出现的、可能比现状更前沿/更优的工具·MCP·开源仓库·技术路线**，并在它们进库
之前用「去炒作 + 去低质」门槛过滤掉垃圾。原则一句话：**广撒网发现、严准入筛选、对比式裁决、宁缺毋滥**。
发现阶段不直接改任何 shard——它只产出一个**候选池**交给核实/差分阶段。

发现阶段读 `domains/<domain>.md` 拿到该域的**现有首选 + 现有条目 + 各条目的 barrier route（①②③④）**，
作为对比基线；下面所有「替代升级」裁决都是相对这个基线做的。

### D1. 发现源清单（discovery surfaces）

按「覆盖什么 / 怎么查 / 信号质量」三栏组织。每个域至少覆盖 A/B/C 三大类发现源（注册中心、GitHub、社区）；
能替代付费的免费方案（route ④/③）要专门跑 D 类。

**A. MCP 注册中心**（覆盖：现成可即插即用的 MCP server）
| 发现源 | 怎么查 | 信号质量 |
|---|---|---|
| smithery.ai | 按域关键词搜 + 看「新上架 / 安装量排序」 | 中。安装量是弱采用度信号，但有刷量；很多是套壳 |
| glama.ai/mcp | 关键词搜 + 它给的质量评分/排行 | 中。有自带质量分可参考，仍需复核 |
| mcp.so | 关键词搜 + 分类浏览 | 中低。收录广但噪声大、停更多 |
| pulsemcp.com | 关键词搜 + 「Newest」时间序 + 周报 newsletter | 中高。**时间序最适合「自上次以来的新增」**；周报已做一轮人工筛 |
| registry.modelcontextprotocol.io（官方 registry） | 官方索引/API 查 | 高（权威来源）。但收录滞后、覆盖不全 |
| mcp.apify.com / Apify Store | 搜 actor + 看运行量、评分、维护者 | 中高。actor 有真实运行量与定价，采用度信号较硬 |

**B. GitHub**（覆盖：开源仓库、自托管/浏览器路线、有无现成 MCP wrapper）
| 发现源 | 怎么查 | 信号质量 |
|---|---|---|
| Trending（按语言/按周） | github.com/trending 按域语言筛 | 中。能抓「正在起势」，但易被运营/营销带节奏 |
| 新建高星仓库 | GitHub Search API：`created:>last_verified stars:>N`，按 star 排序 | 中高。**「新建 + 已聚星」是前沿性最强信号之一**，但要查刷量 |
| 近期高活跃 | Search：`pushed:>last_verified` + 关键词，按更新排序 | 中。抓「老仓库突然加速」 |
| awesome-lists | 搜 `awesome <domain> mcp` / `awesome <platform>`，取近期 commit 的清单的 diff | 中高。人工策展 + 看清单本身是否在维护 |
| topic 搜索 | 按 topic（`mcp-server`、`web-scraping`、`twitter`…）+ 排序 | 中。覆盖广，需配合活跃度过滤 |
| 现有首选仓库的 network | 看现有 top pick 的 forks/「used by」/「dependents」与 release notes | 高。能发现「替代品」「更活跃的 fork」「上游已弃用」 |

**C. 社区讨论 / 信号面**（覆盖：真实采用、口碑、踩坑、是否炒作）
| 发现源 | 怎么查 | 信号质量 |
|---|---|---|
| Hacker News | Algolia HN API 搜域关键词 + 工具名，看 points/评论质量 | 高。**评论区是去炒作的金矿**——HN 会直接拆穿 vaporware/套壳 |
| Reddit | 对应 subreddit（r/webscraping、r/SEO、r/algotrading…）搜近月帖 | 中。真实使用反馈多，也有营销号；看评论而非楼主 |
| X / 推特 | 复用本 skill 的 x-twitter 源搜工具名 | 中低。**发现力强但炒作最重**，只当线索不当证据 |
| Product Hunt | 按域类目看近期 launch + upvote/评论 | 中低。营销驱动，upvote 可买；只取「真有人用」的信号 |

**D. 各工具 changelog / release（覆盖：现有条目与候选的真实维护节奏、能力变更、定价变更）**
| 发现源 | 怎么查 | 信号质量 |
|---|---|---|
| GitHub Releases / CHANGELOG | 现有首选 + 候选仓库的 release 频率与最近一条 | 高。维护节奏的硬证据，停更/加速一眼可见 |
| 官方 pricing / blog | 抓官网定价页 + 更新日志（验证价，不信 subagent 记忆） | 高（L1）。**barrier-route 漂移的权威来源**（API 转付费、免费层砍量） |

### D2. 多模态盲扫策略（multi-angle blind scan）

对**同一个域**派多个 subagent，**各自只从一个角度扫、互相不知道对方结论**（盲扫，减少互相锚定的盲区），
最后由 combiner 去重合并。每个域的盲扫角度（按域繁忙度取 2–4 个，受 Budget 上限约束）：

- **角度①「注册中心视角」**：只扫 A 类（MCP 注册中心）。问：该域有哪些新上架/高安装量的 MCP？
- **角度②「GitHub 视角」**：只扫 B 类。问：该域有哪些新建高星 / 近期高活跃 / 有现成 MCP wrapper 的仓库？
- **角度③「社区视角」**：只扫 C 类。问：HN/Reddit 最近在推荐/吐槽哪些该域工具？口碑与踩坑是什么？
- **角度④「免费替代付费视角」**（route ④/③ 专扫，**最高价值**）：问：有没有新的免费 OSS / 浏览器
  act-like-human 方案，能替代本域当前那个**付费**首选（点名现有 top pick 与其价格）？要求它直接对标
  现有付费源的能力缺口。

盲扫纪律：每个 subagent **只准报自己角度查到的**，禁止脑补其他角度；禁止编造仓库名/star 数——所有数字
必须来自 GitHub API / 注册中心页 / changelog 的**实抓**，附 URL。返回结构化候选单（见 D5）。

### D3. 评分（前沿性 × 质量，满分各维度后取加权）

对每个候选打分。**前沿性与质量是两个轴，缺一不可**——只前沿不优质 = 炒作；只老牌不前沿 = 停滞。
维度（每项 0–2 分，标注证据 URL，无证据该项记 0 并标 `unverified`）：

| 维度 | 0 | 1 | 2 | 反陷阱注记 |
|---|---|---|---|---|
| **活跃度** | 停更 >12 月 / archived | 6–12 月内有提交 | 近 3 月有 release/commit 且节奏稳 | 看**提交节奏**不只看最后一次；一次性 dump 仓库≠活跃 |
| **采用度** | 仅作者自用 | 有少量真实用户/第三方提及 | 多个独立来源（HN/Reddit/dependents）在真实用 | **高 star ≠ 采用**——查 star 时间曲线，一夜暴涨=刷量嫌疑 |
| **现成 MCP** | 无、需自己包 | 有社区 MCP 但维护存疑 | 有维护良好的官方/社区 MCP | 有现成 MCP 降低接入成本，但别为「有 MCP」牺牲数据质量 |
| **barrier 路线优劣** | 比现状更脆/更易封/更贵 | 与现状同级 | **比现状更优**（更免费/更稳/更难被封/拿到 API 藏的字段） | route ④ 免费且拿到更全字段 → 加分；纯套壳付费 API → 不加分 |
| **成本** | 比现状贵且无新能力 | 与现状相当 | 免费或显著更便宜且能力不降 | 「免费但要自备账号+代理+承担封号」要在 risk 栏写清，不算白嫖 |
| **是否真比现有条目更好** | 不如现有首选 | 与现有条目互补（覆盖新子能力） | 在现有首选的核心能力上**实测/有证据更强** | **这是裁决核心**——没有「比现状更好」的证据，再新也只是「新增候选」不是「替换」 |

**入池门槛**：总分需达阈值**且**「活跃度」「barrier 路线优劣」两项均 ≥1，**且**至少有 1 个独立第三方采用
证据（采用度 ≥1）。任一不满足 → 不入池（理由记录在 reject log，避免下次重复发现同一垃圾）。

**两个硬陷阱明令**：
- **「新 ≠ 好」**：新建仓库若采用度=0 且无现成可用形态，只标记为 *watchlist*（观察名单），不进候选池，
  留待下一轮看是否成势。前沿性高但未被验证的，**不收录、只观察**。
- **「高星 ≠ 适用」**：star 高但 (a) 与本域能力不匹配、或 (b) 停更、或 (c) star 曲线异常暴涨 → 直接降级。
  适用性以「能不能在本域 barrier route 下真正拿到我们要的数据」为准，不以 star 为准。

### D4. 去炒作 / 去低质（reject filters，宁缺毋滥）

任一命中即**拒收**（记入 reject log，附命中理由 + 证据 URL）：

- **Vaporware**：只有 landing page / waitlist / demo 视频，无可用仓库或可调用 endpoint。
- **营销号吹捧无实证**：发现仅来自 Product Hunt/X 软文，HN/Reddit 无独立用户复述其真实效果。
- **star 灌水嫌疑**：star 曲线短期陡升、star 数与 issue/PR/fork/contributor 数严重背离（高星零 issue 零 fork）、
  贡献者高度集中于单账号或新号集群。
- **停更/弃坑**：最后提交 >12 月、archived、README 标 deprecated、或上游已迁移到别处而此仓库是旧壳。
- **套壳工具**：只是对某付费 API 的薄包装却不揭示底层依赖/不增任何能力/不省成本——尤其当它把别人的
  免费 OSS 重新包装后收费。套壳但**真降低接入成本或补了能力**的可保留，但要在条目里点明底层依赖。
- **来源单一不可复核**：所有证据都来自同一发布方（L3），无 L1/L2 佐证 → 不够格做首选，最多 watchlist。

发现阶段同样遵守 SKILL.md 的核实门槛：**所有 star/价格/能力数字必须实抓带 URL，禁止凭 subagent 记忆。**

### D5. 「替代升级」逻辑（candidate → 裁决）

每个入池候选必须带一条**相对现有 shard 基线**的裁决，三选一，且**必须给对比理由**（缺理由的裁决无效）：

- **【新增 ADD】**：覆盖了现有条目没有的子能力 / 新 barrier route，但不取代现有首选。
  理由格式：`补足 <现有条目缺的能力>；与现有首选 <X> 互补，不替换`。
- **【替换首选 REPLACE】**：在现有首选的**核心能力**上更优，且 D3「是否真比现有更好」=2。
  理由格式：`相较现首选 <X>：在 <核心能力/成本/路线> 上更优（证据 URL）；劣势 <…>；建议把首选改为本候选，
  旧首选降为备选`。**REPLACE 门槛最高**：必须有能力对比证据（最好实测/第三方对比），不能仅凭「更新更火」。
- **【不收录 SKIP / WATCH】**：未过门槛 → SKIP（记 reject log）；前沿但未验证 → WATCH（记 watchlist，下轮复看）。

裁决产物交给核实/差分阶段：ADD/REPLACE 经独立核实后才落 shard；REPLACE 还需同步改 `sources-index.md` 的
top pick 并在 CHANGELOG 写明「why replaced」。WATCH/SKIP 不动 shard，但维护在 refresh-protocol 旁的
`volatile/discovery-state.md`（watchlist + reject log，带发现日期），让后续运行不重复造轮子、也能追踪成势。

### D6. 发现阶段返回的候选单结构（structured candidate unit）

每个盲扫 subagent 对每个候选返回（沿用 SKILL.md 的字段化要求，禁自由散文）：

```
{ name, repo_or_registry_url, domain, discovery_surface(A/B/C/D + 具体源),
  barrier_route(①②③④), has_ready_mcp(bool + url),
  evidence: { stars, star_trend_note, last_commit_date, release_cadence, adoption_signals[url...], price[url] },
  score: { activity, adoption, mcp, route, cost, better_than_existing },  // 各 0–2 + 证据 url
  reject_hits[],                  // 命中的 D4 过滤项（空=通过）
  verdict: ADD|REPLACE|WATCH|SKIP,
  vs_current_top_pick: "对比理由（REPLACE 必填能力对比证据）" }
```

## Horizon scan（发现新角度 / 新域 —— 与时俱进，不只完善已有）

Discovery phase 在**已知 13 个域内**找更好的工具。但工具世界会长出**全新的域和调研角度**——新平台崛起、
新一类工具出现、新的调研方法论成形、API 政策剧变打开/关闭一整条路线。只完善已有 = 框架被冻结在过去。
Horizon scan 是 PHILOSOPHY.md **P1（改框架，不只改症状）应用到本 skill 自己的范围上**：定期问"地图本身
是不是该长大了？"，并在适当时**新增子域 / 子 skill**。

**何时跑：** 每次全量扫（Jan/Apr/Jul/Oct）必跑；月度轻量扫做一个 10 分钟的"当月脉搏"快照即可。

### H1. 扫什么（跨域、看趋势，而非看单个工具）
- **当月发生了什么**：本月该领域的大事件——平台 API 政策变动、重大收购、某类工具突然爆发、某条壁垒
  路线被打开或封死。来源：HN/Reddit 月度热帖、各大框架的 release/blog、MCP 注册中心的**新类目**。
- **新平台 / 新数据territory**：出现了现有 13 域装不下的新数据源吗？（如一个新社交平台成气候、一种新的
  另类数据市场、一个新的内容形态）。
- **新一类工具**：出现了**全新品类**的工具/MCP 吗？（不是"又一个 X 抓取器"，而是"一种以前不存在的能力"，
  如某种新的 agent 记忆服务、实时多模态采集、新的反检测范式）。
- **新调研角度 / 方法论**：有没有**更新颖的"做调研"的方式**本身？（如一种新的交叉验证手段、一种新的
  信号源、一种把多个域串起来的新工作流）——这是用户明确要的"比较新颖的调研角度"。

### H2. 决策：折叠 / 新增子域 / 新增子 skill（默认最小，门槛递增）
对每个发现的新角度，三选一，**必须给理由**：
- **【折叠 FOLD】（默认）**：作为新行/新路线并入某个现有域。绝大多数新工具属于这一类。
- **【新增子域 NEW-DOMAIN】**：仅当它是一块**与现有 13 域都不同的独立数据territory**、且**有 ≥3 个真实
  可用源**、且**有反复出现的相关性**（不是一次性热点）。落地 = 新建 `domains/<x>.md` + 加 `sources-index.md`
  一行（保持 index↔shard 一致，否则闸门 STRUCT 拦截）+ CHANGELOG 写明"为何它值一个新域"。
- **【新增子 skill NEW-SKILL】（最高门槛，需人类拍板）**：仅当该角度需要自己的**触发词 + 工作流 + 分诊
  逻辑**，已超出"源矩阵一行"能承载的范畴（如它本身就是一套独立的多步流程）。自动运行**不得**自建新 skill，
  只能写入提案交人审。

### H3. 防膨胀门槛（用 P3 约束 P1 —— 范围增长不等于腐化）
"与时俱进"绝不等于"什么新东西都加一个域"。膨胀本身就是一种退化。所以：
- **新 ≠ 需要一个新域**：新角度先进 `volatile/discovery-state.md` 的 **new-angle watchlist**（带发现日期），
  **至少跨 2 次扫仍持续相关**才可提名升级为新域——一次性炒作会自然过期。
- **必须过生成式检验**（PHILOSOPHY.md）："这是在改框架（真的有一块没被覆盖的territory），还是只在打补丁
  （其实塞进现有域更对）？" 倾向折叠；提名新域/新 skill 的举证责任在提名方。
- **结构性变更永远走人审**：新增域/子 skill 是高权限结构变更，自动运行只产出**提案**（写入 watchlist +
  CHANGELOG 草案 + PR 描述），由人类批准才落地；绝不自动新建并直接合并。

### H4. 产出
Horizon scan 产出一个 **新角度提案清单**（每条：发现的角度 + 来源证据 URL + FOLD/NEW-DOMAIN/NEW-SKILL
裁决 + 理由 + 是否已在 watchlist 复现）。FOLD 项交给正常的核实/差分阶段；NEW-DOMAIN/NEW-SKILL 项进 PR 等
人审。无新角度时显式写"本月无新territory，已扫 H1 四类"——不留白、不假装。

## Budget

Treat a full sweep like a `deep` run: cap at 12 subagents, single round each, plus verification.
Don't let a refresh balloon — it's a diff against an existing matrix, not a from-scratch survey.

**发现阶段的预算分配**：13 个域 × 多角度盲扫会爆 subagent 上限，因此**分波而非全量并行**：每波取一个
「域 × 角度」批，受 depth 的 max-subagents 上限约束；**优先把预算给波动快的域**（x-twitter / web-scraping /
social-publishing / crypto-defi / browser-automation，见 Cadence）和**角度④（免费替代付费）**——这两类
ROI 最高。其余域每轮至少跑角度②（GitHub）+ 角度③（社区）两个角度做最小覆盖。combiner 合并候选后再进
核实，主 agent 不读 subagent 的原始页面 dump，只读候选单。

## 防退化协议（强制 —— 保证只进化不退化）

无人值守更新有退化风险（幻觉仓库、误删好源、填错价、丢方法论）。原则：**LLM 只提议，确定性闸门否决；
坏更新进不了 main；护栏只增不减。** 每次自动运行必须遵守：

0. **先读 `CONSTITUTION.md`（仓库根），逐条作为硬约束遵守 C1–C10。** 自动运行**不得修改**宪法/`tools/`。
1. **只在 `refresh/<date>` 分支工作，绝不直推 main。**
2. **事实一律 API 实测**：每个收录/改动的仓库用 `gh api repos/<o>/<r>` 核实存在 + 真实 star（写 API 返回的
   真值，标 `(NNk★)` 紧贴仓库名）；价格核官网。**禁止凭记忆**。核实不了 → 不收录（C1/C6）。
3. **删除是高权限操作**：必须带死亡码 + 证据（C4：D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED）；死条目移入
   "Avoid (dead)" 墓碑行而非静默删除；机器判活的源默认不可删。
4. **增量编辑，不重写**（C7）；大改（>40% 或整表替换）转人审。
5. **编辑后跑确定性闸门**：`python tools/verify_matrix.py`（检查 STRUCT/REPO 存在性/STAR 容差/FRESH 时间
   单调/METH 方法论完整/COVER 防批量误删/CONST 宪法未改）。**任一 BLOCK → 回滚、不提交、Discord 告警、停。**
   闸门有最终否决权；LLM reviewer 只能更保守，不能把 FAIL 改成 PASS。
6. **全绿才落地**：写 CHANGELOG + 升 version + commit 到分支 + push + `gh pr create`（**开 PR，不自动 merge**）
   + Discord 通知人审。合并后由 `tools/deploy_skill.sh` 同步到生效版 skill（先在 main 上重跑闸门才部署）。

> 调度脚本 `the scheduled refresh script` 已实现 1/5/6 的编排骨架与 scope guard（拒绝越界改动）。
> v1 闸门覆盖协议强制的格式（github URL + star 标注）；裸 slug 无标注的漏检由 ROADMAP 的「机读镜像块」补全。

## 文档层防腐协议（anti-rot）—— 保证 L2 逐工具文档不因迭代而失效或丢追踪

L2 逐工具文档（`reference/tools/<slug>.md`）+ L0 `install-guide.md` 是 v0.10.0 起的一等资产。迭代最易在
这层出三种腐化：**孤儿文档 · 静默过期 · 丢追踪**。三道防线兜底：**确定性闸门否决 + 协议强制 + 周期独立审计**。

### R1. 增删工具 = 四文件原子操作
新增一个工具 ⇒ 必须**同时**落：(a) 分片行 `domains/<域>.md`、(b) 索引行 `tools/index.md`、(c) 文档
`tools/<slug>.md`、(d) 机读清单 `tools/registry.json` 一条 `{slug,name,kind,repo,domain,top_pick}`。
绝不允许只改其一。闸门三网兜底：**REGISTRY**（registry↔index↔doc 三方一致，**含非仓库 SaaS**，不符即
BLOCK——这是 SaaS 工具的确定性追踪网）+ **TOOLS**（index↔doc，缺即 BLOCK）+ **DOCCOVER**（活跃分片仓库无
文档即 WARN）。`registry.json` 是工具清单的**权威来源**，由 `index.md` + 文档**派生生成**（再生成脚本见
CHANGELOG 0.10.2）——改完工具后重跑该脚本即可保持同步，不必手编。

### R2. 扫到一个域，复检该域的全部文档（不止变更项）
旧步骤 3b 只更新「被改动」工具的文档，不变的会静默腐化。补足：每次 sweep 对**所扫域**的每份
`tools/<slug>.md` 复检——`gh api` 复核仓库存活 + star、抓官网复核头条价格——**仅在真正复检后**才把
`## Last verified: YYYY-MM` 推进到当月。闸门 **STALE**（>9 月未检 → WARN，按最旧优先点名复检清单）+
**FRESH**（禁未来日期，防「名新实旧」）。**禁止不复检就改日期**（C8 时间只前进 + 诚实原则）。

### R3. 死亡 = 墓碑，不是删除（保住追踪链）
工具死亡（死亡码 D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED）时：分片行进 `⚠ Avoid (dead, D-xxx)` 墓碑、
索引行去星或标注、**文档保留并在顶部加死亡横幅**（不要删文件）——死条目才不会被下一轮重新「幻觉」回来，
追踪链不断。**改名（rebrand，如 Polygon→Massive）不是死亡**：保留为 live、标 REBRAND，别误套死亡码。

### R4. 经验必须真实，禁止编造
文档的「General experience & gotchas / 踩坑」只能来自：分片沉淀的真实运行教训、`metrics/live-runs.jsonl`
反馈、或本轮实跑/实抓所得——**绝不凭模型记忆编造**（C1/C6），所有 star/价格实测带 URL。每轮 sweep 派一个
**零上文的独立审计 subagent**（仿 `citation-audit` 模式）抽检若干文档：核对仓库存在性、star 容差、价格、
以及 shard↔doc↔index↔pricing 四者自洽，发现即修。`metrics/live-runs.jsonl` 是经验的活水——真实调研中触到
新坑就回写一行，下轮据此把对应 `tools/<slug>.md` 的踩坑段加厚。

## Cleanup pass (mandatory every sweep)

Doc/script entropy grows silently. Every full sweep must include a 5-min cleanup pass that
kills accumulated cruft. Without this, the skill bloats by ~5-10% per cycle and new users
get buried.

### What to check + cut

1. **One-shot session artifacts** — any runbook/doc that's clearly tied to a past session's
   task list (e.g. `phase3-handoff.md`, `bucket-B-checklist.md`). If all items are
   completed → delete; if any pending → migrate the pending parts into a generic runbook
   and delete the stub.
2. **Stale Mode-B / out-of-band-backup references** — under Mode A the OneDrive backup
   scripts are no-ops. They live in `scripts/legacy/` per v0.9.0 convention. If a runbook
   still references them as live, fix to "Mode B fallback only".
3. **CHANGELOG bloat** — once a major doctrinal pivot lands (e.g. Mode B → Mode A,
   spec v1 → v2), compress all pre-pivot entries to a single summary paragraph. Keep
   only entries from the current doctrinal era as full text.
4. **PII drift in committed READMEs** — grep `tools/*/README.md` for email patterns,
   phone numbers, real usernames. Per spec §4.3 these belong in
   `secrets/_credentials.env` + `secrets/_account-info.env`, not in committed docs.
5. **Duplicate or near-duplicate docs** — when a runbook covers one Windows gotcha or one
   provider quirk, ask "should this be a standalone file or a section in a larger
   runbook?" Single-purpose files <80 lines that share an audience with a sibling are
   merge candidates.
6. **Per-tool docs with `## Last verified` >9mo old** — covered by the STALE gate, but
   the cleanup pass should triage: re-verify, deprecate, or tombstone (`⚠ Avoid (dead)`).
7. **Skill `metrics/live-runs.jsonl`** — keep all entries; this is the feedback ledger and
   the refresh consumes it. Don't compress.
8. **Auto-advance `## Last verified` from real runs** (v0.17.0) — at the END of cleanup
   pass, for every slug that appears in `live-runs.jsonl` since last refresh with
   `outcome: "verified"`, advance its `tools/<slug>.md` `## Last verified: YYYY-MM`
   line to the current month. Rationale: truthful "I just used it and it worked" is
   stronger evidence than a scheduled re-check; the STALE gate WARN on >9mo unchecked
   docs is exempted for these. Record the auto-bumped slug list in the sweep's
   CHANGELOG entry under "Auto-verified from live-runs".

### Downstream: companion-config sync (skip if no companion repo)

When this skill is paired with a `market-intel-config` repo (per-machine inventory of
installed + keyed tools), the matrix changes from the sweep need to be reconciled
downstream — otherwise the config repo accumulates orphan secrets, dead MCP entries,
and broken `installed:true` flags.

After the sweep, run **`python scripts/sync-check.py`** in the config repo. It reports
six drift buckets (A: matrix has it / config doesn't · B: config points to a missing
skill doc / renamed-or-deleted · C: config points to a tombstoned doc · D: orphan secret
· E: orphan MCP · F: `installed:true` with no secret file). Per-bucket action is in the
config repo's `runbooks/sync-with-skill.md`.

Key invariant: the link between the two repos is the config registry's
`matrix_slug` field == the skill's `tools/<slug>.md` filename. If you rename a tool in
the skill, you MUST update `matrix_slug` everywhere that pointed to the old name.

This downstream sync is a separate concern from the cleanup pass above (cleanup =
inside the skill; sync = skill→config drift) and should be done in the same session so
the CHANGELOG can record both.

### What NOT to cut

- Per-tool docs (`tools/<slug>.md`) regardless of count — they're load-on-demand.
- Domain shards regardless of length — same.
- Companion-config-* docs (overview/spec/hardening) — three distinct audiences.
- Active feedback ledgers (`live-runs.jsonl`, `discovery-state.md`).

### Output

In the sweep CHANGELOG entry, the cleanup pass gets its own section:

```
### Cleanup (mandatory per-sweep)
- Deleted: <files>
- Merged: <a> → <b>
- Compressed: CHANGELOG pre-<version>
- PII stripped from: <N> READMEs

### Downstream config sync (when companion repo present)
- sync-check buckets cleared: B=<n>, C=<n>, D=<n>, E=<n>, F=<n>
- Renames: <old> → <new>
- Tombstoned in config: <slug> (code D-xxx)
```

## Trigger

- Manual: ask "refresh the market-intel source matrix" / "刷新工具库".
- Scheduled: Windows Task `RefreshMarketIntel` (monthly) runs `the scheduled refresh script`.
