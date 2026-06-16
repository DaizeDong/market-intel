# market-intel

一个用于商业/市场调研的**瘦编排 skill**。它负责给课题分诊、找到对的专业数据源（并帮你装上），然后把繁重的检索·验证·合成**委托**给你已有的调研引擎——而不是重造一遍。

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Domains](https://img.shields.io/badge/Source%20Matrix-15%20domains-green?style=flat)](skills/market-intel/reference/sources-index.md)
[![Tool docs](https://img.shields.io/badge/Tool%20docs-per--tool%20how--to-blue?style=flat)](skills/market-intel/reference/tools/index.md)
[![Version](https://img.shields.io/badge/version-0.10.7-purple?style=flat)](CHANGELOG.md)
[![Sister skill](https://img.shields.io/badge/sister-shopping--aggregator-yellow?style=flat)](https://github.com/DaizeDong/shopping-aggregator)

[English](README.md) | [中文版](README_CN.md)

---

## ⭐ 先读这个：设计理念

market-intel 建立在一条原则上——**从根本进行设计，而非小修小补。** 出了问题，我们改的是它底下的假设，
而不是它表面的症状。正是这一条催生了这里的每个决定：浏览器自动化被从脚注提升为一等路线（而不是"加几个
免费工具"）；这是一个瘦委托层（而不是"又一个 deep-research"）；更新走一道只能让矩阵变好的确定性闸门
（而不是"设个提醒去刷新"）。**理念的优先级高于任何单个功能**——未来每次改动都要通过一个检验：*它是在改
框架，还是只在打补丁？*

📜 **[阅读完整设计理念 → PHILOSOPHY.md](PHILOSOPHY.md)**（6 条原则，每条都给出"补丁 vs 根本"的对比，以及
它在本仓库催生的真实决定）。

---

## 它是什么（不是什么）

Claude Code 已经内置了 `deep-research`（fan-out → 抓取 → 验证 → 合成）和 `research-lit`。这两个擅长**通用网页**和**学术**调研。但一旦课题需要**有信息壁垒的专业商业数据源**——真实的 X/推特数据、亚马逊历史价、链上数据、SEO 指标、社媒舆情、B2B 潜客——它们就够不着了。

`market-intel` 就是补这个缺口的**瘦层**。它**只做三件别人不做的事**，其余全部委托出去：

1. **分诊** —— 把商业课题映射到 14 个数据方向中的 1~N 个。
2. **检测 + 引导安装** —— 用 `claude mcp list`（不是靠工具名瞎猜）查哪些专业 MCP 真的连上了；关键源缺失时，直接给你那条 `claude mcp add` 命令——或打开它的**逐工具操作文档**（[`reference/tools/`](skills/market-intel/reference/tools/index.md)）查安装 + 鉴权 + 用法 + 踩坑，由[多层安装指南](skills/market-intel/reference/install-guide.md)引导。
3. **质量护栏** —— 引用回验、源等级、多源印证、强制反方检索、显式缺口。

真正的 fan-out、抓取、对抗式验证、带引用合成，**委托**给 `deep-research` / `research-lit`。不重造引擎，不抢触发。

---

## 安装

```
/plugin install github:DaizeDong/market-intel
```

或手动克隆：

```bash
git clone https://github.com/DaizeDong/market-intel.git ~/.claude/plugins/market-intel
```

遇到 `市场调研`、`竞品分析`、`调研这个市场`、`找套利机会`、`X/推特舆情`、`SEO 情报`、`产品趋势` 等会自动触发。单点查询或纯网页报告它会主动让位（用普通搜索 / `deep-research`）；学术文献则交给 `research-lit`。

---

## 60 秒演示

你说：

```
调研一下 <产品> 的竞争格局和 X 舆情，再看看有没有套利空间
```

会发生：

1. **分诊** → 映射到 `x-twitter`、`trends-discovery`、`ecommerce-arbitrage`；选定深度档位并绑死上限（fan-out 不会失控）。
2. **检测** → 跑 `claude mcp list`，发现 X/电商相关 MCP 一个都没连，记下来。
3. **引导安装**（不阻塞）→ "这依赖真实 X 数据。装 twitterapi.io：`claude mcp add -s user ...` —— 注意需重连会话才生效。本轮先用网页兜底并标注缺口。"
4. **委托** → fan-out 子任务 / 调 `deep-research`，每个返回**结构化证据单元**（`论断·来源·原文引用·等级·日期·置信度`），而非原始网页堆。
5. **护栏** → 独立 verifier 重新 fetch 每条引用 URL；决策级结论需 ≥2 个独立源；专门的反向检索子任务去挖风险/失败案例。
6. **报告** → 带数据快照日期、源等级标注、分歧矩阵、强制的**风险与反方证据**章节，以及显式的**"配了 X 源可更深"**缺口清单。

---

## 姊妹 skill — 消费侧特化

对于**消费者购物比价**（Amazon / eBay / Walmart / Target / 淘宝 / 京东 价格对比 + Keepa /
Camelcamelcamel / 慢慢买 历史价 + Capital One Shopping / Karma / 购物党 优惠码 + Honey 2026
信任事件），market-intel 委托给姊妹 skill：
**[`shopping-aggregator`](https://github.com/DaizeDong/shopping-aggregator)**。market-intel
管广义商业调研+卖家侧 ecommerce-arbitrage；shopping-aggregator 管消费者购买决策。两个 skill 可
共存——见 [`consumer-price-compare`
shard](skills/market-intel/reference/domains/consumer-price-compare.md) 路由逻辑。

```
/plugin install github:DaizeDong/shopping-aggregator
```

## 源矩阵（15 个方向）

核心知识资产。每个方向分片标明首选工具、**信息壁垒路线**、如何检测、装什么。薄索引 → 只加载你需要的方向。每个工具还配有一份 [`reference/tools/`](skills/market-intel/reference/tools/index.md) 下的**逐工具操作文档**（安装 + 鉴权 + 用法 + 踩坑），通过薄工具索引按需加载。

| 方向 | 首选（壁垒路线） |
|---|---|
| [x-twitter](skills/market-intel/reference/domains/x-twitter.md) | twikit ④③ · twitterapi.io ② 转售 |
| [reddit-community](skills/market-intel/reference/domains/reddit-community.md) | HN MCP ① · reddit-mcp-buddy ① |
| [web-scraping](skills/market-intel/reference/domains/web-scraping.md) | Tavily/Exa + Firecrawl + Bright Data |
| [ecommerce-arbitrage](skills/market-intel/reference/domains/ecommerce-arbitrage.md) | Keepa ① 官方（卖家侧） |
| [finance-markets](skills/market-intel/reference/domains/finance-markets.md) | SEC EDGAR + FRED ① 免费 |
| [crypto-defi](skills/market-intel/reference/domains/crypto-defi.md) | CoinGecko ① + ccxt |
| [seo-keywords](skills/market-intel/reference/domains/seo-keywords.md) | GSC ① 免费 + DataForSEO ② |
| [social-publishing](skills/market-intel/reference/domains/social-publishing.md) | Buffer ① · Postiz 开源 |
| [content-cms](skills/market-intel/reference/domains/content-cms.md) | Sanity/WordPress MCP ① |
| [leadgen-crm](skills/market-intel/reference/domains/leadgen-crm.md) | Apollo.io ① + Hunter ① |
| [trends-discovery](skills/market-intel/reference/domains/trends-discovery.md) | GDELT + Product Hunt MCP ① 免费 |
| [frontier-research](skills/market-intel/reference/domains/frontier-research.md) | arXiv API + HF Daily Papers ① 免费 |
| [ready-skills](skills/market-intel/reference/domains/ready-skills.md) | coreyhaines31/marketingskills |
| [browser-automation](skills/market-intel/reference/domains/browser-automation.md) | playwright MCP + browser-use / crawl4ai ④ |
| [consumer-price-compare](skills/market-intel/reference/domains/consumer-price-compare.md) | **委托给姊妹 skill** shopping-aggregator |

**壁垒路线：** ① 官方 API（合规、多为付费）· ② 转售 API（服务商承担壁垒、便宜、灰区）· ③ 自托管抓取（逆向 API、免费、自备账号+代理、有封号风险）· ④ **浏览器自动化 / 模拟人**——真实登录态浏览器（playwright MCP + 免费开源仓库）。**一等路线，不是脚注：** 常能拿到比付费 API 更丰富的数据（渲染后/登录后视图、API 不返回的字段），且零 API 成本。skill 在适用时**优先走路线 ④**，只在需要它无法回溯的历史数据（如 Keepa 历史价）、规模化可靠性、或合规（无封号风险）时才用 ①/②。

三层安装指南：[`install-guide.md`](skills/market-intel/reference/install-guide.md)（L0 安装机制）→ [`pricing-install.md`](skills/market-intel/reference/volatile/pricing-install.md)（L1 逐方向命令 + 价格，带 `last_verified` 时间戳）→ [`tools/<slug>.md`](skills/market-intel/reference/tools/index.md)（L2 逐工具）。时效价格引用前请到官网二次核实。

---

## 质量护栏

合成阶段强制执行的硬规则（见 [SKILL.md](skills/market-intel/SKILL.md)）：

- **引用回验闸门** —— 独立 verifier 重新 fetch 每条引用 URL，确认页面确含该数值（逐字引文）。死链丢弃；无引文的数字降级为"未证实"。
- **决策级结论需 ≥2 个独立源**；每条标置信度高/中/低。
- **源等级** L1 一手 → L5 兜底/推断；厂商自述不得作为唯一支撑。
- **拒绝静默降级** —— 从壁垒源回落到网页，必须在对应章节标注。
- **时效数据打双日期** —— 每个价格/政策带抓取日 + 发布日。
- **强制反方检索** —— 反向检索子任务挖骗局/失败/风险；套利类强制列执行摩擦。
- **亮出冲突而非抹平**；**失败转为显式覆盖缺口**。

---

## 保持更新

矩阵会过时——API 转付费、工具被收购、价格变动。[刷新协议](skills/market-intel/reference/refresh-protocol.md) 会对每个方向重新扫一遍（每方向一个子任务 → 结构化 diff → 增量改分片 → `CHANGELOG.md` + 升版本）。默认每季度；快变方向（x-twitter、web-scraping、social-publishing、crypto-defi）每月。手动触发说 `刷新工具库`，或接一个定时 headless 运行（见 [ROADMAP](ROADMAP.md)）。

---

## 设计说明

本 skill 是一次 12-子任务工具调研 + 5-子任务对抗式设计评审的产物。评审推翻了最初"再造一个全栈 deep-research"的方案（那会是带触发冲突的克隆），证实了 `claude mcp add` 需重连会话才生效，并强制加入了引用回验闸门、源等级、强制反方检索。后续计划见 [ROADMAP.md](ROADMAP.md)。
