import streamlit as st
from agents import set_default_openai_api, set_tracing_disabled
from app.dispatcher.dispatcher import dispatch
import uuid
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# =====================
# Global config（只在入口）
# =====================
set_default_openai_api("chat_completions")
set_tracing_disabled(True)

st.set_page_config(page_title="企业职能机器人")

# =====================
# Streamlit session init
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好，我是企业职能助手，可以 AI 对话，也可以调用内部工具。"}
    ]

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# 标记异步运行状态
if "running" not in st.session_state:
    st.session_state.running = False

# =====================
# Sidebar
# =====================
with st.sidebar:
    st.title("职能 AI + 智能问答")

    key = st.session_state.get("API_TOKEN", "")
    st.session_state["API_TOKEN"] = st.text_input("输入 Token:", type="password", value=key)

    model_name = st.selectbox("选择模型", ["qwen-flash", "qwen-max"])
    use_tool = st.checkbox("使用工具", value=True)


    def clear_chat():
        # 只清对话相关状态
        keys_to_clear = [
            "messages",
            "pending_prompt",
            "session_id",
            "agent_session_id",
            "running",
        ]

        for k in keys_to_clear:
            if k in st.session_state:
                del st.session_state[k]

        # 重新初始化 messages
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "你好，我是企业职能助手，可以 AI 对话，也可以调用内部工具。"
            }
        ]
        st.session_state["conversation_id"] = str(uuid.uuid4())

    st.button("清空聊天", on_click=clear_chat)

# =====================
# 展示聊天历史
# =====================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# =====================
# Chat input
# =====================
token_ready = bool(st.session_state.get("API_TOKEN"))

prompt = st.chat_input(
    "请输入你的问题",
    disabled=not token_ready
)

if not token_ready:
    st.info("请先在左侧输入 API Token")

if prompt:
    # 保存 pending prompt
    st.session_state.pending_prompt = prompt
    # 显示用户消息
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )
    # 显示占位 assistant
    st.session_state.messages.append(
        {"role": "assistant", "content": "思考中..."}
    )

    st.rerun()

# =====================
# 调用 agent
# =====================
messages = st.session_state.messages
pending_prompt = st.session_state.get("pending_prompt")
api_key = st.session_state.get("API_TOKEN")
session_id = st.session_state.get("session_id")

ready_to_call = (
    messages
    and messages[-1]["role"] == "assistant"
    and messages[-1]["content"] == "思考中..."
    and st.session_state.pending_prompt is not None
    and not st.session_state.running
)

if ready_to_call:
    st.session_state.running = True
    try:
        import asyncio

        conversation_id = st.session_state.conversation_id
        reply = asyncio.run(
            dispatch(
                    prompt=pending_prompt,
                    conversation_id=conversation_id,
                    model_name=model_name,
                    api_key=api_key,
                    server_url="http://localhost:8900/sse",
                    use_tool=use_tool,
            )
        )

        # 原地更新 assistant
        messages[-1]["content"] = reply

        # 清理 pending 状态（非常重要）
        st.session_state.pending_prompt = None

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        result = type("Dummy", (), {"final_output": f"执行失败: {e}"})()

    finally:
        st.session_state.running = False
        st.rerun()


