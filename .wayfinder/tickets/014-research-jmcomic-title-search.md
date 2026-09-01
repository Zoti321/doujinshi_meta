---
title: 调研禁漫按标题/关键词搜索 API
labels: [wayfinder:research]
status: closed
assignee: agent
map: map-title-search.md
blocked_by: []
---

## Question

禁漫通过**本子标题或关键词**定位本子时，应使用 `search_site` 还是 `search_work`（或其他 `search_*`）？需明确：

1. 各 `search_*` 对标题类查询的差异与推荐选择
2. 分页（`page`、是否有 `page_count`）、每页条数
3. 列表项字段：`iter_id_title` / `iter_id_title_tag` 与详情 `get_album_detail` 的 tag 完整度差异
4. 对完整标题 vs 关键词的匹配行为；日文/中文标题实践
5. 与现有 `jmcomic_ops` 的集成点

产出：`docs/research/jmcomic-title-search.md`（或更新 `jmcomic-tags.md` 专节），含推荐调用路径与示例。

## Resolution

产出 [`docs/research/jmcomic-title-search.md`](../../docs/research/jmcomic-title-search.md)。

- 标题/关键词默认 **`search_site`**（`main_tag=0`）；`search_work` 等仅用于已知 IP/作者/tag/角色维度
- 分页每页 **80** 条；`page.total` / `page_count` 可用
- API 列表 **`iter_id_title_tag()` 恒为空**；完整 tags 须 **`get_album_detail`** → 复用 `fetch_comic_jmcomic`
- 集成：在 `jmcomic_ops.py` 新增 `search_comics_jmcomic` + 现有详情 fetch
