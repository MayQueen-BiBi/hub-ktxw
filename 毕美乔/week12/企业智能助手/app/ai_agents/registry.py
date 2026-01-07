from .agent_role import AgentRole
from app.mcp_views.builds import build_news_mcp_view, build_tools_mcp_view


AGENT_CONFIG = {
    AgentRole.CHAT: {
        "system_prompt": "你是企业通用聊天助手。",
        "mcp_builder": None,
    },
    AgentRole.NEWS: {
        "system_prompt": "你是新闻查询助手，仅在必要时调用新闻工具。",
        "mcp_builder": build_news_mcp_view,
    },
    AgentRole.TOOLS: {
        "system_prompt": "你是企业工具助手，仅在需要时调用内部工具。",
        "mcp_builder": build_tools_mcp_view,
    },
}
