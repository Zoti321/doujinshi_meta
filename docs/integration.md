# 集成指南

本文档面向**准备接入 doujinshi-meta（`djm`）的其他项目**（Flutter App、桌面工具、脚本、CI 流水线等），说明能力边界、集成方式、JSON 契约与运维约定。

> 契约细节见 [`schema.md`](./schema.md)；凭证与代理见 [`credentials.md`](./credentials.md)；领域词汇见 [`CONTEXT.md`](../CONTEXT.md)。

---

## 1. 项目定位

| 项 | 说明 |
|----|------|
| **做什么** | 从哔咔（`bika`）、禁漫天堂（`jmcomic`）爬取本子**元数据**：标题、页数（可选）、多维 Tag |
| **不做什么** | 不写数据库、不下载漫画内容、不提供 HTTP 服务、不维护跨站 tag 别名 |
| **持久化** | 由**调用方**负责（本地 DB、缓存 JSON、assets 等） |
| **当前版本** | `0.3.0`（CLI 命令 `djm`） |

---

## 2. 集成方式概览

```
┌─────────────────┐     子进程 / 静态文件      ┌──────────────────┐
│  Flutter / 其他  │ ────────────────────────▶ │  doujinshi-meta  │
│  宿主项目        │ ◀── stdout JSON 契约 ──── │  (djm CLI)       │
└─────────────────┘                           └──────────────────┘
         │                                              │
         │  Python 脚本 / 测试                           │ HTTPS
         └──────── import doujinshi_meta ──────────────┘
                                                          ▼
                                              哔咔 / 禁漫 API
```

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| **A. CLI 子进程** | Flutter、Electron、任意语言 | 调用 `djm` 命令，解析 **stdout JSON**；**推荐** |
| **B. 静态 JSON** | 词表、离线资源 | CI/构建期跑 `catalog -o ...`，App 加载 assets |
| **C. Python 库** | 同仓库脚本、自动化测试 | `import doujinshi_meta`，返回与 JSON 同结构的 dataclass |

Flutter **不能**直接 import Python；桌面/移动端若走方式 A，需内置 Python 环境或后续打包 standalone 二进制。

---

## 3. 安装与验证

### 3.1 作为 CLI 工具

```bash
# 开发 / 源码目录
git clone <repo-url> doujinshi-meta && cd doujinshi-meta
uv sync
uv run djm --help

# 全局安装（可选）
uv tool install /path/to/doujinshi-meta
djm --help
```

**环境要求**：Python ≥ 3.11。

### 3.2 作为 Python 依赖

在宿主项目的 `pyproject.toml` 中添加（路径或发布后包名）：

```toml
[project]
dependencies = [
    "doujinshi-meta @ file:///path/to/doujinshi-meta",
]
```

或在 monorepo 内通过 workspace / editable install 引用 `src/doujinshi_meta`。

### 3.3 冒烟测试

```bash
# 禁漫：无需账号
djm fetch --source jmcomic --ids 410090

# 哔咔：需账号（见第 6 节）
djm fetch --source bika --ids YOUR_COMIC_ID
```

成功时 **stdout 为纯 JSON**（`ensure_ascii=False`，中文不转义），stderr 可能含进度日志（`search-batch`）。

---

## 4. 四大能力与选型

| 能力 | CLI | 典型用途 | 响应类型 |
|------|-----|----------|----------|
| **按 ID 拉元数据** | `fetch` | 已知来源站 ID，补 tag | `FetchTagsResponse` |
| **按标题搜索** | `search` | 单本刮削、用户搜索 | `SearchTagsResponse` |
| **批量按标题刮削** | `search-batch` | 本地库/系列批量补元数据 | `SearchBatchResponse` |
| **构建 tag 词表** | `catalog` | 全站 tag 统计、筛选器数据源 | `TagCatalogResponse` |

### 4.1 按 ID 拉元数据 — `fetch`

```bash
djm fetch --source jmcomic --ids 410090,427413
djm fetch --source bika --ids-file ids.txt -o result.json
```

