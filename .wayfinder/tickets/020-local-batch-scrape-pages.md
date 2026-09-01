---
title: 实现 search 页数消歧与 search-batch 批量本地刮削
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee: agent
parent: map-local-scrape.md
blocked_by: []
---

## Problem Statement

作为将 `doujinshi-meta` 集成进漫画 App 的开发者，我的 App 本地库中有大量本子，通常只有**文件名/标题**，有时还有**本地统计页数**，缺少来源站 `external_id` 与 tags。现有 `djm search` 虽能按标题搜索，但在同一标题多汉化/多上传时会**对前 N 条全部拉详情**，无法自动选定与用户本地文件一致的那一本；也**没有**面向「系列文件夹」或「整库」的批量输入契约。我需要在 CLI 与 Python 库中支持：**可选页数消歧**、**单本 `page_count` 输出**，以及 **`search-batch` 批量刮削**（JSONL 输入，带 `local_id`），以便 App 以子进程或库 API 驱动本级/系列级/库级刮削并把结果写回本地 DB。

## Solution

1. **扩展 `djm search`**：新增可选 **`--pages N`**。提供时启用**页数消歧**——在搜索候选中选取页数最接近的一本，仅对其拉完整 tags 并输出；无法唯一确定时写入 **`ambiguous[]`**。未提供 `--pages` 时行为不变。
2. **扩展输出**：`ComicTagsItem` 增加可选 **`page_count`**；`SearchTagsResponse` 增加可选 **`ambiguous[]`**。
3. **新增 `djm search-batch`** 与库函数 **`search_batch_tags`**：读取 **`--input`** JSONL（每行 `local_id` + `title` + 可选 `pages`），逐本执行与 search 相同的 search→消歧→detail 管线，输出 **`SearchBatchResponse`**（`items[]` / `ambiguous[]` / `errors[]` 均带 `local_id`）。
4. 更新 **`docs/schema.md`**、JSON Schema 与 **`CONTEXT.md`**（已在 grilling 阶段更新词汇）。

## User Stories

### 页数消歧（search）

1. As a CLI 用户, I want `djm search --source jmcomic "标题" --pages 42`, so that 多命中时自动选页数最接近 42 的本子。
2. As a CLI 用户, I want 未传 `--pages` 时 search 行为与现版完全一致, so that 现有脚本与测试不受影响。
3. As a CLI 用户, I want 页数消歧成功时 `items[]` 仅含 1 条, so that App 可直接写入 DB 而无需再选。
4. As a CLI 用户, I want 消歧失败（平局或无页数数据）时 `items=[]` 且 `ambiguous[]` 列出候选, so that App 可提示用户手动选择。
5. As a CLI 用户, I want `ambiguous[]` 中候选含 `external_id`、`title`、`page_count`（已知时）, so that UI 能展示对比信息。
6. As a CLI 用户, I want `--pages` 与 `--limit` 协同：limit 限制**扫描候选数**（默认 10）, so that 宽关键词不会拉取过多详情。
7. As a CLI 用户, I want 消歧时优先用搜索列表中的页数字段, so that 多数情况少打详情请求。
8. As a CLI 用户, I want 列表无页数时对候选拉详情补 `page_count` 再比对, so that 禁漫等来源仍可消歧。
9. As a CLI 用户, I want 命中 0 条时 `items=[]`、`ambiguous=[]`, so that 与现版空结果语义一致。
10. As a CLI 用户, I want 消歧选定后仍走 search→detail 完整 tags, so that tags 与 fetch 一致（非列表页子集）。
11. As a CLI 用户, I want 选定本的 `page_count` 出现在 `items[]`, so that App 可校验与本地统计是否一致。
12. As a CLI 用户, I want `--pages` 必须为正整数, so that 误输入可被 CLI 拒绝。
13. As a CLI 用户, I want 搜索阶段致命错误仍 exit 2, so that 与 fetch/search 现语义一致。
14. As a CLI 用户, I want 消歧成功但详情失败时记入 `errors[]`, so that 与 fetch 部分失败语义一致。

### 批量刮削（search-batch）

