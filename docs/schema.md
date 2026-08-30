# Tag 输出 Schema（v2）

> 修订：无数据库、无 album 持久化；CLI **stdout 输出 JSON**；可被 Flutter 等项目集成。

## 两大功能

| 功能 | CLI 命令（草案） | 输出 |
|------|------------------|------|
| **1. 构建 tag 词表** | `dtg catalog --source {bika\|jmcomic}` | 去重 tag 列表 + 出现次数 |
| **2. 爬取本子 tag** | `dtg fetch --source … --ids id1,id2` | 每本漫画的 tag 列表（不落库） |

持久化由**调用方**负责（Flutter 写本地 DB、缓存 JSON 等）；本工具只负责爬取与序列化。

---

## 设计原则

| 原则 | 说明 |
|------|------|
| **词表即 tag 库** | 功能 1 只产出 `TagCatalog`；不维护 album / 关联表 |
| **无内置存储** | 不写 SQLite；可选 `-o path.json` 写文件，默认打印 stdout |
| **稳定 JSON 契约** | 版本字段 + JSON Schema，供 Flutter `jsonDecode` / 代码生成 |
| **双入口** | CLI（子进程集成）+ Python 库 API（同结构 dataclass） |
| **kind 分维** | 禁漫 `works`/`actors`/`authors` 与 `tags` 分开，不混数组 |

---

## 公共类型

### Source

`"bika"` | `"jmcomic"`

### TagKind

`"tag"` | `"category"` | `"work"` | `"actor"` | `"author"`

| kind | 哔咔 | 禁漫 |
|------|------|------|
| `tag` | `comic.tags[]` | `album.tags[]` |
| `category` | `comic.categories[]` | — |
| `work` | — | `album.works[]` |
| `actor` | — | `album.actors[]` |
| `author` | `comic.author` | `album.authors[]` |

---

## 功能 1：`TagCatalogResponse`

全量爬取过程中在内存聚合 `(source, kind, name) → count`，结束后输出。

```json
{
  "schema_version": "1.0",
  "command": "catalog",
  "source": "jmcomic",
  "generated_at": "2026-08-30T05:00:00Z",
  "stats": {
    "albums_scanned": 12000,
    "tags_unique": 3842,
    "errors": 3
  },
  "tags": [
    { "kind": "tag", "name": "巨乳", "count": 1523 },
    { "kind": "work", "name": "原神", "count": 89 }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `tags[].kind` | string | TagKind |
| `tags[].name` | string | 原始标签名 |
| `tags[].count` | int | 出现于多少本子 |

v1 按 **source 分词表**，不做跨站合并。

---

## 功能 2：`FetchTagsResponse`

单个或批量 ID；每本一条，**不写入 tag 词表文件**（调用方可自行合并）。

```json
{
  "schema_version": "1.0",
  "command": "fetch",
  "source": "bika",
  "generated_at": "2026-08-30T05:00:00Z",
  "items": [
    {
      "external_id": "64a1b2c3d4e5f6789012345",
      "title": "[xx组] 示例标题",
      "tags": [
        { "kind": "tag", "name": "全彩" },
        { "kind": "category", "name": "同人" },
        { "kind": "author", "name": "作者名" }
      ]
    }
  ],
  "errors": [
    { "external_id": "bad-id", "message": "not found" }
  ]
}
```

批量：`--ids id1,id2` 或 `--ids-file paths.txt`（一行一个 ID）。

---

## CLI 约定

```bash
# 开发（uv）
uv sync
uv run dtg catalog --source jmcomic

# 安装 CLI
uv tool install .

# 功能 1：构建 tag 词表
dtg catalog --source jmcomic
dtg catalog --source bika -o bika-tags.json

# 功能 2：爬取本子 tag
dtg fetch --source jmcomic --ids 410090,427413
dtg fetch --source bika --ids-file ids.txt

# 通用（默认直连，不设代理）
dtg catalog --source jmcomic

# 单次使用代理
dtg --proxy http://127.0.0.1:7890 catalog --source bika

