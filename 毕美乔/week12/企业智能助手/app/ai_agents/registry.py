from .agent_role import AgentRole


AGENT_CONFIG = {
    AgentRole.CHAT: {
        "system_prompt": "你是企业通用聊天助手。",
    },
    AgentRole.NEWS: {
        "system_prompt": "你是新闻查询助手，仅在必要时调用新闻工具。",
    },
    AgentRole.TOOLS: {
        "system_prompt": "你是企业工具助手，仅在需要时调用内部工具。",
    },
}
