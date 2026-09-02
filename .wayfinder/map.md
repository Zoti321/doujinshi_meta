---
title: 从哔咔与禁漫天堂爬取本子元数据
labels: [wayfinder:map]
status: open
---

## Destination

交付 **`uv` 管理的 Python 包** `doujinshi-meta`（CLI：`djm`），无数据库，**stdout / 文件输出 JSON**，便于 Flutter 等项目集成：

1. **`djm catalog`** — 全量爬取，构建 **tag 词表**（仅 tags，无 album 持久化）
2. **`djm fetch`** — 单个/批量爬取本子元数据（含 tag 列表），JSON 输出

契约见 [`docs/schema.md`](docs/schema.md)。

## Notes

- **领域**：本子元数据采集（当前交付含 Tag 词表与按需 fetch）；consult `CONTEXT.md`
- **技术栈**：Python + **uv**（包/项目管理）；禁漫 `jmcomic`，哔咔非官方 REST API
- **集成**：JSON Schema + CLI 子进程；Flutter 解析 stdout 或 assets JSON
- **无持久化**：本工具不写 DB；tag 库 = catalog 命令输出的词表 JSON
- **路径**：先方案（Wayfinder 地图）→ 再实现（地图走完后开工）

## Decisions so far

- [调研哔咔 API 的 tag 与本子枚举能力](tickets/001-research-bika-api-tags.md) — 单本走详情 API；全站走分类分页 + N+1 详情；需 login + 签名；国内通常需代理
- [调研禁漫天堂的 tag 与本子枚举能力](tickets/002-research-jmcomic-tags.md) — 单本走 `get_album_detail`；全站走 `categories_filter_gen` + 详情聚合；优先 `api` 客户端
- [定义统一 tag 数据 schema](tickets/004-grilling-unified-schema.md) — **v2 修订**：无 DB/album 表；tag 词表 + fetch JSON 契约；pip 包 + CLI；见 `docs/schema.md`
- [按需爬取 CLI 接口形态](tickets/006-grilling-on-demand-cli.md) — `catalog` / `fetch` 子命令；stdout JSON；Flutter 子进程集成
- [全量爬取遍历与限速策略](tickets/005-grilling-full-crawl-strategy.md) — 分类分页 / categories_filter_gen；串行+延迟；checkpoint JSON；见 `docs/crawl-strategy.md`
- [代理与哔咔凭证本地管理方案](tickets/007-grilling-credentials-proxy.md) — 哔咔环境变量；**默认直连**；`djm config` / `--proxy` 手动启用代理
- [项目重命名为 doujinshi-meta](tickets/011-rename-doujinshi-meta.md) — 发行名/包/`djm`；配置目录与 `DJM_*`；0.2.0 双轨兼容（已关闭）
- [移除 dtg / DTG_* 遗留兼容](tickets/012-remove-legacy-dtg-naming.md) — 0.3.0 删除 CLI 别名、旧 env、doujinshi-tag-getter 自动迁移
- [本地本子批量刮削与页数消歧](map-local-scrape.md) — `search --pages` + `search-batch`；见 tickets/019–020
- [打包脚本与 Windows 分发产物](tickets/021-packaging-distribution-scripts.md) — Nuitka onefile + wheel + GitHub Release + 集成文档；见 ADR 0003、[`docs/integration.md`](../docs/integration.md) §3.4（已关闭）

## Not yet specified

- Tag 跨站别名（v1 不做）
- macOS / Linux / 移动端 Standalone 二进制（v1 仅 Windows x64）

## 地图状态

**规划已完成**（003 为可选环境自测）。008–012、021–026 已关闭。

## Out of scope

- 云端部署、多用户服务、对外 API
- 漫画图片或章节内容下载（仅元数据；当前契约以 Tag 为中心）
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
| [修正哔咔代理提示、清理死代码并回滚 App 头](tickets/008-fix-proxy-hint-client-cleanup.md) | task | closed | — |
| [catalog 命令可选表格输出](tickets/009-catalog-table-output.md) | task | closed | — |
| [catalog 命令按 Tag Kind 过滤词表](tickets/010-catalog-kind-filter.md) | task | closed | — |
| [项目重命名为 doujinshi-meta（本子元数据爬取）](tickets/011-rename-doujinshi-meta.md) | task | closed | — |
| [移除 dtg / DTG_* 与 doujinshi-tag-getter 遗留兼容（0.3.0）](tickets/012-remove-legacy-dtg-naming.md) | task | closed | — |
| [打包脚本与 Windows 分发产物（Nuitka + wheel + GitHub Release）](tickets/021-packaging-distribution-scripts.md) | task | closed | — |
| [→ CLI 版本标识](tickets/022-packaging-cli-version.md) | task | closed | — |
| [→ 本地 Nuitka 二进制与 manifest](tickets/023-packaging-nuitka-binary-manifest.md) | task | closed | — |
| [→ 构建脚本扩展](tickets/024-packaging-build-script-extensions.md) | task | closed | — |
| [→ GitHub Release CI](tickets/025-packaging-github-release-ci.md) | task | closed | — |
| [→ 分发与集成文档](tickets/026-packaging-integration-docs.md) | task | closed | — |
