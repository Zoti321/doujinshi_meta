# JMComic（禁漫天堂）按标题/关键词搜索调研

> 基于 [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)（PyPI: `jmcomic` v2.7.5，与项目 `uv.lock` 一致）  
> 关联调研：[jmcomic-tags.md](./jmcomic-tags.md)（tag 枚举与详情字段）  
> Wayfinder ticket：[014-research-jmcomic-title-search.md](../../.wayfinder/tickets/014-research-jmcomic-title-search.md)

---

## 1. 结论摘要

| 问题 | 结论 |
|------|------|
| 标题/关键词搜索用哪个 API？ | **`search_site`**（`main_tag=0`，站内综合搜索） |
| 何时用其他 `search_*`？ | 按作品 IP → `search_work`；作者 → `search_author`；标签 → `search_tag`；角色 → `search_actor` |
| 分页 | `page` 从 1 起；**每页 80 条**；`page.total` / `page.page_count` 可用 |
| 列表页 tags | **API 客户端列表项 tags 恒为空**；`iter_id_title_tag()` 无实用价值（除车号直达） |
| 完整 tags | 必须 **`get_album_detail`**（复用现有 `fetch_comic_jmcomic`） |
| 日文/中文 | 均可搜；简繁体 tag 名通常各自有效；标题匹配为站点模糊搜索，非精确相等 |
| 集成点 | 在 `jmcomic_ops.py` 新增 `search_comics_jmcomic`；详情走现有 `fetch_comic_jmcomic` |

---

## 2. `search_*` 系列对比

### 2.1 底层模型

五个 `search_*` 方法均委托同一 `search()`，仅 `main_tag` 不同（源码 `jm_client_interface.py` → `JmSearchAlbumClient`）：

| 方法 | `main_tag` | 搜索维度 | 适用场景 |
|------|-----------|----------|----------|
| **`search_site(query, page=1, ...)`** | 0 | **站内综合**（标题、描述等） | **用户输入标题/关键词时的默认选择** |
| `search_work(query, ...)` | 1 | 作品（IP/原作，`works` 字段） | 已知原作名，如「原神」「Fate」 |
| `search_author(query, ...)` | 2 | 作者（`authors`） | 按作者名查本子 |
| `search_tag(query, ...)` | 3 | 标签（`tags`） | 已知 tag 名，非标题搜索 |
| `search_actor(query, ...)` | 4 | 登场人物（`actors`） | 按角色名查本子 |

通用可选参数（与分类浏览一致）：

- `order_by`：`ORDER_BY_LATEST`（默认，最新）/ `ORDER_BY_VIEW`（观看数）/ `ORDER_BY_LIKE` 等
- `time`：`TIME_ALL`（默认）/ `TIME_WEEK` / `TIME_MONTH` / `TIME_TODAY`
- `category` / `sub_category`：**仅 `JmHtmlClient` 支持**；项目默认 `api` 客户端忽略这两项

也可用 `search_gen(query, main_tag=0, page=1, ...)` 自动翻页，语义与 `search_site` + 循环等价。

### 2.2 实测差异（2026-09-01，`JmApiClient`，`proxies=None`）

| 查询 | `search_site` | `search_work` | `search_tag` | `search_actor` |
|------|--------------|---------------|--------------|----------------|
| `原神` | 3915 | 3616 | **14** | — |
| `申鶴` | 133 | — | — | 105 |
| `うぱ西` | 44 | — | — | —（`search_author` → 41） |
| `C101` | 1775 | — | 1652 | — |
| `410090`（车号） | 1（直达详情） | — | — | — |

要点：

- **`search_tag('原神')` 仅 14 条**——只匹配标签字段中含「原神」的本子，与标题/作品搜索完全不同；**不可用于标题搜索**。
- **`search_site` 与 `search_work` 结果高度重叠但不等同**：`search_site` 范围更广（含标题、描述等文本）；`search_work` 限定作品元数据。
- **角色名**（如「申鶴」）用 `search_site` 可命中标题含该字的条目；`search_actor` 更窄，仅匹配 `actors` 字段。

### 2.3 搜索语法（布尔组合）

`JmSearchAlbumClient` 文档注释（与禁漫网页搜索一致）：

