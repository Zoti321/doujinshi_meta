---
title: catalog 命令可选表格输出
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee: agent
parent: map
blocked_by: []
blocks: []
---

## Problem Statement

作为在终端本地运行 `dtg catalog` 的用户，我需要在爬取完成后快速浏览 tag 词表里的 **kind**、**name** 与 **count**，而不必在终端里滚动大段缩进 JSON。当前 catalog 只输出 `TagCatalogResponse` JSON，对人眼不友好；同时 Flutter / 脚本集成仍依赖 JSON 契约，不能因「好看」而破坏默认交付形态。

## Solution

为 `dtg catalog` 增加可选的 **`--table` 开关**：默认行为不变（stdout 或 `-o` 输出完整 JSON）；启用 `--table` 时，stdout 输出一张三列表格（`kind` | `name` | `count`），使用 `rich` 渲染对齐。表格是 **CLI 呈现层**，不属于输出契约；`build_catalog` 库 API 不新增表格格式化。`--table` 与 `-o` 互斥；表格不附带 `source` / `stats` 等元信息 preamble。

## User Stories

1. As a CLI 用户, I want `dtg catalog` 默认仍输出 `TagCatalogResponse` JSON, so that Flutter 子进程与现有脚本集成不受影响。
2. As a CLI 用户, I want 通过 `--table` 将 catalog 结果以表格打印到 stdout, so that 我能在终端快速扫读词条。
3. As a CLI 用户, I want 表格包含 `kind`、`name`、`count` 三列, so that 我能同时看到维度、标签名与出现次数。
4. As a CLI 用户, I want 表格列顺序与 JSON 词表条目语义一致（按 count 降序）, so that 表格与 JSON 的优先级感相同。
5. As a CLI 用户, I want 空词表时仍显示表头、无数据行, so that 我能区分「无数据」与「命令失败」。
6. As a CLI 用户, I want `--table` 时 stdout 不含 JSON, so that 管道/重定向不会被 JSON 与表格混杂。
7. As a CLI 用户, I want `--table` 与 `-o` / `--output` 同时指定时报错退出, so that 不会出现「文件里是表还是 JSON」的歧义。
8. As a CLI 用户, I want 仅使用 `-o` 时文件内容仍为完整 JSON, so that 我能把词表交给 CI / assets 流程。
9. As a CLI 用户, I want catalog 爬取进度日志仍在 stderr, so that `--table` 不污染人类进度输出与 stdout 数据面分离约定。
10. As a CLI 用户, I want 表格模式下 stdout 不打印 `source` / `generated_at` / `stats` 摘要, so that 表格专用于扫词条；元信息仍可从默认 JSON 获取。
11. As a CLI 用户, I want 表格对中文/日文标签名对齐可读, so that CJK 词表浏览体验可接受。
12. As a 库调用方, I want `build_catalog` 仍只返回 `TagCatalogResponse` dataclass, so that Python 集成路径不被 CLI 呈现细节污染。
13. As a Flutter/子进程调用方, I want 未传 `--table` 时 stdout 契约与 `docs/schema.md` 一致, so that `jsonDecode` 与 Schema 生成无需改动。
14. As a 维护者, I want 表格渲染逻辑封装在 CLI 层（或 CLI 私有辅助）, so that 领域模型与 catalog 聚合逻辑保持纯净。
15. As a 维护者, I want 复用 Typer 传递依赖的 `rich` 打表, so that 不引入新的表格依赖。
16. As a 维护者, I want `CONTEXT.md` 明确「表格视图 ≠ 输出契约」, so that 后续贡献者不会把 `--table` 当作集成交付格式。
17. As a CLI 用户, I want `fetch` 命令本阶段不提供 `--table`, so that 范围聚焦 catalog 词表浏览。
18. As a CLI 用户, I want `--table` 不影响 catalog 退出码语义（含既有 errors / albums_scanned 规则）, so that 脚本错误处理行为不变。
19. As a 测试维护者, I want 用 CliRunner 在 CLI 接缝验收表格输出, so that 不测 rich 内部实现细节。
20. As a 测试维护者, I want 通过 mock/stub `build_catalog` 注入固定词表, so that 测试不依赖真网爬取。
21. As a CLI 用户, I want `--table` 与 `--limit` 等现有 catalog 标志可组合, so that 本地试跑小样本时也能看表。
22. As a 文档读者, I want `docs/schema.md` 或 README 提及 `--table` 为人类可读可选输出, so that 我发现该开关而不误当作 JSON 契约字段。

