---
title: CLI 版本标识（djm --version）
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee:
parent: 021-packaging-distribution-scripts.md
blocked_by: []
---

## Parent

[021-packaging-distribution-scripts.md](021-packaging-distribution-scripts.md)

## What to build

维护者与集成宿主可通过 `djm --version` 获取与发行版一致的语义化版本号；Python 库调用方可通过 `doujinshi_meta.__version__` 对账。版本来源为包元数据（与 `pyproject.toml` 同步），不手写重复常量。

## Acceptance criteria

- [x] 运行 `djm --version` 打印单行版本（如 `0.3.0`）且 exit 0
- [x] `doujinshi_meta.__version__` 与 CLI 输出一致
- [x] CliRunner 测试断言版本字符串与 `pyproject.toml` 中 `[project].version` 匹配
- [x] 现有测试套件仍全部通过
