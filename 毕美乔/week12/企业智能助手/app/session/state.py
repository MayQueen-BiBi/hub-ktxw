from dataclasses import dataclass, field

@dataclass
class SessionState:
    session_id: str # 唯一标识
    agent_session_id: str | None = None  # 对应 AgentRuntime
    messages: list[dict] = field(default_factory=list)
    current_intent: str | None = None
    trace: list[dict] = field(default_factory=list)
    slots: dict = field(default_factory=dict)  # ✅ 默认空字典





