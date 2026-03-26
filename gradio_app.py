import uuid
import requests
import gradio as gr

BACKEND = "http://127.0.0.1:8000"

import os
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"

def ensure_session(session_id):
    return session_id or str(uuid.uuid4())

def send_message(message, history, session_id):
    session_id = ensure_session(session_id)

    resp = requests.post(
        f"{BACKEND}/chat",
        json={
            "session_id": session_id,
            "message": message,
            "stream": False
        },
        timeout=120
    )
    data = resp.json()

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": data["answer"]},
    ]

    debug_text = (
        f"route: {data['route']}\n\n"
        f"rewritten_query: {data['rewritten_query']}\n\n"
        f"memory_used:\n- " + "\n- ".join(data["memory_used"]) + "\n\n"
        f"reflection:\n{data['reflection']}\n\n"
        f"references:\n- " + "\n- ".join(data["references"])
    )

    retrieval_text = "\n\n".join([
        f"菜品: {x['dish_name']}\n分类: {x['category']}\n难度: {x['difficulty']}\n分数: {x['rrf_score']}\n片段: {x['preview']}"
        for x in data["retrieval_debug"]
    ])

    return history, session_id, debug_text, retrieval_text, ""

def load_memory(session_id):
    session_id = ensure_session(session_id)
    resp = requests.get(f"{BACKEND}/sessions/{session_id}/memory", timeout=30)
    data = resp.json()

    text = (
        f"session_id: {session_id}\n\n"
        "短期记忆:\n- " + "\n- ".join(data["short_memory"]) + "\n\n"
        "长期记忆:\n- " + "\n- ".join(data["long_memory"]) + "\n\n"
        "反思:\n- " + "\n- ".join(data["reflections"])
    )
    return session_id, text

def load_kb_stats():
    resp = requests.get(f"{BACKEND}/kb/stats", timeout=30)
    data = resp.json()
    return str(data)

with gr.Blocks() as demo:
    gr.Markdown("# 食谱 RAG 对话系统")

    session_id = gr.State("")
    with gr.Tab("聊天"):
        chatbot = gr.Chatbot(type="messages", height=500)
        msg = gr.Textbox(label="输入问题")
        send_btn = gr.Button("发送")

        with gr.Row():
            debug_box = gr.Textbox(label="决策/记忆/反思", lines=18)
            retrieval_box = gr.Textbox(label="检索调试信息", lines=18)

        send_btn.click(
            send_message,
            inputs=[msg, chatbot, session_id],
            outputs=[chatbot, session_id, debug_box, retrieval_box, msg]
        )

    with gr.Tab("会话记忆"):
        memory_btn = gr.Button("刷新记忆")
        memory_box = gr.Textbox(label="会话短期/长期记忆与反思", lines=24)
        memory_btn.click(
            load_memory,
            inputs=[session_id],
            outputs=[session_id, memory_box]
        )

    with gr.Tab("知识库状态"):
        kb_btn = gr.Button("刷新知识库统计")
        kb_box = gr.Textbox(label="知识库统计", lines=12)
        kb_btn.click(load_kb_stats, outputs=[kb_box])

demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)