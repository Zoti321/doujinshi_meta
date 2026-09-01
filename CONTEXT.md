# 领域词汇表

## 产品（doujinshi-meta / `djm`）

从外部来源站爬取**本子元数据**的 CLI / Python 库。当前交付主要为标题与多维 Tag（见输出契约）；`meta` 描述现状，不承诺近期扩封面/页数等字段。CLI 主命令为 `djm`。
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

## SearchTagsResponse（按标题搜索输出）

按标题搜索命令的 JSON 契约。`items[]` / `errors[]` 与 `FetchTagsResponse` 同形；另含 `query`、`total_hits` 等搜索元字段。`command` 为 `"search"`。
_Avoid_: 与 `FetchTagsResponse` 混称；列表页不完整 tags 当作最终输出

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
