from app.ai_agents import build_agent, build_router_agent
from app.session import SessionState, get_or_create_agent_runtime
from app.ai_agents.registry import AGENT_CONFIG
from .intent_mapping import map_intent_to_role
from agents import Runner
from contextlib import AsyncExitStack
import json
import logging
logger = logging.getLogger(__name__)


async def dispatch(
    prompt: str,
    biz_session: SessionState,
    model_name: str,
    api_key: str,
    server_url: str,
    use_tool: bool,
) -> str:
    """
    dispatch 只使用 AgentRuntime，不管理生命周期。
    MCP 为短生命周期，每次调用 ensure 生成新的 server 列表。
    """

    # ----------------------
    # 1️⃣ 写入用户消息
    # ----------------------
    biz_session.messages.append({"role": "user", "content": prompt})

    # ----------------------
    # 2️⃣ Router 判定 intent
    # ----------------------
    router_agent = build_router_agent(model_name, api_key)
    router_result = await Runner.run(router_agent, input=prompt, session=None)
    route = json.loads(router_result.final_output)
    intent = route.get("intent", "none")
    biz_session.current_intent = intent
    biz_session.slots.update(route.get("slots", {}))
    role = map_intent_to_role(intent)

    # ----------------------
    # 3️⃣ 获取 AgentRuntime
    # ----------------------
    agent_runtime = await get_or_create_agent_runtime(biz_session.agent_session_id)
    biz_session.agent_session_id = agent_runtime.session.session_id

    # ----------------------
    # 4️⃣ 构建 MCP server（短生命周期）
    # ----------------------
    mcp_server = None
    if use_tool:
        config = AGENT_CONFIG[role]
        builder = config.get("mcp_builder")
        if builder:
            mcp_server = builder(server_url)

    # ----------------------
    # 5️⃣ 构建 agent
    # ----------------------
    if mcp_server:
        async with mcp_server:
            agent = build_agent(
                role=role,
                model_name=model_name,
                api_key=api_key,
                mcp_servers=[mcp_server]
            )

            try:
                result = await Runner.run(agent, input=prompt, session=agent_runtime.session)
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                result = type("Dummy", (), {"final_output": f"执行失败: {e}"})()

    else:
        agent = build_agent(
            role=role,
            model_name=model_name,
            api_key=api_key,
        )

        try:
            result = await Runner.run(agent, input=prompt, session=agent_runtime.session)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            result = type("Dummy", (), {"final_output": f"执行失败: {e}"})()

    # ----------------------
    # 7️⃣ 写回 assistant 消息
    # ----------------------
    biz_session.messages.append({"role": "assistant", "content": result.final_output})

    # ----------------------
    # 8️⃣ trace
    # ----------------------
    mcp_view = "news" if intent == "news" else "tool" if intent == "tool" else "none"
    biz_session.trace.append({"intent": intent, "mcp_view": mcp_view})

    return result.final_output

