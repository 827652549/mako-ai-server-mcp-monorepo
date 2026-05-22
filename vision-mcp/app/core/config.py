"""
核心配置模块
"""
import json
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 项目
    PROJECT_NAME: str = Field(default="Vision MCP Server")
    VERSION: str = Field(default="1.0.0")

    # MCP 鉴权（本地可随意填，远程部署时对外保密）
    MCP_API_KEY: str = Field(..., description="MCP 服务鉴权 Key")
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, list):
            origins = v
        elif isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    origins = json.loads(v)
                except json.JSONDecodeError:
                    origins = [o.strip() for o in v.split(",") if o.strip()]
            else:
                origins = [o.strip() for o in v.split(",") if o.strip()]
        else:
            origins = ["http://localhost:3000"]
        origins = [str(x).strip() for x in origins if str(x).strip()]
        if "*" in origins:
            raise ValueError("ALLOWED_ORIGINS 禁止使用通配符")
        return origins or ["http://localhost:3000"]

    # 视觉模型（小米中转，Anthropic 兼容格式）
    VISION_BASE_URL: str = Field(
        default="https://token-plan-cn.xiaomimimo.com/anthropic",
        description="视觉 API base URL，末尾不含 /v1/messages",
    )
    VISION_AUTH_TOKEN: str = Field(..., description="视觉 API 鉴权 Token")
    VISION_MODEL: str = Field(default="mimo-v2.5")
    VISION_MAX_TOKENS: int = Field(default=2048)
    VISION_TIMEOUT: float = Field(default=60.0)

    # 日志
    LOG_LEVEL: str = Field(default="INFO")
    JSON_LOGS: bool = Field(default=True)

    # 监控
    PROMETHEUS_ENABLED: bool = Field(default=True)

    # HTTP 客户端
    HTTP_CLIENT_TIMEOUT: float = Field(default=60.0)
    HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS: int = Field(default=20)
    HTTP_CLIENT_MAX_CONNECTIONS: int = Field(default=50)

    # 服务器
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8001)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
