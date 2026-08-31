---
title: 代理与哔咔凭证本地管理方案
labels: [wayfinder:grilling]
status: closed
assignee: agent
parent: map
blocked_by: [003-task-bika-account-proxy.md]
blocks: []
---

## Question

本地工具如何安全存放与加载：

- 哔咔账号密码或 token（`.env` + gitignore？运行时 login？）
- 代理 URL（全局 vs 仅哔咔）
- 禁漫是否默认走同一代理

需选定具体方案并记录于实现方案文档，**禁止**将真实凭证提交仓库。

## Resolution

详见 [`docs/credentials.md`](../../docs/credentials.md)。

- 哔咔凭证：优先 `DTG_BIKA_EMAIL` / `DTG_BIKA_PASSWORD`；缺失时在交互终端提示输入；非交互且无 env 则报错。运行时 login；**token 首版仅内存持有，持久化缓存延后**
- 代理：**非全局必须**；**默认不使用**；`dtg config set proxy` / `--proxy` / `DTG_PROXY` 手动启用