| 写法 | 含义 | 示例 |
|------|------|------|
| `+词A +词B` | 必须同时包含 | `+原神 +C101` → 65 条 |
| `词A -词B` | 包含 A 但排除 B | `全彩 -人妻` |
| `词A 词B`（空格） | 包含任一即可 | `全彩 人妻` |

实测 `search_site('+原神 +C101')` 有效；适合用户多关键词收窄结果。

### 2.4 车号快捷路径

当查询为**纯数字车号**（或 `JM` 前缀车号）且命中唯一条目时，API 返回 `redirect_aid`，库自动：

1. 调用 `get_album_detail(aid)`
2. 包装为 `JmSearchPage.wrap_single_album()`
3. 设置 `page.single_album` → 完整 `JmAlbumDetail`（含完整 tags）

```python
page = client.search_site('410090')       # 或 'JM410090'
album = page.single_album                 # JmAlbumDetail，tags 完整
```

**注意**：`single_album` 仅在上述 redirect 场景存在；普通多结果搜索访问 `page.single_album` 会 `AttributeError`。应使用 `hasattr(page, 'album')` 或 `getattr(page, 'album', None)` 判断。

---

## 3. 分页模型

### 3.1 常量与属性

| 项 | 值 / 说明 |
|----|----------|
| `JmModuleConfig.PAGE_SIZE_SEARCH` | **80** |
| `page.page_number` | 当前页码（传入的 `page` 参数） |
| `page.page_size` | 固定 80 |
| `page.total` | 总命中数（int；极大结果可能封顶 **10000**） |
| `page.page_count` | `ceil(total / page_size)` |
| `len(page.content)` | 当前页实际条数（末页 ≤ 80） |

### 3.2 迭代方式

```python
# 单页
page = client.search_site('原神', page=1)
for album_id, title in page:                    # 等价 iter_id_title()
    ...

# 自动翻页
for page in client.search_gen('原神', page=1):
    for album_id, title in page:
        ...
```

`search_gen` 内部 `do_page_iter` 根据 `page_count` 终止；支持 `gen.send({'page': 3, 'search_query': '...'})` 动态改参。

### 3.3 排序与时间过滤

- `order_by=ORDER_BY_VIEW` 会改变结果顺序（实测「原神」首页从最新上传变为高观看条目）。
- `time` 参数在 API 端可用；对极高命中词（如「原神」）实测 `TIME_WEEK` 与 `TIME_ALL` 返回相同 `total`，窄查询（如 `CRYOGENIC`）亦可能无差异——**不宜依赖 time 过滤做精确增量**。

---

## 4. 列表字段：`iter_id_title` vs `iter_id_title_tag` vs 详情

### 4.1 迭代器语义

```python
for album_id, title in page.iter_id_title():
    ...

for album_id, title, tag_list in page.iter_id_title_tag():
    ...
```

`JmPageContent.__iter__` 委托 `iter_id_title()`；`JmSearchPage` 与 `JmCategoryPage` 为同一基类。

### 4.2 API 客户端（项目默认）：列表 tags 为空

`JmPageTool.parse_api_to_search_page` 中 `adapt_content` 对 API 列表项仅 `setdefault('tags', [])`——**移动端搜索 JSON 不含 tags 字段**。

实测（`search_site('原神')` 首页 80 条）：

- `iter_id_title_tag()` → 全部 `tag_list == []`
- 对首条 `get_album_detail` → `detail.tags` 有 3+ 项（如 `['AI繪圖', 'NTR', 'CG']`）

**结论：在 `impl=api` 下，`iter_id_title_tag()` 不提供可用 tags；与 [jmcomic-tags.md](./jmcomic-tags.md) 分类页结论一致。**

### 4.3 例外：车号 redirect

`search_site('410090')` 经 `wrap_single_album` 后，列表项 `tags` 来自详情，**完整**（10 项，与 `get_album_detail` 一致）。

### 4.4 HTML 客户端（对比，非项目默认）

`parse_html_to_search_page` 从列表 HTML 解析部分 tags（如 `['AI绘图', 'NTR', 'CG']`），仍为**展示用子集**，且 HTML 端 `page.total` 解析可能为 0（页面结构变动风险）。**不推荐为 `djm search` 切换客户端**；若需 tags 一律走详情。

### 4.5 与 `get_album_detail` 的字段对照

