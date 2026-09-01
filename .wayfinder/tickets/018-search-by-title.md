---
title: 实现 djm search — 按标题/关键词爬取本子元数据
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee: agent
parent: map-title-search.md
blocked_by: []
blocks: []
---

## Problem Statement

作为在本地使用 `djm` 的用户（含通过子进程集成的 Flutter 应用），我手头往往只有**本子标题或关键词**（来自文件名、手动输入或 UI），而不是来源站的 `external_id`。现有 `djm fetch` 仅接受 ID 列表，无法从标题定位本子并拿到与 fetch 一致的元数据（`title` + 多维 `tags[]`）。我需要在不引入数据库的前提下，通过 CLI 与 Python 库完成「搜索 → 拉详情 → JSON 输出」的闭环。

## Solution

新增 **`djm search`** 子命令与库函数 **`search_tags`**：用户传入 positional **QUERY**（标题或关键词）与 `--source {bika|jmcomic}`，工具在来源站搜索匹配本子，对前 **`--limit` 条**（默认 **10**）按既有详情管线拉取完整 tags，stdout 或 `-o` 输出 **`SearchTagsResponse` JSON**。内部恒为 **search → detail**（列表页 tags 不完整，与调研结论一致）。排序沿用来源站默认（哔咔 advanced-search `sort=ua`；禁漫 `search_site` 默认）。

## User Stories

1. As a CLI 用户, I want `djm search --source jmcomic "关键词"`, so that 我能从标题/关键词拿到本子元数据而不必先查 ID。
2. As a CLI 用户, I want `djm search --source bika "关键词"`, so that 哔咔本子同样可按标题检索。
3. As a CLI 用户, I want search 默认 stdout 输出 JSON, so that Flutter 子进程可 `jsonDecode` 解析。
4. As a CLI 用户, I want `-o path.json` 将搜索结果写入文件, so that 我能缓存或交给 CI/assets 流程。
5. As a CLI 用户, I want 每条命中本子含 `external_id`、`title`、`tags[]`（含 `kind`/`name`）, so that 与 `fetch` 单本条目语义一致。
6. As a CLI 用户, I want 响应含 `query` 与 `total_hits`, so that 我知道搜了什么以及来源站报告的总命中数。
7. As a CLI 用户, I want `--limit N` 限制拉详情的本子数（默认 10）, so that 宽关键词不会触发过多 N+1 请求。
8. As a CLI 用户, I want v1 只搜来源站第 1 页再按 limit 截断, so that CLI 表面简单、行为可预期。
9. As a CLI 用户, I want 搜索无结果时 `items=[]` 且正常 JSON 结构, so that 集成方可区分「空结果」与「命令崩溃」。
10. As a CLI 用户, I want 部分详情失败时记入 `errors[]` 且其余 `items[]` 仍返回, so that 与 `fetch` 批量语义一致。
11. As a CLI 用户, I want 退出码与 `fetch` 对齐（0 全成功；1 部分失败；2 致命/无有效输入）, so that 脚本错误处理可复用。
12. As a CLI 用户, I want `--proxy` / `--no-proxy` / `--config` 与 `fetch` 一致, so that 网络与哔咔凭证配置无需新学。
13. As a CLI 用户, I want `--delay` 控制详情请求间隔, so that 我能降低被封/限速风险。
14. As a CLI 用户, I want 空 QUERY 时报错退出码 2, so that 误用可被及时发现。
15. As a 库调用方, I want `search_tags(query, source, *, limit=10, ...)` 返回 `SearchTagsResponse`, so that 测试与脚本可不经过 CLI。
16. As a 库调用方, I want `search_tags` 从 `doujinshi_meta` 包导出, so that 与 `fetch_tags` / `build_catalog` 并列。
17. As a Flutter 集成方, I want `items[]` / `errors[]` 与 `fetch` 同形, so that 解析 `ComicTagsItem` 的逻辑可复用。
18. As a Flutter 集成方, I want `command` 字段为 `"search"`, so that 我能区分 search 与 fetch 响应。
19. As a 维护者, I want 哔咔搜索走 `POST /comics/advanced-search`, so that 与活跃客户端生态一致（非遗留 GET search）。
20. As a 维护者, I want 禁漫搜索走 `search_site`, so that 标题/关键词走站内综合搜索而非 tag/作者维度 API。
21. As a 维护者, I want 哔咔 `BikaClient` 新增分页搜索方法, so that HTTP 细节封装在 client 层。
22. As a 维护者, I want 禁漫 `jmcomic_ops` 新增搜索列表函数, so that 与 `fetch_comic_jmcomic` 并列。
23. As a 维护者, I want 详情阶段复用 `fetch_comic_bika` / `fetch_comic_jmcomic`, so that tag 提取逻辑不重复。
24. As a 维护者, I want 搜索阶段 progress 日志写 stderr, so that stdout 保持纯 JSON 数据面。
25. As a 文档读者, I want `docs/schema.md` 含 `SearchTagsResponse` 专节与 CLI 示例, so that 契约与实现同步。
26. As a 文档读者, I want JSON Schema 文件 `search_tags.schema.json`, so that 可 codegen Dart model。
27. As a 测试维护者, I want 在库接缝 stub 来源搜索+详情, so that 测试不依赖真网。
28. As a 测试维护者, I want CliRunner 测试 CLI 参数校验与 JSON stdout, so that CLI 行为可回归。
29. As a CLI 用户, I want v1 不提供 `--ids-only`, so that 产品聚焦「搜完即元数据」而非两阶段工作流。
30. As a CLI 用户, I want v1 不提供 `--page`, so that 分页复杂度留给后续版本。
31. As a CLI 用户, I want v1 不支持 `--titles-file` 批量标题, so that 范围可控。
32. As a 维护者, I want `schema_version` 仍为 `"1.0"`, so that 与 catalog/fetch 版本策略一致。
33. As a CLI 用户, I want 哔咔 search 需已配置凭证（同 fetch）, so that 认证行为一致。
34. As a 维护者, I want README 列出 `djm search` 示例, so that 用户发现新命令。

