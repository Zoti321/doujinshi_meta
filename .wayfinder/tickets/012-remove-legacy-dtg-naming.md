---
title: 移除 dtg / DTG_* 与 doujinshi-tag-getter 遗留兼容（0.3.0）
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee:
parent: map
blocked_by: []
blocks: []
---

## Problem Statement

作为 `doujinshi-meta` 的维护者与集成方，我在 0.2.0 已完成产品重命名（`djm`、`DJM_*`、`doujinshi-meta` 配置目录），但代码、包装与文档仍保留 **`dtg` CLI 别名**、**`DTG_*` 环境变量双读**、**`doujinshi-tag-getter` 用户目录自动迁移** 及大量弃用警告。这些兼容层增加了测试矩阵、文档双轨与认知负担；且 ticket 011 已承诺在 **0.3.0** 移除。我需要一次干净的收尾，让对外表面只剩 `djm` / `DJM_*` / `doujinshi-meta`，不再暗示旧「tag-getter」叙事。

## Solution

在 **0.3.0** 版本中彻底删除遗留命名兼容：**移除 `dtg` console script** 与 CLI 入口弃用分支；**停止读取** `DTG_PROXY`、`DTG_BIKA_ACCOUNT`、`DTG_BIKA_EMAIL`、`DTG_BIKA_PASSWORD`；**移除**从 `doujinshi-tag-getter` 用户目录到 `doujinshi-meta` 的自动迁移逻辑。文档、词汇表与 Wayfinder 地图只描述 `djm` 与 `DJM_*`。输出契约（`TagCatalogResponse` 等）与 JSON 形状不变。已迁移到新目录的用户无感；仍只使用旧 CLI/旧 env/仅旧目录且从未跑过 0.2.x 的用户需手动改用 `djm` 并设置 `DJM_*` 或迁移配置文件（本规格不自动兜底旧目录）。

## User Stories

