# 领域词汇表

## 产品（doujinshi-meta / `djm`）

从外部来源站爬取**本子元数据**的 CLI / Python 库。当前交付主要为标题、页数（可选）与多维 Tag（见输出契约）。CLI 主命令为 `djm`。
_Avoid_: 把产品范围等同于「只做 tag getter」

## Tag（标签）

漫画元数据中的分类/描述词。不同来源命名可能不同，输出保留原始值。

## Tag 库 / Tag 词表（Tag Catalog）

本项目的「tag 库」指 **去重 tag 列表**（`kind` + `name` + `count`），由功能 1 全量爬取聚合产出。**不包含**本子持久化或本子–tag 关联表。

## Tag Kind（标签维度）

契约中的标签维度字面量（与来源站 API 字段名无关）：

- `tag` — 自由标签
- `parody` — 原作、IP 或被同人化的系列
- `character` — 登场角色
- `author` — 作者

_Avoid_: `work`、`actor`（旧 Kind 名）；`category`（不再作为 Tag Kind——平台分区只用于本子枚举，不进入词表/fetch）

## Kind 过滤（Kind Filter）

`catalog` 命令可选地只聚合/输出指定 Tag Kind 的词表子集（如仅 `tag`）。**不改变**本子枚举与详情请求策略；过滤发生在聚合与输出阶段。
_Avoid_: 爬取类型（作领域名）、维度过滤（含糊）

## 来源站（Source）

`bika`（哔咔）、`jmcomic`（禁漫天堂）。

## 输出契约（Output Contract）

工具通过 **JSON（stdout 或 `-o` 文件）** 交付数据，不写数据库。详见 [`docs/schema.md`](docs/schema.md)：

- `TagCatalogResponse` — 功能 1
- `FetchTagsResponse` — 功能 2（单本/批量 tag，由调用方决定是否缓存）
- `SearchTagsResponse` — 功能 3（按标题搜索）
- `SearchBatchResponse` — 功能 4（批量按标题搜索）

## 表格视图（Table View）

`djm catalog --table` 时 CLI 在 stdout 打印人类可读表格（`kind` / `name` / `count`），仅供终端浏览。
**不属于**输出契约；Flutter / 脚本集成仍只依赖 JSON 契约。
_Avoid_: 表格输出、pretty 输出（作契约名）

## 集成方式

- **CLI 子进程**：Flutter / 其他项目调用 `djm` 命令，解析 JSON
- **Python 库**：同结构 API，供脚本或测试使用
- **静态 JSON 文件**：CI 生成词表后放入 Flutter `assets`

## 全量爬取 / 按需爬取 / 按标题搜索

- **全量（catalog）**：枚举本子 → 内存聚合 tag 词表 → 输出 JSON
- **按需（fetch）**：指定 ID → 输出每本 tag 列表 JSON
- **按标题搜索（search）**：标题或关键词 → 来源站搜索 → 对命中本子拉详情 → 输出 `SearchTagsResponse` JSON
- **批量按标题搜索（search-batch）**：多本**本地本子**（标题 ± 页数）→ 逐本 search → 输出 `SearchBatchResponse` JSON

## 本地本子（Local Book）

集成 App 中用户已拥有、待补全元数据的漫画条目。通常已知**标题**（来自文件名或 UI），有时已知**页数**（来自本地文件统计）。本地本子 **不是** 来源站 ID；刮削即把本地本子映射到来源站 `external_id` 与 tags。
_Avoid_: 专辑（album，易与禁漫 API 字段混淆）；本地漫画（过长）

## 刮削级别（Scrape Scope）

按**本地本子批量范围**划分，**不是** Tag Kind 或 tag 词表层级：

- **本级** — 单本本地本子按标题刮削
- **系列级** — 同一系列/文件夹下多本本地本子批量刮削
- **库级** — 整个 App 本地库批量刮削

系列级与库级共用同一批量能力（`search-batch`），差别仅在调用方传入的本子数量与分组；本工具不区分「系列」与「库」命令。
_Avoid_: 系列级 = parody Tag；库级 = Tag 词表 / catalog

## 页数消歧（Page Count Disambiguation）

当标题搜索命中多条候选时，用调用方提供的**页数提示**（本地统计页数）选取 `|候选页数 − 提示页数|` 最小者。页数提示可选；未提供时行为与 v1 `search` 一致（对前 `--limit` 条拉详情）。

搜索命中在内部归一为 **SearchCandidate**（`external_id` / `title` / `list_page_count`）；adapter 负责把来源站列表字段映射为 `list_page_count`，消歧规则集中在 `page_disambiguation` 模块，与 HTTP 解耦。
_Avoid_: 页码（pagination）；相似度排序（本工具 v1 不做标题 fuzzy 匹配）

## 页数（Page Count）

本子图像页总数，用于输出契约字段 `page_count` 与页数消歧。来源站字段名因站而异（如禁漫 `page_count`、哔咔 `pagesCount`）；输出统一为 `page_count`。
_Avoid_: pages（易与搜索分页混淆）

## SearchTagsResponse（按标题搜索输出）

按标题搜索命令的 JSON 契约。`items[]` / `errors[]` 与 `FetchTagsResponse` 同形；另含 `query`、`total_hits` 等搜索元字段；启用页数消歧时可含 `ambiguous[]`。`command` 为 `"search"`。
_Avoid_: 与 `FetchTagsResponse` 混称；列表页不完整 tags 当作最终输出

## SearchBatchResponse（批量按标题搜索输出）

批量刮削命令的 JSON 契约。`items[]` 每条含 `local_id`（调用方本地键）及与 search 相同的本子字段；`ambiguous[]` 记录无法唯一消歧的本地本子；`errors[]` 含 `local_id` 与错误信息。`command` 为 `"search-batch"`。
_Avoid_: 与 `SearchTagsResponse` 混称；把 batch 结果当作 tag 词表

## 哔咔：用户凭证（User Credentials）

用户需提供的秘密信息，仅 **账号 + 密码**。导线层字段名可能叫 `email`，领域仍称「账号」（值可以是邮箱形态的字符串）。
_Avoid_: 邮箱（作领域名）、账号 token、api-key、签名密钥（这些不是用户配置项）

## 哔咔：客户端常量（Client Constants）

模拟官方 App 所需的固定值，硬编码于客户端（如 `api-key`、HMAC `secret_key`、App 请求头）。
用户无需、也不应配置；若密钥轮换，通过更新客户端代码或高级环境变量覆盖。
_Avoid_: 凭证、用户秘密

## 网络可达性 / 代理（Network Reachability）

代理 **不是** 哔咔 API 的逻辑前提，而是当运行环境无法直连 `picaapi.picacomic.com` 时的可选兜底。
默认直连；国内本地 Windows 环境常需手动配置代理或依赖 VPN。
_Avoid_: 刚需代理、API 必填项
