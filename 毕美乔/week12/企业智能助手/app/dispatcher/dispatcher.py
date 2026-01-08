from app.ai_agents import build_agent, build_router_agent
from app.store.conversation_store import conversation_store
from app.mcp_views import build_mcp_view
from .intent_mapping import map_intent_to_role
from .parser import parse_intent
from agents import Runner
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def dispatch(
    prompt: str,
    conversation_id: str,
    model_name: str,
    api_key: str,
    server_url: str,
    use_tool: bool,
) -> str:

    # 1️⃣ 读取历史
    history = conversation_store.load(conversation_id)

    # 2️⃣ 写入用户消息
    conversation_store.append(conversation_id, "user", prompt)

    # 3️⃣ Router 判 intent
    router_agent = build_router_agent(model_name, api_key)
    router_result = await Runner.run(router_agent, input=prompt)
    route = json.loads(router_result.final_output)
    intent = parse_intent(route.get("intent", "none"))

    role = map_intent_to_role(intent)

    # 4️⃣ 构建 MCP server（短生命周期）
    mcp_server = build_mcp_view(server_url, intent) if use_tool else None

    # 5️⃣ 构建 agent 并运行
    # messages = history + [{"role": "user", "content": prompt}]
    messages = [{"role": "user", "content": prompt}]

    if mcp_server:
        async with mcp_server:
            agent = build_agent(
                role=role,
                model_name=model_name,
                api_key=api_key,
                mcp_servers=[mcp_server],
            )
            result = await Runner.run(agent, input=messages)
    else:
        agent = build_agent(
            role=role,
            model_name=model_name,
            api_key=api_key,
        )
        result = await Runner.run(agent, input=messages)

    # 6️⃣ 写回 assistant
    conversation_store.append(
        conversation_id, "assistant", result.final_output
    )

    # trace
    logger.info(
        "conversation=%s intent=%s role=%s use_tool=%s",
        conversation_id,
        intent,
        role,
        use_tool,
    )

    return result.final_output