## Implementation Decisions

- **接缝（主测试接缝）**：**库层 `search_tags()`**（新建 `search.py`，镜像 `fetch.py` 编排）。测试在该函数上 stub **`search_comics_bika` / `search_comics_jmcomic`**（搜索列表，返回 `(external_id, title)[]` 与 `total_hits`）以及 **`fetch_comic_bika` / `fetch_comic_jmcomic`**（详情），断言 `SearchTagsResponse` 的 `query`、`total_hits`、`items`、`errors`、limit 截断与 delay 调用次数。**不**在测试中断言 HTTP 路径或 jmcomic 内部 `main_tag` 数值。CLI 测试（次要接缝）用 `CliRunner` stub `search_tags`，覆盖空 QUERY、stdout JSON、`command=="search"`；prior art：`tests/test_cli_catalog_table.py`。
- **CLI 形态**：
  - 子命令：`djm search`
  - Positional：`QUERY`（必填字符串）
  - Options：`--source`（必填）、`--limit`（int，默认 10，≥1）、`--output`/`-o`、`--proxy`、`--no-proxy`、`--delay`、`--config`
  - 与 `fetch` 共享 proxy/config/credentials 解析 helper
- **库 API**：`search_tags(query: str, source: Source | str, *, limit: int = 10, proxy=..., delay=..., stderr=..., credentials_path=...) -> SearchTagsResponse`；导出至包 `__init__.py`。
- **编排（search.py）**：
  1. 打开来源 client（同 fetch）
  2. 调用来源 search 函数 → 得 ID 列表 + `total_hits`
  3. 取前 `limit` 个 ID
  4. 串行 `fetch_comic_*`，间隔 `delay`（默认同 fetch：哔咔 1.5s，禁漫 0.4s）
  5. 组装 `SearchTagsResponse`
- **哔咔（BikaClient + bika_ops）**：
  - `BikaClient.search_comics_page(keyword, page=1, sort="ua", categories=None)` → `POST comics/advanced-search?page={page}`，JSON body `{"keyword", "sort", "categories": []}`；解析 `data.comics.docs`、分页字段、`total`
  - `search_comics_bika(client, keyword) -> tuple[list[tuple[str,str]], int]`：仅第 1 页，返回 `[(id, title), ...]` 与 total