15. As a CLI 用户, I want `djm search-batch --source jmcomic --input books.jsonl`, so that 一次命令刮削多本本地本子。
16. As a CLI 用户, I want JSONL 每行含 `local_id` 与 `title`, so that 输出能关联回 App 本地键。
17. As a CLI 用户, I want JSONL 每行可选 `pages`, so that 批量场景也能页数消歧。
18. As a CLI 用户, I want 输出 `SearchBatchResponse` 且 `command` 为 `"search-batch"`, so that 集成方可区分单搜与批搜。
19. As a CLI 用户, I want `items[]` 每条含 `local_id` + 与 search 相同的本子字段, so that 解析逻辑可复用 `ComicTagsItem`。
20. As a CLI 用户, I want `ambiguous[]` 每条含 `local_id` 与 `candidates[]`, so that App 能逐本处理未决条目。
21. As a CLI 用户, I want `errors[]` 含 `local_id` 与 `message`, so that 批量失败可定位到具体本地本子。
22. As a CLI 用户, I want batch 串行处理并尊重 `--delay`, so that 整库刮削不会瞬间打爆来源站。
23. As a CLI 用户, I want batch 共享 `--proxy` / `--config` / 哔咔凭证, so that 配置与 search 一致。
24. As a CLI 用户, I want 空 input 文件或全无效行时 exit 2, so that 误用可被发现。
25. As a CLI 用户, I want JSONL 中单行 JSON 解析失败记入 `errors[]` 并继续下一行, so that 单行脏数据不拖垮整批。
26. As a CLI 用户, I want 缺少 `local_id` 或 `title` 的行记入 `errors[]`, so that 契约字段强制可验证。
27. As a Flutter 集成方, I want 系列级刮削 = 把文件夹内本子写成 JSONL 调 search-batch, so that 我不需要不同 CLI 命令。
28. As a Flutter 集成方, I want 库级刮削 = 把全库写成 JSONL 调 search-batch, so that 系列级与库级共用同一集成路径。
29. As a Flutter 集成方, I want batch stdout 为单一 JSON 对象, so that 子进程一次解析拿全库结果。
30. As a Flutter 集成方, I want 部分成功时 exit 1、全无 items 仅 errors 时 exit 2, so that 与 fetch/search 退出码策略对齐。

### 库 API 与 fetch 扩展

31. As a 库调用方, I want `search_tags(..., pages=N)` 支持页数消歧, so that 测试与脚本可不经过 CLI。
32. As a 库调用方, I want `search_batch_tags(input_path, source, ...)` 返回 `SearchBatchResponse`, so that 与 CLI 同结构。
33. As a 库调用方, I want 两函数从 `doujinshi_meta` 导出, so that 与现有 API 并列。
34. As a 库调用方, I want `fetch_tags` 产出的 `ComicTagsItem` 也含 `page_count`, so that 按 ID 拉取与 search 字段一致。
35. As a 维护者, I want 页数提取封装在来源 ops 层, so that 哔咔/禁漫字段差异不泄漏到 search 编排。
36. As a 维护者, I want 搜索列表函数返回 `(id, title, page_count|None)` 三元组, so that 消歧层可统一处理。
37. As a 维护者, I want 消歧逻辑集中在 search 编排模块, so that search 与 search-batch 共用同一函数。
38. As a 维护者, I want search-batch 内部对每行调用共享的「单本刮削」逻辑, so that 行为不与 search 分叉。

### 来源站

39. As a 维护者, I want 禁漫详情 `album.page_count` 映射到输出 `page_count`, so that 与调研文档一致。
40. As a 维护者, I want 哔咔列表 `pagesCount` 与详情页数字段映射到 `page_count`, so that 消歧可优先用列表。
41. As a 维护者, I want 哔咔 `pagesCount` 缺失时不伪造页数, so that 消歧可降级到详情或 ambiguous。
42. As a 维护者, I want 双来源 search-batch 均支持, so that App 按来源站分 batch 调用。

### 文档与契约

43. As a 文档读者, I want `docs/schema.md` 描述 `page_count`、`ambiguous`、`SearchBatchResponse`, so that 契约与实现同步。
44. As a 文档读者, I want JSON Schema 更新且新字段 optional, so that 旧客户端不因新字段崩溃。
45. As a 文档读者, I want README 含 search `--pages` 与 search-batch 示例, so that 集成方发现新能力。
46. As a 文档读者, I want CONTEXT 中刮削级别与页数消歧术语已定义, so that spec 与词汇表一致。

