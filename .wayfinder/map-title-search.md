---
title: 通过本子标题爬取本子元数据
labels: [wayfinder:map]
status: open
parent_map: null
---

## Destination

交付 **`djm search`** CLI 子命令与 Python 库 API：用户输入**标题或关键词**，从 **`bika` / `jmcomic`** 搜索匹配本子，对前 **`--limit` 条**（默认 10）拉取完整元数据，stdout / `-o` 输出 **`SearchTagsResponse` JSON**（`external_id`、`title`、`tags[]`，及 `query`、`total_hits`）。

内部管线：**search → detail**（不复用列表页 tags）。契约见 [`docs/schema.md`](../docs/schema.md)（实现时增补 search 专节）。

## Notes

- **领域**：本子元数据采集；consult [`CONTEXT.md`](../CONTEXT.md)
- **前置**：主地图 [从哔咔与禁漫天堂爬取本子元数据](map.md) 已交付 `catalog` / `fetch`（按 ID）
- **实现 spec**：[018-search-by-title.md](tickets/018-search-by-title.md)（`ready-for-agent`）

## Decisions so far

- [按标题搜索的目标形态与边界](tickets/015-grilling-search-destination-scope.md) — `djm search` 双站；search→detail；多命中 `--limit` 默认 10 全拉详情；`SearchTagsResponse`；批量标题 v1 不做
- [调研禁漫按标题/关键词搜索 API](tickets/014-research-jmcomic-title-search.md) — `search_site`；列表无 tags；`search_comics_jmcomic` + `fetch_comic_jmcomic`；见 `docs/research/jmcomic-title-search.md`
- [调研哔咔按标题/关键词搜索 API](tickets/013-research-bika-title-search.md) — `POST /comics/advanced-search`；列表无 tags；`search_comics_page()` + `fetch_comic_bika`；见 `docs/research/bika-title-search.md`
- [search 命令 CLI 与输入形态](tickets/016-grilling-search-cli-interface.md) — positional QUERY；对齐 fetch flags；limit 默认 10；无 page/ids-only
- [search 输出 JSON 契约](tickets/017-grilling-search-output-contract.md) — `SearchTagsResponse`；errors 语义对齐 fetch；`search_tags.schema.json`

## Not yet specified

（无 — 规划已完成，待实现）

## Out of scope

- 跨来源站合并搜索
- 本地全文索引 / 离线标题库
- 漫画内容下载
- 改造 `catalog` 全量枚举策略
- v1 批量标题文件（`--titles-file`）
- `--page`、`--ids-only`

## 地图状态

**已实现**（018 已关闭）。Feature 已交付：`djm search` / `search_tags`。

## 子 Ticket

| Ticket | 类型 | 状态 | 阻塞 |
|--------|------|------|------|
| [调研哔咔按标题/关键词搜索 API](tickets/013-research-bika-title-search.md) | research | closed | — |
| [调研禁漫按标题/关键词搜索 API](tickets/014-research-jmcomic-title-search.md) | research | closed | — |
| [按标题搜索的目标形态与边界](tickets/015-grilling-search-destination-scope.md) | grilling | closed | — |
| [search 命令 CLI 与输入形态](tickets/016-grilling-search-cli-interface.md) | grilling | closed | — |
| [search 输出 JSON 契约](tickets/017-grilling-search-output-contract.md) | grilling | closed | — |
| [实现 djm search — 按标题/关键词爬取本子元数据](tickets/018-search-by-title.md) | task | closed | — |
