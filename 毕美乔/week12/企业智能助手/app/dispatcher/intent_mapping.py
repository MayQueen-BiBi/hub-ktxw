from app.dispatcher.intent import Intent
from app.ai_agents.agent_role import AgentRole


INTENT_TO_AGENT_ROLE = {
    Intent.NEWS: AgentRole.NEWS,
    Intent.TOOL: AgentRole.TOOLS,
    Intent.CHAT: AgentRole.CHAT,
}


def map_intent_to_role(intent: Intent) -> AgentRole:
    return INTENT_TO_AGENT_ROLE.get(intent, AgentRole.CHAT)
