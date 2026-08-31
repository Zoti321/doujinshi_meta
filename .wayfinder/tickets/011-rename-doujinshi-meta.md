---
title: 项目重命名为 doujinshi-meta（本子元数据爬取）
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee: agent
parent: map
blocked_by: []
blocks: []
---

## Problem Statement

作为使用本工具的开发者与本机 CLI 用户，我发现项目自称 `doujinshi-tag-getter` / `dtg`，读起来像「只抓 tag」；实际主业是从哔咔、禁漫等外部来源站爬取本子元数据（当前交付含标题与多维 Tag 等），并输出 JSON 供 Flutter / 脚本集成。名称误导后续集成方与文档读者；发行名、包名、CLI、配置目录与 `DTG_*` 环境变量也彼此绑在过时的「tag-getter」叙事上。需要一次与已 grilling 共识一致的重命名，并在兼容期内不弄丢本机已存的代理与哔咔用户凭证。

## Solution

将产品表面标识改为英文 **`doujinshi-meta`**（包名 `doujinshi_meta`，CLI 主命令 **`djm`**），文档与描述改为「本子元数据爬取」口径；**本阶段不改动**输出契约中的 `TagCatalogResponse` / `FetchTagsResponse` 等 Tag 前缀类型与 JSON 形状。配置目录改为 `doujinshi-meta`，环境变量主前缀改为 `DJM_*`；首次读写时**自动迁移**旧 `doujinshi-tag-getter` 目录内容；旧 CLI 名 `dtg` 与旧 `DTG_*` 在兼容窗口内仍可读/可调用并发出弃用警告，约在 **0.2.0** 起警告、**0.3.0** 移除。`meta` 仅描述当前交付（标题 + Tag 等），不承诺近期扩封面/页数等字段。

## User Stories

1. As a 新读者, I want README 与包描述写明「爬取本子元数据」而非「只抓 tag」, so that 我不会低估工具实际能力。
2. As a CLI 用户, I want 主命令名为 `djm`, so that 短名与 `doujinshi-meta` 对齐且便于记忆。
3. As a CLI 用户, I want 在兼容期内仍能运行 `dtg`, so that 旧肌肉记忆与未改脚本暂不立刻报错。
4. As a CLI 用户, I want 调用 `dtg` 时看到明确的弃用提示（指向 `djm`）, so that 我知道该迁移。
5. As a Python 库用户, I want `import doujinshi_meta`, so that import 路径与发行名一致。
6. As a 包安装者, I want PyPI/发行名 `doujinshi-meta`, so that `uv add` / 依赖声明不再含 tag-getter。
7. As a CI/脚本作者, I want 使用 `DJM_PROXY`、`DJM_BIKA_ACCOUNT`、`DJM_BIKA_PASSWORD`, so that 环境变量前缀与新 CLI 一致。
8. As a CI/脚本作者, I want 兼容期内 `DTG_*` 仍被读取, so that 我不必同一天改完所有流水线。
9. As a 本机用户, I want 用户配置目录名为 `doujinshi-meta`, so that 磁盘上的应用数据目录与产品名一致。
10. As a 本机用户, I want 首次使用新包时自动把旧目录中的 `config.toml` / `credentials.toml` 迁到新目录, so that 代理与哔咔凭证不丢。
11. As a 本机用户, I want 迁移后写入只发生在新目录, so that 不会长期双处配置分叉。
12. As a 本机用户, I want 迁移完成时可选提示旧目录可手动删除, so that 我知道残留文件是否还需要。
13. As a 本机用户, I want 若新目录已有配置则不覆盖、不以旧目录为准强行覆盖, so that 已在新位置写过的配置不被回滚。
14. As a Flutter/子进程调用方, I want `catalog` / `fetch` 的 JSON 输出契约（含 `TagCatalogResponse` 等）本阶段保持不变, so that 现有解析代码无需因改名而改。
15. As a Flutter/子进程调用方, I want `schema_version` 与字段名本阶段不变, so that 重命名不触发契约 bump。
16. As a 文档读者, I want `CONTEXT.md` 与地图文案区分「产品名」与「Tag 词表/按需 fetch 功能」, so that 领域词 Tag 仍准确、产品自称不再窄化。
17. As a 文档读者, I want 示例命令主推 `djm` 并注明 `dtg` 为临时别名, so that 新文档不继续传播旧主名。
18. As a 维护者, I want 源码包目录与 import 一并改为 `doujinshi_meta`, so that 仓库内无残留旧包路径。
19. As a 维护者, I want 测试与内部引用全部切到新包名, so that CI 全绿且无双包并存。
20. As a 维护者, I want 版本在重命名落地时 bump 到 **0.2.0** 并开始对旧 CLI/旧 env 写路径发出 DeprecationWarning（或等价 stderr 提示）, so that 弃用窗口有版本锚点。
21. As a 维护者, I want 文档写明计划在 **0.3.0** 移除 `dtg` 入口与对「仅旧 env / 仅旧目录写入」的支持, so that 别名不会变成永久双轨。
22. As a 本机用户, I want `djm config show|set|unset` 行为与现 `dtg config` 一致（仅路径/前缀更新）, so that 配置工作流不因改名改变。
23. As a 本机用户, I want 解析代理时优先级保持「CLI 显式 > 配置文件 > 环境变量」, so that 只换前缀不换语义。
24. As a 本机用户, I want 同时存在 `DJM_*` 与 `DTG_*` 时优先新前缀, so that 迁移后旧 env 不会盖住新设置。
25. As a 本机用户, I want 仍接受遗留 `DTG_BIKA_EMAIL`（兼容期内，优先级低于 account 类变量）, so that 与现 ADR/实现的 email 兼容不无故打断。
26. As a 集成方, I want 了解到相邻 Flutter 仓库当前未硬编码旧名、但仍应改示例中的 `Process.run('dtg')` 为 `djm`, so that 文档示例不落伍。
27. As a 操作者, I want 工作区/磁盘文件夹改名为与包名对齐（如 `doujinshi_meta`）可作为本规格执行后的显式步骤, so that Cursor 根目录与产品名一致且不在未确认时擅自搬根。
28. As a 测试维护者, I want 用临时目录与 monkeypatch 验证迁移与 env 优先级, so that 不依赖真实 APPDATA。
29. As a 测试维护者, I want 断言 `dtg` 仍能启动同一 CLI app 且带弃用信号, so that 兼容期有回归保护。
30. As a 产品负责人, I want `meta` 的含义在文档中写清为「当前元数据交付」而非路线图承诺, so that 半年内不必因「还没做封面」再改名。
31. As a 维护者, I want Wayfinder 地图 Destination 更新为新包名/CLI, so that tracker 与产品自称一致。
32. As a 维护者, I want 遵守现有 ADR：哔咔凭证仍落在用户目录 `credentials.toml`、与 `config.toml` 分离、不进仓库, so that 改名不推翻凭证持久化决策。
33. As a CLI 用户, I want `--help` / 子命令 help 中的工具名显示为 `djm`（或新产品名）, so that 帮助文本不继续自称 dtg-only。
34. As a 脚本作者, I want 子命令 `catalog` / `fetch` / `config` 名称与标志语义不变, so that 迁移成本集中在可执行文件名与 env 前缀。
35. As a 安全意识用户, I want 迁移为复制（或等价安全搬迁）且不在日志中打印密码明文, so that 改名过程不新增凭证泄露面。

