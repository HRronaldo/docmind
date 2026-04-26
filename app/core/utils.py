"""
DocMind 工具函数

包含重试机制、通用工具函数等。
"""

import time
import functools
from typing import Callable, Any, Optional, Tuple, Type
from app.core.logger import get_logger, log_error

logger = get_logger("docmind.utils")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    重试装饰器。

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增因子
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数 (exception, attempt) -> None

    用法:
    ```python
    @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
    def fetch_data():
        # 网络请求
        pass
    ```

    或者用于异步函数:
    ```python
    @retry(max_attempts=3, delay=1.0)
    async def fetch_data_async():
        # 异步网络请求
        pass
    ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败"
                        )
                        raise

                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt} 次尝试失败: {e}. "
                        f"{current_delay:.1f}秒后重试..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(current_delay)
                    current_delay *= backoff

            # 理论上不会到达这里，但为了类型安全
            if last_exception:
                raise last_exception

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            import asyncio

            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"异步函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败"
                        )
                        raise

                    logger.warning(
                        f"异步函数 {func.__name__} 第 {attempt} 次尝试失败: {e}. "
                        f"{current_delay:.1f}秒后重试..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            if last_exception:
                raise last_exception

        # 根据函数类型返回合适的包装器
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


def safe_call(func: Callable, *args, default: Any = None, **kwargs) -> Any:
    """
    安全调用函数，捕获所有异常并返回默认值。

    Args:
        func: 要调用的函数
        *args: 位置参数
        default: 异常时返回的默认值
        **kwargs: 关键字参数

    Returns:
        函数返回值或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(e, f"safe_call: {func.__name__}")
        return default
