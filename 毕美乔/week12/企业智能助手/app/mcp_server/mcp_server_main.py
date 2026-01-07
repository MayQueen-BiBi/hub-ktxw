import asyncio
from fastmcp import FastMCP, Client

from news import mcp as news_mcp
from saying import mcp as saying_mcp
from tool import mcp as tool_mcp
from sentiment import mcp as sentiment_mcp


# 创建 MCP Server
mcp = FastMCP(
    name="MCP-Server"
)


# 把 3 个 MCP Server，合并进当前 MCP Server
async def setup():
    await mcp.import_server(news_mcp, prefix="news")
    await mcp.import_server(saying_mcp, prefix="saying")
    await mcp.import_server(tool_mcp, prefix="tool")
    await mcp.import_server(sentiment_mcp, prefix="sentiment")


# “自检代码”, 非必须
# 用 MCP Client, 连到 当前这个 server，列出 Agent 能看到的所有 tool
async def test_filtering():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])


if __name__ == "__main__":
    # agent 启动前保证tools注册
    asyncio.run(setup())
    # 启动前自检，确保 tools 已正确暴露
    asyncio.run(test_filtering())
    mcp.run(transport="sse", port=8900)
