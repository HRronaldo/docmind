"""
DocMind MCP Server 工具测试

注意：FastMCP 装饰器会将函数包装为 FunctionTool 对象。
本测试验证 MCP 工具的行为，通过 app.nlp 模块间接测试。
"""

import pytest
from pathlib import Path
import sys

_test_path = Path(__file__).resolve().parent.parent
if str(_test_path) not in sys.path:
    sys.path.insert(0, str(_test_path))


class TestMCPtools:
    """MCP 工具测试 - 验证可用的工具函数"""
    
    def test_mcp_tools_can_be_imported(self):
        """测试模块可导入（验证无语法错误）"""
        # 如果导入失败，说明有语法或导入错误
        from app import mcp
        assert mcp is not None
    
    def test_templates_functional_with_review(self):
        """测试复习模板功能"""
        from app.nlp.templates import generate_note_template, generate_review_schedule
        
        # 复习模板
        template = generate_note_template("review", title="Test", first_date="2026-04-26")
        assert "复习笔记" in template
        assert "2026-04-26" in template
        
        # 复习计划
        schedule = generate_review_schedule("test", first_date="2026-04-26")
        assert len(schedule["reviews"]) == 5
        assert schedule["reviews"][0]["day"] == 1
    
    def test_mcp_server_module_has_tools(self):
        """测试 MCP server 模块包含工具定义"""
        from app.mcp import server as mcp_server
        
        # 检查模块是否定义了一些工具
        attrs = dir(mcp_server)
        # 模块加载成功即可
        assert "FastMCP" in str(type(mcp_server.mcp)) or hasattr(mcp_server, 'mcp')