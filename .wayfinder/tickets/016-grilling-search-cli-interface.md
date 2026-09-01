---
title: search 命令 CLI 与输入形态
labels: [wayfinder:grilling]
status: closed
assignee: agent
map: map-title-search.md
blocked_by: []
---

## Question

`djm search`（或等价）的 CLI _flags_ 与输入形态如何设计？

依赖 API 能力与 destination 边界，需决策：

1.  positional `QUERY` vs `--query` / `-q`
2. `--source`、`--proxy`、`--delay` 等与 `fetch` 的对齐
3. `--limit` / `--page` 分页暴露方式
4. `--ids-only`（只搜不拉详情）是否提供
5. Python 库 API 命名（如 `search_tags(query, source, ...)`）

## Resolution

Grilling 采纳推荐项：

1. **Positional `QUERY`**（必填）
2. **`--source`、`--proxy`、`--no-proxy`、`--delay`、`--config`、`-o`** 与 `fetch` 对齐
3. **`--limit`** 默认 10；v1 **不暴露 `--page`**（固定第 1 页 + limit 截断）
4. v1 **不做 `--ids-only`**
5. Python API：**`search_tags(query, source, *, limit=10, ...)`**，包级导出
