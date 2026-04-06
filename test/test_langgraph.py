"""测试 langgraph_agent"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.langgraph_agent import graph

# 测试1：无 URL
result = graph.invoke(
    {
        "user_input": "你好，今天天气如何？",
        "urls_found": [],
        "confirmed_urls": [],
        "content": "",
        "response": "",
    }
)
print(result)

# 测试2：有 URL（≤5个，自动抓取）
result = graph.invoke(
    {
        "user_input": "请总结 https://example.com",
        "urls_found": [],
        "confirmed_urls": [],
        "content": "",
        "response": "",
    }
)
print(result)

# 测试3：多个 URL（>5个，会暂停等待确认）
result = graph.invoke(
    {
        "user_input": "请访问这些链接",
        "urls_found": ["url1", "url2", "url3", "url4", "url5", "url6"],
        "confirmed_urls": [],
        "content": "",
        "response": "",
    }
)
print(result)
