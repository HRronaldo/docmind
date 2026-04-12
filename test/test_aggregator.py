"""测试 aggregator"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.agent.aggregator import aggregator_node, AggregatorState

# 测试
state = AggregatorState(
    user_input="这两个网站的主要区别是什么？",
    worker_results=[
        {
            "url": "https://example.com",
            "content": "Example 是一个示例网站，提供各种示例代码。",
        },
        {"url": "https://test.com", "content": "Test 是一个测试网站，用于测试功能。"},
    ],
    need_qa=True,
    final_response="",
)

print("测试 Aggregator...")
result = aggregator_node(state)
print(f"\n结果: {result['final_response'][:300]}...")
