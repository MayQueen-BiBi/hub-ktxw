# 【作业】

## 作业1
复现现有职能助手代码，环境要有 fastmcp、streamlit、openai-agent 库。   
python mcp_server_main.py   
streamlit run streamlit_demo.py

## 作业2
尝试新定义一个工具，进行文本情感分析，输入文本判断文本的情感类别。最终可以在界面通过agent 在对话中调用这个工具

```test
@mcp.tool
def sentiment_classification(text: Annotated[str, "The text to analyze"]):
    """Classifies the sentiment of a given text."""
    pass
```

## 作业3
尝试需要在对话中选择工具，增加 tool_filter 的逻辑。
查询新闻的时候，只调用news的工具
调用工具的时候，只调用tools的工具
### 自己的方案
```
User Query
   ↓
Router Agent
   ↓  (intent / capability decision)
构造 MCP View（tools / permissions / context）
   ↓
Task Agent (QA / Search / SQL / Doc / etc.)
   ↓
Run
```

### 毛老师 给的方案
```
User Query
   ↓
Router / Supervisor
   ↓
handoff → Agent A (自带 MCP View)
        → Agent B (自带 MCP View)
```

### 两种方案对比  

| 维度                     | 方案 1：Router + 动态 MCP View + 执行 Agent                                                     | 方案 2：多 Agent + 预绑定 MCP + handoff                                          |
| ---------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **1️⃣ 权限与数据隔离**        | ✅ **强**<br>• MCP View 运行时构造<br>• 可按用户 / 部门 / session 动态裁剪工具与数据权限<br>• 同一 Agent 可服务不同权限用户 | ⚠️ **弱 / 复杂**<br>• Agent 与工具强绑定<br>• 权限变化需复制 Agent 或复杂条件判断<br>• 易产生权限泄漏风险 |
| **2️⃣ Intent 与能力解耦**   | ✅ **清晰分层**<br>• Intent = 路由信号（决策层）<br>• Agent = 执行层<br>• Tool = 能力层                      | ❌ **易混淆**<br>• Agent 同时承担决策 + 执行<br>• Intent 隐含在 Agent 选择中<br>• 架构语义不清晰   |
| **3️⃣ 可测试性与可维护性**      | ✅ **高**<br>• Router / MCP View / Agent 可独立单测<br>• 链路稳定、可预测<br>• 适合 CI / 回归测试             | ⚠️ **低**<br>• handoff 路径组合爆炸<br>• 端到端测试为主，难单测<br>• Debug 成本高              |
| **4️⃣ 扩展性（Intent 增长）** | ✅ **可控扩展**<br>• Intent 数量可增长<br>• Agent 数量保持稳定<br>• 通过 MCP View 组合能力                     | ❌ **不可控**<br>• Intent ≈ Agent 数量<br>• Agent 数快速膨胀<br>• 后期难以维护             |
| **5️⃣ 成本与推理稳定性**       | ✅ **稳定、低波动**<br>• 推理链路固定（Router → Agent）<br>• 行为 deterministic<br>• 易做缓存与兜底              | ⚠️ **不稳定、成本高**<br>• 多次推理 + handoff<br>• 同问题路径不一致<br>• 成本与时延不可控            |



### 方案二 优点/适用情况：
- Agent 能力非常异质（如：代码 Agent、SQL Agent、BI Agent）
- 工具边界非常稳定
- 已经有成熟的 Agent 平台
- 更偏 复杂任务规划 / 多步协作

📌 典型场景
- 自动化数据分析
- 复杂运维
- AutoGPT / Devin-like 系统