## Implementation Decisions

- **接缝（唯一对外测试接缝）**：CLI 层——`CliRunner` 调用 `dtg catalog`，在边界 stub/mock `build_catalog` 返回已知 `TagCatalogResponse`，断言 stdout 含三列表头与注入条目、且 stdout 非 JSON；`--table` 与 `-o` 同传时断言非零退出与明确错误信息。不把 rich 内部渲染细节（边框字符、精确列宽）作为验收标准。
- **新 flag**：`catalog` 子命令增加 `--table`（bool，默认 `False`）。
- **默认路径**：未指定 `--table` 时，行为与现实现完全一致（`_write_json` → stdout 或 `-o`）。
- **表格路径**：`--table` 为真时，将 `TagCatalogResponse.tags` 转为行列表，列 `kind` / `name` / `count`（整数）；用 `rich.table.Table` 或等价 API 打印到 stdout；不调用 `_write_json`。
- **排序**：表格行顺序与 JSON `tags[]` 相同（当前聚合为 count 降序）；表格模式不重新排序。
- **互斥**：`--table` 与 `-o` / `--output` 同时出现 → `typer.echo` 错误到 stderr，`Exit(code=2)`。
- **空词表**：渲染带表头的空表（零数据行），正常退出（除非既有 errors 规则触发非零退出）。
- **元信息**：表格 stdout 不含 preamble；`stats` / `source` / `generated_at` 仅在默认 JSON 路径可见。
- **库 API**：`build_catalog` 签名与返回类型不变；不暴露 `format_catalog_table` 等公开 helper。
- **范围**：仅 `catalog`；`fetch` 不在本规格内。
- **领域词汇**：在 `CONTEXT.md`「输出契约」旁补充「表格视图（Table View）」——CLI 可选人类可读呈现，非 JSON 契约的一部分。
- **依赖**：使用已有 `rich`（Typer 传递依赖）；若需显式声明 dev/runtime 依赖再评估，优先不新增包。

## Testing Decisions

- **好测试**：只断言外部可见行为——stdout 是否含列名与已知 tag 行、是否非 JSON、`--table`+`-o` 是否退出码 2；不断言 rich 边框样式或精确空白填充。
- **模块**：CLI 接缝（`tests/test_cli_catalog_table.py` 或并入现有 CLI 测试文件）；mock 目标为 `build_catalog`（与 `catalog_cmd` 同模块导入路径）。
- **必测场景**：
  1. 默认（无 `--table`）→ stdout 为合法 JSON，含 `tags` 数组；
  2. `--table` + 注入 2+ 词条 → stdout 含 `kind`/`name`/`count` 表头与各 name；
  3. `--table` + 空 `tags` → stdout 含表头、无 JSON；
  4. `--table` + `-o /tmp/out.json` → 退出码 2，stderr 含互斥说明；
  5. （可选）条目顺序与 mock 返回的 `tags` 列表顺序一致。
- **Prior art**：`tests/test_cli_credentials.py` 的 `CliRunner` + `app.invoke` 模式；不引入真网 catalog 集成测。

## Out of Scope

- `fetch` 命令的表格或 `--pretty` JSON
- `--format json|table` 通用格式框架（v1 仅 `--table` 布尔开关）
- 表格模式下的 `source` / `stats` 摘要行（stdout 或 stderr）
- `-o` 写入表格文本文件
- 库层 `build_catalog` 的表格格式化 API
- 跨命令全局 `--table` / `--pretty`
- 修改 `TagCatalogResponse` schema 或 JSON 字段
- Markdown / CSV / TSV 等其它人类可读格式

## Further Notes

- Grilling 会话（catalog 输出美化）已全部决议；Q3 选用三列（含 `count`），其余采纳推荐项。
- 实现时 `--table` help 文案应写明「人类可读；默认 JSON 为集成契约」。
- 若 rich 在 Windows 终端编码异常，实现阶段可 fallback 到 `Console(force_terminal=True)` 或文档注明终端要求；本规格不强制 fallback，以实现时实测为准。

## Resolution

已实现：`dtg catalog --table` 用 rich 打印 `kind`/`name`/`count` 表格；默认仍为 JSON；与 `-o` 互斥（exit 2）；`build_catalog` 不变。CLI 接缝测试见 `tests/test_cli_catalog_table.py`。`CONTEXT.md` 表格视图、`docs/schema.md` / README 已同步。`rich` 升为直接依赖。
