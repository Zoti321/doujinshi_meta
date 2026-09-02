# doujinshi-meta

从哔咔、禁漫天堂爬取本子元数据（标题、多维 Tag 等），JSON 输出，供 Flutter 等项目集成。

CLI 主命令：`djm`。

## 0.3.0 破坏性变更

自 0.3.0 起已移除：

- CLI 别名 `dtg`（请改用 `djm`）
- 环境变量前缀 `DTG_*`（请改用 `DJM_PROXY`、`DJM_BIKA_ACCOUNT`、`DJM_BIKA_PASSWORD`）
- 从 `doujinshi-tag-getter` 用户目录的自动配置迁移（请手动复制到 `doujinshi-meta` 目录，或先使用 0.2.x 完成迁移）

## 安装

```bash
uv sync
uv run djm --help
```

## 用法

```bash
# 禁漫：单个/批量本子元数据（含 tag）
uv run djm fetch --source jmcomic --ids 410090

# 禁漫：按标题/关键词搜索（可选页数消歧）
uv run djm search --source jmcomic "CRYOGENIC DREAMER"
uv run djm search --source jmcomic "CRYOGENIC DREAMER" --pages 42

# 批量本地本子刮削（系列级/库级）
uv run djm search-batch --source jmcomic --input books.jsonl

# 禁漫：构建 tag 词表（耗时长，建议 --checkpoint）
uv run djm catalog --source jmcomic --limit 10

# 终端浏览词表（人类可读表格；默认仍是 JSON 契约）
uv run djm catalog --source jmcomic --limit 10 --table

# 哔咔：可直接运行；无环境变量时会提示输入账号密码（成功后自动保存）
uv run djm fetch --source bika --ids YOUR_COMIC_ID
uv run djm search --source bika "关键词"

# 或预先设置环境变量（适合 CI / 脚本）
export DJM_BIKA_ACCOUNT=...
export DJM_BIKA_PASSWORD=...

# 国内直连失败时再配代理
uv run djm config set proxy http://127.0.0.1:7890
uv run djm fetch --source bika --ids YOUR_COMIC_ID

# 持久代理 / 已存凭证
uv run djm config show
uv run djm config unset proxy
uv run djm config unset bika-credentials
```

文档：[`docs/integration.md`](docs/integration.md)（**对接集成**）· [`docs/schema.md`](docs/schema.md) · [`docs/credentials.md`](docs/credentials.md)

## 构建 Standalone 二进制（维护者）

v1 目标平台为 **Windows x64**，使用 [Nuitka](docs/adr/0003-nuitka-standalone-binary.md) 编译 **Standalone 二进制**（`djm.exe`），供集成宿主子进程调用。

### 前置条件

| 项 | 说明 |
|----|------|
| 操作系统 | Windows x64 |
| 编译器 | [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)，勾选「使用 C++ 的桌面开发」（提供 `cl.exe`） |
| 包管理 | [uv](https://docs.astral.sh/uv/) |

### 构建命令

```bash
uv sync --all-groups

# 默认：Nuitka onefile + manifest.json + Release zip + --version/--help 冒烟
uv run python scripts/build.py

# 额外产出 wheel 与 sdist（与二进制同版本）
uv run python scripts/build.py --wheel
```

### `scripts/build.py` 常用选项

| 选项 | 说明 |
|------|------|
| `--wheel` | 调用 `uv build`，在 `dist/` 产出 `.whl` 与 `.tar.gz` |
| `--onedir` | Nuitka 目录模式，便于排查缺模块（输出仍在 `dist/djm-{version}-windows-x64/`） |
| `--smoke-full` | 构建后对 exe 跑真网 `fetch --source jmcomic --ids 410090`（**仅本地**，需网络；CI 不跑） |
| `--clean --no-binary` | 清理 `dist/` 下当前版本相关产物 |
| `--no-binary` | 跳过 Nuitka，仅执行其他步骤（如配合 `--wheel`） |

### 产物布局（`dist/`）

```text
dist/
  djm-{version}-windows-x64/
    djm.exe
    manifest.json
  djm-{version}-windows-x64.zip    # Release 附件：exe + manifest
  doujinshi_meta-{version}-py3-none-any.whl
  doujinshi_meta-{version}.tar.gz
```

发版：确保 `pyproject.toml` 版本与 git tag（如 `v0.3.0`）一致后 `git push origin v0.3.0`，由 [`.github/workflows/release.yml`](.github/workflows/release.yml) 构建并创建 GitHub Release。

集成方如何从 Release 下载、校验 manifest SHA256、捆绑进 Flutter，见 [`docs/integration.md` §3.4](docs/integration.md#34-获取-standalone-二进制)。