1. As a CLI 用户, I want 安装后只有 `djm` 命令可用, so that 我不必在 muscle memory 与文档间纠结两个名字。
2. As a CLI 用户, I want 运行 `dtg` 时得到「命令不存在」而非静默成功, so that 未迁移脚本会立刻暴露而非误以为仍受支持。
3. As a CLI 用户, I want `djm --help` 与所有子命令 help 不再提及 `dtg` 弃用, so that 帮助文本干净一致。
4. As a CI/脚本作者, I want 仅 `DJM_PROXY`、`DJM_BIKA_ACCOUNT`、`DJM_BIKA_PASSWORD` 被识别, so that 流水线 env 命名与文档一致。
5. As a CI/脚本作者, I want 设置 `DTG_*` 时不再被读取且无 DeprecationWarning, so that 旧 env 不会静默失效后仍以为生效（应显式失败或忽略——见实现决策）。
6. As a 本机用户, I want 配置与凭证仍只读写 `doujinshi-meta` 用户目录, so that 路径语义不变。
7. As a 本机用户, I want 不再自动从 `doujinshi-tag-getter` 目录复制文件, so that 兼容层代码路径减少；若我尚未迁移，我接受需手动复制或先跑 0.2.x。
8. As a 本机用户, I want 已在新目录的 `config.toml` / `credentials.toml` 继续正常工作, so that 0.2.x 正常用户升级无断档。
9. As a Python 库用户, I want `resolve_proxy` / `require_bika_credentials` 只文档化 `DJM_*`, so that 库 API 行为与 CLI 一致。
10. As a Flutter/子进程集成方, I want 文档与示例只展示 `Process.run('djm', …)`, so that 集成指南无旧名。
11. As a Flutter/子进程集成方, I want JSON 输出契约与 `schema_version` 不变, so that 移除旧命名不触发解析变更。
12. As a 文档读者, I want README、`docs/credentials.md`、`docs/schema.md` 删除 `DTG_*` 与 `dtg` 兼容说明, so that 新读者不会配置已废弃项。
13. As a 文档读者, I want `CONTEXT.md` 产品条目不再提 `dtg` 兼容别名, so that 领域词汇表与实现一致。
14. As a 维护者, I want `pyproject.toml` 仅声明 `djm` script, so that 打包产物无双入口。
15. As a 维护者, I want 删除 `config.py` 中 legacy app 名、迁移函数与 DTG env 分支, so that 配置模块单一职责。
16. As a 维护者, I want 删除 `cli.py` 中 `run()` 的 dtg 检测与 stderr 警告, so that 入口简化为直接 `app()`（或等价）。
17. As a 维护者, I want 版本号 bump 至 **0.3.0**, so that semver 与移除承诺对齐。
18. As a 测试维护者, I want 移除或改写依赖 `DTG_*` / `dtg` 的测试, so that CI 只断言新命名行为。
19. As a 测试维护者, I want 断言仅 `DJM_*` 生效、legacy env 被忽略, so that 回归保护新契约。
20. As a 测试维护者, I want 断言默认配置路径不再触发 legacy 目录迁移, so that 迁移逻辑删除有覆盖。
21. As a 测试维护者, I want 删除 `test_run_warns_when_invoked_as_dtg` 等弃用期测试, so that 测试集反映 0.3.0 行为。
22. As a 维护者, I want Wayfinder `map.md` Destination 去掉「兼容别名 dtg 至 0.3.0」表述, so that 地图与发布一致。
23. As a 维护者, I want 本 ticket 关闭时在 Resolution 记录变更摘要, so that 与 011 形成闭环。
24. As a 安全意识用户, I want 移除兼容层不改变凭证存储位置与 ADR 0001 语义, so that 改名收尾不削弱凭证模型。
25. As a 操作者, I want CHANGELOG 或 README 简短说明 0.3.0  breaking：移除 `dtg`、`DTG_*`、自动迁移, so that 升级前可查。
26. As a 历史文档读者, I want 已关闭的旧 ticket 正文可保留当时 `dtg` 用词（历史记录）, so that 决策考古不被 bulk 重写破坏。
27. As a 库测试作者, I want `test_bika_credentials` 等用例全面改用 `DJM_*` fixture, so that 测试即文档。
28. As a 代理用户, I want `djm config set proxy` 与 `--proxy` 行为不变, so that 仅 env 前缀清理。
29. As a 非交互环境用户, I want 缺少 `DJM_BIKA_*` 时错误信息仍指向新变量名, so that 排错路径正确。
30. As a 产品负责人, I want 「Tag」领域词与输出类型前缀仍保留, so that 本规格只做表面命名收尾、不做 schema 重命名。

## Implementation Decisions

- **版本**：落地为 **0.3.0**（minor bump，因移除已公告的公开兼容面）。
- **CLI**：从 `[project.scripts]` 删除 `dtg`；`run()` 不再检查 `sys.argv[0]`，直接调用 Typer `app()`（或保留 `run()` 作为 `djm` 唯一入口的薄包装）。
- **环境变量**：仅识别 `DJM_PROXY`、`DJM_BIKA_ACCOUNT`、`DJM_BIKA_PASSWORD`。删除对 `DTG_PROXY`、`DTG_BIKA_ACCOUNT`、`DTG_BIKA_EMAIL`、`DTG_BIKA_PASSWORD` 的读取与 `DeprecationWarning`。若仅设置 `DTG_*`，行为等同于未设置（代理为直连、凭证走文件/交互/报错），**不**在 stderr 打印「请改用 DJM_*」（避免永久噪音；breaking 说明放在 CHANGELOG/README）。
- **用户目录**：删除 `LEGACY_APP_NAME`、`legacy_config_dir()`、`migrate_user_config()`、`_ensure_defaults_migrated()` 及所有调用点。`default_config_path` / `default_credentials_path` / `load_*` / `save_*` 直接使用 `doujinshi-meta` 目录，无首次迁移提示。
- **凭证 ADR**：继续 ADR 0001——`credentials.toml` 明文、与 config 分离、env 不回写；仅去掉 legacy 路径与 DTG env。
- **契约冻结**：不改动 `TagCatalogResponse`、`FetchTagsResponse` 等 JSON 类型与字段；不 bump `schema_version`。
- **文档**：更新 README、`CONTEXT.md`、`docs/credentials.md`、`docs/schema.md`、`.wayfinder/map.md`；新示例一律 `djm` / `DJM_*`。**不**批量改写已关闭 ticket 正文中的历史 `dtg` 用词。
- **调研文档**：`docs/research/*` 中历史对照表可保留 `DTG_*` 作为「当时调研快照」，或仅在脚注注明已废弃——优先 **不动调研档案**，除非表头造成主动误导。
- **模块影响（概念层）**：包装 scripts、CLI 入口、用户配置/凭证/代理解析、测试 fixtures、用户可见文档。爬取与 catalog/fetch 业务逻辑不变。

