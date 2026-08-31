---
title: catalog 命令按 Tag Kind 过滤词表
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee: agent
parent: map
blocked_by: []
blocks: []
---

## Problem Statement

作为运行 `dtg catalog` 的用户，我有时只需要某一类 Tag Kind 的去重词表（例如只要自由标签 `tag`，不要哔咔的 `category`/`author` 或禁漫的 `work`/`actor`/`author`），以便更快生成面向特定维度的 assets、或在终端/表格里浏览更窄的词表。当前 catalog 始终聚合并输出全部 Kind，词表体积大、与我的使用场景不匹配；我无法在命令行指定「只统计哪些 Kind」。

## Solution

为 `dtg catalog` 增加可重复的 **`--kind`** 选项：默认不传时行为与现实现完全一致（聚合全部 Kind）；传入一个或多个 Tag Kind 时，仍完整枚举本子并拉取详情（网络成本不变），但在聚合与输出阶段只保留所选 Kind。JSON 响应增加可选字段 `kinds` 记录本次过滤条件；`stats.tags_unique` 与 `tags[]` 仅反映过滤后的子集。`--checkpoint` / `--resume` 持久化并在恢复时校验 `kinds` 一致性。`fetch` 命令本阶段不提供 Kind 过滤。

## User Stories

1. As a CLI 用户, I want `dtg catalog` 默认仍聚合全部 Tag Kind, so that 现有脚本与全量词表流程不受影响。
2. As a CLI 用户, I want 通过 `--kind tag` 只输出自由标签词表, so that 我能得到更窄、更贴近「tag 库」语义的 JSON。
3. As a CLI 用户, I want 可重复指定多个 `--kind`（如 `--kind tag --kind author`）, so that 我能灵活组合所需维度而不必跑多次全量爬取。
4. As a CLI 用户, I want 指定 Kind 后仍走完整本子枚举与详情拉取, so that 出现次数（count）统计基于相同样本集，仅输出面变窄。
5. As a CLI 用户, I want 对当前来源站无效的 Kind（如 jmcomic + `category`）启动即报错退出, so that 我不会误以为爬取成功却得到空词表。
6. As a CLI 用户, I want 无效 Kind 错误信息列出该 source 合法 Kind 集合, so that 我能快速修正命令行。
7. As a CLI 用户, I want 过滤后的 JSON 含可选字段 `kinds` 列出实际使用的 Kind, so that Flutter/CI 能区分全量词表与 Kind 子集。
8. As a CLI 用户, I want 未指定 `--kind` 时 JSON 不包含 `kinds` 或其为 null/省略（与全量语义一致）, so that 全量词表契约保持简洁。
9. As a CLI 用户, I want `stats.tags_unique` 只计输出 `tags[]` 中的唯一词条, so that 统计数字与可见词表一致。
10. As a CLI 用户, I want `stats.albums_scanned` 仍表示已处理本子数, so that 进度与全量爬取可比。
11. As a CLI 用户, I want `--checkpoint` 保存本次 `kinds` 过滤条件, so that 续爬语义明确。
12. As a CLI 用户, I want `--resume` 时若 CLI `--kind` 与 checkpoint 中 `kinds` 不一致则拒绝续爬（exit 2）, so that 不会因过滤条件变化污染词表含义。
13. As a CLI 用户, I want checkpoint 中 `kinds` 为 null 或省略表示「全量 Kind」, so that 与未传 `--kind` 的默认行为对齐。
14. As a CLI 用户, I want `--table` 与 `--kind` 可组合且表格只显示过滤后的行, so that 终端浏览与 JSON 一致。
15. As a CLI 用户, I want `--kind` 与 `-o`、`--limit`、`--proxy`、`--delay` 等现有 catalog 标志可组合, so that 本地试跑与持久化流程不变。
16. As a Flutter/子进程调用方, I want 未传 `--kind` 时 stdout JSON 与 `docs/schema.md` 全量形态兼容, so that 现有 `jsonDecode` 路径无需改动。
17. As a Flutter/子进程调用方, I want 传 `--kind` 时 `tags[]` 条目均满足 `tags[].kind` 属于请求集合, so that 下游可安全假设维度纯度。
18. As a 库调用方, I want `build_catalog` 接受可选 `kinds` 参数（与 CLI 语义一致）, so that Python 集成不必绕道子进程。
19. As a 库调用方, I want `build_catalog(..., kinds=None)` 与现签名默认行为等价, so that 测试与脚本无破坏性变更。
20. As a 维护者, I want Kind 合法集合按 source 集中定义（哔咔 `tag|category|author`；禁漫 `tag|work|actor|author`）, so that CLI 与库层校验一致。
21. As a 维护者, I want 过滤逻辑落在聚合层（`TagCounter` 或 `build_catalog` 出口）而非改各站 `extract_tags_*`, so that 来源站提取保持「全量 TagRef」单一职责。
22. As a 维护者, I want `CONTEXT.md` 记录「Kind 过滤」术语, so that 「爬取类型」等口语与 Tag Kind 对齐。
23. As a 维护者, I want `docs/schema.md` 补充 `kinds` 可选字段与 `--kind` CLI 说明, so that 契约文档可发现该能力。
24. As a CLI 用户, I want 重复传入相同 `--kind` 去重后生效, so that 脚本拼接参数时不会因重复报错。
25. As a CLI 用户, I want 传入的 `--kind` 值大小写按小写 canonical 处理（或严格小写枚举）, so that 与 JSON `TagKind` 字面量一致。
26. As a CLI 用户, I want 至少指定一个有效 Kind 才进入爬取（若解析后为空集则 exit 2）, so that 误用空过滤被及早发现。
27. As a 测试维护者, I want 在 CLI 接缝用 mock `build_catalog` 断言 `kinds` 传参, so that 不测真网且覆盖参数透传。
28. As a 测试维护者, I want 库层单测验证 `TagCounter`/`build_catalog` 过滤后 `to_entries` 仅含指定 Kind, so that 聚合语义有回归保护。
29. As a CLI 用户, I want Kind 过滤不改变 catalog 退出码既有规则, so that 脚本错误处理行为不变。
30. As a CLI 用户, I want `fetch` 本阶段无 `--kind`, so that 范围聚焦 catalog 词表构建。

