"""
Streamlit 前端 —— RAG 问答界面

启动：streamlit run app.py
（需要先启动后端：uvicorn main:app --reload）
"""
import streamlit as st
import requests

# ── 后端地址 ──
API_BASE = "http://127.0.0.1:8000"


# ── 页面配置 ──
st.set_page_config(page_title="RAG 问答助手", layout="wide")
st.title("📄 RAG 知识库问答助手")


# ── 侧边栏：文件上传 ──
with st.sidebar:
    st.header("📤 上传文档")
    uploaded_file = st.file_uploader("选择 PDF 文件", type=["pdf"])

    if uploaded_file and st.button("上传并索引", type="primary"):
        with st.spinner("正在处理 PDF..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                resp = requests.post(f"{API_BASE}/upload", files=files)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(data["message"])
                    st.info(f"📄 {data['pages']} 页 | {data['chars']} 字 | 切为 {data['chunks']} 块")
                else:
                    st.error(f"上传失败：{resp.json().get('detail', '未知错误')}")
            except requests.exceptions.ConnectionError:
                st.error("无法连接到后端，请确认 uvicorn 已启动")


# ── 主区域：对话 ──
st.header("💬 提问")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 如果有来源，显示来源
        if "sources" in msg:
            with st.expander("📎 查看来源"):
                for i, src in enumerate(msg["sources"]):
                    st.markdown(f"**来源 {i+1}** — 第 {src['page']} 页")
                    st.markdown(f"> {src['content']}")

# 输入框
if prompt := st.chat_input("输入你的问题"):
    # 显示用户问题
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调后端
    with st.spinner("思考中..."):
        try:
            resp = requests.post(f"{API_BASE}/chat", json={"question": prompt})
            if resp.status_code == 200:
                data = resp.json()
                answer = data["answer"]
                sources = data.get("sources", [])

                # 显示回答
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    if sources:
                        with st.expander("📎 查看来源"):
                            for i, src in enumerate(sources):
                                st.markdown(f"**来源 {i+1}** — 第 {src['page']} 页")
                                st.markdown(f"> {src['content']}")

                # 存到历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })
            else:
                error = resp.json().get("detail", "未知错误")
                st.error(f"问答失败：{error}")
        except requests.exceptions.ConnectionError:
            st.error("无法连接到后端，请确认 uvicorn 已启动")


# ── 底部提示 ──
st.divider()
st.caption("💡 先上传 PDF → 再提问 | 后端地址：" + API_BASE)
