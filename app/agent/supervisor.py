"""
Supervisor - 任务规划器
=====================

职责：
1. 分析用户输入的复杂度
2. 决定并行策略（single/parallel/sequential）
3. 分解任务，分配给 Workers
"""

import json
import re
import sys
from pathlib import Path
from typing import TypedDict, List, Dict, Any

# 添加项目根目录到 sys.path（必须在 app 导入之前）
_current = Path(__file__).resolve()
_docmind_root = _current.parent.parent
if str(_docmind_root) not in sys.path:
    sys.path.insert(0, str(_docmind_root))

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatZhipuAI

from app.core.config import GLM_MODEL, GLM_TEMPERATURE, ZHIPU_API_KEY


class SupervisorState(TypedDict):
    """Supervisor 状态"""

    user_input: str
    strategy: str  # single | parallel | sequential
    tasks: List[Dict]  # [{"type": "fetch", "url": "..."}, ...]
    need_qa: bool


def _get_llm() -> ChatZhipuAI:
    """获取 LLM 实例"""
    return ChatZhipuAI(
        model=GLM_MODEL,
        temperature=GLM_TEMPERATURE,
        api_key=ZHIPU_API_KEY,
    )


def _parse_llm_response(content: str) -> dict:
    """
    解析 LLM 的 JSON 响应。

    处理两种情况：
    1. 直接是 JSON: {"strategy": "..."}
    2. 包含在 markdown 代码块中: ```json {...} ```
    """
    # 默认值
    default = {"strategy": "single", "tasks": [], "need_qa": True}

    # 方法1: 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 方法2: 提取 markdown 代码块中的 JSON
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 方法3: 尝试提取 {...} 块
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 全部失败，返回默认值
    print(f"[Supervisor] 解析失败，使用默认策略。原始内容: {content[:100]}")
    return default


def _validate_decision(decision: dict) -> dict:
    """
    验证决策格式，确保包含必要字段。

    Args:
        decision: LLM 返回的决策字典

    Returns:
        验证后的决策字典
    """
    defaults = {"strategy": "single", "tasks": [], "need_qa": True}

    # 检查必要字段，不存在则使用默认值
    for key, default_value in defaults.items():
        if key not in decision:
            decision[key] = default_value
        elif isinstance(default_value, type(decision[key])):
            # 类型不匹配，使用默认值
            pass
        else:
            # 类型匹配，保留原值
            pass

    # 验证 strategy 值
    valid_strategies = ["single", "parallel", "sequential"]
    if decision["strategy"] not in valid_strategies:
        print(f"[Supervisor] 无效 strategy '{decision['strategy']}'，使用 'single'")
        decision["strategy"] = "single"

    # 验证 tasks 是列表
    if not isinstance(decision["tasks"], list):
        decision["tasks"] = []

    return decision


def supervisor_node(state: SupervisorState) -> dict:
    """
    Supervisor 分析任务，决定执行策略。

    流程：
    1. LLM 分析用户输入
    2. 返回 strategy + tasks + need_qa

    Returns:
        包含 strategy, tasks, need_qa 的字典
    """
    llm = _get_llm()
    user_input = state["user_input"]

    # ⭐ System prompt：指导 LLM 输出结构化决策
    system_prompt = """你是一个任务规划专家。分析用户输入，决定执行策略。

输出格式（必须是有效 JSON）：
{
    "strategy": "single",  // single=单任务, parallel=并行多任务, sequential=顺序多任务
    "tasks": [             // 任务列表
        {"type": "fetch", "url": "https://..."},
        {"type": "qa", "question": "..."}
    ],
    "need_qa": true        // 是否需要问答
}

判断规则：
- 单个简单问题 → strategy: "single", need_qa: true
- 多个 URL 需要抓取 → strategy: "parallel", 每个 URL 一个 fetch 任务
- 需要先研究再回答 → strategy: "sequential"
- 需要总结多个来源 → strategy: "parallel", need_qa: true

请只输出 JSON，不要有其他内容。"""

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]
    )

    # 解析 + 验证
    raw_content = str(response.content)
    print(f"[Supervisor] LLM 原始输出: {raw_content[:200]}")

    decision = _parse_llm_response(raw_content)
    decision = _validate_decision(decision)

    print(
        f"[Supervisor] 决策: strategy={decision['strategy']}, tasks={len(decision['tasks'])}, need_qa={decision['need_qa']}"
    )

    return decision


# ===== 测试 =====
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    # 测试
    state = SupervisorState(
        user_input="帮我总结 https://example.com 和 https://python.langchain.com",
        strategy="",
        tasks=[],
        need_qa=False,
    )

    result = supervisor_node(state)
    print(f"\n结果: {result}")
