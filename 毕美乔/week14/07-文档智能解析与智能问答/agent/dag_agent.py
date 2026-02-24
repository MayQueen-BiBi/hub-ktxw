import os
import json
import asyncio
import httpx
import numpy as np
from openai import AsyncOpenAI
from transformers import AutoTokenizer, AutoModel
import torch
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# =========================================
# 1️⃣ Qwen Embedding
# =========================================

class QwenEmbedding:
    def __init__(self, model_name="Qwen/Qwen3-Embedding-0.6B"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def embed(self, texts):
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.numpy()


# =========================================
# 2️⃣ MCP JSON-RPC 调用
# =========================================

class MCPClient:
    def __init__(self, url):
        self.url = url
        self.id_counter = 0

    async def call(self, method, params=None):
        self.id_counter += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": method,
            "params": params or {}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.url, json=payload)
            print(resp.json())
            return resp.json()["result"]

    async def list_tools(self):
        return await self.call("tools/list")

    async def call_tool(self, name, arguments):
        return await self.call("tools/call", {
            "name": name,
            "arguments": arguments
        })


# =========================================
# 3️⃣ Agent 主体
# =========================================

class IndustrialAgent:

    def __init__(self, mcp_url):
        self.mcp = MCPClient(mcp_url)
        self.embedder = QwenEmbedding()
        self.llm = AsyncOpenAI(
            api_key=os.environ["DASHSCOPE_API_KEY"],
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    # -------- Tool Retrieval --------
    async def retrieve_tools(self, question, top_k=5):
        tools = await self.mcp.list_tools()

        descriptions = [
            f"{t['name']} : {t['description']}"
            for t in tools
        ]

        tool_embeddings = self.embedder.embed(descriptions)
        query_embedding = self.embedder.embed([question])[0]

        scores = tool_embeddings @ query_embedding
        top_idx = np.argsort(scores)[::-1][:top_k]

        return [tools[i] for i in top_idx]

    # -------- LLM 决策 --------
    async def decide_tool(self, question, candidate_tools):

        tools_prompt = ""

        for tool in candidate_tools:
            tools_prompt += f"""
工具名称: {tool['name']}
描述: {tool['description']}
参数 schema:
{json.dumps(tool['inputSchema'], ensure_ascii=False, indent=2)}

"""

        prompt = f"""
你是一个严谨的函数调用决策系统。

用户问题：
{question}

候选工具如下：
{tools_prompt}

请返回 JSON：

{{
  "tool_name": "...",
  "arguments": {{...}}
}}

如果没有合适工具：
{{ "tool_name": null }}
只返回 JSON，不要解释。
"""

        response = await self.llm.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except:
            return {"tool_name": None}

    # -------- 最终回答生成 --------
    async def generate_final_answer(self, question, tool_result):

        prompt = f"""
用户问题：
{question}

工具执行结果：
{json.dumps(tool_result, ensure_ascii=False)}

请生成最终自然语言回答。
"""

        response = await self.llm.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content

    # -------- Agent 主流程 --------
    async def run(self, question):

        # 1️⃣ 召回工具
        candidate_tools = await self.retrieve_tools(question)

        # 2️⃣ LLM 决策
        decision = await self.decide_tool(question, candidate_tools)

        if decision.get("tool_name") is None:
            return "没有合适工具可调用"

        # 3️⃣ 调用 MCP
        result = await self.mcp.call_tool(
            decision["tool_name"],
            decision["arguments"]
        )

        # 4️⃣ 生成最终回答
        final_answer = await self.generate_final_answer(
            question,
            result
        )

        return final_answer


# =========================================
# 4️⃣ 运行
# =========================================

async def main():
    agent = IndustrialAgent("http://localhost:8000")

    question = "已知房屋面积为120平方米，按照我们的租金建模方法，预期的月租金是多少？"
    answer = await agent.run(question)

    print("最终回答：")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())

