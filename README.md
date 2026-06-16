# 📄 RAG Agent 智能问答系统

基于 **LangChain + LangGraph + ChromaDB + Streamlit** 构建的 RAG 智能问答系统，支持 PDF 上传、向量检索、大模型生成，以及多工具 Agent 编排。

## 功能

- ✅ **PDF 上传** — 自动切片、向量化、建立知识库索引
- ✅ **智能问答** — 基于 RAG 检索增强生成，回答可追溯来源
- ✅ **HyDE 优化** — 假设文档嵌入提升召回准确率
- ✅ **Reranker 精排** — BGE Cross-Encoder 重排序去噪音
- ✅ **Agent 工具编排** — LangGraph ReAct Agent，支持知识库搜索、计算器
- ✅ **多轮记忆** — Agent 记住上下文，支持连续对话

## 快速开始

### 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（阿里云 DashScope）
# 在 .env 文件中写入：
# DASHSCOPE_API_KEY=sk-xxxxx

# 3. 启动
streamlit run app.py
```

### 在线体验

部署在 HuggingFace Spaces：[链接待填写]

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Streamlit |
| 后端 | FastAPI + LangChain |
| Agent 框架 | LangGraph |
| 向量数据库 | ChromaDB |
| LLM | 通义千问 qwen-max（DashScope）|
| Embedding | text-embedding-v3 |

## 项目结构

```
├── app.py                    # Streamlit 前端
├── app_hf.py                 # HF Spaces 部署版
├── main.py                   # FastAPI 后端
├── rag_engine.py             # RAG 引擎（核心）
├── demo_01_basic_rag.py      # Day 1: 基础 RAG
├── demo_02_pdf_rag.py        # Day 3: PDF 加载
├── demo_03_langgraph_basic.py # Day 9: LangGraph 基础
├── demo_04_langgraph_tools.py # Day 10: Agent 工具
├── demo_05_langgraph_memory.py # Day 11: 多轮记忆
├── INTERVIEW_QA.md           # 面试题积累
└── requirements.txt          # 依赖清单
```
