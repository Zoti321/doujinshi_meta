---
title: 按需爬取 CLI 接口形态
labels: [wayfinder:grilling]
status: closed
assignee: agent
parent: map
blocked_by: [004-grilling-unified-schema.md]
blocks: []
---

## Question

在统一 schema 确定后，设计按需爬取的用户界面：

- CLI 子命令（如 `fetch-album`, `fetch-search`, `build-catalog`）
- 输入：来源站、本子 ID / 关键词 / tag 过滤
- 输出：stdout JSON vs 写入 DB/文件
- 与全量爬取命令的关系

## Resolution

随 schema v2 一并定稿，见 [`docs/schema.md`](../../docs/schema.md)。

- `dtg catalog` → `TagCatalogResponse`
- `dtg fetch` → `FetchTagsResponse`
- 默认 stdout JSON；`-o` 写文件
- Flutter：`Process.run('dtg', …)` 或 assets 静态 JSON
