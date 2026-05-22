from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 项目
    PROJECT_NAME: str = Field(default="Vision MCP Server")
    VERSION: str = Field(default="1.0.0")

    # MCP 鉴权（本地可随意填，远程部署时对外保密）
    MCP_API_KEY: str = Field(..., description="MCP 服务鉴权 Key")
    # 逗号分隔的允许域名，多个域名示例：https://a.com,https://b.com
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

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
