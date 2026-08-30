# doujinshi-tag-getter

从哔咔、禁漫天堂爬取 tag 元数据，JSON 输出，供 Flutter 等项目集成。

## 安装

```bash
uv sync
uv run dtg --help
```

## 用法

```bash
# 禁漫：单个/批量 tag
uv run dtg fetch --source jmcomic --ids 410090

# 禁漫：构建 tag 词表（耗时长，建议 --checkpoint）
uv run dtg catalog --source jmcomic --limit 10

# 哔咔（需环境变量 + 可选代理）
export DTG_BIKA_EMAIL=...
export DTG_BIKA_PASSWORD=...
uv run dtg config set proxy http://127.0.0.1:7890
uv run dtg fetch --source bika --ids YOUR_COMIC_ID

# 持久代理配置
uv run dtg config show
uv run dtg config unset proxy
```

文档：[`docs/schema.md`](docs/schema.md) · [`docs/credentials.md`](docs/credentials.md)
