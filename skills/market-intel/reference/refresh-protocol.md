# Refresh protocol — keep the source matrix current

This skill's value is a curated source matrix. Tools, prices, and barriers in the commercial-data
space move fast (every survey round found acquisitions, price changes, and dead tools within
months). Re-run this protocol periodically to keep `domains/`, `volatile/pricing-install.md`, and
`sources-index.md` accurate.

## Cadence

- **Default: quarterly** (every ~3 months) full sweep.
- **Faster (monthly)** for volatile domains: x-twitter, web-scraping, social-publishing, crypto-defi,
  browser-automation (fast-moving OSS repos + frequent API-policy and pricing changes).
- Also refresh opportunistically whenever you hit a dead/changed tool during a real research run —
  fix that one shard immediately.

## Procedure (full sweep)

每次自动运行分两阶段：**发现阶段（Discovery，找新东西）** + **核实/差分阶段（Verify & Diff，旧条目校验
+ 落库）**。旧版协议只做后者，会停滞——必须先跑发现阶段主动挖掘更前沿的工具，再用准入门槛过滤。

> 发现阶段的完整规则见下方 **「Discovery phase（前沿发现 + 质量筛选）」** 一节。它产出一个
> 「候选池（candidate pool）」，核实/差分阶段只处理通过准入门槛的候选 + 旧条目复检。

1. **跑发现阶段**：按下方 Discovery phase 规则，对每个域并行盲扫多个发现源，产出候选池
   （每个候选附带：来源、score、对现有首选的「新增/替换/不收录」裁决 + 理由）。
2. **Apply the same quality guardrails** as a normal run (verify each claimed tool exists and the
   price against its official site — do not trust a subagent's recalled pricing).
3. **Incremental edit, don't rewrite**: for each domain, update only changed rows in
   `domains/<domain>.md`; move/refresh price+install lines in `volatile/pricing-install.md`; bump
   that section's `last_verified: YYYY-MM`. Update `sources-index.md` only if a domain's top pick
   changed.
4. **Record the diff** in `CHANGELOG.md` at the repo root (date + per-domain added/removed/changed),
   and bump the plugin `version` in `.claude-plugin/plugin.json`.
5. **Commit + push** to the repo (DaizeDong/market-intel).

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

## Trigger

- Manual: ask "refresh the market-intel source matrix" / "刷新工具库".
- Scheduled: Windows Task `RefreshMarketIntel` (monthly) runs `the scheduled refresh script`.
