---
title: search 输出 JSON 契约
labels: [wayfinder:grilling]
status: closed
assignee: agent
map: map-title-search.md
blocked_by: []
---

## Question

按标题搜索的 stdout JSON 契约如何定？

需决策：

1. 复用 `FetchTagsResponse`（`command: "fetch"`）还是新 `SearchTagsResponse`（含 `query`、命中数、候选排名等）
2. 多命中时 `items[]` 是否全部拉详情，还是仅列表字段 + 可选 `--full`
3. `errors[]` 语义（无结果 vs 部分详情失败）
4. `schema_version` 与 JSON Schema 文件命名
5. Flutter 集成是否要求与 `fetch` 相同解析路径

## Resolution

Grilling 采纳推荐项：

1. 新 **`SearchTagsResponse`**，`command: "search"`；`items[]`/`errors[]` 与 fetch 同形
2. 多命中：前 **`limit` 条全部拉详情**（无 `--full` 开关）
3. **无结果** → `items=[]`，不进 `errors`；**详情失败** → `errors[]`（对齐 fetch）
4. **`schema_version: "1.0"`**；**`schemas/search_tags.schema.json`**
5. Flutter 复用 `ComicTagsItem` / `FetchError` 解析；靠 `command` 区分来源
