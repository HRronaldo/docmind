"""
Human-in-the-Loop 增强模块
=========================

提供可复用的人机协作功能：
1. Approval Workflow - 批准/拒绝操作
2. Input Editor - 编辑输入后继续
3. Force Stop - 强制停止

这些功能可以集成到任何 LangGraph Agent 中。
"""

from typing import TypedDict, Literal, Dict, Any, Optional
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage


# ===== Human Decision Types =====
class ApprovalDecision(TypedDict):
    """批准决策"""

    action: str  # approve, reject, edit, stop
    reason: Optional[str]  # 原因
    edited_value: Optional[Any]  # 编辑后的值


class ApprovalRequest(TypedDict):
    """批准请求"""

    title: str  # 操作标题
    description: str  # 操作描述
    details: Dict[str, Any]  # 详细信息
    options: list[str]  # 可选操作


# ===== Human-in-the-Loop 节点 =====


def request_approval(
    title: str,
    description: str,
    details: Dict[str, Any],
    options: Optional[list[str]] = None,
) -> ApprovalDecision:
    """
    请求人类批准。

    Args:
        title: 操作标题
        description: 操作描述
        details: 详细信息
        options: 可选操作列表（默认：["approve", "reject", "edit", "stop"]）

    Returns:
        人类的决定
    """
    if options is None:
        options = ["approve", "reject", "edit", "stop"]

    request = ApprovalRequest(
        title=title,
        description=description,
        details=details,
        options=options,
    )

    # 使用 interrupt 暂停，等待人类输入
    decision = interrupt(request)

    return decision


def approval_node(state: Dict[str, Any], title: str, description: str) -> dict:
    """
    批准节点：包装 request_approval 用于 LangGraph。
    """
    details = {
        "current_state": state.get("user_input", ""),
    }

    decision = request_approval(title, description, details)

    if decision["action"] == "reject":
        return {
            "response": f"操作已被拒绝：{decision.get('reason', '未提供原因')}",
            "approved": False,
        }
    elif decision["action"] == "stop":
        return {
            "response": "操作已停止",
            "approved": False,
            "stopped": True,
        }
    elif decision["action"] == "edit":
        # 使用编辑后的值更新状态
        new_value = decision.get("edited_value", state.get("user_input", ""))
        return {
            "user_input": new_value,
            "approved": True,
            "edited": True,
        }
    else:
        # approve
        return {
            "approved": True,
        }


def confirm_action(question: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    简单的确认对话。

    Args:
        question: 确认问题
        context: 上下文信息

    Returns:
        True 表示确认，False 表示取消
    """
    request = {
        "question": question,
        "context": context or {},
        "type": "confirm",
    }

    decision = interrupt(request)

    return decision.get("confirmed", False)


def get_human_input(prompt: str, default: Optional[str] = None) -> str:
    """
    获取人类输入。

    Args:
        prompt: 提示信息
        default: 默认值

    Returns:
        人类输入的内容
    """
    request = {
        "prompt": prompt,
        "default": default,
        "type": "input",
    }

    result = interrupt(request)

    return result.get("value", default or "")


# ===== 预定义的 Approval 工作流 =====


def approve_url_fetch(urls: list[str]) -> ApprovalDecision:
    """
    批准 URL 抓取。
    """
    return request_approval(
        title="URL 抓取确认",
        description="Agent 准备抓取以下 URL",
        details={"urls": urls},
        options=["confirm", "edit", "cancel"],
    )


def approve_edit_urls(
    original_urls: list[str], edited_urls: list[str]
) -> ApprovalDecision:
    """
    批准编辑后的 URL 列表。
    """
    return request_approval(
        title="URL 列表已编辑",
        description="确认修改后的 URL 列表",
        details={
            "original_urls": original_urls,
            "edited_urls": edited_urls,
        },
        options=["confirm", "cancel"],
    )


def approve_sensitive_action(action: str, details: Dict[str, Any]) -> ApprovalDecision:
    """
    敏感操作批准（如写文件、发送消息等）。
    """
    return request_approval(
        title=f"敏感操作：{action}",
        description="此操作需要您的批准",
        details=details,
        options=["approve", "reject", "cancel"],
    )


# ===== 实用工具 =====


def create_human_loop_node(node_name: str):
    """
    装饰器：为节点创建人类确认包装器。

    Usage:
        @create_human_loop_node("fetch")
        def fetch_node(state):
            ...
    """

    def decorator(func):
        def wrapper(state):
            # 先执行原有逻辑
            result = func(state)

            # 检查是否需要人类确认
            if result.get("requires_approval"):
                decision = request_approval(
                    title=result.get("title", "确认操作"),
                    description=result.get("description", ""),
                    details=result.get("details", {}),
                )

                if decision["action"] == "reject":
                    return {"response": "操作已拒绝", "approved": False}
                elif decision["action"] == "stop":
                    return {"response": "操作已停止", "stopped": True}

            return result

        return wrapper

    return decorator
