---
title: 本地本子批量元数据刮削与页数消歧
labels: [wayfinder:map]
status: closed
parent_map: map.md
---

## Destination

扩展 **`djm search`** 与新增 **`djm search-batch`**：集成 App 对**本地本子**（已知标题，可选页数）按标题从 **`bika` / `jmcomic`** 刮削元数据。支持**页数消歧**（多命中时选页数最接近者）；系列级/库级刮削统一走 **`search-batch`** JSONL 输入。契约见 [`docs/schema.md`](../docs/schema.md)（实现时增补）。

## Notes

- **领域**：本地本子刮削级别（本级 / 系列级 / 库级）；consult [`CONTEXT.md`](../CONTEXT.md)
- **前置**：[`map-title-search.md`](map-title-search.md) 已交付 `djm search` / `search_tags`
- **实现 spec**：[020-local-batch-scrape-pages.md](tickets/020-local-batch-scrape-pages.md)（`ready-for-agent`）

## Decisions so far

- [本地批量刮削边界与页数消歧](tickets/019-grilling-local-batch-scrape.md) — 系列级/库级 = 批量 search；`--pages` 消歧；独立 `search-batch`；`page_count` 输出

## Not yet specified

- batch 断点续传（v1 不做）
- 标题相似度 / fuzzy 匹配（v1 不做）

## Out of scope

- 改造 `catalog` 全量枚举
- 本地 DB / 持久化（仍由调用方负责）
- 跨来源站单次 batch
- 漫画内容下载

## 地图状态

**已实现**（020 已关闭）。Feature 已交付：`search --pages`、`search-batch`。

## 子 Ticket

| Ticket | 类型 | 状态 | 阻塞 |
|--------|------|------|------|
| [本地批量刮削边界与页数消歧](tickets/019-grilling-local-batch-scrape.md) | grilling | closed | — |
| [实现 search 页数消歧与 search-batch](tickets/020-local-batch-scrape-pages.md) | task | closed | — |
