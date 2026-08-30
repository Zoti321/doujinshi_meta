---
title: 调研哔咔 API 的 tag 与本子枚举能力
labels: [wayfinder:research]
status: closed
assignee: agent
parent: map
blocked_by: []
blocks: [004-grilling-unified-schema.md, 005-grilling-full-crawl-strategy.md]
---

## Question

哔咔（PicaComic）非官方 API 能否支撑本项目两类需求？

1. **单本 tag**：给定本子 ID，如何获取 tags 及关联元数据（categories、author 等）？
2. **全站枚举**：是否存在分类/排行榜/搜索等分页接口，可遍历「全部或绝大部分本子」以聚合 tag 词表？分页参数、速率限制、认证（login + signature + timestamp）的具体要求是什么？

产出：`docs/research/bika-api-tags.md`，每条结论附 primary source（官方不可用时引用开源库源码或 Apifox 文档 URL）。

## Resolution

结论见 [`docs/research/bika-api-tags.md`](../../docs/research/bika-api-tags.md)。

- 单本 tag：`GET /comics/{id}` → `data.comic.tags`
- 全站词表：无 tag 目录 API；主路径为分类分页枚举 + 逐本拉详情
- 认证：login token + HMAC-SHA256 签名头；国内需代理，建议低 QPS
