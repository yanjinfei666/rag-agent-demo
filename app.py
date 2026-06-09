"""
Streamlit 前端 —— RAG 问答界面（Day 6 完善版）

改进：
  1. 启动时自动检查后端状态
  2. 上传后侧边栏持久显示文件信息
  3. 清空对话按钮
  4. 来源展示美化
  5. 未上传时禁用提问

启动：streamlit run app.py
（需要先启动后端：uvicorn main:app --reload）
"""
import streamlit as st
import requests

# ── 后端地址 ──
API_BASE = "http://127.0.0.1:8000"


# ════════════════════════════════════════════════════
# 页面配置
# ════════════════════════════════════════════════════
st.set_page_config(page_title="RAG 问答助手", layout="wide")
st.title("📄 RAG 知识库问答助手")


# ════════════════════════════════════════════════════
# 初始化 session_state
# ════════════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_info" not in st.session_state:
    st.session_state.doc_info = None  # {"filename": ..., "pages": ..., "chunks": ..., "chars": ...}


# ════════════════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════════════════
def check_backend_status() -> dict | None:
    """GET /status，返回引擎状态 dict，连不上返回 None"""
    try:
        resp = requests.get(f"{API_BASE}/status", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.ConnectionError:
        pass
    return None


def format_sources_html(sources: list) -> str:
    """把来源列表渲染成 HTML 卡片"""
    parts = []
    for i, src in enumerate(sources):
        page = src.get("page", "?")
        content = src.get("content", "")
        parts.append(
            f"""<div style="
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px 14px;
                margin-bottom: 10px;
                background: #f9f9f9;
            ">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 4px;">
                    📖 来源 {i+1} · 第 {page} 页
                </div>
                <div style="color: #333; line-height: 1.5;">
                    {content}
                </div>
            </div>"""
        )
    return "\n".join(parts)


# ════════════════════════════════════════════════════
# 侧边栏
# ════════════════════════════════════════════════════
with st.sidebar:
    st.header("📤 上传文档")

    # ── 上传控件 ──
    uploaded_file = st.file_uploader("选择 PDF 文件", type=["pdf"])

    col1, col2 = st.columns([1, 1])
    with col1:
        upload_btn = st.button("上传并索引", type="primary", use_container_width=True)
    with col2:
        # 清空对话按钮（放侧边栏底部也行，但放这里更方便）
        if st.button("🗑 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    if uploaded_file and upload_btn:
        with st.spinner("正在处理 PDF..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                resp = requests.post(f"{API_BASE}/upload", files=files)
                if resp.status_code == 200:
                    data = resp.json()
                    # 存到 session_state，刷新不丢
                    st.session_state.doc_info = {
                        "filename": uploaded_file.name,
                        "pages": data["pages"],
                        "chars": data["chars"],
                        "chunks": data["chunks"],
                    }
                    st.success(data["message"])
                    st.rerun()
                else:
                    st.error(f"上传失败：{resp.json().get('detail', '未知错误')}")
            except requests.exceptions.ConnectionError:
                st.error("❌ 无法连接到后端，请确认 uvicorn 已启动")

    # ── 当前知识库状态卡片 ──
    st.divider()
    st.subheader("📚 知识库状态")

    # 优先用 session_state，没有则调后端查
    doc_info = st.session_state.doc_info
    if doc_info is None:
        # 首次加载或刷新后，尝试从后端恢复
        status = check_backend_status()
        if status and status.get("has_doc"):
            doc_info = {
                "filename": status.get("filename", "未知"),
                "pages": status.get("pages", 0),
                "chars": status.get("chars", 0),
                "chunks": status.get("chunks", 0),
            }
            st.session_state.doc_info = doc_info

    if doc_info:
        st.markdown(
            f"""
            <div style="
                border: 1px solid #4CAF50;
                border-radius: 8px;
                padding: 12px;
                background: #f1f8e9;
            ">
                <div style="font-size: 0.9em; color: #2e7d32; font-weight: bold; margin-bottom: 8px;">
                    ✅ 已索引
                </div>
                <table style="width: 100%; font-size: 0.85em;">
                    <tr><td style="padding: 2px 0; color: #555;">文件</td>
                        <td style="padding: 2px 0; font-weight: 500;">{doc_info['filename']}</td></tr>
                    <tr><td style="padding: 2px 0; color: #555;">页数</td>
                        <td style="padding: 2px 0;">{doc_info['pages']} 页</td></tr>
                    <tr><td style="padding: 2px 0; color: #555;">字数</td>
                        <td style="padding: 2px 0;">{doc_info['chars']:,} 字</td></tr>
                    <tr><td style="padding: 2px 0; color: #555;">切片</td>
                        <td style="padding: 2px 0;">{doc_info['chunks']} 块</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("📭 尚未上传 PDF，请先上传文档")

    # ── 后端状态指示器 ──
    backend_status = check_backend_status()
    st.divider()
    if backend_status is not None:
        st.caption("🟢 后端已连接")
    else:
        st.caption("🔴 后端未连接")
        st.caption("请在终端运行：`uvicorn main:app --reload`")


# ════════════════════════════════════════════════════
# 主区域：对话
# ════════════════════════════════════════════════════
st.header("💬 对话")

# ── 消息数提示 ──
msg_count = len([m for m in st.session_state.messages if m["role"] == "assistant"])
if msg_count > 0:
    st.caption(f"已提问 {msg_count} 次 · 共 {len(st.session_state.messages)} 条消息")

# ── 显示历史消息 ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📎 查看来源"):
                st.markdown(format_sources_html(msg["sources"]), unsafe_allow_html=True)

# ── 输入框 ──
has_doc = st.session_state.doc_info is not None
chat_disabled = not has_doc
placeholder = "输入你的问题…" if has_doc else "请先在左侧上传 PDF 文件"

if prompt := st.chat_input(placeholder=placeholder, disabled=chat_disabled):
    # 显示用户问题
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调后端
    with st.spinner("🤔 思考中..."):
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
                            st.markdown(format_sources_html(sources), unsafe_allow_html=True)

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
            st.error("❌ 无法连接到后端，请确认 uvicorn 已启动")


# ── 底部提示 ──
st.divider()
st.caption("💡 左侧上传 PDF → 下方提问 | 后端地址：" + API_BASE)
