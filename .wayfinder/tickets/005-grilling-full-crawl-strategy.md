---
title: 全量爬取遍历与限速策略
labels: [wayfinder:grilling]
status: closed
assignee: agent
parent: map
blocked_by: [001-research-bika-api-tags.md, 002-research-jmcomic-tags.md]
blocks: []
---

## Question

全站 **tag 词表**（内存聚合，输出 JSON）的遍历路径：

- 每站选用哪条 API 链路作为主路径（分类 / 排行榜 / 搜索）？
- 并发度、请求间隔、失败重试、代理
- 可选 `--checkpoint` 续爬格式（非 tag 库，仅进度文件）
- 预估数据量与单次全量耗时量级

## Resolution

详见 [`docs/crawl-strategy.md`](../../docs/crawl-strategy.md)。

| 站 | 枚举主路径 | 默认 delay | 并发 |
|----|-----------|------------|------|
| bika | `/categories` + `/comics?c=&page=` → 详情 | 1.5 s | 1 |
| jmcomic | `categories_filter_gen`（多 category 去重）→ 详情 | 0.4 s | 1 |

- checkpoint：JSON 文件，含 `phase` / `tag_counter` / `seen_ids`
- 体量：10⁵ 本量级，数小时～数十小时；stderr 日志，stdout 仅 JSON
