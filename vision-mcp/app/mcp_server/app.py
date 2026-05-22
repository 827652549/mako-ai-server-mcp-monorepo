"""
Vision MCP Server 实例
注册视觉工具箱
"""
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.core.logging import get_logger
from app.tools.base import create_mcp_tool_decorator

logger = get_logger()

# Configure transport security for production deployment
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["vision-mcp.onrender.com", "vision-mcp.onrender.com:*"],
    allowed_origins=["https://vision-mcp.onrender.com"],
)

mcp = FastMCP(
    "Vision-MCP",
    streamable_http_path="/",
    stateless_http=True,
    transport_security=transport_security,
)

mcp_tool = create_mcp_tool_decorator(mcp)

# 注册视觉工具
from app.tools import vision  # noqa: E402

logger.info("mcp_server_initialized", server_name="Vision-MCP")

__all__ = ["mcp", "mcp_tool"]
