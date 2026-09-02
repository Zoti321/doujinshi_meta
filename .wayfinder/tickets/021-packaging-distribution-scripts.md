---
title: 打包脚本与 Windows 分发产物（Nuitka + wheel + GitHub Release）
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee:
parent: map.md
blocked_by: []
---

## Problem Statement

作为将 `doujinshi-meta` 集成进 **Flutter 桌面**或其他非 Python 宿主的开发者，我需要在目标机器上调用 `djm` 子进程解析 JSON，但宿主环境**未必已安装 Python**。现有仓库仅支持 `uv sync` / `uv tool install` / editable install，缺少可复现的**打包脚本**与**分发产物**（Standalone 二进制、`wheel`、校验清单）。我希望一条命令（或 CI tag）产出带版本与 SHA256 的 Windows x64 产物，并发布到 GitHub Release，以便宿主构建期捆绑、校验与升级。

## Solution

1. 新增统一构建入口 **`scripts/build.py`**（或等价模块）：默认构建 **Nuitka Standalone 二进制**（onefile），可选 `--wheel`、`--onedir`；输出至 **`dist/djm-{version}-windows-x64/`**，含 **`djm.exe`** 与 **`manifest.json`**（version、platform、sha256、build_time）。
2. 构建前 **preflight** 检测 Windows x64 与 **MSVC** 可用性，失败时给出可操作建议（安装 Visual Studio Build Tools）。
3. CLI 新增 **`djm --version`**，输出来自包版本（与 `pyproject.toml` 一致），供冒烟测试与宿主校验。
4. 本地完整冒烟：**`--version`** + **`--help`** + 可选 **`--smoke-full`**（真网 `fetch --source jmcomic --ids 410090`）。
5. 新增 **GitHub Actions**：**`workflow_dispatch`** + **push `v*` tag** 时构建；CI 冒烟仅 version/help（无真网）；Release 附件：**zip**（exe + manifest）、**wheel**、**sdist**。
6. 更新 **`docs/integration.md`** 与 **README** 中的分发/捆绑说明。

## User Stories

### 构建脚本（本地）

1. As a 维护者, I want `uv run python scripts/build.py` 默认产出 Windows x64 Standalone 二进制, so that 一条命令完成最常见集成路径。
2. As a 维护者, I want `scripts/build.py --wheel` 额外产出 wheel/sdist（`uv build`）, so that Python 宿主无需 Nuitka 也能安装同版本。
3. As a 维护者, I want `scripts/build.py --onedir` 产出目录模式二进制, so that 排查 Nuitka 缺模块时比 onefile 更快。
4. As a 维护者, I want 默认 onefile 时 `djm.exe` 位于 `dist/djm-{version}-windows-x64/`, so that 与 onedir 输出目录约定一致。
5. As a 维护者, I want 同目录生成 `manifest.json`, so that 宿主构建期可校验 SHA256 与版本。
6. As a 维护者, I want manifest 含 `version`、`platform`、`artifact`、`sha256`、`built_at`, so that Flutter 缓存与升级逻辑有稳定字段。
7. As a 维护者, I want 版本号从 `pyproject.toml` 解析, so that 不与手写常量分叉。
8. As a 维护者, I want 构建前检测非 Windows 或缺少 MSVC 时 exit 非 0 并打印明确错误, so that 不会等到 Nuitka 深处才失败。
9. As a 维护者, I want `dist/` 在 `.gitignore` 中且脚本可 `clean` 旧产物, so that 仓库不被二进制污染。
10. As a 维护者, I want Nuitka 包含 `jmcomic`、`httpx`、`typer`、`rich` 等依赖, so that frozen 二进制可执行 fetch/search。
11. As a 维护者, I want 构建脚本在 dev 依赖组声明 `nuitka`, so that `uv sync` 即可准备构建环境。
12. As a 维护者, I want `--smoke-full` 在本地构建后跑真网 jmcomic fetch, so that 集成功能冒烟与 CI 分离。
13. As a 维护者, I want 无 `--smoke-full` 时至少跑 `--version` 与 `--help`, so that 每次构建有快速验收。

### CLI 版本

14. As a CLI 用户, I want `djm --version` 打印语义化版本（如 `0.3.0`）, so that 脚本与宿主可识别捆绑二进制版本。
15. As a CLI 用户, I want `djm --version` exit 0, so that CI 可简单断言。
16. As a Flutter 集成方, I want 子进程 `djm --version` 输出单行版本, so that 不必解析 `--help` 文本。
17. As a 库调用方, I want 包级 `__version__` 与 CLI 一致, so that Python 与二进制版本可对账。

