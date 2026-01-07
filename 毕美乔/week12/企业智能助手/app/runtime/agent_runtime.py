from dataclasses import dataclass
from agents import SQLiteSession
from contextlib import AsyncExitStack


@dataclass
class AgentRuntime:
    session: SQLiteSession
    exit_stack: AsyncExitStack
