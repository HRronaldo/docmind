# Changelog

All notable changes to DocMind are documented here.

## [0.7.0] - 2026-04-26

### Added
- **复习笔记模板** (`review`) - 间隔重复复习笔记模板
- **复习计划生成** (`generate_review_schedule`) - 基于艾宾浩斯记忆曲线
- **MCP 工具注册** - 新工具已注册到 MCP Server

### Features
- 复习间隔：1, 3, 7, 14, 30 天
- 复习类型：快速回顾 → 记忆巩固 → 理解深化 → 知识串联 → 长期记忆
- 模板类型：summary, book, meeting, tutorial, review

### Test
- 拆分测试文件为 5 个模块
- 31 个测试全部通过

## [0.6.0] - 2026-04-12

### Added
- 知识图谱（实体识别 + 关系抽取）
- PDF/EPUB 文档解析
- Obsidian 同步

## [0.5.0] - 2026-04-05

### Added
- 中文 NLP 优化（分词、关键词、术语识别）
- Multi-Agent 对话系统