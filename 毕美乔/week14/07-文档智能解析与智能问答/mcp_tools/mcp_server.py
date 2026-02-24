from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
from tool_registry import ToolRegistry
from fastapi import FastAPI, Request

# =====================================
# FastAPI app
# =====================================

app = FastAPI(title="Formula MCP Server")

# =====================================
# 初始化 Tool Registry
# =====================================

registry = ToolRegistry()
BASE_DIR = Path(__file__).resolve().parent
directory = BASE_DIR.parent / "data" / "model_expression"
registry.load_from_directory(str(directory))

# ====================================
# JSON-RPC 错误构造函数
# ====================================

def jsonrpc_error(id_value, code, message):
    return {
        "jsonrpc": "2.0",
        "id": id_value,
        "error": {
            "code": code,
            "message": message
        }
    }


def jsonrpc_result(id_value, result):
    return {
        "jsonrpc": "2.0",
        "id": id_value,
        "result": result
    }


# =====================================
# 请求模型
# =====================================

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


class JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


# ====================================
# 统一 JSON-RPC 入口
# ====================================

@app.post("/")
async def handle_rpc(req: JsonRpcRequest):

    # 基本校验
    if req.jsonrpc != "2.0":
        return jsonrpc_error(None, -32600, "Invalid JSON-RPC version")

    method = req.method
    params = req.params or {}
    id_value = req.id

    if not method:
        return jsonrpc_error(id_value, -32600, "Missing method")

    # =========================
    # 方法分发
    # =========================

    elif method == "initialize":
        return jsonrpc_result(id_value, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "formula-mcp-server",
                "version": "1.0.0"
            }
        })

    elif method == "tools/list":

        tools = []

        for name in registry.list_tools():
            tool = registry.get(name)

            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": tool.required
                }
            })

        return jsonrpc_result(id_value, tools)

    elif method == "tools/call":

        try:
            tool_call = ToolCallRequest(**params)
        except Exception as e:
            return jsonrpc_error(id_value, -32602, f"Invalid params: {e}")

        tool = registry.get(tool_call.name)

        if not tool:
            return jsonrpc_error(id_value, -32601, "Tool not found")

        try:
            result = tool.execute(**tool_call.arguments)

            return jsonrpc_result(id_value, {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            })

        except Exception as e:
            return jsonrpc_error(id_value, -32603, str(e))

    else:
        return jsonrpc_error(id_value, -32601, "Method not found")

