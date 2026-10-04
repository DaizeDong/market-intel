# market-intel

把商业课题在 15 个数据方向上分诊、自动检测对的专业数据源，再把繁重的检索·验证·合成委托给你已有的调研引擎。

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![源矩阵](https://img.shields.io/badge/%E6%BA%90%E7%9F%A9%E9%98%B5-15%20%E4%B8%AA%E6%96%B9%E5%90%91-green?style=flat)](skills/market-intel/reference/sources-index.md)
[![工具文档](https://img.shields.io/badge/%E5%B7%A5%E5%85%B7%E6%96%87%E6%A1%A3-%E9%80%90%E5%B7%A5%E5%85%B7%E6%93%8D%E4%BD%9C-green?style=flat)](skills/market-intel/reference/tools/index.md)
[![语言](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-EN%20%2F%20CN-blue?style=flat)](#语言)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.30.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## ⭐ 先读这个， 设计理念

商业调研常在选源时就出了问题：普通搜索结果无法替代所需的交易历史、平台数据或鉴权操作。
工具负责分诊、安装指引和证据要求，检索与综合交给已有调研引擎。浏览器访问与官方 API 等来源并列，
但是否可用，必须在当前会话中核验。

这样可以减少重复维护，代价是覆盖范围取决于宿主、权限和数据源的实际行为。
配置存在、发现工具、调用成功、内容可用是四种不同证据，缺哪一层就明确记录设置需求或覆盖缺口。
只浏览目录无需在线探测；采集当前机器清单需要显式执行，结果只写入已核验的 PRIVATE 伴生仓。

矩阵修改需要通过已声明规则的确定性检查，并保留来源证据。这些检查能拦住已定义的退化，
不能证明每条推荐都更好，也不能证明服务商此刻可用。刷新现已改为手动启动，日期和覆盖范围必须留给读者判断。

📜 **[阅读完整设计理念 → PHILOSOPHY.md](PHILOSOPHY.md)**（七条原则说明选源、委托、证据、更新检查和按需加载）。

---

## 它是什么（不是什么）

Claude Code 已经内置了 `deep-research`（fan-out → 抓取 → 验证 → 合成）和 `research-lit`。这两个擅长**通用网页**和**学术**调研。但一旦课题需要**有信息壁垒的专业商业数据源**,真实的 X/推特数据、亚马逊历史价、链上数据、SEO 指标、社媒舆情、B2B 潜客，它们就够不着了。

`market-intel` 就是补这个缺口的**瘦层**。它**只做三件别人不做的事**，其余全部委托出去：

1. **分诊**, 把商业课题映射到 15 个数据方向中的 1~N 个。
2. **检测 + 引导安装**, 在当前 Claude 或 Codex 会话中核验选定操作，分别检查工具是否开放、执行是否成功、鉴权是否通过，以及返回内容是否可用。证据不足时说明要补什么；安装和鉴权步骤见[逐工具文档](skills/market-intel/reference/tools/index.md)。
3. **质量护栏**, 引用回验、源等级、多源印证、强制反方检索、显式缺口。

真正的 fan-out、抓取、对抗式验证、带引用合成，**委托**给 `deep-research` / `research-lit`。不重造引擎，不抢触发。

---

## 安装

```
/plugin install github:DaizeDong/market-intel
```

或手动克隆：

```bash
git clone --recurse-submodules https://github.com/DaizeDong/market-intel.git ~/.claude/plugins/market-intel
```

在检出的工具仓中运行 `python -m pip install -r requirements.txt`，安装 Python 维护命令的依赖；
离线测试依赖见 `requirements-dev.txt`。目录浏览、数据采集和确定性检查无需模型适配包。
可选的事故说明和变更记录起草工具使用当前安装的 `llmcall`，配置步骤见[模型适配器说明](CONFIG.md#model-adapter)。

遇到 `市场调研`、`竞品分析`、`调研这个市场`、`找套利机会`、`X/推特舆情`、`SEO 情报`、`产品趋势` 等会自动触发。单点查询或纯网页报告它会主动让位（用普通搜索 / `deep-research`）；学术文献则交给 `research-lit`。

---

## 配置

运行维护命令前，先找到完整的工具检出目录。把 `<absolute-market-intel-checkout>`
替换为它的绝对路径，并确认其中存在 `tools/console.py` 和 `.claude-plugin/plugin.json`。
安装插件不会让这些脚本出现在当前项目目录中。

`market-intel` 是**带 config 的 skill**, 它从一个**独立、私有**的伴随 config 仓读取每用户状态(密钥、已装工具
注册表)。仓根契约见 [CONFIG.md](CONFIG.md);权威深规范见
[`companion-config-spec.md`](skills/market-intel/reference/companion-config-spec.md)(v1.3, STABLE)。

- **挂载(发现顺序):** `$MARKET_INTEL_CONFIG` → `~/.market-intel-config/` →
  `~/.config/market-intel-config/`。命中第一个即用；都没有则降级为纯矩阵模式照常运行。
- **首次配置：**
  ```bash
  python "<absolute-market-intel-checkout>/scripts/init_config.py"        # 生成符合规范的 config 骨架(确定性)
  export MARKET_INTEL_CONFIG=~/.market-intel-config  # 或给 init 传 --out <dir>
  python "<absolute-market-intel-checkout>/scripts/verify_config.py"       # doctor:逐项 PASS/FAIL,明确报缺什么
  ```
- **切换 config(即插即用):** 把环境变量指向另一个 config 目录即可， config 自包含，无需别的改动：
  `export MARKET_INTEL_CONFIG=~/configs/work` ↔ `~/configs/personal`。
- **密钥：** 按伴生仓声明的存储模式维护。Mode A 仅在已核验的 PRIVATE Git 仓中记录凭据；
  Mode B 忽略凭据文件，并要求另行备份。自带初始化工具只支持 Mode B。两种模式都禁止把密钥写进公开工具仓，
  详见 [CONFIG.md](CONFIG.md#secrets-and-storage-modes-e6)。

---

## 目录浏览与当前操作状态

维护控制台保留 `status`、`tool <slug>`、`connect <slug>`。浏览目录不要求初始化
DATA，不探测机器清单，也不写文件。`--capability` 为目录中的 `source_id` 指定操作，默认使用该条目的 `capability_id`。
当前证据通过 `MARKET_INTEL_HOST`、`MARKET_INTEL_SESSION_ID` 和
`MARKET_INTEL_CAPABILITIES` 提供。[schema v1 说明](skills/market-intel/reference/host-capabilities.md)
列出了 `available-now`、带原因的 `setup` 和有证据支持的 `hard-gap` 的判定条件。

只有显式 `--refresh` 才采集机器清单，并写入已核验为 PRIVATE、已有版本历史的
伴生仓。写入失败会返回非零状态，保留先前快照。离线回归测试不能证明真实调研、
已安装宿主或服务商当前可用。

## 快速开始， 装免费无密钥三件套（3 分钟）

不想配 API key 也想试用?先装这 3 个免费无密钥的 MCP, 覆盖 HN / Reddit 风格社区 + 全球趋势 + AI 论文，零成本：

```bash
# 1. Hacker News (社区)
claude mcp add -s user mcp-hn -- uvx mcp-hn

# 2. GDELT (全球新闻 + 趋势,无 key)
claude mcp add -s user gdelt -- uvx gdelt-mcp

# 3. arXiv (研究论文,无 key)
claude mcp add -s user arxiv -- uvx arxiv-mcp-server
```

然后**重启 Claude 会话**，核验这个会话中的选定操作。
使用 **Codex** 时，在 Codex 的 MCP 设置或已安装 app 中启用来源，重连后检查 Codex
当前可调用的工具。Claude 的配置不能证明 Codex 可用。详见[宿主证据说明](skills/market-intel/reference/host-capabilities.md)。

接着说： `调研一下 AI agent 工具生态的趋势`。skill 会用通过核验的来源检索社区信号、趋势和论文，再生成带引用的报告。只有选定来源通过当前操作和内容核验后，才把它计为可用。

之后，看下面 [60 秒演示](#60-秒演示)了解**专用 MCP**(付费 X 数据、Bright Data、Keepa 等), 那些才是 skill 真正设计的高质量路线。

### 装完之后， 该读哪个?

按目的选一条：

| 你想做的… | 打开这个 |
|---|---|
| **直接用 skill**(让它自动触发跑研究) | 啥也不用读， skill 已加载，直接打研究问题。 |
| **装第一个专用 MCP**(比如真 X 数据源 / 金融 API) | `skills/market-intel/reference/install-guide.md`, L0 装机机制；然后 `skills/market-intel/reference/tools/<slug>.md` 看你从下面源矩阵挑的那个工具。 |
| **建私有 companion config repo** 跨机持久化你的安装状态 + 密钥(>1 工具时推荐) | `skills/market-intel/reference/companion-config-repo.md`, 概述 + 教程。然后 `companion-config-spec.md`(正式契约)和 `companion-config-hardening.md`(首次推送**前**做 GitHub 端锁定)。 |

大多数人先走路径 2,工具/机器累积到 >1 后再走路径 3。

---

## 60 秒演示

你说：

```
调研一下 <产品> 的竞争格局和 X 舆情，再看看有没有套利空间
```

会发生：

1. **分诊** → 映射到 `x-twitter`、`trends-discovery`、`ecommerce-arbitrage`；选定深度档位并绑死上限（fan-out 不会失控）。
2. **检测** → 检查当前宿主会话开放的工具，核验选定的 X 或电商操作，并说明还缺哪些配置或证据。
3. **引导安装**（不阻塞）→ "这依赖真实 X 数据。装 twitterapi.io：`claude mcp add -s user ...`, 注意需重连会话才生效。本轮先用网页兜底并标注缺口。"
4. **委托** → fan-out 子任务 / 调 `deep-research`，每个返回**结构化证据单元**（`论断·来源·原文引用·等级·日期·置信度`），而非原始网页堆。
5. **护栏** → 独立 verifier 重新 fetch 每条引用 URL；决策级结论需 ≥2 个独立源；专门的反向检索子任务去挖风险/失败案例。
6. **报告** → 带数据快照日期、源等级标注、分歧矩阵、强制的**风险与反方证据**章节，以及显式的**"配了 X 源可更深"**缺口清单。

### 拿这些当你的第一个真实查询

装完上面的快速开始后，试试用一个具体课题触发 skill：

- `调研一下 AI agent 工具生态最近一个月的趋势`, 跑 趋势 + 社区 + 前沿研究
- `compare the top 3 hosted MCP marketplaces (Smithery / Glama / PulseMCP) — coverage, pricing, signal-to-noise`，跑 trends-discovery + web-scraping
- `find me 3 underrated open-source web-scraping tools released in 2026 with > 200 stars`, 跑 web-scraping + GitHub 星速发现
- `who's been launching credible LLM eval skills in the last 3 months`, 跑 ready-skills + 前沿研究

每个都会 fan-out 子任务、亮出带引用的证据，最后给一份"配了 <X> 源可更深"缺口清单。如果某个查询只出网页兜底，那是 skill 在诚实地说明它的覆盖范围，见 install-guide 加一个专用 MCP 拿更深的数据。

---

## 速览 skill

### 源矩阵（15 个方向）

核心知识资产。每个方向分片标明首选工具、**信息壁垒路线**、如何检测、装什么。薄索引 → 只加载你需要的方向。每个工具还配有一份 [`reference/tools/`](skills/market-intel/reference/tools/index.md) 下的**逐工具操作文档**（安装 + 鉴权 + 用法 + 踩坑），通过薄工具索引按需加载。

| 方向 | 首选（壁垒路线） |
|---|---|
| [x-twitter](skills/market-intel/reference/domains/x-twitter.md) | twscrape ③ · playwright ④ · twitterapi.io ② 转售 |
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

**壁垒路线：** ① 官方 API（合规、多为付费）· ② 转售 API（服务商承担壁垒、便宜、灰区）· ③ 自托管抓取（逆向 API、免费、自备账号+代理、有封号风险）· ④ **浏览器自动化 / 模拟人**,真实登录态浏览器（playwright MCP + 免费开源仓库）。**一等路线，不是脚注：** 常能拿到比付费 API 更丰富的数据（渲染后/登录后视图、API 不返回的字段），且零 API 成本。skill 在适用时**优先走路线 ④**，只在需要它无法回溯的历史数据（如 Keepa 历史价）、规模化可靠性、或合规（无封号风险）时才用 ①/②。

三层安装指南：[`install-guide.md`](skills/market-intel/reference/install-guide.md)（L0 安装机制）→ [`pricing-install.md`](skills/market-intel/reference/volatile/pricing-install.md)（L1 逐方向命令 + 价格，带 `last_verified` 时间戳）→ [`tools/<slug>.md`](skills/market-intel/reference/tools/index.md)（L2 逐工具）。时效价格引用前请到官网二次核实。

### 姊妹 skill, 消费侧特化

对于**消费者购物比价**（Amazon / eBay / Walmart / Target / 淘宝 / 京东 价格对比 + Keepa /
Camelcamelcamel / 慢慢买 历史价 + Capital One Shopping / Karma / 购物党 优惠码 + Honey 2026
信任事件），market-intel 委托给姊妹 skill：
**[`shopping-aggregator`](https://github.com/DaizeDong/shopping-aggregator)**。market-intel
管广义商业调研+卖家侧 ecommerce-arbitrage；shopping-aggregator 管消费者购买决策。两个 skill 可
共存，见 [`consumer-price-compare`
shard](skills/market-intel/reference/domains/consumer-price-compare.md) 路由逻辑。

```
/plugin install github:DaizeDong/shopping-aggregator
```

---

## 如何触发

遇到 `市场调研`、`competitor analysis`、`research this market`、`find arbitrage opportunities`、
`X/Twitter sentiment`、`SEO intel`、`product trends`、`调研这个市场`、`竞品分析`、`找套利机会`、
`X/推特舆情`、`SEO 情报`、`产品趋势` 等会自动触发。要刷新源矩阵，说 `刷新工具库` /
`refresh the market-intel source matrix`。

单点查询或纯网页报告它会主动让位（用普通搜索 / `deep-research`）；学术文献交给 `research-lit`。

---

## 示例输出

一份完成的报告带数据快照日期、源等级标注，由**结构化证据单元**（`论断·来源·原文引用·等级·日期·置信度`）
而非原始网页堆构成：

- 决策级结论带 ≥2 个独立源，每条标置信度高/中/低。
- 分歧矩阵亮出冲突，而不是抹平它们。
- 强制的**风险与反方证据**章节（反向检索子任务挖骗局/失败/风险）。
- 凡回落到网页之处，给一份显式的**"配了 X 源可更深"**缺口清单。

具体怎么产出这份报告，见上面的 [60 秒演示](#60-秒演示)。

---

## 质量护栏

合成阶段强制执行的硬规则（见 [SKILL.md](skills/market-intel/SKILL.md)）：

- **引用回验闸门**, 独立 verifier 重新 fetch 每条引用 URL，确认页面确含该数值（逐字引文）。死链丢弃；无引文的数字降级为"未证实"。
- **决策级结论需 ≥2 个独立源**；每条标置信度高/中/低。
- **源等级** L1 一手 → L5 兜底/推断；厂商自述不得作为唯一支撑。
- **拒绝静默降级**, 从壁垒源回落到网页，必须在对应章节标注。
- **时效数据打双日期**, 每个价格/政策带抓取日 + 发布日。
- **强制反方检索**, 反向检索子任务挖骗局/失败/风险；套利类强制列执行摩擦。
- **亮出冲突而非抹平**；**失败转为显式覆盖缺口**。

---

## 局限

- **矩阵会过时：** API 转付费、工具被收购、价格变动，都需要按[刷新协议](skills/market-intel/reference/refresh-protocol.md)重新核验来源、审查证据并记录已接受的修改。原每月刷新任务和每周动态采集已于 2026-10-01 退役，现在通过 `刷新工具库` / `refresh the market-intel source matrix` 手动启动。每月复核方向、每周关注快变来源、每季度做 Horizon scan，只是安排复核时的参考频率，不表示有任务正在运行。见 [ROADMAP](ROADMAP.md)。
- **网页兜底是诚实，不是魔法**, 没连专用 MCP 时，skill 会如实说明并标注缺口，而不是假装网页答案一样深。
- **不重造引擎**, fan-out/验证/合成的深度委托给 `deep-research` / `research-lit`；market-intel 是路由 + 检测 + 护栏的接缝，不是它自己的调研引擎。

本 skill 是一次 12-子任务工具调研 + 5-子任务对抗式设计评审的产物。评审推翻了最初"再造一个全栈 deep-research"的方案（那会是带触发冲突的克隆），证实了 `claude mcp add` 需重连会话才生效，并强制加入了引用回验闸门、源等级、强制反方检索。

---

## 语言

English（[`README.md`](README.md)，权威版本）· 中文（`README_CN.md`）。

---

## Roadmap · 贡献 · 许可

见 [ROADMAP.md](ROADMAP.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [LICENSE](LICENSE)（MIT）。

想加一个工具、修一个挂掉的条目、或者提一个新方向?[CONTRIBUTING.md](CONTRIBUTING.md) 是一页指南，
覆盖 3 种贡献模式、4 文件同步规则、PR 必过的验证闸门。更深的设计文档：[PHILOSOPHY.md](PHILOSOPHY.md) ·
[CONSTITUTION.md](CONSTITUTION.md) · [EVOLUTION.md](EVOLUTION.md)。
