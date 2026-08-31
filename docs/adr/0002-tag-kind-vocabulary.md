# Tag Kind 词汇：去掉 category，work/actor 更名为 parody/character

词表与 fetch 契约只保留 `tag` / `parody` / `character` / `author`。哔咔平台分区（`comic.categories`）只用于本子枚举，不再作为 Tag Kind 输出——分区粒度粗、与自由标签语义不同，进入词表会污染「tag 库」。禁漫源字段仍读 `works`/`actors`，契约字面量改为 `parody`/`character`，贴近常见同人标签习惯并脱离 API 字段名。此为硬切（`schema_version` 仍为 `1.0`），旧字面量无读写别名；含旧 `kinds` 的 checkpoint 须重跑。
