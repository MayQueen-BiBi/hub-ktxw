from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI
from .registry import AGENT_CONFIG
from .agent_role import AgentRole


def build_agent(
    role: AgentRole,
    model_name: str,
    api_key: str,
    mcp_servers: list | None = None,   # ✅ 注意这里
) -> Agent:
    config = AGENT_CONFIG[role]

    # ① OpenAI Client
    openai_client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # ② Model
    model = OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=openai_client,
    )

    # ③ Agent
    if mcp_servers is not None:
        return Agent(
            name=f"{role.value}-agent",
            instructions=config["system_prompt"],
            model=model,
            mcp_servers=mcp_servers,
        )
    else:
        return Agent(
            name=f"{role.value}-agent",
            instructions=config["system_prompt"],
            model=model
        )


def build_router_agent(model_name: str, api_key: str) -> Agent:
    # ① OpenAI Client
    openai_client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    model = OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=openai_client,
    )

    return Agent(
        name="router-agent",
        instructions="""
你是一个企业系统的“意图路由器”。

请判断用户意图，并以 JSON 输出：

{
  "intent": "chat | news | tool",
  "confidence": 0.0-1.0,
  "slots": { key: value }
}

以下情况可以判断为tool类别：
- 获取指定城市天气
- 解析地址信息
- 获取电话号码归属地
- 查询景点信息
- 获取花语
- 货币兑换

如果与新闻或者资讯相关，判断为news类别；
其他情况为chat类别。
只输出 JSON，不要多余文字。
""",
        model=model,
    )