### 测试

47. As a 测试维护者, I want 在 `search_tags` 接缝 stub search+fetch 测消歧, so that 不依赖真网。
48. As a 测试维护者, I want 覆盖：唯一最近页数、平局 ambiguous、无页数 ambiguous、无 `--pages` 回归。
49. As a 测试维护者, I want `search_batch_tags` 测多行成功/ambiguous/error 混合, so that 批量语义可回归。
50. As a 测试维护者, I want CliRunner 测 search `--pages` 与 search-batch 参数校验, so that CLI 薄层可回归。

## Implementation Decisions

### 接缝（测试）

- **主测试接缝（唯一）**：库层 **`search_tags()`**（扩展 `pages: int | None`）与新建 **`search_batch_tags()`**。测试 stub **`search_comics_*`**（返回含可选 `page_count` 的候选列表 + `total_hits`）与 **`fetch_comic_*`**（返回含 `page_count` 的 `ComicTagsItem`），断言消歧结果、`ambiguous[]`、`SearchBatchResponse` 结构与 exit 语义。**不**在测试中断言 HTTP 路径或来源站内部字段名。
- **次要接缝**：CliRunner stub 上述库函数，覆盖 `--pages` 校验、空 input、stdout JSON 形状；prior art：`tests/test_search_tags.py`、`tests/test_cli_search.py`。

### 领域（grilling 019 已采纳）

- **本级** = 单本 `djm search`；**系列级 / 库级** = 同一 `djm search-batch`，差别仅在 JSONL 行数。
- **页数消歧** = 最小化 `|候选 page_count − 提示 pages|`；平局或无数据 → `ambiguous[]`。

### CLI

**扩展 `djm search`**

- 新增 `--pages`（可选 int，≥1）。与 positional `QUERY` 同用。
- 提供 `--pages` 时：扫描前 `--limit` 个搜索候选做消歧；成功则 **1** 条 `items[]`；失败则 `ambiguous[]`。
- 不提供 `--pages`：现行为不变。

**新增 `djm search-batch`**

- 必填：`--source`、`--input PATH`（JSONL）
- 可选：`-o`、`--proxy`、`--no-proxy`、`--delay`、`--config`（与 search 对齐）
- **无** `--limit`（每行独立 search；每行消歧扫描仍用 search 默认 limit=10，可通过后续扩展 `--scan-limit` 但 v1 固定 10）
- JSONL 行 schema：`{"local_id": str, "title": str, "pages": int?}`

### 库 API

```python
def search_tags(
    query: str,
    source: Source | str,
    *,
    limit: int = 10,
    pages: int | None = None,  # 新增：页数提示；None = 不消歧
    ...
) -> SearchTagsResponse

def search_batch_tags(
    input_path: Path | str,
    source: Source | str,
    *,
    limit: int = 10,  # 每行 search 扫描候选上限
    ...
) -> SearchBatchResponse
```

### 消歧算法（共享 `resolve_search_hit`）

1. 调用来源 search → `candidates: list[(external_id, title, page_count|None)]`，`total_hits`
2. 若 `pages is None`：现逻辑——对前 `limit` 个 ID 串行 fetch，返回多条 `items`
3. 若 `pages` 有值：
   - 取前 `limit` 个候选
   - 对每个候选：若 `page_count is None`，fetch 详情补 `page_count`（仅 tags+page_count 所需；仍用现有 fetch 函数）
   - 计算差值；取最小者
   - 唯一最小 → fetch 完整 tags（若上步已 fetch 可复用）→ 单条 `items`
   - 多个相同最小差值，或所有候选均无 `page_count` → `ambiguous[]`（含已知的 id/title/page_count）
4. `--pages` 模式下不再对 limit 条全部输出到 `items`

### 数据模型