## Implementation Decisions

- **接缝（主对外测试接缝）**：CLI 层——`CliRunner` 调用 `dtg catalog`，stub/mock `build_catalog`，断言 `--kind tag`（及多值）将规范化后的 `kinds` 传入；断言对非法 Kind（如 `--source jmcomic --kind category`）exit 2 且 stderr 含合法 Kind 提示。可选补充：库层 `TagCounter`/`build_catalog` 单测验证过滤输出，不作为唯一验收面。
- **CLI 新选项**：`catalog` 子命令增加可重复 `--kind`（Typer `multiple=True` 或等价）；值对应 `TagKind` 字面量。
- **默认值**：未传任何 `--kind` → `kinds=None` 内部语义 → 聚合全部 Kind；JSON 省略 `kinds` 或显式 `null`（实现择一并在 schema 文档写明）。
- **规范化**：解析后去重、排序；canonical 小写字符串；传入重复值不报错。
- **来源站校验**：在 CLI 与 `build_catalog` 入口校验 `kinds` 是否为该 `source` 的子集；任一非法 → `RuntimeError` / typer exit 2，消息含该 source 允许列表。
- **爬取流程不变**：枚举 `seen_ids`、详情 `fetch_tags_for_id`、`extract_tags_*` 仍返回完整 `list[TagRef]`；过滤在 `counter.absorb` 之后或 `to_entries(kinds=...)` / 等价出口应用。
- **响应契约**：`TagCatalogResponse` 增加可选字段 `kinds: list[str] | None`；有过滤时写入规范化列表；`tags[]` 仅含所列 Kind；`stats.tags_unique = len(过滤后唯一键)`。
- **库 API**：`build_catalog(..., kinds: Sequence[str] | None = None)`；`kinds=None` 保持现行为。
- **Checkpoint**：checkpoint JSON 增加 `kinds` 字段（`null` = 全量）；`resume` 时比较当前参数与 checkpoint；不一致 → exit 2，说明冲突。
- **表格模式**：`--table` 使用过滤后的 `result.tags`，不单独实现表格层过滤。
- **范围**：仅 `catalog`；`fetch` 不在本规格内。
- **schema_version**：保持 `1.0`；`kinds` 为向后兼容的可选字段。
- **领域词汇**：`CONTEXT.md` 已补充「Kind 过滤」；避免用「爬取类型」作契约名。

## Testing Decisions

- **好测试**：只断言外部可见行为——CLI 是否将正确 `kinds` 传给 `build_catalog`、非法 Kind 是否 exit 2、stdout JSON 的 `tags[].kind` 是否属于请求集（由 mock 或库层固定输入验证）；不断言内部 Counter 实现细节。
- **模块**：CLI 接缝（`tests/test_cli_catalog_kind_filter.py` 或并入现有 CLI 测试）；可选 `tests/test_tag_counter_kind_filter.py` 或 catalog 库测。
- **必测场景**：
  1. 无 `--kind` → `build_catalog` 收到 `kinds=None`（或等价）；
  2. `--kind tag` → 传 `kinds=["tag"]`；
  3. `--kind tag --kind author` → 传规范化列表；
  4. `jmcomic --kind category` → exit 2，stderr 含合法 Kind；
  5. mock 返回混合 Kind 词条 + CLI `--kind tag` → stdout JSON `tags` 仅 tag（若测库层过滤）；
  6. `--resume` + checkpoint `kinds` 与 CLI 不一致 → exit 2；
  7. `--table --kind tag` → stdout 表头存在且无非 tag 行（mock 注入）。
- **Prior art**：`tests/test_cli_catalog_table.py` 的 CliRunner + mock `build_catalog` 模式；`tests/test_bika_catalog_enum.py` 等库层测作补充。

## Out of Scope

- `fetch` 命令的 `--kind` 过滤
- 通过 Kind 过滤减少网络请求或跳过详情字段（仍全量拉详情）
- 跨站合并或 Kind 别名映射
- 修改各站 `extract_tags_*` 只提取部分字段
- `TagCatalogResponse` 大版本升级或破坏性字段重命名
- 按 tag **名称**过滤（仅 Kind 维度）
- 全局 `--kind` 跨子命令共享

## Further Notes

- Grilling 会话已全部决议并采纳推荐项（Q1–Q9）。
- 哔咔合法 Kind：`tag`、`category`、`author`。禁漫合法 Kind：`tag`、`work`、`actor`、`author`。
- 实现时 `--kind` help 文案应写明「仅影响词表聚合/输出；仍爬取全部本子详情」。
- `kinds` 在 JSON 中建议按字母序排列以便 diff 稳定。

## Resolution

已实现：`dtg catalog --kind`（可重复）按 Tag Kind 过滤词表聚合/输出；默认全量 Kind 不变。`TagCatalogResponse` 增加可选 `kinds` 字段；`build_catalog(..., kinds=...)` 与 checkpoint `kinds` 校验。CLI 接缝测试见 `tests/test_cli_catalog_kind_filter.py`；`TagCounter.to_entries(kinds=...)` 见 `tests/test_tag_counter_kind_filter.py`。`docs/schema.md` 已同步。
