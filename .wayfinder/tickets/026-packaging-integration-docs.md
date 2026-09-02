---
title: 分发与集成文档
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee:
parent: 021-packaging-distribution-scripts.md
blocked_by: [025-packaging-github-release-ci.md]
---

## Parent

[021-packaging-distribution-scripts.md](021-packaging-distribution-scripts.md)

## What to build

集成宿主开发者无需阅读构建脚本源码，即可从文档获知如何获取 **Standalone 二进制**、校验 **manifest**、在本地复现构建，以及从 GitHub Release 下载 zip/wheel。README 面向贡献者说明 Windows x64、MSVC、uv 前置条件与构建命令。

## Acceptance criteria

- [x] `docs/integration.md` 新增「获取 Standalone 二进制」小节：Release zip 下载、manifest 字段与 SHA256 校验、Flutter 捆绑指引（指针级即可）
- [x] `README.md` 含本地构建命令、`scripts/build.py` 常用选项与 MSVC 前置条件说明
- [x] 文档与 ADR 0003、CONTEXT 词汇（分发产物、Standalone 二进制）一致
- [x] 按文档步骤可从 `dist/` 或（CI 就绪后）Release 完成集成方视角验收

## Blocked by

- [025-packaging-github-release-ci.md](025-packaging-github-release-ci.md)
