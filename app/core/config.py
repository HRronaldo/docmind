"""Core configuration and initialization.

DocMind 核心配置模块
====================

负责加载环境变量和管理应用配置。
"""

import os
import subprocess
import signal
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

# Model Configuration
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4")
GLM_TEMPERATURE = float(os.getenv("GLM_TEMPERATURE", "0.7"))
GLM_MAX_TOKENS = int(os.getenv("GLM_MAX_TOKENS", "4096"))

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")


def kill_port(port: int) -> bool:
    """
    杀死占用指定端口的进程。

    这是一个常见的开发问题：之前的进程没有正确退出，
    导致端口被占用。这个函数自动查找并杀死占用进程。

    Args:
        port: 要检查的端口号

    Returns:
        True 如果成功杀死进程，False 如果没有找到占用进程
    """
    try:
        # Windows: 查找占用端口的进程
        result = subprocess.run(
            f"netstat -ano | findstr :{port}",
            shell=True,
            capture_output=True,
            text=True,
        )

        if result.stdout:
            # 解析输出，提取进程ID
            for line in result.stdout.split("\n"):
                if f":{port}" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            pid = int(pid)
                            # 杀死进程
                            if sys.platform == "win32":
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", str(pid)],
                                    capture_output=True,
                                )
                            else:
                                os.kill(pid, signal.SIGKILL)
                            print(f"[OK] Killed process on port {port} (PID: {pid})")
                            return True
                        except (ValueError, ProcessLookupError):
                            pass
        return False
    except Exception as e:
        print(f"⚠️ 清理端口时出错: {e}")
        return False


def ensure_port_available(port: int) -> bool:
    """
    确保端口可用，如果被占用则尝试清理。

    Args:
        port: 端口号

    Returns:
        True 如果端口可用
    """
    import socket

    # 检查端口是否被占用
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("", port))
        sock.close()
        return True
    except OSError:
        # 端口被占用，尝试清理
        print(f"[!] Port {port} occupied, trying to kill...")
        if kill_port(port):
            return True
        print(f"[X] Cannot clean port {port}, please close the process manually")
        return False