## Implementation Decisions

- **产品定位**：主业 = 从来源站爬取本子元数据；当前交付范围 = 既有 `catalog` Tag 词表 + `fetch` 单本/批量（含标题与 Tag 等）。`meta` 描述现状，不扩展字段范围。
- **命名对照**：
  - 发行名：`doujinshi-meta`
  - 包 / import：`doujinshi_meta`
  - CLI 主命令：`djm`
  - CLI 临时别名：`dtg`
  - 配置目录名：`doujinshi-meta`（替换 `doujinshi-tag-getter`）
  - 环境变量主前缀：`DJM_*`（`DJM_PROXY`、`DJM_BIKA_ACCOUNT`、`DJM_BIKA_PASSWORD`；兼容期内仍读 `DTG_*` 与遗留 `DTG_BIKA_EMAIL`）
- **契约冻结（本阶段）**：不重命名 `TagCatalogResponse`、`TagCatalogEntry`、`FetchTagsResponse`、`ComicTagsItem`、`TagRef` 等；不 bump `schema_version`；不改 JSON 字段名。
- **分阶段表面**：本规格改发行名、包路径、文档/描述、CLI 双入口、配置目录与 env；**不**在本规格内改输出 schema 类型前缀。
- **配置迁移**：解析默认用户目录时，若新目录缺少所需文件而旧目录存在，则首次相关读写前将旧目录中的 `config.toml` / `credentials.toml`（及同级已有约定文件）复制到新目录；新目录已存在对应文件则不覆盖。写路径只使用新目录。可读旧 env；写文档与示例只教新 env。新旧 env 同时存在时 **新前缀优先**。
- **弃用窗口**：落地版本 **0.2.0**：`dtg` 入口与使用旧 env（在存在新前缀替代时）发出 DeprecationWarning 或 CLI stderr 弃用提示。计划 **0.3.0** 移除 `dtg` 脚本入口、停止依赖旧目录作为唯一配置源、停止将 `DTG_*` 作为支持的写入/文档主路径（具体删除项在 0.3 规格确认，本规格至少完成警告与双读）。
- **凭证 ADR**：继续遵循「用户目录 `credentials.toml` 明文、与 config 分离、交互成功后写入、env 不回写」；仅目录名与注释中的产品名更新。
- **文档**：更新 README、`CONTEXT.md`（产品自称 vs Tag 领域词）、Wayfinder `map.md` Destination、credentials/crawl 等文档中的命令与前缀示例；调研文档标题可不强制改历史用词，但新示例用 `djm`。
- **工作区文件夹**：磁盘上仓库根目录改名为 `doujinshi_meta`（或等价）属执行阶段的操作者步骤；实现 agent 先完成仓内包与标识重命名，根目录搬迁需用户确认后另做（可配合工作区切换）。
- **无 git remote**：不包含 GitHub 仓库改名。
- **模块影响（概念层）**：包装配置（发行名、scripts、包发现）、CLI 应用名与双 console script、用户配置/凭证/代理解析、全库 import 路径、测试 import、用户可见文案。来源站爬取逻辑与 Tag 聚合语义不变。

