from enum import Enum


class AgentRole(str, Enum):
    CHAT = "chat"
    NEWS = "news"
    TOOLS = "tools"
