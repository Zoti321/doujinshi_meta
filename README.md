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

# 禁漫：构建 tag 词表（耗时长，建议 --checkpoint）
uv run djm catalog --source jmcomic --limit 10

# 终端浏览词表（人类可读表格；默认仍是 JSON 契约）
uv run djm catalog --source jmcomic --limit 10 --table

# 哔咔：可直接运行；无环境变量时会提示输入账号密码（成功后自动保存）
uv run djm fetch --source bika --ids YOUR_COMIC_ID

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

文档：[`docs/schema.md`](docs/schema.md) · [`docs/credentials.md`](docs/credentials.md)
