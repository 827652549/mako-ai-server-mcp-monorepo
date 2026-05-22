"""
Vision MCP Server 实例
注册视觉工具箱
"""
from mcp.server.fastmcp import FastMCP

from app.core.logging import get_logger
from app.tools.base import create_mcp_tool_decorator

logger = get_logger()

mcp = FastMCP(
    "Vision-MCP",
    streamable_http_path="/",
    stateless_http=True,
)

mcp_tool = create_mcp_tool_decorator(mcp)

# 注册视觉工具
from app.tools import vision  # noqa: E402

logger.info("mcp_server_initialized", server_name="Vision-MCP")

__all__ = ["mcp", "mcp_tool"]