### 集成宿主

18. As a Flutter 桌面开发者, I want 从 Release 下载 zip 解压得到 `djm.exe`, so that 可放入 `native_assets` 或构建脚本拷贝路径。
19. As a Flutter 桌面开发者, I want manifest 中 sha256 与 zip 内 exe 一致, so that 构建期可检测损坏或篡改。
20. As a 通用 CLI 集成方, I want Release 提供独立 `djm.exe` zip, so that Electron/Rust 等也能子进程调用。
21. As a Python 集成方, I want Release 附带 wheel, so that 不必克隆源码即可 `pip install` 同版本。
22. As a CI 维护者, I want wheel 与二进制来自同一 tag 的同一构建, so that 版本不会漂移。

### GitHub Actions / Release

23. As a 发布者, I want push `v*` tag 时自动构建并创建 GitHub Release, so that 发版可重复。
24. As a 发布者, I want `workflow_dispatch` 手动触发构建, so that 调试 Nuitka 不必打 tag。
25. As a 发布者, I want Release 附件含 `djm-{version}-windows-x64.zip`（exe + manifest）, so that 宿主一次下载拿全。
26. As a 发布者, I want Release 附件含 `.whl` 与 `.tar.gz`（sdist）, so that PyPI 外也能从 Release 安装。
27. As a 发布者, I want CI 冒烟仅 `djm --version` 与 `djm --help`, so that 来源站波动不阻塞发版。
28. As a 发布者, I want CI 在 Windows runner 上构建, so that 与 v1 目标平台一致。
29. As a 发布者, I want tag 构建失败时不发布半成品 Release, so that 用户不会下到坏包。

### 配置与 frozen 行为

30. As a CLI 用户, I want frozen `djm.exe` 仍读写 `%APPDATA%\doujinshi-meta\` 配置与凭证, so that 与源码安装行为一致。
31. As a CLI 用户, I want frozen 二进制仍支持 `DJM_PROXY` / `DJM_BIKA_*` 环境变量, so that 非交互集成不受影响。
32. As a 维护者, I want 不因打包引入新的配置路径或 env 前缀, so that `docs/credentials.md` 仍有效。

### 文档

33. As a 文档读者, I want `docs/integration.md` 说明如何获取 Standalone 二进制与 manifest, so that 集成方不必读构建脚本源码。
34. As a 文档读者, I want README 含构建前置条件（Windows x64、MSVC、uv）, so that 贡献者可本地复现。
35. As a 文档读者, I want ADR 记录 Nuitka 选型理由, so that 未来换 PyInstaller 需有意识决策。
36. As a 文档读者, I want CONTEXT 中「分发产物」「Standalone 二进制」术语与实现一致, so that 词汇表可依赖。

### 测试

37. As a 测试维护者, I want CliRunner 测 `djm --version` 输出匹配 `pyproject` 版本, so that CLI 薄层可回归。
38. As a 测试维护者, I want 构建接缝测试在本地/CI 跑产物 `--version`/`--help`, so that 不测 Nuitka 内部模块列表。
39. As a 测试维护者, I want manifest 生成逻辑有单元测（给定假文件算 sha256）, so that 不必每次全量 Nuitka 验证 JSON 形状。

## Implementation Decisions

### 接缝（测试，已与用户确认）

- **主测试接缝（唯一）**：**构建管线出口**——执行 `scripts/build.py`（或 CI 等价步骤）后，对 `dist/djm-{version}-windows-x64/djm.exe` 子进程调用 **`--version`**（断言版本字符串）与 **`--help`**（exit 0）。本地可选 **`--smoke-full`** 真网 jmcomic fetch；**CI 不跑真网**。
- **补充接缝**：CliRunner 测 `djm --version`；`manifest.json` 生成函数纯单元测（sha256、字段齐全）。

### 构建入口

- **`scripts/build.py`**（推荐 Python，便于跨步骤编排与 preflight）：
  - `--binary`（默认 true）/ `--no-binary`
  - `--wheel`：调用 `uv build`，wheel/sdist 输出到 `dist/`
  - `--onedir`：Nuitka 目录模式；默认 **onefile**
  - `--smoke-full`：构建后真网 fetch（仅本地推荐）
  - `--clean`：清理 `dist/` 下本版本产物
- 版本：读取 `pyproject.toml` `[project].version`（可用 `tomllib` 或 hatchling 元数据，避免硬编码）。

### Nuitka

- 入口：`doujinshi_meta.cli:run`（与 `[project.scripts]` 一致）。
- 模式：默认 `--onefile`；`--onedir` 时输出同目录 `djm.exe` + 依赖。
- 需 `--include-package` / `--include-package-data` 覆盖 `jmcomic`、`doujinshi_meta` 及隐式数据文件（按构建报错迭代，写入脚本注释或 nuitka 配置模块）。
- **Preflight**：`sys.platform == win32`、检测 `cl.exe` 或 VS 环境（如 `vswhere` / `where cl`）；失败 exit 2 + 文档链接。
- 见 ADR [`docs/adr/0003-nuitka-standalone-binary.md`](../../docs/adr/0003-nuitka-standalone-binary.md)。

### manifest.json 形状（示意）

```json
{
  "name": "doujinshi-meta",
  "version": "0.3.0",
  "platform": "windows-x64",
  "artifact": "djm.exe",
  "sha256": "<hex>",
  "built_at": "2026-09-02T05:00:00+00:00"
}
```

### dist/ 布局

```
dist/
  djm-0.3.0-windows-x64/
    djm.exe
    manifest.json
  doujinshi_meta-0.3.0-py3-none-any.whl   # --wheel 时
  doujinshi_meta-0.3.0.tar.gz
  djm-0.3.0-windows-x64.zip               # Release 用：打包上述目录
