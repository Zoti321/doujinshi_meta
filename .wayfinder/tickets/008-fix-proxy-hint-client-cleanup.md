---
title: 修正哔咔代理提示、清理死代码并回滚 App 头
labels: [wayfinder:task, ready-for-agent]
status: closed
assignee: agent
parent: map
blocked_by: []
blocks: []
---

## Problem Statement

作为在国内 Windows 上用 `dtg` 拉哔咔 tag 的用户，我遇到两类误导与漂移：

1. **代理提示挂错场景**：登录响应 `code=200` 但缺 `data`/`token`（账号、签名等问题）时，错误信息却建议 `dtg config set proxy` / `--proxy`；真正 `ConnectError`/超时且当前直连时，反而没有按 `docs/credentials.md` 约定给出代理兜底提示。
2. **实现漂移**：无调用方的 `proxy_to_httpx` 仍留在配置模块；哔咔 `app-channel` / `app-build-version` 被改成与 pica-cli 对齐的值，但调研明确写「无需为对齐而改，仅在签名/兼容失败时再试」。

我希望 CLI/库在失败时说对原因，客户端常量回到未经验证变更前的基线，并去掉已无用的代理适配空壳。

## Solution

从用户视角：

- 跑 `dtg fetch` / `dtg catalog`（哔咔）时：若因**网络连不上**失败且当前为直连，stderr/错误信息会提示可配置代理；若因**登录/鉴权/签名**失败，只谈账号密码（及必要时网络环境笼统说明），**不**把「去设代理」当成主因。
- 已配置代理时，同类连接失败不再怂恿「再去设代理」。
- 客户端请求头回到 `app-channel=1`、`app-build-version=44`；`proxy_to_httpx` 从公开 API 中移除。
- ticket 007 与 `docs/credentials.md` 对「环境变量 + 缺失时交互提示」的表述对齐，避免「完成定义」歧义。

## User Stories

1. As a CLI 用户, I want 直连哔咔因连接失败退出时看到可配置代理的提示, so that 我知道国内环境下的下一步不是瞎改账号。
2. As a CLI 用户, I want 已用 `--proxy` / 配置文件 / `DTG_PROXY` 时连接失败不再提示「去设代理」, so that 提示不会重复且不误导。
3. As a CLI 用户, I want 登录失败（错误密码或响应无 token）时看到账号/密码相关说明, so that 我不会先去折腾代理。
4. As a CLI 用户, I want `code=200` 但响应缺 data 时同样不主推代理提示, so that 签名/协议类问题与网络问题可区分。
5. As a CLI 用户, I want `dtg fetch --source bika` 与 `dtg catalog --source bika` 在上述失败语义上一致, so that 两个命令不会一个对一个错。
6. As a 库调用方, I want `fetch_tags` / `build_catalog` 抛出的错误信息与 CLI 同源语义, so that 子进程集成与 Python 集成行为一致。
7. As a 国内 Windows 用户, I want 错误文案仍提及 `dtg config set proxy` 与 `--proxy`, so that 我能对照 README / credentials 文档操作。
8. As a CI/脚本用户, I want 非交互且无完整 env 时仍按现有凭证规则失败, so that 本规格不破坏已实现的交互/env 契约。
9. As a 维护者, I want 删除无调用方的 `proxy_to_httpx`, so that 配置模块不再暴露死包装。
10. As a 维护者, I want 确认全仓库无 `proxy_to_httpx` 引用后才删除, so that 不会留下半截导入。
11. As a 维护者, I want 哔咔默认头回滚为 `app-channel`=`1`、`app-build-version`=`44`, so that 未经验证的 pica-cli 对齐被撤销。
12. As a 维护者, I want 调研文档中「本项目当前值」与代码一致, so that 文档不会仍写已回滚前的对照表。
13. As a 阅读 credentials 的用户, I want 「连接失败且直连」与「登录失败」的提示规则写清, so that 文档与实现同一套契约。
14. As a 阅读 ticket 007 的用户, I want Resolution 注明凭证可为 env 或交互提示、token 首版仅内存, so that 与 living `docs/credentials.md` 无歧义。
15. As an agent 实现者, I want 在 CLI/集成层用伪造传输失败验证提示, so that 测的是用户可见行为而非内部 helper 名。
16. As an agent 实现者, I want 登录缺 token/data 的集成断言不含代理配置短语, so that 错误归因回归可自动抓住。
17. As an agent 实现者, I want 已注入 proxy 的集成路径连接失败时断言不含「去设代理」主提示, so that 条件分支被锁住。
18. As a Flutter/子进程调用方, I want 致命网络/登录错误仍以非 0 退出且信息不含密码, so that 日志安全与现有退出码约定不变。
19. As a 禁漫用户, I want 本规格不改变 jmcomic 代理/`proxies=None` 行为, so that 范围不扩散到无关来源。
20. As a 产品决策读者, I want 明确「代理提示是环境建议不是 API 必填」, so that 与 CONTEXT 领域词汇一致。