# 持久配置代理
dtg config set proxy http://127.0.0.1:7890
dtg config show
dtg config unset proxy

# 忽略持久配置，强制直连
dtg --no-proxy catalog --source bika
```

| 选项 | 说明 |
|------|------|
| `-o, --output` | 写文件；省略则 stdout |
| `--proxy` | 单次 HTTP 代理 URL；默认不使用代理 |
| `--no-proxy` | 强制直连，忽略 `config.toml` / `DTG_PROXY` |
| `--config` | 配置文件路径（默认见 `docs/credentials.md`） |
| `dtg config` | `set proxy` / `unset proxy` / `show` — 持久代理配置 |
| 哔咔凭证 | 环境变量 `DTG_BIKA_EMAIL`、`DTG_BIKA_PASSWORD`；缺失时交互提示输入 |
| 退出码 | `0` 成功；`1` 部分失败（见 `errors`）；`2` 致命错误 |

---

## Python 库 API（同 JSON 结构）

供非 CLI 场景或测试使用：

```python
from doujinshi_tag_getter import build_catalog, fetch_tags
from doujinshi_tag_getter.models import Source

catalog = build_catalog(Source.JMCOMIC)  # 默认直连
catalog = build_catalog(Source.JMCOMIC, proxy="http://127.0.0.1:7890")
# catalog.tags: list[TagCatalogEntry]

result = fetch_tags(Source.BIKA, ["id1", "id2"], proxy=...)
# result.items: list[ComicTagsItem]
```

Flutter **不直接 import Python**；推荐通过 **CLI 子进程** 或 **预生成 JSON 文件** 集成。

---

## Flutter 集成

### 方式 A：子进程调用 CLI（推荐）

```dart
final result = await Process.run('dtg', [
  'fetch',
  '--source', 'jmcomic',
  '--ids', albumId,
]);
final json = jsonDecode(result.stdout as String) as Map<String, dynamic>;
final items = json['items'] as List;
```

- 打包：桌面/移动端需内置 Python 环境，或发布 standalone 二进制（PyInstaller / 后续考虑）
- 开发期：本机已 `pip install` 即可

### 方式 B：读取 JSON 文件

构建/CI 跑 `dtg catalog -o assets/tags/jmcomic.json`，Flutter `rootBundle.loadString` 加载词表。

### 方式 C：Flutter 侧维护 tag 库

1. 用功能 1 定期生成 `TagCatalogResponse` JSON → 导入 App 本地存储（Hive/SQLite/isar）
2. 用功能 2 按需拉单本 tag → 合并进本地词表（由 Flutter 实现，非本工具职责）

### JSON Schema

实现时提供 `schemas/tag_catalog.schema.json` 与 `schemas/fetch_tags.schema.json`，便于 `quicktype` / `json_serializable` 生成 Dart model。

---

## 爬取实现要点（无 DB 断点）

| 项 | 策略 |
|----|------|
| 全量枚举 | 哔咔：分类分页；禁漫：`categories_filter_gen` |
| 聚合 | 内存 `dict[(kind,name)] += 1`；可选 `--checkpoint FILE` 写进度（**非 tag 库**，仅续爬） |
| 限速 | 哔咔 ~1 req/s；禁漫低并发 |
| 错误 | 记入 response `errors[]`，不中断整批（fetch） |

---

## v1 不做

- album / album_tag 表或等价持久化
- 内置 SQLite / 数据库
- HTTP 服务
- 跨站 tag 别名
- 漫画内容下载

## 交付物形态

```
doujinshi-tag-getter/          # uv 项目（pyproject.toml）
  pyproject.toml               # uv sync / uv run
  src/doujinshi_tag_getter/
    cli.py                     # dtg 入口
    catalog.py                 # 功能 1
    fetch.py                   # 功能 2
    models.py                  # dataclass ↔ JSON
    sources/bika.py, jmcomic.py
  schemas/*.schema.json        # Flutter / 其他语言代码生成
```

地图走完后按此结构实现。
