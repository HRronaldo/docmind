"""测试 supervisor"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.agent.supervisor import supervisor_node, SupervisorState

# 测试
state = SupervisorState(
    user_input="帮我总结 https://example.com 和 https://python.langchain.com",
    strategy="",
    tasks=[],
    need_qa=False,
)

print("测试 Supervisor...")
result = supervisor_node(state)
print(f"\n结果: {result}")
