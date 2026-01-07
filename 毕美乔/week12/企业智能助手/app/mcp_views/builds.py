from typing import Optional, Any
from agents.mcp.server import MCPServerSse
from agents.mcp.util import ToolFilterCallable, ToolFilterContext
from typing import List, Optional


def build_news_mcp_view(
    server_url: str,
    tool_filter: Optional[ToolFilterCallable] = None,
) -> MCPServerSse:
    """
    News Agent 可见的 MCP View（列表形式返回）

    - 默认只暴露 news 前缀工具
    - tool_filter 是扩展位（不破坏默认策略）
    """

    def default_filter(ctx: ToolFilterContext, tool: Any) -> bool:
        return tool.name.startswith("_news")

    mcp_view = MCPServerSse(
        name="news-mcp_views-view",
        params={"url": server_url},
        tool_filter=tool_filter or default_filter,
        client_session_timeout_seconds=20,
    )
    print(">>> MCPServerSse final URL:", mcp_view.params["url"])
    # 返回列表
    return mcp_view


def build_tools_mcp_view(
    server_url: str,
    tool_filter: Optional[ToolFilterCallable] = None,
) -> MCPServerSse:
    """
    Tools Agent 可见的 MCP View

    - 不假设 tool 命名规则
    - tool_filter 仅作为扩展位（权限 / 灰度 / 实验）
    """

    mcp_view = MCPServerSse(
        name="tools-mcp_views-view",
        params={"url": server_url},
        tool_filter=tool_filter,  # 可以是 None
        client_session_timeout_seconds=20,
    )
    print(">>> MCPServerSse final URL:", mcp_view.params["url"])
    # 返回列表
    return mcp_view
