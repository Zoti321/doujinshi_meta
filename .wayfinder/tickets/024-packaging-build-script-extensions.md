---
title: 构建脚本扩展（wheel / onedir / 完整冒烟 / zip）
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee:
parent: 021-packaging-distribution-scripts.md
blocked_by: [023-packaging-nuitka-binary-manifest.md]
---

## Parent

[021-packaging-distribution-scripts.md](021-packaging-distribution-scripts.md)

## What to build

在最小 Nuitka 构建路径之上，维护者可通过构建脚本可选产出 **Python 分发包**与**调试/验收模式**：`--wheel` 调用 `uv build` 生成 wheel 与 sdist；`--onedir` 切换 Nuitka 目录模式便于排查缺模块；`--smoke-full` 在本地对构建产物执行真网 `fetch --source jmcomic --ids 410090`；`--clean` 清理本版本 `dist/` 产物。脚本还生成 `djm-{version}-windows-x64.zip`（含 exe + manifest），供 GitHub Release 直接上传。

## Acceptance criteria

- [x] `scripts/build.py --wheel` 在 `dist/` 产出 wheel 与 sdist，且与二进制同版本
- [x] `scripts/build.py --onedir` 在同约定目录产出 `djm.exe`（目录模式）+ manifest
- [x] `scripts/build.py --smoke-full` 在本地对 exe 跑 jmcomic fetch 且 exit 0（需网络；文档注明仅本地使用）
- [x] `scripts/build.py --clean` 可清理当前版本相关产物
- [x] 构建流程生成 `djm-{version}-windows-x64.zip`，解压后含 `djm.exe` 与 `manifest.json`
- [x] 默认构建（无 `--smoke-full`）仍只跑 `--version` / `--help` 快速冒烟

## Blocked by

- [023-packaging-nuitka-binary-manifest.md](023-packaging-nuitka-binary-manifest.md)
