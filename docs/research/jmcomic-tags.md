# JMComic（禁漫天堂）Tag 抓取调研

> 基于 [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)（PyPI: `jmcomic`，当前源码版本 v2.7.5）  
> 主要来源：[Read the Docs](https://jmcomic.readthedocs.io/zh-cn/latest/)、[常用类和方法](https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/0_common_usage/)、[配置文件指南](https://jmcomic.readthedocs.io/zh-cn/latest/option_file_syntax/)、[域名与重试策略](https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/12_domain_strategy/)、[entity API](https://jmcomic.readthedocs.io/zh-cn/latest/api/entity/)、源码 `jm_entity.py` / `jm_client_impl.py` / `jm_client_interface.py` / `jm_config.py`

---

## 1. 单本 Tag：`get_album_detail` 字段

### 1.1 实体类与调用方式

```python
from jmcomic import JmOption

client = JmOption.default().new_jm_client()
album = client.get_album_detail('410090')  # 或 'JM410090'
```

返回 `JmAlbumDetail`（[entity 文档](https://jmcomic.readthedocs.io/zh-cn/latest/api/entity/)）。

### 1.2 四类元数据字段

| 字段 | 类型 | 含义 | 网页端解析来源 |
|------|------|------|----------------|
| `tags` | `List[str]` | 標籤 | `<li class="tagset tags">` 内 `<a>` 文本 |
| `works` | `List[str]` | 作品（IP/原作） | `<li class="tagset works">` |
| `actors` | `List[str]` | 登場人物 | `<li class="tagset actors">` |
| `authors` | `List[str]` | 作者 | `<li class="tagset authors">` |

源码注释（`jm_entity.py`）：

```python
self.works: List[str] = works      # 作品
self.actors: List[str] = actors    # 登場人物
self.tags: List[str] = tags        # 標籤
self.authors: List[str] = authors  # 作者
```

`author` 属性返回 `authors[0]`；多作者请用 `authors` 列表。

### 1.3 实测示例（album `410090`）

来源：[tests/test_jmcomic/test_jm_client.py](https://github.com/hect0x7/JMComic-Crawler-Python/blob/master/tests/test_jmcomic/test_jm_client.py)

| 字段 | 示例值 |
|------|--------|
| `works` | `['原神', 'Genshin']` |
| `actors` | `['申鶴', '神里綾華', '甘雨']` |
| `tags` | `['C101', '巨乳', '校服', '口交', '乳交', '群交', '連褲襪', '中文', '禁漫漢化組', '纯爱']` |
| `authors` | `['うぱ西']` |

### 1.4 其他有用字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `album_id` / `id` | `str` | 本子 ID |
| `name` / `title` | `str` | 标题 |
| `description` | `str` | 叙述 |
| `page_count` | `int` | 总页数 |
| `pub_date` / `update_date` | `str` | 上架/更新日期 |
| `likes` / `views` | `str` | 喜欢数/观看数（带 K 等单位） |
| `comment_count` | `int` | 评论数 |
| `episode_list` | `List[Tuple]` | 章节列表 `(photo_id, index, title, pub_date)` |

打印全部属性：

```python
props = album.get_properties_dict()
```

### 1.5 搜索页快捷获取 tags

按车号搜索时可直接拿到完整实体：

```python
page = client.search_site(search_query='427413')
album = page.single_album  # JmAlbumDetail
print(album.tags)
```

来源：[常用类和方法 - 搜索本子](https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/0_common_usage/#搜索本子)

---

## 2. 全站枚举：分类 / 排行榜 / 搜索 / 标签搜索

### 2.1 库提供的枚举 API

| 方法 | `main_tag` | 用途 | 返回 |
|------|-----------|------|------|
| `search_site(query, page=1, ...)` | 0 | 站内搜索 | `JmSearchPage` |
| `search_work(query, ...)` | 1 | 按作品搜索 | `JmSearchPage` |
| `search_author(query, ...)` | 2 | 按作者搜索 | `JmSearchPage` |
| `search_tag(query, ...)` | 3 | 按标签搜索 | `JmSearchPage` |
| `search_actor(query, ...)` | 4 | 按登场人物搜索 | `JmSearchPage` |
| `categories_filter(page, time, category, order_by, ...)` | — | 分类浏览 | `JmCategoryPage` |
| `month_ranking(page)` | — | 月排行（= 月+观看数） | `JmCategoryPage` |
| `week_ranking(page)` | — | 周排行 | `JmCategoryPage` |
| `day_ranking(page)` | — | 日排行 | `JmCategoryPage` |

`search_*` 系列均委托底层 `search()`，`main_tag` 区分搜索维度（源码 `jm_client_interface.py`）。

`JmCategoryPage` 与 `JmSearchPage` 为同一类型别名（`jm_entity.py`）。

### 2.2 分类与排行榜

```python
from jmcomic import JmOption, JmMagicConstants

cl = JmOption.default().new_jm_client()

# 全部分类 + 全部时间 + 按观看数
page = cl.categories_filter(
    page=1,
    time=JmMagicConstants.TIME_ALL,
    category=JmMagicConstants.CATEGORY_ALL,
    order_by=JmMagicConstants.ORDER_BY_VIEW,
)

# 排行榜是 categories_filter 的语法糖
page = cl.month_ranking(1)
page = cl.week_ranking(1)
```

可用 `categories_filter_gen()` 自动翻页（[分类/排行榜文档](https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/0_common_usage/#分类--排行榜)）。

**分类常量**（`JmMagicConstants`，`jm_config.py`）：

| 常量 | 值 | 含义 |
|------|-----|------|
| `CATEGORY_ALL` | `'0'` | 全部 |
| `CATEGORY_DOUJIN` | `'doujin'` | 同人 |
| `CATEGORY_SINGLE` | `'single'` | 单本 |
| `CATEGORY_SHORT` | `'short'` | 短篇 |
| `CATEGORY_HANMAN` | `'hanman'` | 韩漫 |
| `CATEGORY_MEIMAN` | `'meiman'` | 美漫 |
| `CATEGORY_3D` | `'3D'` | 3D |
| … | … | 另有 `another`、`doujin_cosplay`、`english_site` 等 |

**时间** `TIME_ALL` / `TIME_MONTH` / `TIME_WEEK` / `TIME_TODAY`  
**排序** `ORDER_BY_LATEST` / `ORDER_BY_VIEW` / `ORDER_BY_PICTURE` / `ORDER_BY_LIKE` 等

### 2.3 搜索页迭代器

```python
page = client.search_tag('無修正', page=1)

# 仅 ID + 标题
for album_id, title in page.iter_id_title():
    ...

# ID + 标题 + 列表页 tags（可能不完整）
for aid, atitle, tag_list in page.iter_id_title_tag():
    ...
```

`iter_id_title_tag()` 来自 `JmPageContent`：列表项 `ainfo['tags']` 为搜索/分类结果页携带的标签子集，**不等于**详情页完整 tag 集。

### 2.4 能否构建完整 Tag 词表？

| 方式 | 能枚举本子 ID？ | 能直接给出全站 tag 列表？ | 结论 |
|------|----------------|--------------------------|------|
| `categories_filter_gen` × 分类 × 时间 × 排序 | ✅ | ❌ | **全量爬取本子 ID 的主路径** |
| `month/week/day_ranking` | ✅（热门子集） | ❌ | 补充热门覆盖，不能替代全量 |
| `search_site` | ✅（需关键词） | ❌ | 适合按需/补洞，不适合词表发现 |
| `search_tag` | ✅（需已知 tag 名） | ❌ | **不能反推全站 tag 列表**；仅正向按 tag 查本子 |

**结论：jmcomic 没有「列出所有 tag」的 API。** 构建 tag 词表的标准流程：

1. 用 `categories_filter_gen`（必要时叠加多 `category` / `time` / `order_by`）收集 `album_id`；
2. 对每个 ID 调用 `get_album_detail` 提取 `tags` / `works` / `actors` / `authors`；
3. 本地去重聚合为词表。

`search_tag` 适合：已知 tag 名后的增量同步或校验，不适合从零发现词表。

### 2.5 高级搜索（仅网页端）

`category` + `sub_category` 组合搜索**仅 `JmHtmlClient` 支持**；移动端 API 明确不支持（`jm_client_impl.py` 注释 + [高级搜索文档](https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/0_common_usage/#高级搜索分类副分类)）。

---

## 3. Web（`JmHtmlClient`）vs Mobile（`JmApiClient`）

### 3.1 创建与默认实现

```python
# 网页端
html_cl = JmHtmlClient(postman=..., domain_list=['18comic.vip'], retry_times=5)

# API 端（APP）
api_cl = JmApiClient(postman=..., domain_list=JmModuleConfig.DOMAIN_API_LIST, retry_times=5)

# 通过 option（默认 impl='api'）
client = JmOption.default().new_jm_client()           # api
client = JmOption.default().new_jm_client(impl='html') # html
```

默认客户端：`JmModuleConfig.DEFAULT_CLIENT_IMPL = 'api'`（`jm_config.py`）。

### 3.2 官方对比（配置文件指南）

> - **api** — APP 端，**不限 IP，兼容性好**
> - **html** — 网页端，**限制 IP 地区，但效率高**

来源：[option_file_syntax](https://jmcomic.readthedocs.io/zh-cn/latest/option_file_syntax/)

### 3.3 IP 限制与错误码

`jm_config.py` 内置错误映射：

| 场景 | 表现 |
|------|------|
| HTTP 403 | `ip地区禁止访问/爬虫被识别` |
| 响应文本 `Restricted Access!` | `禁漫拒绝你所在ip地区的访问，你可以选择: 换域名/换代理` |
| HTTP 500/520/524 | 服务端过载/超时，可换 IP 或稍后重试 |

网页端 `JmHtmlClient.check_special_http_code()` 会识别上述状态并抛错。

### 3.4 功能差异摘要

| 能力 | `JmHtmlClient` | `JmApiClient` |
|------|----------------|---------------|
| 搜索 `category` / `sub_category` | ✅ | ❌ |
| 分类 `sub_category` | ✅ | ❌ |
| 评论发帖 `album_comment` | ✅ | ❌（抛 `NotImplementedError`） |
| 全站评论 `total` / `page_count` | `None` | 有值 |
| API 域名自动更新 | — | ✅ `FLAG_API_CLIENT_AUTO_UPDATE_DOMAIN` |
| 必须携带 cookies | 否 | ✅ `FLAG_API_CLIENT_REQUIRE_COOKIES`（`/setting` 获取） |
| 详情 `get_album_detail` | HTML 正则解析 | JSON API + `JmApiAdaptTool` |

两端 `get_album_detail` 均返回相同结构的 `JmAlbumDetail`，tag 相关字段语义一致。

### 3.5 代理配置

默认使用**系统代理**（`DEFAULT_PROXIES = ProxyBuilder.system_proxy()`）。

`option.yml` 示例：

```yaml
client:
  impl: api   # 或 html
  postman:
    meta_data:
      proxies: 127.0.0.1:7890
      # proxies: null      # 禁用代理
      # proxies: system    # 系统代理（默认）
```

Linux 服务器无全局代理时，动态拉取网页域名也需手动传 proxy（[域名策略文档](https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/12_domain_strategy/)）：

```python
JmModuleConfig.get_html_domain_all(
    postman=JmModuleConfig.new_postman(proxies={
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890',
    })
)
```

**建议：**

- **国内/受限网络**：优先 `api` 客户端；若仍失败再配代理。
- **需要 `sub_category` 细分枚举**：必须用 `html` + 代理。
- **纯 tag 元数据抓取**：`api` 通常足够，无需下载图片。

---

## 4. 分页、限速与最佳实践

### 4.1 分页参数

| 常量 | 值 |
|------|-----|
| `PAGE_SIZE_SEARCH` | **80**（搜索/分类页） |
| `PAGE_SIZE_FAVORITE` | 20（收藏夹） |

分页属性（`JmSearchPage` / `JmPageContent`）：

- `page.total` — 总结果数
- `page.page_size` — 每页条数（搜索固定 80）
- `page.page_count` — `ceil(total / page_size)`
- `page.page_number` — 当前页码

```python
page = client.search_site('+MANA +无修正', page=1)
print(page.total, page.page_size, page.page_count)
```

### 4.2 自动翻页生成器

```python
# 搜索
for page in client.search_gen('mana', page=1):
    for aid, title in page:
        ...

# 分类
for page in client.categories_filter_gen(
    page=1,
    time=JmMagicConstants.TIME_WEEK,
    category=JmMagicConstants.CATEGORY_ALL,
    order_by=JmMagicConstants.ORDER_BY_VIEW,
):
  ...
```

`do_page_iter` 根据 `page_count` 自动终止；也可用 `generator.send({"page": 3})` 动态改参。

### 4.3 重试与域名切换

| 机制 | 默认值 | 说明 |
|------|--------|------|
| `retry_times` | 5 | 单域名失败重试次数，耗尽后换下一域名 |
| `domain` 列表 | 按 impl 自动 | 顺序 failover |
| `advanced_retry` 插件 | 可选 | 多轮域名轮询、单域名失败上限 |

```yaml
plugins:
  after_init:
    - plugin: advanced_retry
      kwargs:
        retry_config:
          retry_rounds: 3
          retry_domain_max_times: 5
```

### 4.4 限速与礼貌爬取

库**未内置固定 QPS 限速**；文档通过下载并发间接提示对站点压力：

- 下载默认 `image: 30` 并发；「数值小，对禁漫压力小」
- 网页端一次最多约 50 张图

**Tag 抓取建议（元数据 only）：**

1. 单线程或低并发（如 2–5 req/s）调用 `get_album_detail`；
2. 开启 `client.cache: true`（`level_option`）避免重复请求；
3. 捕获 `RequestRetryAllFailException` / `MissingAlbumPhotoException` 并记录失败 ID；
4. 持久化 checkpoint（已处理 `album_id`），支持断点续爬；
5. 全量枚举用 `categories_filter_gen`，勿对 `search_tag` 穷举未知 tag 名。

### 4.5 异常处理

```python
from jmcomic import (
    MissingAlbumPhotoException,
    RequestRetryAllFailException,
    JsonResolveFailException,
)

try:
    album = client.get_album_detail(aid)
except MissingAlbumPhotoException:
    ...  # 本子不存在
except RequestRetryAllFailException:
    ...  # 重试耗尽
```

---

## 5. 推荐方案：`doujinshi_tag_geter` 本地工具

### 5.1 架构概览

```
┌─────────────────────────────────────────────────────────┐
│  JmOption (impl=api, proxy, cache, retry)               │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
  全量模式 (crawl)                  按需模式 (fetch)
  categories_filter_gen             get_album_detail(id)
  → album_id 队列                   search_site(id) → single_album
  → get_album_detail                search_tag(name) 补洞
  → SQLite/JSON 存储
         │                               │
         └───────────────┬───────────────┘
                         ▼
              统一 schema: source, album_id, title,
              tags[], works[], actors[], authors[], raw_metadata
                         ▼
                   tag_catalog 聚合表
```

### 5.2 推荐 `option.yml` 骨架

```yaml
log: true
client:
  impl: api                    # IP 兼容性优先
  retry_times: 5
  cache: level_option          # 按需查询去重
  postman:
    meta_data:
      proxies: system            # 或 127.0.0.1:7890
```

### 5.3 全量爬取（构建 tag 词表）

```python
from jmcomic import JmOption, JmMagicConstants

client = JmOption.default().new_jm_client()

CATEGORIES = [
    JmMagicConstants.CATEGORY_ALL,
    JmMagicConstants.CATEGORY_DOUJIN,
    JmMagicConstants.CATEGORY_HANMAN,
    # ... 按需扩展
]

seen_ids = set()
for category in CATEGORIES:
    for page in client.categories_filter_gen(
        page=1,
        category=category,
        time=JmMagicConstants.TIME_ALL,
        order_by=JmMagicConstants.ORDER_BY_LATEST,
    ):
        for album_id, title in page:
            if album_id in seen_ids:
                continue
            seen_ids.add(album_id)
            album = client.get_album_detail(album_id)
            # 写入 DB: album.tags, album.works, album.actors, album.authors
```

注意：同一本子可能出现在多个分类/排序结果中，**必须按 `album_id` 去重**。全站体量极大，务必 checkpoint + 限速。

### 5.4 按需查询

```python
def fetch_album_tags(client, album_id: str) -> dict:
    album = client.get_album_detail(album_id)
    return {
        'source': 'jmcomic',
        'album_id': album.id,
        'title': album.name,
        'tags': album.tags,
        'works': album.works,
        'actors': album.actors,
        'authors': album.authors,
    }
```

按 tag 名拉取关联本子（已知 tag 时）：

```python
for page in client.search_gen('無修正', main_tag=3):  # search_tag 等价
    for aid, title, tags in page.iter_id_title_tag():
        ...
```

### 5.5 客户端选型决策

| 场景 | 推荐 |
|------|------|
| 默认元数据抓取 | **`api`** |
| 需要 `sub_category` 细分 | **`html` + 代理** |
| 受限地区 / 403 | **`api`** 或代理 + 换域名 |
| 高重复按需查询 | `cache: level_option` |
| 大规模详情请求 | 低并发 + checkpoint，**不要**用下载器默认 30 图并发 |

### 5.6 与项目域模型对齐

依据 [CONTEXT.md](../../CONTEXT.md)：

- 保留 `tags` / `works` / `actors` / `authors` 原始值（含繁体，可选 `zhconv` 规范化）；
- `source = "jmcomic"`，`album_id` 为 JM 车号；
- 词表由全量爬取聚合；`search_tag` 仅作增量，不作词表发现源。

---

## 6. 参考链接

| 资源 | URL |
|------|-----|
| GitHub 仓库 | https://github.com/hect0x7/JMComic-Crawler-Python |
| Read the Docs | https://jmcomic.readthedocs.io/zh-cn/latest/ |
| 常用 API | https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/0_common_usage/ |
| 配置语法 | https://jmcomic.readthedocs.io/zh-cn/latest/option_file_syntax/ |
| 域名/重试 | https://jmcomic.readthedocs.io/zh-cn/latest/tutorial/12_domain_strategy/ |
| Entity 文档 | https://jmcomic.readthedocs.io/zh-cn/latest/api/entity/ |
| `JmAlbumDetail` 源码 | https://github.com/hect0x7/JMComic-Crawler-Python/blob/master/src/jmcomic/jm_entity.py |
| Client 实现 | https://github.com/hect0x7/JMComic-Crawler-Python/blob/master/src/jmcomic/jm_client_impl.py |
| 单元测试（字段示例） | https://github.com/hect0x7/JMComic-Crawler-Python/blob/master/tests/test_jmcomic/test_jm_client.py |

---

*调研日期：2026-08-30*
