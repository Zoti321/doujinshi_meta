---
title: 本地批量刮削边界与页数消歧
labels: [wayfinder:grilling]
status: closed
assignee: agent
map: map-local-scrape.md
blocked_by: []
---

## Question

集成 App 需对大量**本地本子**按标题刮削元数据；「系列级」「库级」与「本级」边界如何划分？多命中如何消歧？CLI 形态与输出契约？

## Resolution

用户澄清与推荐项全部采纳：

### 刮削级别（领域）

1. **本级** — 单本本地本子，`djm search QUERY`
2. **系列级 / 库级** — 均为**多本本地本子批量刮削**，差别仅在 App 传入数量与分组；CLI **不**分命令，统一 **`djm search-batch`**
3. **不是** tag 词表（`catalog`）或 Tag Kind「系列」（`parody`）

### 页数消歧

4. **`djm search`** 可选 **`--pages N`**（本地统计页数提示）
5. 提供页数时：在搜索候选（仍受 `--limit` 约束，默认扫描前 10 条）中按 **`|候选页数 − N|` 最小** 选唯一一本拉完整详情
6. 候选页数优先取自**搜索列表**（哔咔 `pagesCount`）；缺失时再对候选拉详情取 `page_count`（禁漫列表常无页数）
7. **平局**（差值相同）或**无任何候选页数**且无法唯一确定 → 写入 **`ambiguous[]`**，不放入 `items[]`
8. **未提供 `--pages`** 时行为与现有 search **完全一致**（对前 limit 条全拉详情）

### CLI 与批量

9. 批量用新子命令 **`djm search-batch`**（不与 positional QUERY 混用）
10. 输入 **`--input`** JSONL，每行：`{"local_id":"…","title":"…","pages":42}`；`pages` 可选
11. 输出 **`SearchBatchResponse`**（`command: "search-batch"`）
12. batch 串行处理每行，共享 proxy/config/credentials；行间 `delay` 同 search
13. v1 **不做** batch checkpoint / 断点续传

### 输出契约

14. **`ComicTagsItem`** 增加可选 **`page_count`**（int）；`fetch` / `search` / batch 均可在详情阶段填充
15. **`SearchTagsResponse`** 增加可选 **`ambiguous[]`**（仅在使用 `--pages` 且未唯一命中时出现）
16. **`SearchBatchResponse`**：`items[]` 含 `local_id`；`ambiguous[]` / `errors[]` 亦含 `local_id`
17. **`schema_version`** 仍为 **`"1.0"`**；新字段均为可选，向后兼容

### 测试接缝

18. 主接缝：**库层 `search_tags()`**（扩展 `pages` 参数）与 **`search_batch_tags()`**（新建）；stub 来源 search + fetch，不断言 HTTP 细节
