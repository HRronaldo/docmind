# DocMind 项目简历优化 & 模拟面试 Prompt

## 项目信息

**项目名称**：DocMind - 中文深度阅读 + AI 写作闭环平台

**GitHub**：https://github.com/HRronaldo/docmind

**技术栈**：
- 核心框架：LangGraph（状态机工作流）
- 协议：MCP（Model Context Protocol）
- 架构：多 Agent 架构（Supervisor + Workers + Aggregator）
- LLM：智谱 GLM-4 API
- 文档解析：PDFplumber, EbookLib
- 笔记同步：Obsidian 本地写入
- 中文 NLP：jieba, TF-IDF, TextRank
- 测试：pytest（22 个单元测试）

## 项目架构

```
用户输入 → Supervisor (LLM 决策) → Workers (执行) → Aggregator (汇总) → 最终回答
                            ↓
              fetch / qa / parse_pdf / parse_epub / sync_obsidian / extract_keywords / recognize_terms / build_knowledge_graph
```

## MCP 可用工具

```
对话:              chat
URL处理:           summarize_url, extract_article_content, extract_keywords_from_url, recognize_terms_in_url
文本处理:          extract_keywords_from_text, recognize_terms_in_text
知识图谱:          build_knowledge_graph_from_text, query_knowledge_graph
文档处理:          parse_document, analyze_document_full, sync_to_obsidian
```

## 项目文件结构

```
docmind/
├── app/
│   ├── agent/          # Agent 核心
│   │   ├── supervisor.py      # 任务规划器
│   │   ├── aggregator.py    # 结果汇总器
│   │   ├── multi_agent.py   # 多 Agent 架构
│   │   └── tools.py        # 工具定义
│   ├── nlp/            # 中文 NLP
│   │   ├── segmenter.py    # 分词
│   │   ├── keywords.py   # 关键词
│   │   ├── terms.py      # 术语识别
│   │   └── kg.py        # 知识图谱
│   └── mcp/           # MCP Server
├── test/
│   └── test_unit.py   # 22 tests
└── pyproject.toml
```

---

## 我的角色

1. 帮我优化简历中 DocMind 项目的描述
2. 模拟技术面试，问我关于这个项目的问题
3. 指出我回答中的问题并给出改进建议

## 约束

- 简历关键词：LangGraph, MCP, 多 Agent, Supervisor 模式, ReAct, 状态机, 中文 NLP, 知识图谱
- 面试风格：偏重工程实践，不是背书
- 诚实回答，不知道就说不知道

---

## 评估维度

### 1. LangGraph 状态机
- 什么是状态机？
- 什么时候用 LangGraph？
- Checkpoint 是做什么的？

### 2. MCP 协议
- MCP 是什么？
- MCP Server 和 Client 的关系？
- 如何设计 MCP 工具？

### 3. 多 Agent 架构
- Supervisor 决策逻辑？
- ReAct 循环是什么？
- Aggregator 什么时候用？

### 4. 中文 NLP
- jieba 分词原理？
- TF-IDF vs TextRank 区别？
- 知识图谱如何构建？

### 5. 工程化
- 日志系统设计？
- 错误处理策略？
- 单元测试怎么写？

---

## 开始对话示例

```
你好！我想让你帮我优化简历中 DocMind 项目的描述，并进行模拟面试。

项目信息：[上面的项目信息]

请先问我第一个问题。
```