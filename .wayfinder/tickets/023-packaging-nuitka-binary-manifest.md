---
title: 本地 Nuitka 二进制与 manifest（最小构建路径）
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee:
parent: 021-packaging-distribution-scripts.md
blocked_by: [022-packaging-cli-version.md]
---

## Parent

[021-packaging-distribution-scripts.md](021-packaging-distribution-scripts.md)

## What to build

在 Windows x64 且 MSVC 可用的环境中，维护者执行 `uv run python scripts/build.py` 即可产出 **Standalone 二进制**分发目录：`dist/djm-{version}-windows-x64/djm.exe` 与同目录 `manifest.json`（含 name、version、platform、artifact、sha256、built_at）。构建前 preflight 检测平台与编译器，失败时给出可操作建议；构建完成后对 exe 自动执行 `--version` 与 `--help` 冒烟。dev 依赖组声明 `nuitka`。

## Acceptance criteria

- [x] `scripts/build.py` 存在且默认构建 Nuitka onefile 至约定目录
- [x] `manifest.json` 字段齐全且 sha256 与 `djm.exe` 一致
- [x] 非 Windows 或缺少 MSVC 时脚本 exit 非 0 并打印明确错误
- [x] 构建成功后子进程 `djm.exe --version` 与 `djm.exe --help` 均 exit 0
- [x] `pyproject.toml` dev 依赖含 `nuitka`；`dist/` 已在 `.gitignore`
- [x] manifest 生成逻辑有单元测（给定假文件断言 sha256 与 JSON 形状）
- [x] frozen 二进制仍使用 `%APPDATA%\doujinshi-meta\` 配置路径（行为与源码安装一致，无新 env 前缀）