## Testing Decisions

- **好测试**：只断言可观察行为——`DJM_*` 生效、legacy env 不生效、默认 config 根为 `doujinshi-meta` 且无 legacy 目录复制、打包仅含 `djm` 入口；不断言内部是否删除某私有函数名。
- **主接缝（唯一行为验收面）**：**配置与 env 解析的公开 API**（`resolve_proxy`、`require_bika_credentials`、`load_config` / `save_config` 在注入的临时根路径上）。用 `tmp_path` + `monkeypatch`：
  1. 仅 `DJM_PROXY` / `DJM_BIKA_*` → 解析成功；
  2. 仅 `DTG_*`（无 DJM）→ 等同于未设置 env（代理 `None`；凭证需文件或交互）；
  3. `load_config()` 在仅有 legacy 目录、新目录为空时 → **不**自动出现新目录文件（迁移已移除）；
  4. 新目录已有 config → 正常读取。
- **薄补充**：删除 `test_cli_rename.py` 中 dtg 弃用警告用例；可选 packaging 断言 `pyproject.toml` scripts 仅 `djm`（或通过 import 常量，不测 hatch 内部）。
- **Prior art**：`tests/test_config_rename_migration.py`（改写为 0.3.0 行为）、`tests/test_bika_credentials.py`（fixture 改 DJM）、011 Resolution 中的迁移测。
- **不必测**：真网爬取、APPDATA 真实路径、已关闭 ticket 文档内容。

## Out of Scope

- 输出契约去 `Tag` 前缀或 schema v3
- 重命名 GitHub remote / PyPI yank（当前无 remote）
- 删除用户磁盘上遗留的 `doujinshi-tag-getter` 目录（仅停止代码读写/迁移）
- 为仅 `DTG_*` 用户提供运行时自动映射到 `DJM_*`（属永久兼容，违背本规格）
- 恢复 `dtg` 为永久别名
- 修改 ADR 0001 / 0002 的核心决策
- 批量重写已关闭 Wayfinder ticket 历史正文

## Further Notes

- **前置**：ticket [011-rename-doujinshi-meta](011-rename-doujinshi-meta.md) 已在 0.2.0 落地双轨；本 ticket 为其 0.3.0 收尾。
- **Grilling 已确认（2026-08-31）**：
  - 0.3.0 删除 `dtg`、`DTG_*`、legacy 目录迁移；
  - legacy env **静默忽略**（非 stderr 提示），breaking 靠版本号与 CHANGELOG；
  - 从未跑 0.2.x、配置仅在 `doujinshi-tag-getter` 的用户不自动迁移；
  - 历史 closed ticket 不改写。
- **主测试接缝（已确认）**：配置/env 解析公开行为（`resolve_proxy`、`require_bika_credentials`、`load_config` / `save_config`）；非 CLI packaging 接缝。

## Resolution

- 版本 **0.3.0**；`pyproject.toml` 仅保留 `djm` script。
- 删除 `config.py` 中 `doujinshi-tag-getter` 迁移、`DTG_*` 双读与 DeprecationWarning；`cli.py` 去掉 `dtg` 入口分支。
- 文档/README/CONTEXT/credentials/schema 移除兼容说明；README 增加 0.3.0 breaking 摘要。
- 测试：`test_config_rename_migration.py`、`test_bika_credentials.py`、`test_cli_rename.py` 等改写；全量 **62 passed**。