## Implementation Decisions

- **接缝（唯一对外测试接缝）**：CLI / 集成层——经 `fetch_tags`（及与之同路径的 catalog 哔咔入口）驱动真实调用链，在边界注入可失败的 HTTP 传输（例如替换/mock 哔咔客户端所用的 httpx 传输或 client），断言用户可见的异常文案 / stderr 语义。不把「是否抽了某个私有 helper」当作验收标准。`BikaClient` 内部可改，但规格验收以集成行为为准。
- **代理提示触发条件**：仅当发生传输层失败（连接失败、超时等）且本次解析到的代理为「直连」（`None`）时，错误信息须包含可操作的代理配置提示（`dtg config set proxy` 与/或 `--proxy`）。
- **代理提示抑制条件**：传输层失败但已配置非空 proxy 时，可报告连接失败，但不得再主推「去设置代理」。
- **登录/载荷解析失败**：缺 `data`、缺 `token`、非 200 业务码等——文案聚焦账号/密码（及既有业务 message）；**不得**把「去设代理」作为主建议（与 credentials 文档「连接失败」条款对齐）。
- **CLI 与库**：`dtg fetch` / `dtg catalog` 与对应库函数共享同一错误语义；不必为 CLI 再做一套文案分支。
- **删除 `proxy_to_httpx`**：该函数在 httpx 0.28 后仅为恒等包装且无调用方；从配置模块公开面移除；调用点继续直接传 proxy URL 字符串给 httpx。
- **回滚客户端常量**：哔咔默认请求头恢复为 `app-channel`=`1`、`app-build-version`=`44`；不在本规格内引入 `DTG_BIKA_SECRET_KEY` 或可配置 channel。
- **文档**：更新 `docs/credentials.md` 明确区分「连接失败提示」与「登录失败提示」；同步调研对照表中本项目当前 channel/build；修订 ticket 007 Resolution 一句，写明凭证 = env 优先，缺失可交互，token 首版内存、持久化延后。
- **领域词汇**：沿用 CONTEXT——用户凭证、客户端常量、网络可达性/代理（非 API 必填）。
- **不改**：凭证解析顺序、Git Bash 可见密码回退、代理优先级、`HTTPS_PROXY` 不继承、token 不落盘。

## Testing Decisions

- **好测试**：只断言外部行为（抛错类型/文案关键短语、CLI 退出后用户能看到的语义）；不绑定私有函数名或是否 soft-wrap。
- **模块**：以哔咔 `fetch_tags` 集成路径为主（可复用同一注入方式覆盖 catalog 哔咔入口若成本低；至少一条 fetch 路径锁住语义）。既有 `tests/test_bika_login.py`、`test_bika_credentials.py`、`test_password_prompt.py` 可保留/微调，但本规格新增验收以集成层为准。
- **必测场景**：
  1. 直连 + 传输连接失败 → 文案含代理配置提示；
  2. 已设 proxy + 传输连接失败 → 文案不含「去设代理」类主提示；
  3. 登录成功 HTTP 但载荷无 token/data → 文案含登录/账号语义，不含代理配置主提示；
  4. `proxy_to_httpx` 已不存在（导入失败或仓库检索无符号即可作为守护）；
  5. 默认头为 channel `1`、build `44`（可读默认 headers 或经客户端暴露的常量断言——若只能集成测，则至少在单元只读常量处锁住，并注明常量回滚是支撑决策）。
- **Prior art**：现有测试用 `monkeypatch` / `MagicMock` 注入 `post` 与凭证回调；集成层可沿用「替换 client 传输/方法」风格，避免真网。

## Out of Scope

- Token 持久化缓存到用户目录
- 可配置 `secret_key` / `app-channel` 环境变量覆盖
- 为对齐 pica-cli 再次改 nonce / channel / build
- 系统 `HTTP(S)_PROXY` 自动继承
- 禁漫来源行为变更、Flutter 侧解析变更
- 真实打网联调（仍属 003 可选自测）
- 大规模重构错误类型体系（保持 `RuntimeError`/现有退出码即可）

## Further Notes

- 源自对 `256c332...HEAD` 的 Spec/Standards 审查：代理提示条件错误、死包装 `proxy_to_httpx`、未要求的 app 头变更、007 与 credentials 完成定义歧义。
- 验收以 `docs/credentials.md` living 契约为准；007 Resolution 仅作歧义消除补丁。
- 发布标签：`ready-for-agent`（可直接认领实现）。

## Resolution

已实现并通过 `tests/test_fetch_bika_errors.py` 集成验收：

- 直连 + 传输失败 → 错误含 `dtg config set proxy` / `--proxy`；已设 proxy 时不主推
- 登录缺 data/token → 仅账号/密码语义，不含代理主提示
- 删除 `proxy_to_httpx`；`app-channel`/`app-build-version` 回滚为 `1`/`44`
- 更新 `docs/credentials.md` 失败提示规则；修订 007 Resolution 与 living 契约对齐
