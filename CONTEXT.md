# 领域词汇表

## Tag（标签）

漫画元数据中的分类/描述词。不同来源命名可能不同，输出保留原始值。

## Tag 库 / Tag 词表（Tag Catalog）

本项目的「tag 库」指 **去重 tag 列表**（`kind` + `name` + `count`），由功能 1 全量爬取聚合产出。**不包含**本子持久化或本子–tag 关联表。

## Tag Kind（标签维度）

- `tag` — 自由标签
- `category` — 平台分区（哔咔）
- `work` / `actor` / `author` — 禁漫元数据维度

## 来源站（Source）

`bika`（哔咔）、`jmcomic`（禁漫天堂）。

## 输出契约（Output Contract）

工具通过 **JSON（stdout 或 `-o` 文件）** 交付数据，不写数据库。详见 [`docs/schema.md`](docs/schema.md)：

- `TagCatalogResponse` — 功能 1
- `FetchTagsResponse` — 功能 2（单本/批量 tag，由调用方决定是否缓存）

## 集成方式

- **CLI 子进程**：Flutter / 其他项目调用 `dtg` 命令，解析 JSON
- **Python 库**：同结构 API，供脚本或测试使用
- **静态 JSON 文件**：CI 生成词表后放入 Flutter `assets`

## 全量爬取 / 按需爬取

- **全量（catalog）**：枚举本子 → 内存聚合 tag 词表 → 输出 JSON
- **按需（fetch）**：指定 ID → 输出每本 tag 列表 JSON