| 字段 | 列表（API 搜索） | 列表（车号 redirect） | `get_album_detail` |
|------|-----------------|----------------------|-------------------|
| `album_id` | ✅ | ✅ | ✅ |
| `title` / `name` | ✅ | ✅ | ✅ |
| `tags` | ❌ 空 | ✅ 完整 | ✅ 完整 |
| `works` / `actors` / `authors` | ❌ | ✅ | ✅ |
| `description` 等 | ❌ | ✅ | ✅ |

---

## 5. 匹配行为：完整标题 vs 关键词；日文/中文

### 5.1 匹配类型

禁漫搜索为**站点侧模糊/分词匹配**，非本地精确字符串相等：

| 查询类型 | 实测 | 说明 |
|----------|------|------|
| 车号 `410090` / `JM410090` | 1 条，redirect 详情 | 最可靠 |
| 独特英文片名 `CRYOGENIC` | 1 条，含 `410090` | 关键词越独特越准 |
| 常见 IP `原神` | 3915 条 | 需结合 `+` 语法或二次筛选 |
| 角色名 `申鶴` | 133 条 | 标题/标签/描述均可能命中 |
| 完整标题字符串 | `total` 仍可能 >1（实测 2691） | **不适合作为唯一键** |
| 作者名片段 `うぱ西` | 44 条（`search_site`） | 日文作者名有效 |

### 5.2 简繁体

| 查询 | `total` |
|------|---------|
| `纯爱`（简） | 10000（封顶） |
| `純愛`（繁） | 10000（封顶） |

站点索引简繁体分别存储的情况较常见；**不做本地简繁转换也可搜**，但命中集可能不完全重叠。项目若需合并结果，可在应用层用 `zhconv` 规范化（与 [jmcomic-tags.md](./jmcomic-tags.md) §5.6 一致），非 jmcomic 库职责。

### 5.3 相关性排序

默认 `order_by=ORDER_BY_LATEST`（按最新）；改为 `ORDER_BY_VIEW` 首页结果完全不同。**相关性由站点算法决定**，库不暴露 score 字段；`djm search` 宜原样返回前 N 条或交由上层消歧。

---

## 6. 与现有 `jmcomic_ops.py` 的集成

### 6.1 现有能力（可复用）

```1:77:src/doujinshi_meta/sources/jmcomic_ops.py
# create_jmcomic_client  — api 客户端、proxies=None、cache、retry
# extract_tags_jmcomic   — album → list[TagRef]
# fetch_comic_jmcomic    — album_id → ComicTagsItem（含完整 tags）
# iter_comic_ids_jmcomic — 全量 catalog 枚举（与搜索无关）
```

搜索实现应**共用 `create_jmcomic_client`**，详情提取**复用 `fetch_comic_jmcomic`**，避免重复解析逻辑。

### 6.2 建议新增接缝

```python
from typing import Iterator
from dataclasses import dataclass

@dataclass
class JmSearchHit:
    external_id: str
    title: str

def search_comics_jmcomic(
    client,
    query: str,
    *,
    page: int = 1,
    limit: int | None = None,
) -> tuple[list[JmSearchHit], int]:
    """search_site 单页；返回 (hits, total)。"""
    page_obj = client.search_site(query, page=page)
    hits: list[JmSearchHit] = []
    for album_id, title in page_obj.iter_id_title():
        hits.append(JmSearchHit(external_id=str(album_id), title=title))
        if limit is not None and len(hits) >= limit:
            break
    return hits, int(page_obj.total or 0)


def search_comics_jmcomic_gen(
    client,
    query: str,
    *,
    max_pages: int | None = None,
) -> Iterator[JmSearchHit]:
    """跨页枚举；用于需要超过 80 条候选时。"""
    for i, page_obj in enumerate(client.search_gen(query, page=1)):
        if max_pages is not None and i >= max_pages:
            break
        for album_id, title in page_obj.iter_id_title():
            yield JmSearchHit(external_id=str(album_id), title=title)
```

### 6.3 推荐 `djm search` 调用链

```
用户 query
    │
    ▼
search_comics_jmcomic(client, query, limit=N)   # 仅 ID + 标题
    │
    ├─ 若仅 1 条且 hasattr(page, 'album')：可直接用 page.single_album，省一次请求
    │
    ▼
对每个候选 external_id：
    fetch_comic_jmcomic(client, id)               # 完整 ComicTagsItem + tags
    │
    ▼
FetchTagsResponse（或未来的 SearchTagsResponse）
```