- **禁漫（jmcomic_ops）**：
  - `search_comics_jmcomic(client, keyword) -> tuple[list[tuple[str,str]], int]`：`client.search_site(keyword, page=1)`，`iter_id_title()` 收集列表，`page.total` 为 total_hits
- **数据模型（models.py）**：

```python
@dataclass
class SearchTagsResponse:
    schema_version: str = "1.0"
    command: str = "search"
    source: str = ""
    query: str = ""
    total_hits: int = 0
    generated_at: str = ""
    items: list[ComicTagsItem] = field(default_factory=list)
    errors: list[FetchError] = field(default_factory=list)
```

- **errors 语义**：搜索阶段致命错误（未登录、网络全失败）→ 抛 `RuntimeError`，CLI exit 2；搜索成功但 0 条 → 空 `items`，exit 0；有 ID 但某本详情失败 → `errors[]`，若仍有 `items` 则 exit 1，若全无 items 仅 errors 则 exit 2（对齐 fetch）。
- **JSON Schema**：新增 `schemas/search_tags.schema.json`；更新 `docs/schema.md` 功能表与 CLI 示例。
- **领域词汇**：`CONTEXT.md` 已有「按标题搜索」「SearchTagsResponse」；实现后确认与 schema 一致即可。
- **调研依据**：`docs/research/bika-title-search.md`、`docs/research/jmcomic-title-search.md`；Wayfinder 015–017 决议。

## Testing Decisions

- **好测试**：只断言外部可见行为——`SearchTagsResponse` 字段、`items`/`errors` 内容、limit 截断、CLI stdout JSON 与退出码；不断言 Bika 签名算法或 jmcomic 分页内部属性。
- **主模块**：`search.py` 的 `search_tags`（`tests/test_search_tags.py`）；stub 目标为 `doujinshi_meta.search` 内 import 的 `search_comics_*` 与 `fetch_comic_*`。
- **CLI 模块**：`tests/test_cli_search.py` — CliRunner + stub `search_tags`；测空 query、正常 JSON、`command`/`query`/`total_hits` 字段存在。
- **必测场景（库）**：
  1. 搜索返回 3 ID、limit=10 → 3 items，total_hits 来自 stub；
  2. 搜索返回 20 ID、limit=5 → 5 items，fetch 被调用 5 次；
  3. 搜索 0 结果 → items=[]，total_hits=0；
  4. 1 本详情失败 → errors 含该 id，其余 items 仍在，exit 语义由 CLI 层测；
  5. 双来源各至少 1 个 smoke（stub 不同 search 函数）。
- **Prior art**：`tests/test_fetch_bika_errors.py`（库层 + monkeypatch）；`tests/test_cli_catalog_table.py`（CliRunner stub `build_catalog`）。

## Out of Scope

- `--ids-only`（只搜不拉详情）
- `--page` 暴露多页搜索
- `--titles-file` 批量标题
- 跨站合并搜索
- 客户端标题相似度排序 / 消歧 UI
- 表格或人类可读 search 输出
- 修改 `catalog` 枚举策略
- 漫画内容下载
- HTTP 服务

## Further Notes

- Grilling（016 CLI、017 契约）与 Destination（015）决议均已采纳推荐项；无需 prototype。
- 哔咔 `categories` 搜索 body 字段 v1 传空数组（全部分区）；后续可按需扩展 `--category`。
- 禁漫 `total_hits` 极大时 API 可能封顶 10000；原样透传 `page.total` 即可。
- 实现完成后关闭 Wayfinder map-title-search 或将其标为规划完成。

## Resolution

已实现：`djm search`、`search_tags()`、`SearchTagsResponse`；哔咔 `search_comics_page` / `search_comics_bika`；禁漫 `search_comics_jmcomic`；测试 `tests/test_search_tags.py`、`tests/test_cli_search.py`；`schemas/search_tags.schema.json`；文档同步。71 tests pass。