```

### CLI `--version`

- Typer 全局 callback 或 `@app.callback`：`--version` 打印版本后 exit 0。
- `doujinshi_meta/__init__.py` 暴露 `__version__`（从 `importlib.metadata` 或单点常量与 pyproject 同步）。

### GitHub Actions

- 文件：`.github/workflows/release.yml`（名称可调整）。
- **on**：`push: tags: ['v*']`、`workflow_dispatch`。
- **runs-on**：`windows-latest`。
- **steps**：checkout → setup uv → `uv sync`（含 dev）→ `uv run python scripts/build.py --wheel` → 子进程冒烟 `--version`/`--help` → zip `dist/djm-*-windows-x64/` → `softprops/action-gh-release` 上传 zip + wheel + sdist。
- **不**在 CI 跑 `--smoke-full`。

### 依赖

- `[dependency-groups] dev` 增加 `nuitka`（版本 pin 合理下限）。

### 文档

- `docs/integration.md`：新增「获取 Standalone 二进制」小节（Release zip、manifest 校验、Flutter 捆绑示例指针）。
- `README.md`：构建命令与 MSVC 前置条件。

### 领域词汇

- 沿用 `CONTEXT.md`：**集成宿主**、**分发产物**、**Standalone 二进制**。

## Testing Decisions

- **好测试**：只断言子进程 exit 码、stdout 版本字符串、manifest JSON 字段与 sha256；不断言 Nuitka 命令行每一 flag 或内部 import 图。
- **模块**：`tests/test_cli_version.py`（CliRunner）；`tests/test_build_manifest.py`（manifest 生成纯函数）；可选 `tests/test_build_smoke.py` 标记 `@pytest.mark.integration` 且默认 skip（需本地已构建 exe）。
- **CI**：构建 job 内直接 `subprocess.run([exe, '--version'])`。
- **Prior art**：`tests/test_cli_search.py` CliRunner 模式；仓库尚无构建测试。

## Out of Scope

- macOS / Linux Standalone 二进制（v1 仅 Windows x64）
- Android / iOS 内嵌 Python 或二进制
- PyPI 自动发布（仅 GitHub Release 附件；PyPI 可后续 ticket）
- 代码签名（Authenticode）与 notarization
- 自动更新 / delta 更新协议
- Docker 镜像分发
- 将 `schemas/` 打入 zip（宿主从 git 获取；若需离线 bundle 另开 ticket）
- CI 真网冒烟（明确排除，避免卡 Release）

## Further Notes

- Grilling 021 已关闭全部 frontier；Nuitka vs PyInstaller 见 ADR 0003。
- `jmcomic` 可能有动态导入或数据文件——实现时按 Nuitka 报错增补 `--include-package-data`，优先收敛到 `scripts/build.py` 单处配置。
- Release tag 建议 `v0.3.1` 与 `pyproject.toml` version bump 同步（发版流程可在 PR 说明，本 spec 不强制自动化 bump）。
- 实现完成后更新 [`map.md`](../map.md)「Not yet specified」并关闭本 ticket。
