---
title: 定义统一 tag 数据 schema
labels: [wayfinder:grilling]
status: closed
assignee: agent
parent: map
blocked_by: [001-research-bika-api-tags.md, 002-research-jmcomic-tags.md]
blocks: [006-grilling-on-demand-cli.md]
---

## Question

两站调研完成后，锁定 v1 统一数据模型：

- 本子级记录字段（`source`, `album_id`, `title`, `tags[]`, `raw_metadata` 等）
- Tag 词表记录字段（`tag`, `source`, `count`, `first_seen` 等）
- 禁漫的 `works`/`actors`/`authors` 是否纳入 `tags[]` 还是仅放 `raw_metadata`？
- 持久化格式（SQLite 表结构 vs JSONL 文件）

需更新 `CONTEXT.md` 词汇（若引入新术语）并产出 schema 草案（可放在 `docs/schema.md`）。

## Resolution

Schema 定稿于 [`docs/schema.md`](../../docs/schema.md)。

**v2 修订（2026-08-30，用户反馈）：**

| 项 | v1 | v2 |
|----|----|----|
| 存储 | SQLite + album 表 | **无 DB**；JSON stdout / `-o` |
| tag 库 | album + album_tag | **仅 tag 词表**（catalog 输出） |
| 集成 | — | **pip 包 + CLI**；JSON Schema 供 Flutter |

详见 [`docs/schema.md`](../../docs/schema.md) v2。
