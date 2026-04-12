"""
Multi-Agent 架构 - Supervisor + Workers 模式
"""

import sys
from pathlib import Path

_docmind = Path(__file__).resolve().parent.parent
if str(_docmind) not in sys.path:
    sys.path.insert(0, str(_docmind))

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

from app.agent.tools import (
    fetch_url_content,
    parse_pdf,
    parse_epub,
    sync_to_obsidian,
)
from app.agent.supervisor import supervisor_node
from app.agent.aggregator import aggregator_node


class MultiAgentState(TypedDict):
    user_input: str
    strategy: str
    tasks: List[Dict]
    need_qa: bool
    worker_results: List[Dict]
    final_response: str


def execute_workers_node(state: MultiAgentState) -> dict:
    tasks = state.get("tasks", [])
    worker_results = []

    print(f"[Workers] 开始执行 {len(tasks)} 个任务...")

    for i, task in enumerate(tasks):
        task_type = task.get("type", "qa")
        print(f"[Workers] 任务 {i + 1}/{len(tasks)}: {task_type}")

        if task_type == "fetch":
            url = task.get("url", "")
            if url:
                try:
                    content = fetch_url_content.invoke({"url": url})
                    worker_results.append(
                        {"url": url, "content": str(content), "type": "fetch"}
                    )
                    print(f"[Workers] 任务 {i + 1} 完成: {len(str(content))} 字符")
                except Exception as e:
                    worker_results.append(
                        {"url": url, "content": f"Error: {str(e)}", "type": "fetch"}
                    )

        elif task_type == "parse_pdf":
            file_path = task.get("file_path", "")
            if file_path:
                try:
                    content = parse_pdf.invoke({"file_path": file_path})
                    worker_results.append(
                        {
                            "file_path": file_path,
                            "content": str(content),
                            "type": "parse_pdf",
                        }
                    )
                    print(f"[Workers] 任务 {i + 1} 完成: {len(str(content))} 字符")
                except Exception as e:
                    worker_results.append(
                        {
                            "file_path": file_path,
                            "content": f"Error: {str(e)}",
                            "type": "parse_pdf",
                        }
                    )

        elif task_type == "parse_epub":
            file_path = task.get("file_path", "")
            if file_path:
                try:
                    content = parse_epub.invoke({"file_path": file_path})
                    worker_results.append(
                        {
                            "file_path": file_path,
                            "content": str(content),
                            "type": "parse_epub",
                        }
                    )
                    print(f"[Workers] 任务 {i + 1} 完成: {len(str(content))} 字符")
                except Exception as e:
                    worker_results.append(
                        {
                            "file_path": file_path,
                            "content": f"Error: {str(e)}",
                            "type": "parse_epub",
                        }
                    )

        elif task_type == "sync_obsidian":
            content = task.get("content", "")
            title = task.get("title", "")
            vault_path = task.get("vault_path", "")
            folder = task.get("folder", "DocMind")
            if content and title and vault_path:
                try:
                    result = sync_to_obsidian.invoke(
                        {
                            "content": content,
                            "title": title,
                            "vault_path": vault_path,
                            "folder": folder,
                        }
                    )
                    worker_results.append(
                        {
                            "title": title,
                            "content": str(result),
                            "type": "sync_obsidian",
                        }
                    )
                    print(f"[Workers] 任务 {i + 1} 完成: Obsidian 同步")
                except Exception as e:
                    worker_results.append(
                        {
                            "title": title,
                            "content": f"Error: {str(e)}",
                            "type": "sync_obsidian",
                        }
                    )

        elif task_type == "qa":
            question = task.get("question", "")
            worker_results.append({"url": "qa", "content": question, "type": "qa"})

    print(f"[Workers] 执行完成，共 {len(worker_results)} 个结果")
    return {"worker_results": worker_results}


def route_after_supervisor(state: MultiAgentState) -> str:
    tasks = state.get("tasks", [])
    return "execute_workers" if tasks else "aggregator"


builder = StateGraph(MultiAgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("execute_workers", execute_workers_node)
builder.add_node("aggregator", aggregator_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {"execute_workers": "execute_workers", "aggregator": "aggregator"},
)
builder.add_edge("execute_workers", "aggregator")
builder.add_edge("aggregator", END)

multi_agent_graph = builder.compile(checkpointer=InMemorySaver())


class MultiAgent:
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        import secrets

        if session_id is None:
            session_id = secrets.token_urlsafe(16)
        self.sessions[session_id] = {"created_at": "now"}
        return session_id

    async def process_message(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if session_id is None or session_id not in self.sessions:
            session_id = self.create_session(session_id)

        config = {"configurable": {"thread_id": session_id}}

        try:
            result = multi_agent_graph.invoke(
                {
                    "user_input": message,
                    "strategy": "",
                    "tasks": [],
                    "need_qa": True,
                    "worker_results": [],
                    "final_response": "",
                },
                config=config,
            )

            return {
                "session_id": session_id,
                "response": result.get("final_response", ""),
                "strategy": result.get("strategy", ""),
                "tasks_count": len(result.get("tasks", [])),
                "worker_results_count": len(result.get("worker_results", [])),
                "success": True,
            }
        except Exception as e:
            import traceback

            traceback.print_exc()
            return {
                "session_id": session_id,
                "response": f"错误: {str(e)}",
                "success": False,
            }


_multi_agent_instance: Optional[MultiAgent] = None


def get_multi_agent() -> MultiAgent:
    global _multi_agent_instance
    if _multi_agent_instance is None:
        _multi_agent_instance = MultiAgent()
    return _multi_agent_instance


def init_multi_agent(api_key: str, **kwargs) -> MultiAgent:
    global _multi_agent_instance
    _multi_agent_instance = MultiAgent(api_key=api_key, **kwargs)
    return _multi_agent_instance
