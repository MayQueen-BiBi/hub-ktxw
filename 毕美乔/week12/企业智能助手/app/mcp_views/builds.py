from typing import Optional, Any
from agents.mcp.server import MCPServerSse
from agents.mcp.util import ToolFilterCallable, ToolFilterContext
from typing import List, Optional
from app.dispatcher.intent import Intent


INTENT_TOOL_PREFIX = {
    Intent.NEWS: ("news_",),
    Intent.TOOLS: ("tools_",)
}


def make_intent_tool_filter(
    intent: Intent,
) -> ToolFilterCallable:
    """
    根据 Router 判定的 intent
    动态生成 MCP tool_filter
    """

    allowed_prefixes = INTENT_TOOL_PREFIX.get(intent, ())

    if not allowed_prefixes:
        raise ValueError(f"No tool prefixes configured for intent: {intent}")

    # def _filter(ctx: ToolFilterContext, tool: Any) -> bool:
    #     # 1️⃣ 能力边界（intent）
    #     if not tool.name.startswith(allowed_prefixes):
    #         return False
    #
    #     # 2️⃣ 权限控制（Context）
    #     if tool.name.startswith("tools_") and not getattr(ctx, "is_pro_user", False):
    #         return False
    #
    #     # 3️⃣ 未来：灰度 / quota / 实验
    #     return True

    def _filter(ctx: ToolFilterContext, tool: Any) -> bool:
        allowed = tool.name.startswith(INTENT_TOOL_PREFIX[intent])

        print(
            f"[TOOL_FILTER]"
            f" intent={intent.value}"
            f" tool={tool.name}"
            f" allowed={allowed}"
        )

        return allowed

    return _filter


def get_tool_policy(intent: Intent):
    return {
        "allowed_prefixes": INTENT_TOOL_PREFIX[intent],
        "require_pro": intent == Intent.TOOLS,
    }


def build_mcp_view(
    server_url: str,
    intent: Intent
) -> MCPServerSse | None:
    """
    Tools Agent 可见的 MCP View

    - 不假设 tool 命名规则
    - tool_filter 仅作为扩展位（权限 / 灰度 / 实验）
    """

    if intent == Intent.CHAT:
        return None

    tool_filter = make_intent_tool_filter(intent)

    mcp_view = MCPServerSse(
        name=f"{intent}-mcp_views-view",
        params={"url": server_url},
        tool_filter=tool_filter,
        client_session_timeout_seconds=20,
    )
    print(">>> MCPServerSse final URL:", mcp_view.params["url"])

    # 返回列表
    return mcp_view