```python
@dataclass
class ComicTagsItem:
    external_id: str
    title: str
    tags: list[TagRef]
    page_count: int | None = None  # 新增 optional

@dataclass
class AmbiguousCandidate:
    external_id: str
    title: str
    page_count: int | None = None

@dataclass
class SearchAmbiguous:
    query: str
    candidates: list[AmbiguousCandidate]

@dataclass
class SearchTagsResponse:
    ...
    ambiguous: list[SearchAmbiguous] = field(default_factory=list)  # 仅 pages 模式

@dataclass
class BatchScrapeItem(ComicTagsItem):
    local_id: str

@dataclass
class BatchAmbiguous:
    local_id: str
    title: str
    candidates: list[AmbiguousCandidate]

@dataclass
class BatchError:
    local_id: str
    message: str

@dataclass
class SearchBatchResponse:
    schema_version: str = "1.0"
    command: str = "search-batch"
    source: str = ""
    generated_at: str = ""
    items: list[BatchScrapeItem] = field(default_factory=list)
    ambiguous: list[BatchAmbiguous] = field(default_factory=list)
    errors: list[BatchError] = field(default_factory=list)
```

- `to_dict()`：`page_count is None` 时可省略字段；`ambiguous` 空数组可省略（与 `kinds` 策略一致）或始终输出空数组——**建议始终输出** `ambiguous`/`errors` 键以便集成方解析稳定。
- `schema_version` 保持 `"1.0"`。

### 来源层

- **`search_comics_jmcomic`**：返回候选时尝试从列表对象取页数；若无则 `None`（详情补）
- **`search_comics_bika`**：从 doc `pagesCount` 取；缺失则 `None`
- **`fetch_comic_*`**：填充 `ComicTagsItem.page_count`（禁漫 `album.page_count`；哔咔详情页数字段）

### 退出码

- **search**：与现版一致；`--pages` 且仅 ambiguous 无 items → exit 0（有候选但未决，非致命）或 exit 1——**决议：exit 0**，App 读 `ambiguous`；详情失败仍按现 errors 规则
- **search-batch**：有 items 且有 errors/ambiguous → 1；无 items 仅有 errors → 2

## Testing Decisions

- **好测试**：只断言 `SearchTagsResponse` / `SearchBatchResponse` 外部字段、items/ambiguous/errors 内容与 CLI stdout/退出码；不断言内部函数名或消歧实现细节。
- **主模块**：扩展 `tests/test_search_tags.py`；新建 `tests/test_search_batch_tags.py`。
- **CLI**：扩展 `tests/test_cli_search.py`；新建 `tests/test_cli_search_batch.py`。
- **必测场景（库）**：
  1. 三候选页数 40/42/50，hint=42 → 1 item，page_count=42
  2. 两候选同差值 → ambiguous，items 空
  3. 无候选页数且详情也无 → ambiguous
  4. pages=None 回归：limit 截断行为不变
  5. batch 3 行：成功 / ambiguous / 坏 JSON 各一
  6. fetch 返回 page_count 字段
- **Prior art**：`tests/test_search_tags.py`、`tests/test_cli_search.py`。

## Out of Scope

- batch checkpoint / `--resume`（v1）
- 标题 fuzzy 相似度、编辑距离排序
- `--scan-limit` 与 `--limit` 分离（v1 固定 10）
- 跨 `bika`+`jmcomic` 单次 batch
- 改造 `catalog` 或 tag 词表
- 本地 DB、HTTP 服务
- 漫画内容下载
- search 多页 `--page` 暴露（仍留给后续）

## Further Notes

- Grilling 019 已关闭；`CONTEXT.md` 已增补本地本子、刮削级别、页数消歧、SearchBatchResponse。
- 哔咔 `pagesCount` 在列表阶段可能缺失——消歧依赖详情 fallback，可能增加 N+1；`--limit` 默认 10 为上限。
- 禁漫 `total_hits` 封顶 10000 行为不变；batch 每行独立 search。
- 实现完成后更新 `map-local-scrape.md` 状态并关闭本 ticket。

## Resolution

已实现：`djm search --pages` 页数消歧；`djm search-batch --input`；`search_batch_tags()`；`ComicTagsItem.page_count`；`SearchTagsResponse.ambiguous`；`SearchBatchResponse`；来源 ops 页数提取；测试 84 passed；文档与 JSON Schema 同步。
