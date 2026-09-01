---
title: 调研哔咔按标题/关键词搜索 API
labels: [wayfinder:research]
status: closed
assignee: agent
map: map-title-search.md
blocked_by: []
---

## Question

哔咔通过**本子标题或关键词**定位本子时，应使用哪条 API（`GET /comics/search` vs `POST /comics/advanced-search` vs `GET /comics?t=&a=` 等）？需明确：

1. 请求参数、分页模型、认证/签名要求
2. 列表项返回字段（是否含 `_id`、`title`、部分 tags）
3. 对「完整标题字符串」vs「片段关键词」的匹配行为与结果质量
4. 与现有 `BikaClient` / 详情 `GET /comics/{id}` 的衔接方式
5. 限速与错误模式（空结果、429 等）

产出：`docs/research/bika-title-search.md`（或更新 `bika-api-tags.md` 专节），含推荐调用路径与示例。

## Resolution

产出 [`docs/research/bika-title-search.md`](../../docs/research/bika-title-search.md)。

- 标题/关键词默认 **`POST /comics/advanced-search?page={page}`**（`keyword` + 可选 `categories`/`sort`）；`GET /comics/search` 为遗留端点，新项目不采用
- `GET /comics?t=&a=` 为 tag/作者**结构化筛选**，非标题全文搜索；`c` 生效时其他筛选无效
- 分页：`data.comics.{docs,page,pages,total,limit}`，每页通常 20 条；advanced-search 可能缺 `pagesCount`/`epsCount`
- 列表含 `_id`、`title`、`author`、`categories`，**不含**自由 `tags[]`；完整 tags 须 **`GET /comics/{id}`** → 复用 `fetch_comic_bika`
- 匹配：无精确匹配参数；默认 `sort=ua`（相关性）；按「候选列表 + 客户端消歧」设计
- 集成：新增 `BikaClient.search_comics_page()` + `bika_ops.search_comics_bika()` → search→detail 流水线
