# Issue tracker: Local Markdown

Issues 和 PRD 以 Markdown 文件形式存放在 `.scratch/` 目录下。

## 约定

- 每个功能一个目录: `.scratch/<feature-slug>/`
- PRD 文件: `.scratch/<feature-slug>/PRD.md`
- 实现 Issue: `.scratch/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 编号
- 每个 Issue 文件顶部用 `状态:` 行记录 triage 状态（标签映射见 `triage-labels.md`）
- 评论和对话历史追加在文件末尾 `## 评论` 标题下

## 当技能说 "发布到 Issue 追踪器"

在 `.scratch/<feature-slug>/` 下创建新文件（目录不存在则先创建）。

## 当技能说 "获取相关 ticket"

读取指定路径的文件。用户通常会直接给出路径或 Issue 编号。
