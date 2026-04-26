"""
DocMind 异常定义

定义项目专用的异常类型，便于错误追踪和处理。
"""

from typing import Optional


class DocMindError(Exception):
    """DocMind 基础异常"""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code or "UNKNOWN"
        super().__init__(self.message)


class APIError(DocMindError):
    """API 调用相关错误"""

    def __init__(self, message: str, code: str = "API_ERROR"):
        super().__init__(message, code)


class LLMError(APIError):
    """LLM 调用错误"""

    def __init__(self, message: str, model: Optional[str] = None):
        self.model = model
        super().__init__(message, "LLM_ERROR")


class NetworkError(APIError):
    """网络请求错误"""

    def __init__(self, message: str, url: Optional[str] = None):
        self.url = url
        super().__init__(message, "NETWORK_ERROR")


class ValidationError(DocMindError):
    """输入验证错误"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class DocumentError(DocMindError):
    """文档处理错误"""

    def __init__(self, message: str, file_path: Optional[str] = None):
        self.file_path = file_path
        super().__init__(message, "DOCUMENT_ERROR")


class ObsidianError(DocMindError):
    """Obsidian 同步错误"""

    def __init__(self, message: str, vault_path: Optional[str] = None):
        self.vault_path = vault_path
        super().__init__(message, "OBSIDIAN_ERROR")