**输入**：来源站 `external_id`（逗号分隔或文件每行一个）。

**输出字段要点**：`items[]` 含 `external_id`、`title`、`tags[]`（`kind` + `name`）；失败项在 `errors[]`。

### 4.2 按标题搜索 — `search`

```bash
djm search --source jmcomic "CRYOGENIC DREAMER"
djm search --source jmcomic "CRYOGENIC DREAMER" --pages 42 --limit 5
djm search --source bika "关键词" -o out.json
```

| 选项 | 默认 | 说明 |
|------|------|------|
| `--limit` | 10 | 最多对前 N 条命中拉**完整详情**（列表页 tag 不完整） |
| `--pages` | — | 本地页数提示；多命中时选 `\|page_count − pages\|` 最小者 |

启用 `--pages` 且无法唯一消歧时：`items=[]`，候选在 `ambiguous[]`。

### 4.3 批量刮削本地本子 — `search-batch`

适用于 App 内已有**本地本子**（知标题、可选知页数），需映射到来源站 ID + tags。

**输入 JSONL**（每行一个 JSON 对象，`#` 开头或空行忽略）：

```jsonl
{"local_id": "book-001", "title": "[汉化组] 示例标题", "pages": 42}
{"local_id": "book-002", "title": "仅标题无页数"}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `local_id` | 是 | 调用方本地主键，原样回传 |
| `title` | 是 | 用于来源站搜索 |
| `pages` | 否 | 正整数；用于页数消歧 |

```bash
djm search-batch --source jmcomic --input books.jsonl -o batch.json
```

**输出**：

- `items[]`：成功；含 `local_id`、`external_id`、`title`、`page_count`、`tags`
- `ambiguous[]`：无法唯一消歧；含 `candidates[]`
- `errors[]`：行级校验或刮削失败；含 `local_id`、`message`

批量任务复用**单次会话**（尤其哔咔登录），比循环调用 `search` 更高效。

### 4.4 构建 tag 词表 — `catalog`

```bash
djm catalog --source jmcomic -o assets/tags/jmcomic.json
djm catalog --source jmcomic --kind tag --limit 100   # 测试 / 仅自由标签
djm catalog --source jmcomic --checkpoint progress.json --resume
```

全量爬取耗时长；生产环境建议 `--checkpoint` 断点续爬。`--table` 仅终端可读表格，**不是**集成契约。

---

## 5. JSON 契约

所有命令 stdout（或 `-o` 文件）均为 JSON，含：

```json
{
  "schema_version": "1.0",
  "command": "fetch | search | search-batch | catalog",
  "source": "bika | jmcomic",
  "generated_at": "2026-09-01T06:00:00+00:00",
  ...
}
```

### 5.1 来源站与 Tag Kind

**Source**：`bika` | `jmcomic`

**TagKind**：

| kind | 哔咔 | 禁漫 |
|------|------|------|
| `tag` | 自由标签 | 自由标签 |
| `author` | 作者 | 作者 |
| `parody` | — | 原作/IP |
| `character` | — | 角色 |

哔咔 `categories`（平台分区）**不**进入输出；旧字面量 `category` / `work` / `actor` 已废弃。

### 5.2 JSON Schema（代码生成）

仓库内 Schema 文件（可用于 `quicktype`、`json_serializable`、OpenAPI 工具链）：

| 响应 | Schema 文件 |
|------|-------------|
| `SearchTagsResponse` | [`schemas/search_tags.schema.json`](../schemas/search_tags.schema.json) |
| `SearchBatchResponse` | [`schemas/search_batch.schema.json`](../schemas/search_batch.schema.json) |

`TagCatalogResponse`、`FetchTagsResponse` 字段定义见 [`schema.md`](./schema.md)（Schema 文件待补全时可对照文档手写 model）。

### 5.3 解析约定

- 只解析 **stdout**；勿把 stderr 当 JSON
- 集成侧应校验 `schema_version`；主版本变更时做迁移
- `errors[]` 非空不一定代表进程失败，需结合**退出码**（第 7 节）

---

## 6. 凭证、代理与配置

### 6.1 禁漫（jmcomic）

**无需账号**，国内多数环境可直连。

### 6.2 哔咔（bika）

需提供**账号 + 密码**（环境变量名沿用 `DJM_BIKA_*`）：

| 优先级 | 方式 |
|--------|------|
| 1 | 环境变量 `DJM_BIKA_ACCOUNT`、`DJM_BIKA_PASSWORD` |
| 2 | 用户目录 `credentials.toml` |
| 3 | 交互式输入（TTY；成功后自动保存） |

**非交互集成（Flutter 子进程 / CI）**：务必预先设置环境变量或写好 `credentials.toml`，避免阻塞在密码提示。

配置目录（与 `config.toml` 同目录）：

- Windows：`%APPDATA%\doujinshi-meta\`
- Linux/macOS：`~/.config/doujinshi-meta/`

### 6.3 代理

**默认直连**，不自动读取系统 `HTTP_PROXY`。

| 优先级 | 方式 |
|--------|------|
| 1 | `djm --proxy http://127.0.0.1:7890 ...` |
| 2 | `djm --no-proxy ...`（忽略持久配置） |
| 3 | `config.toml` 中 `proxy = "..."` |
| 4 | 环境变量 `DJM_PROXY` |

