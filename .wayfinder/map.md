---
title: 从哔咔与禁漫天堂爬取 Tag 数据
labels: [wayfinder:map]
status: open
---

## Destination

交付 **`uv` 管理的 Python 包** `doujinshi-tag-getter`（CLI：`dtg`），无数据库，**stdout / 文件输出 JSON**，便于 Flutter 等项目集成：

1. **`dtg catalog`** — 全量爬取，构建 **tag 词表**（仅 tags，无 album 持久化）
2. **`dtg fetch`** — 单个/批量爬取漫画 tag 列表，JSON 输出

契约见 [`docs/schema.md`](docs/schema.md)。

## Notes

- **领域**：本子漫画 tag 元数据采集；consult `CONTEXT.md`
- **技术栈**：Python + **uv**（包/项目管理）；禁漫 `jmcomic`，哔咔非官方 REST API
- **集成**：JSON Schema + CLI 子进程；Flutter 解析 stdout 或 assets JSON
- **无持久化**：本工具不写 DB；tag 库 = catalog 命令输出的词表 JSON
- **路径**：先方案（Wayfinder 地图）→ 再实现（地图走完后开工）

## Decisions so far

- [调研哔咔 API 的 tag 与本子枚举能力](tickets/001-research-bika-api-tags.md) — 单本走详情 API；全站走分类分页 + N+1 详情；需 login + 签名；国内通常需代理
- [调研禁漫天堂的 tag 与本子枚举能力](tickets/002-research-jmcomic-tags.md) — 单本走 `get_album_detail`；全站走 `categories_filter_gen` + 详情聚合；优先 `api` 客户端
- [定义统一 tag 数据 schema](tickets/004-grilling-unified-schema.md) — **v2 修订**：无 DB/album 表；tag 词表 + fetch JSON 契约；pip 包 + `dtg` CLI；见 `docs/schema.md`
- [按需爬取 CLI 接口形态](tickets/006-grilling-on-demand-cli.md) — `catalog` / `fetch` 子命令；stdout JSON；Flutter 子进程集成
- [全量爬取遍历与限速策略](tickets/005-grilling-full-crawl-strategy.md) — 分类分页 / categories_filter_gen；串行+延迟；checkpoint JSON；见 `docs/crawl-strategy.md`
- [代理与哔咔凭证本地管理方案](tickets/007-grilling-credentials-proxy.md) — 哔咔 `DTG_BIKA_*` 环境变量；**默认直连**；`dtg config` / `--proxy` 手动启用代理

## Not yet specified

- Tag 跨站别名（v1 不做）
- standalone 二进制打包（Flutter 移动端无 Python 时）

## 地图状态

**规划已完成**（003 为可选环境自测）。可开始实现。

## Out of scope

- 云端部署、多用户服务、对外 API
- 漫画图片或章节内容下载（仅 tag 元数据）
- 非本地使用的合规/分发考量（已确认为个人本地）

## 子 Ticket

| Ticket | 类型 | 状态 | 阻塞 |
|--------|------|------|------|
| [调研哔咔 API 的 tag 与本子枚举能力](tickets/001-research-bika-api-tags.md) | research | closed | — |
| [调研禁漫天堂的 tag 与本子枚举能力](tickets/002-research-jmcomic-tags.md) | research | closed | — |
| [准备哔咔账号与代理访问环境](tickets/003-task-bika-account-proxy.md) | task | open | — |
| [定义统一 tag 数据 schema](tickets/004-grilling-unified-schema.md) | grilling | closed | — |
| [全量爬取遍历与限速策略](tickets/005-grilling-full-crawl-strategy.md) | grilling | closed | — |
| [按需爬取 CLI 接口形态](tickets/006-grilling-on-demand-cli.md) | grilling | closed | — |
| [代理与哔咔凭证本地管理方案](tickets/007-grilling-credentials-proxy.md) | grilling | closed | — |
