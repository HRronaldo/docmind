# DocMind - 智能文档摘要服务

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Python-3.11+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-0.1+-yellow.svg" alt="LangChain">
  <img src="https://img.shields.io/badge/MCP-Supported-orange.svg" alt="MCP">
</p>

> 基于 LangChain + GLM 的智能文档摘要服务，支持 RESTful API 和 MCP 协议

## ✨ 特性

- 📄 **URL 智能摘要** - 自动抓取网页内容并生成精准摘要
- 🔌 **双协议支持** - 同时支持 RESTful API 和 MCP 协议
- 🤖 **MCP Server** - 可无缝集成到 Claude Desktop、OpenCode、Cursor 等 AI 助手
- 🧠 **多模型支持** - 支持智谱 GLM 系列模型（GLM-4、GLM-4-Flash、GLM-5）
- 💬 **对话记忆** - 支持多轮对话，上下文理解
- 🚀 **一键部署** - Docker Compose 快速部署

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/docmind.git
cd docmind
```

### 2. 配置环境

```bash
# 复制环境配置
copy .env.example .env

# 编辑 .env，填入你的智谱 API Key
# 获取地址：https://open.bigmodel.cn/
```

### 3. 本地运行

```bash
# 安装依赖
uv sync

# 启动服务
uv run python -m app.main
```

服务将在 http://localhost:5000 启动

---

## 🔌 API 使用

### RESTful API

#### 健康检查

```bash
curl http://localhost:5000/api/v1/health
```

#### 发送消息

```bash
curl -X POST http://localhost:5000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "https://example.com/article 请总结"}'
```

#### MCP Server 模式

```bash
# STDIO 模式（用于 Claude Desktop 等）
fastmcp run app.mcp.server

# SSE 模式（用于远程连接）
fastmcp run app.mcp.server sse
```

---

## 🔧 MCP 集成

### OpenCode 集成

在 OpenCode 中配置 MCP Server：

```json
{
  "mcpServers": {
    "docmind": {
      "command": "uv",
      "args": ["--directory", "/path/to/docmind", "run", "python", "-m", "app.mcp.server"],
      "env": {
        "ZHIPU_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Claude Desktop 集成

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "docmind": {
      "command": "uv",
      "args": ["--directory", "/path/to/docmind", "run", "python", "-m", "app.mcp.server"]
    }
  }
}
```

### 可用工具

| 工具 | 说明 |
|------|------|
| `summarize_url` | 抓取 URL 并生成智能摘要 |
| `extract_article_content` | 仅提取网页正文内容 |

---

## 🐳 Docker 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  docmind:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
      - GLM_MODEL=glm-4
    restart: unless-stopped
```

### 启动

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## ⚙️ 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ZHIPU_API_KEY` | 智谱 AI API Key | 必填 |
| `GLM_MODEL` | 模型名称 | glm-4 |
| `GLM_TEMPERATURE` | 采样温度 | 0.7 |
| `GLM_MAX_TOKENS` | 最大 Token 数 | 4096 |
| `PORT` | 服务端口 | 5000 |
| `DEBUG` | 调试模式 | false |

### 支持的模型

- `glm-4` - 平衡模式
- `glm-4-flash` - 免费额度（限流）
- `glm-4-plus` - 高性能
- `glm-5` - 最新版本

---

## 📦 项目结构

```
docmind/
├── app/
│   ├── agent/          # LangChain Agent 核心
│   ├── api/            # FastAPI 路由
│   ├── mcp/            # MCP Server
│   ├── services/       # 业务逻辑
│   ├── core/           # 配置
│   └── main.py         # 入口
├── pyproject.toml      # 项目配置
├── docker-compose.yml  # Docker 部署
└── Dockerfile
```

---

## 🛣️ 路线图

- [ ] 用户认证系统
- [ ] 订阅付费功能
- [ ] 更多模型支持（GPT、Claude）
- [ ] 企业版 MCP 托管服务
- [ ] 插件市场

---

## 📄 许可证

MIT License - 欢迎开源贡献！

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ☕ 支持

如果这个项目对你有帮助，欢迎 star ⭐️

---

**Built with ❤️ using LangChain + GLM**