## Testing Decisions

- **好测试**：只断言用户可观察行为——默认配置根路径名、迁移后新旧目录文件有无、env 新旧前缀优先级、写是否只落新目录、`djm`/`dtg` 均可驱动同一 CLI、弃用提示是否出现；不断言「如何复制文件」的内部辅助函数结构，不测真网爬取。
- **主接缝（唯一行为验收面）**：**配置解析与迁移的公开行为**（默认目录解析、`load`/`save`/`require` 类 API、代理解析）。用 `tmp_path` 注入「旧根/新根」、`monkeypatch` 环境变量与平台路径，断言：
  1. 仅旧根有文件 → 首次读触发迁移 → 新根出现副本且内容可用；
  2. 新根已有文件 → 不覆盖；
  3. `DJM_PROXY` 优于 `DTG_PROXY`；仅 `DTG_*` 仍可读；
  4. `save_*` 写入新根而非旧根。
- **薄补充（非第二领域接缝）**：CLI `CliRunner` 冒烟——同一 app 下 `--help` / `config show` 在指向临时 config 时可用；若可观察，`dtg` 兼容路径带弃用信号。双 console script 名称以包装配置声明为验收（或安装后 smoke），不引入第二套业务逻辑测试金字塔。
- **Prior art**：`tests/test_bika_credentials.py`（env + `credentials_path`）、`tests/test_cli_credentials.py`（CliRunner + 临时 config）、既有 ADR 0001 相关持久化测。
- **不必测**：来源站 `extract_tags_*`、catalog 聚合、Kind 过滤（改名无关）；真实 APPDATA/XDG 上的手工目录（用注入根路径代替）。

## Out of Scope

- 输出契约去 Tag 前缀或 schema v3（封面、页数、描述等更广元数据）
- 新增来源站、改爬取策略、改 Tag Kind 词汇
- 在 0.2.0 落地时立即删除 `dtg` / 停止读 `DTG_*`（属 0.3.0）
- GitHub/远程仓库改名（当前无 remote）
- 未确认前擅自更换 Cursor 工作区根目录（确认后的文件夹改名可作为执行附带步骤）
- 跨站 Tag 别名、DB 持久化、HTTP 服务、漫画内容下载
- 已发布 PyPI Yank/重定向（若尚未发布则无此项）

## Further Notes

- 共识来源：本会话 `/grill-me` 全盘采纳推荐（定位 A、分阶段 D、英文+短缩写、名 `doujinshi-meta`、`djm`+临时 `dtg`、契约冻结、自动迁移、`meta` 描述现状、0.2 警告 / 0.3 移除、执行前再开干）。
- 领域词汇：继续使用 CONTEXT 中的 Tag、Tag 词表、Tag Kind、来源站、输出契约；产品名与「Tag 词表功能」解耦叙述。
- 主测试接缝已在 Implementation/Testing 写明；若你希望改成「以 CLI 为唯一接缝、配置仅作实现细节」，说一声再改 ticket 后再开工。

## Resolution

- 发行名/包 `doujinshi-meta` / `doujinshi_meta`；版本 0.2.0。
- CLI 主入口 `djm`；`dtg` 保留并 stderr 弃用提示。
- 配置目录 `doujinshi-meta`；`DJM_*` 优先；`DTG_*` 双读 + DeprecationWarning；首次读写自动迁移旧目录。
- 输出契约 Tag 前缀未动；文档/README/CONTEXT/map 已更新。
- 测试：`test_config_rename_migration.py`、`test_cli_rename.py`；全量 64 passed。
