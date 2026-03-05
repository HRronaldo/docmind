"""Core configuration and initialization."""

import os
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
