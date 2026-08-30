---
title: 调研禁漫天堂的 tag 与本子枚举能力
labels: [wayfinder:research]
status: closed
assignee: agent
parent: map
blocked_by: []
blocks: [004-grilling-unified-schema.md, 005-grilling-full-crawl-strategy.md]
---

## Question

禁漫天堂（JMComic）通过 `jmcomic` 库或等价 API/Web 端，能否支撑：

1. **单本 tag**：`get_album_detail` 返回的 `tags`、`works`、`actors`、`authors` 字段结构与示例？
2. **全站枚举**：分类页、排行榜、站内搜索、标签搜索等哪种方式最适合「遍历本子建 tag 词表」？Web vs Mobile client 差异、IP/代理需求、分页与 `search_tag` 能否反推全站 tag 列表？

产出：`docs/research/jmcomic-tags.md`，引用 jmcomic 文档与源码。

## Resolution

结论见 [`docs/research/jmcomic-tags.md`](../../docs/research/jmcomic-tags.md)。

- 单本：`get_album_detail` → `tags`/`works`/`actors`/`authors` 四类 `List[str]`
- 全站词表：无 tag 目录 API；主路径为 `categories_filter_gen` 枚举 ID + 批量详情
- 默认 `api` 客户端 IP 兼容性好；`html` 需代理但支持副分类