国内 Windows 访问哔咔失败时，配置代理或 VPN 后重试。详见 [`credentials.md`](./credentials.md)。

### 6.4 配置命令

```bash
djm config show
djm config set proxy http://127.0.0.1:7890
djm config unset proxy
djm config unset bika-credentials
djm --config /path/to/config.toml fetch --source bika --ids ...
```

---

## 7. 退出码与错误处理

| 退出码 | 含义 |
|--------|------|
| `0` | 成功（或 catalog 无致命错误） |
| `1` | 部分失败：有成功项但也有 `errors` / `ambiguous`（`fetch`/`search`）；或 `search-batch` 有 `items` 同时有 `errors`/`ambiguous` |
| `2` | 致命错误：参数错误、凭证缺失、全非失败、运行时异常等 |

**集成建议**：

```text
exit 0     → 解析 JSON，正常使用 items
exit 1     → 解析 JSON，处理 items + errors/ambiguous，提示用户或重试失败项
exit 2     → 读 stderr 错误信息，不要假设 stdout 可解析
```

单条失败**不**中断整批 `fetch`/`search-batch`（除输入文件完全无效）；失败详情在 JSON 的 `errors[]`。

---

## 8. 各语言集成示例

### 8.1 Flutter（Dart）— CLI 子进程

```dart
import 'dart:convert';
import 'dart:io';

Future<Map<String, dynamic>> djmFetch({
  required String source,
  required String id,
  String? djmPath, // 默认 PATH 中的 djm
}) async {
  final executable = djmPath ?? 'djm';
  final result = await Process.run(executable, [
    'fetch',
    '--source', source,
    '--ids', id,
  ]);

  if (result.exitCode == 2) {
    throw Exception('djm failed: ${result.stderr}');
  }

  final json = jsonDecode(result.stdout as String) as Map<String, dynamic>;
  // exitCode 1：仍有 items，但应检查 json['errors']
  return json;
}
```

**批量刮削**：生成临时 JSONL → `search-batch --input ...` → 解析 `SearchBatchResponse`，按 `local_id` 写回本地 DB。

**词表**：构建脚本 `djm catalog -o assets/tags/jmcomic.json`，运行时 `rootBundle.loadString`。

### 8.2 Node.js / TypeScript

```typescript
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function djmSearch(source: string, query: string) {
  const { stdout, stderr } = await execFileAsync("djm", [
    "search", "--source", source, query,
  ], { encoding: "utf8", maxBuffer: 10 * 1024 * 1024 });

  const data = JSON.parse(stdout);
  return { data, stderr };
}
```

### 8.3 Python 库

