"""
日志模块

DocMind 统一日志配置，支持：
- 结构化日志输出
- 日志级别控制
- 多输出目标（控制台、文件）
- 请求追踪（trace_id）
- 环境变量配置
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from functools import wraps

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志配置（可被 config.py 覆盖）
# 默认值：项目根目录下的 logs 文件夹
_DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR = Path(os.getenv("LOG_DIR", str(_DEFAULT_LOG_DIR)))
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(
    name: str = "docmind", level: int = logging.INFO, log_file: Optional[str] = None
) -> logging.Logger:
    """
    创建并配置 Logger 实例。

    Args:
        name: Logger 名称（使用空字符串 "" 表示根 logger）
        level: 日志级别
        log_file: 日志文件路径（可选）

    Returns:
        配置好的 Logger 实例
    """
    # 使用空字符串初始化根 logger，这样所有子 logger 都能继承 handlers
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 传播到根 logger（这样 "docmind.test" 等子 logger 也能继承 handlers）
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_handler = logging.StreamHandler(sys.stdout)
        root_handler.setLevel(level)
        root_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(root_handler)

        if log_file:
            root_file_handler = logging.FileHandler(
                LOG_DIR / log_file, encoding="utf-8"
            )
            root_file_handler.setLevel(level)
            root_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            root_logger.addHandler(root_file_handler)
        root_logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers and logger != root_logger:
        return logger

    # 控制台 Handler（如果 logger 不是根 logger）
    if logger != root_logger:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 文件 Handler（如果 logger 不是根 logger 且指定了文件）
    if log_file and logger != root_logger:
        log_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# 默认 Logger（不在模块级别初始化，由 config.py 控制）
default_logger = None


def get_logger(name: str = "docmind") -> logging.Logger:
    """
    获取 Logger 实例。

    Args:
        name: Logger 名称（建议使用模块名）

    Returns:
        Logger 实例
    """
    logger = logging.getLogger(name)

    # 如果 logger 没有 handlers，从根 logger 继承
    if not logger.handlers and logging.getLogger().handlers:
        for handler in logging.getLogger().handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.getLogger().level)

    return logger


class LoggerMixin:
    """
    Mixin 类，为其他类添加日志功能。

    用法：
    ```python
    class MyService(LoggerMixin):
        def __init__(self):
            self.logger = get_logger(self.__class__.__name__)

        def do_something(self):
            self.logger.info("Doing something")
    ```
    """

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_entry_exit(func):
    """
    装饰器：记录函数入口和出口。

    用法：
    ```python
    @log_entry_exit
    def my_function(arg1, arg2):
        # 函数逻辑
        pass
    ```
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"进入函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"退出函数: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"函数异常退出: {func.__name__} - {e}")
            raise

    return wrapper


def log_llm_call(model: str, input_tokens: int = 0, output_tokens: int = 0):
    """
    记录 LLM 调用日志。

    Args:
        model: 模型名称
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
    """
    logger = get_logger("docmind.llm")
    total_tokens = input_tokens + output_tokens
    logger.info(
        f"LLM 调用 | 模型: {model} | "
        f"输入: {input_tokens} tokens | "
        f"输出: {output_tokens} tokens | "
        f"总计: {total_tokens} tokens"
    )


def log_tool_call(tool_name: str, success: bool, duration_ms: float = 0):
    """
    记录工具调用日志。

    Args:
        tool_name: 工具名称
        success: 是否成功
        duration_ms: 耗时（毫秒）
    """
    logger = get_logger("docmind.tools")
    status = "成功" if success else "失败"
    logger.info(
        f"工具调用 | 工具: {tool_name} | 状态: {status} | 耗时: {duration_ms:.2f}ms"
    )


def log_error(error: Exception, context: str = ""):
    """
    记录错误日志。

    Args:
        error: 异常对象
        context: 错误上下文描述
    """
    logger = get_logger("docmind.error")
    logger.error(
        f"错误 | 上下文: {context} | 类型: {type(error).__name__} | 消息: {str(error)}"
    )
