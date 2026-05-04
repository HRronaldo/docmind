import json
import secrets
from typing import Any, Dict, Literal, Optional, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.types import Command, Interrupt, interrupt
from langchain_community.chat_models import ChatZhipuAI

from app.agent.tools import fetch_url_content
from app.core.config import GLM_MODEL, GLM_TEMPERATURE, ZHIPU_API_KEY


class ReadingAgentState(TypedDict):
    user_input: str
    urls_found: list[str]
    confirmed_urls: list[str]
    content: str
    response: str


# 全局 LLM 实例，会在 init_agent() 时更新
_llm: Optional[ChatZhipuAI] = None


def _get_llm() -> ChatZhipuAI:
    """获取 LLM 实例，优先使用已初始化的，否则使用默认配置。"""
    global _llm
    if _llm is None:
        _llm = ChatZhipuAI(
            model=GLM_MODEL,
            temperature=GLM_TEMPERATURE,
            api_key=ZHIPU_API_KEY,
        )
    return _llm


def analyze(state: ReadingAgentState) -> dict:
    """LLM 提取 URL"""
    llm = _get_llm()
    prompt = f"""从以下用户输入中提取所有 URL。

用户输入：{state["user_input"]}

请返回一个 URL 列表，格式如：["url1", "url2"]
如果没有 URL，返回空列表：[]
"""
    response = llm.invoke(prompt)

    try:
        urls = json.loads(str(response.content))
    except:
        urls = []

    return {"urls_found": urls}


def route(state: ReadingAgentState) -> Literal["fetch", "respond", "confirm"]:
    """路由判断：0个URL直接回答，≤5个自动抓取，>5个确认"""
    urls = state.get("urls_found", [])

    if len(urls) == 0:
        return "respond"
    elif len(urls) <= 5:
        return "fetch"
    else:
        return "confirm"


def respond(state: ReadingAgentState) -> dict:
    """直接回答用户问题（不需要抓取网页）"""
    llm = _get_llm()
    prompt = f"""请回答以下用户问题：
{state["user_input"]}
"""
    response = llm.invoke(prompt)
    return {"response": str(response.content)}


def fetch(state: ReadingAgentState) -> dict:
    """抓取 URL 内容"""
    # 确定要抓取的 URL
    urls = state.get("confirmed_urls") or state.get("urls_found", [])

    # 抓取每个 URL
    contents = []
    for url in urls:
        try:
            content = fetch_url_content.invoke({"url": url})
            contents.append(f"=== {url} ===\n{content}\n")
        except Exception as e:
            contents.append(f"=== {url} ===\n抓取失败: {e}\n")

    return {"content": "\n".join(contents)}


def summarize(state: ReadingAgentState) -> dict:
    """总结抓取的内容并回答用户问题"""
    llm = _get_llm()
    prompt = f"""根据以下抓取的内容，回答用户的问题：
{state["content"]}
用户问题：{state["user_input"]}
请给出一个简洁的回答。
"""
    response = llm.invoke(prompt)
    return {"response": str(response.content)}


def human_confirm(state: ReadingAgentState) -> dict:
    """暂停，等待用户确认"""
    # 构建要确认的信息
    urls = state.get("urls_found", [])

    # ⭐ interrupt 会暂停执行，等待用户输入
    decision = interrupt(
        {
            "question": f"发现 {len(urls)} 个 URL，是否抓取？",
            "urls": urls,
            "options": ["confirm", "edit", "cancel"],
        }
    )

    if decision == "cancel":
        return {"confirmed_urls": [], "content": ""}
    elif decision == "confirm":
        return {"confirmed_urls": urls}
    else:  # edit
        # 用户可能会修改 URL 列表
        return {"confirmed_urls": decision.get("urls", [])}


# 创建图
builder = StateGraph(ReadingAgentState)

# 添加节点
builder.add_node("analyze", analyze)
builder.add_node("respond", respond)
builder.add_node("fetch", fetch)
builder.add_node("summarize", summarize)
builder.add_node("human_confirm", human_confirm)

# 添加边
builder.add_edge(START, "analyze")

# ⭐ 条件边：根据 URL 数量决定下一步
builder.add_conditional_edges(
    "analyze",
    route,
    {"respond": "respond", "fetch": "fetch", "confirm": "human_confirm"},
)

# human_confirm 之后也需要路由
builder.add_conditional_edges(
    "human_confirm",
    lambda state: "fetch" if state.get("confirmed_urls") else "respond",
    {"fetch": "fetch", "respond": "respond"},
)

builder.add_edge("fetch", "summarize")
builder.add_edge("summarize", END)
builder.add_edge("respond", END)

# 编译（需要 checkpointer 支持 interrupt）
graph = builder.compile(checkpointer=InMemorySaver())


class LangGraphAgent:
    """
    LangGraph Agent 封装类。

    提供与 SummaryAgent 相同的接口，方便集成到现有 API。
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """初始化 Agent。"""
        self.api_key = api_key or ZHIPU_API_KEY
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """创建新会话。"""
        if session_id is None:
            session_id = secrets.token_urlsafe(16)
        self.sessions[session_id] = {"created_at": "now"}
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息。"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """删除会话。"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def clear_session(self, session_id: str) -> bool:
        """清空会话历史。"""
        # LangGraph checkpointer 会自动处理，这里只需确保 session 存在
        return session_id in self.sessions

    async def process_message(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息。

        Args:
            message: 用户消息
            session_id: 会话 ID（用作 LangGraph thread_id）

        Returns:
            包含响应内容的字典
        """
        # 创建或获取会话 ID
        if session_id is None or session_id not in self.sessions:
            session_id = self.create_session(session_id)

        config = {"configurable": {"thread_id": session_id}}

        try:
            # 调用 LangGraph 图
            result = graph.invoke(
                {
                    "user_input": message,
                    "urls_found": [],
                    "confirmed_urls": [],
                    "content": "",
                    "response": "",
                },
                config=config,  # type: ignore
            )

            return {
                "session_id": session_id,
                "response": result.get("response", ""),
                "url_processed": ", ".join(result.get("urls_found", [])) if result.get("urls_found") else None,
                "success": True,
            }

        except Exception as e:
            # 处理 interrupt（Human-in-the-Loop 暂停）
            # 使用类型检查而非字符串匹配
            if isinstance(e, Interrupt):
                return {
                    "session_id": session_id,
                    "response": "等待用户确认...",
                    "success": True,
                    "waiting_confirmation": True,
                }

            return {
                "session_id": session_id,
                "response": f"处理消息时出错：{str(e)}",
                "success": False,
                "error": str(e),
            }


# 全局单例
_agent_instance: Optional[LangGraphAgent] = None


def get_agent() -> LangGraphAgent:
    """获取全局 Agent 实例。"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = LangGraphAgent()
    return _agent_instance


def init_agent(api_key: str, **kwargs) -> LangGraphAgent:
    """初始化全局 Agent 实例。"""
    global _agent_instance, _llm
    _llm = ChatZhipuAI(
        model=GLM_MODEL,
        temperature=GLM_TEMPERATURE,
        api_key=api_key,
    )
    _agent_instance = LangGraphAgent(api_key=api_key, **kwargs)
    return _agent_instance
