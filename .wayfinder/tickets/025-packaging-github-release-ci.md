---
title: GitHub Actions Release 流水线
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee:
parent: 021-packaging-distribution-scripts.md
blocked_by: [024-packaging-build-script-extensions.md]
---

## Parent

[021-packaging-distribution-scripts.md](021-packaging-distribution-scripts.md)

## What to build

发布者 push `v*` tag 或通过 `workflow_dispatch` 手动触发时，GitHub Actions 在 `windows-latest` 上执行完整构建（含 `--wheel`），对产物跑 `djm.exe --version` 与 `--help`（**不打真网**），成功后创建 GitHub Release 并上传三类附件：`djm-{version}-windows-x64.zip`、`.whl`、`.tar.gz`。构建失败时不发布半成品 Release。

## Acceptance criteria

- [x] `.github/workflows/release.yml`（或等价）在 `push: tags: v*` 与 `workflow_dispatch` 时触发
- [x] workflow 使用 `uv sync`（含 dev）并执行 `uv run python scripts/build.py --wheel`
- [x] job 内对 `dist/.../djm.exe` 子进程断言 `--version` 与 `--help` exit 0
- [x] 成功时 Release 附件含 zip（exe+manifest）、wheel、sdist
- [x] 构建步骤失败时 workflow 失败且不创建/不上传 Release 资产
- [x] CI **不**执行 `--smoke-full` 或真网 fetch

## Blocked by

- [024-packaging-build-script-extensions.md](024-packaging-build-script-extensions.md)
