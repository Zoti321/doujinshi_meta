---
title: 按标题搜索的目标形态与边界
labels: [wayfinder:grilling]
status: closed
assignee: agent
map: map-title-search.md
blocked_by: []
---

## Question

「通过本子标题爬取本子元数据」的**交付边界**是什么？

需决策：

1. 主场景：用户手头有一个标题（从文件名/手动输入/Flutter UI），要拿到该本的 tags — 是否准确？
2. 新命令 `djm search` vs 扩展 `djm fetch --query` / `--title`
3. 双来源是否 v1 都做
4. v1 是否支持批量标题；是否必须一次只查一本
5. 与现有 `fetch --ids` 的关系（search 内部是否总是 search → detail）

## Resolution

用户采纳全部推荐：

1. **主场景**：关键词/标题搜索；命中多条时返回有限候选并拉详情；**批量标题文件 v1 不做**
2. **CLI**：新子命令 **`djm search`**（不与 `fetch --ids` 混用）
3. **来源站**：v1 **`bika` + `jmcomic` 双站**
4. **多命中**：对前 **`--limit` 条**（默认 **10**）全部拉详情写入 `items[]`
5. **管线**：search 内部恒为 **search → detail**（列表页 tags 不完整，同 `fetch`）；输出为新契约 **`SearchTagsResponse`**（`command: "search"`，`items[]`/`errors[]` 结构与 fetch 一致，另含 `query`、`total_hits` 等元字段）