```python
from doujinshi_meta import build_catalog, fetch_tags, search_batch_tags, search_tags
from doujinshi_meta.config import load_config, resolve_proxy
from doujinshi_meta.models import Source

cfg = load_config()
proxy = resolve_proxy(config=cfg)  # None = 直连

# 与 CLI 同结构
result = fetch_tags(Source.JMCOMIC, ["410090"], proxy=proxy)
payload = result.to_dict()  # 可直接 json.dumps

search = search_tags("关键词", Source.JMCOMIC, limit=10, pages=42, proxy=proxy)
batch = search_batch_tags("books.jsonl", Source.JMCOMIC, proxy=proxy)
catalog = build_catalog(Source.JMCOMIC, proxy=proxy, limit=100)
```

公开 API 见 `doujinshi_meta.__all__`：`build_catalog`、`fetch_tags`、`search_tags`、`search_batch_tags`、`Source`。

---

## 9. 推荐集成模式

### 模式 1：本地漫画 App（最常见）

1. 用户导入文件夹 → 本地生成 `local_id`、`title`、可选 `pages`
2. 调用 `search-batch` 批量刮削
3. 成功项写入本地 DB；`ambiguous` 弹窗让用户选手动；`errors` 可重试
4. 定期或按需 `fetch` 更新已知 `external_id` 的 tags

### 模式 2：Tag 筛选器 / 自动补全

1. CI 或定时任务跑 `catalog -o tags.json`
2. App 启动时加载词表（或增量同步）
3. 用户选 tag 后，由 App 自有逻辑过滤本地书目（本工具不提供按 tag 反查 ID）

### 模式 3：已知 ID 的元数据服务

1. 下载器 / 阅读器已有来源站 ID
2. 直接 `fetch --ids ...`，缓存 JSON 到本地

---

## 10. 性能与限速

| 来源 | 说明 |
|------|------|
| 哔咔 | 约 1 req/s；批量请用 `search-batch` 复用会话 |
| 禁漫 | 低并发；可用 `--delay` 调节请求间隔 |
| `catalog` | 全量极慢；务必 `--checkpoint` + `--resume` |

CLI 全局选项 `--delay`（秒）可覆盖默认间隔。

---

## 11. 版本与破坏性变更

**0.3.0 起**：

| 已移除 | 请改用 |
|--------|--------|
| CLI 别名 `dtg` | `djm` |
| 环境变量前缀 `DTG_*` | `DJM_PROXY`、`DJM_BIKA_ACCOUNT`、`DJM_BIKA_PASSWORD` |
| 旧包名目录自动迁移 | 手动复制配置到 `doujinshi-meta` 目录 |

集成侧请：

- 依赖 `schema_version` 字段而非解析 CLI 文本输出
- 避免使用 `catalog --table` 作为机器可读接口
- 锁定 `djm` 版本或在 CI 中 pin 安装版本

---

## 12. 文档索引

| 文档 | 内容 |
|------|------|
| [`README.md`](../README.md) | 快速上手 |
| [`schema.md`](./schema.md) | 完整 JSON 契约与字段说明 |
| [`credentials.md`](./credentials.md) | 凭证、代理、配置路径 |
| [`CONTEXT.md`](../CONTEXT.md) | 领域词汇（本地本子、页数消歧等） |
| [`schemas/`](../schemas/) | JSON Schema（代码生成） |

---

## 13. 常见问题

**Q：能否只返回 tag 字符串数组？**  
A：契约固定为 `{ kind, name }[]`，集成侧自行 flatten 或按 kind 分组。

**Q：跨站统一 tag 词表？**  
A：v1 按 source 分词表，不做跨站合并或别名。

**Q：stdout 混有日志？**  
A：契约命令的 stdout **仅 JSON**；`search-batch` 进度在 stderr。若自定义包装脚本，勿向 stdout 打印调试信息。

**Q：哔咔在 CI 里卡住？**  
A：设置 `DJM_BIKA_*` 环境变量；必要时 `DJM_PROXY` 或 `--proxy`。

**Q：如何贡献或报告契约变更？**  
A：先改 [`schema.md`](./schema.md) 与 Schema 文件，再 bump `schema_version`（若有 breaking change）。
