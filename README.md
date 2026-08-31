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

# 哔咔：可直接运行；无环境变量时会提示输入账号密码（成功后自动保存）
uv run dtg fetch --source bika --ids YOUR_COMIC_ID

# 或预先设置环境变量（适合 CI / 脚本）
export DTG_BIKA_ACCOUNT=...
export DTG_BIKA_PASSWORD=...

# 国内直连失败时再配代理
uv run dtg config set proxy http://127.0.0.1:7890
uv run dtg fetch --source bika --ids YOUR_COMIC_ID

# 持久代理 / 已存凭证
uv run dtg config show
uv run dtg config unset proxy
uv run dtg config unset bika-credentials
```

文档：[`docs/schema.md`](docs/schema.md) · [`docs/credentials.md`](docs/credentials.md)