与 `fetch.py` 模式对齐：

- 客户端单例、请求间 `sleep`（默认 **0.4s**，见 `DEFAULT_DELAY[Source.JMCOMIC]`）
- 错误记入 `FetchError`，不中断其余候选
- **列表阶段不调 `iter_id_title_tag()`**——无收益

### 6.4 车号输入优化

若 `query.strip()` 匹配 `^\d+$` 或 `^JM\d+$`：

1. 可先 `search_site(query)` 利用 redirect 一次拿到 `single_album`；
2. 或直接 `fetch_comic_jmcomic(client, normalize_id(query))`（与现有 `fetch` 一致）。

两种路径 tags 均完整；后者与 `fetch` 行为统一，实现更简单。

### 6.5 不宜改动

| 模块 | 原因 |
|------|------|
| `iter_comic_ids_jmcomic` | catalog 全量枚举，非搜索 |
| `extract_tags_jmcomic` | 详情解析已满足搜索后补全 |
| 默认改 `impl=html` | IP 限制 + total 解析不稳；仅为列表 tags 得不偿失 |

---

## 7. 错误与限速

| 场景 | 表现 | 处理 |
|------|------|------|
| 无结果 | `total=0`，`content=[]` | 返回空列表 |
| 本子不存在（详情） | `MissingAlbumPhotoException` | 已有 fetch 错误路径 |
| 网络/域名失败 | `RequestRetryAllFailException` | `retry_times=5` + 记录错误 |
| 结果过多 | `total` 封顶 10000 | 提示用户收窄关键词（`+` 语法） |
| 限速 | 库无内置 QPS | 沿用 fetch 的 0.4s 间隔；列表+详情 N+1 需注意总耗时 |

---

## 8. 推荐方案（决策表）

| 用户意图 | API | 列表字段 | 详情补全 |
|----------|-----|----------|----------|
| 标题/关键词/模糊查找 | **`search_site`** | `iter_id_title` | **`fetch_comic_jmcomic`** |
| 已知原作/IP | `search_work` | 同上 | 同上 |
| 已知作者 | `search_author` | 同上 | 同上 |
| 已知角色 | `search_actor` | 同上 | 同上 |
| 已知 tag 名 | `search_tag` | 同上 | 同上 |
| 车号 | `fetch` 或 `search_site` redirect | — | 已完整 |

**v1 `djm search` 默认仅暴露 `search_site`**；其他 `search_*` 可作为 `--dimension work|author|tag|actor` 的后续扩展，无需改详情路径。

---

## 9. 完整示例

```python
from jmcomic import JmMagicConstants
from doujinshi_meta.sources.jmcomic_ops import (
    create_jmcomic_client,
    fetch_comic_jmcomic,
)

client = create_jmcomic_client()

# 1) 关键词搜索（分页）
page = client.search_site("原神", page=1, order_by=JmMagicConstants.ORDER_BY_LATEST)
print(page.total, page.page_count)  # 3915 49

candidates = [(aid, title) for aid, title in page.iter_id_title()]

# 2) 多关键词收窄
page = client.search_site("+原神 +C101", page=1)
print(page.total)  # 65

# 3) 补全 tags（搜索 → fetch）
for album_id, title in candidates[:5]:
    item = fetch_comic_jmcomic(client, album_id)
    print(item.external_id, item.title, len(item.tags))

# 4) 车号直达
page = client.search_site("410090")
if hasattr(page, "album"):
    album = page.single_album
    print(album.tags)  # 完整 10 项
```

---

## 10. 参考

| 资源 | URL |
|------|-----|
| 常用 API（搜索本子） | https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/0_common_usage/ |
| Tag 调研（详情字段） | [jmcomic-tags.md](./jmcomic-tags.md) |
| `JmSearchAlbumClient` | `jm_client_interface.py` |
| `JmApiClient.search` / redirect | `jm_client_impl.py` |
| `JmPageTool.parse_api_to_search_page` | `jm_toolkit.py` |
| 项目接缝 | `src/doujinshi_meta/sources/jmcomic_ops.py` |

---

*调研日期：2026-09-01 · 库版本 jmcomic 2.7.5 · 客户端 impl=api · proxies=None*
