# Wayfinder 本地 Markdown Tracker

本目录存放 Wayfinder 决策地图与子 ticket。约定：

- **地图**：[`map.md`](map.md)，标签 `wayfinder:map`
- **Ticket**：[`tickets/`](tickets/) 下每个文件一个子 issue
- **状态**：`open` | `closed`；**认领**：frontmatter 中 `assignee` 非空即已认领
- **阻塞**：`blocked_by` 列出需先关闭的 ticket 文件名（不含路径）；全部关闭后该 ticket 进入 frontier
- **Frontier**：open + 无 assignee + `blocked_by` 为空或所列 ticket 均已 closed

关闭 ticket 时：在文件末尾追加 `## Resolution`，并将 `status` 改为 `closed`。
