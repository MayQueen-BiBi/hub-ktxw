import uuid
from .state import SessionState
from app.runtime.agent_runtime import AgentRuntime
from contextlib import AsyncExitStack
from agents import SQLiteSession

import logging

logger = logging.getLogger(__name__)


_SESSION_STORE: dict[str, SessionState] = {}


def get_or_create_session(session_id: str | None) -> SessionState:
    if session_id and session_id in _SESSION_STORE:
        return _SESSION_STORE[session_id]

    sid = session_id or str(uuid.uuid4())

    session = SessionState(
        session_id=sid,
        agent_session_id=None,
        current_intent=None,
        slots={},
        trace=[],
        messages=[],
    )

    _SESSION_STORE[sid] = session
    return session


_AGENT_RUNTIME_STORE: dict[str, AgentRuntime] = {}


async def get_or_create_agent_runtime(agent_sid: str | None) -> AgentRuntime:
    if agent_sid and agent_sid in _AGENT_RUNTIME_STORE:
        return _AGENT_RUNTIME_STORE[agent_sid]

    # 新建 runtime
    sid = agent_sid or str(uuid.uuid4())

    stack = AsyncExitStack()
    await stack.__aenter__()

    session = SQLiteSession(sid)

    runtime = AgentRuntime(
        session=session,
        exit_stack=stack,
    )

    # 🔥 初始化 MCP FSM（关键）

    _AGENT_RUNTIME_STORE[sid] = runtime
    return runtime


async def destroy_agent_runtime(agent_sid: str):
    runtime = _AGENT_RUNTIME_STORE.pop(agent_sid, None)
    if not runtime:
        return
    await runtime.exit_stack.aclose()
