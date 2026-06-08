"""
Day 3 RAG Demo —— PyPDFLoader 加载 PDF + 问答

跑法：python demo_02_pdf_rag.py   （Windows 终端建议：set PYTHONIOENCODING=utf-8 && python demo_02_pdf_rag.py）
"""
import os
import sys
from pathlib import Path

# Windows GBK 终端默认不能打印 emoji；统一把 stdout/stderr 切到 utf-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

# ── 配置 ──────────────────────────────────────
DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY")
if not DASHSCOPE_KEY:
    raise RuntimeError("请在 .env 中配置 DASHSCOPE_API_KEY（阿里云百炼 API Key）")
DASHSCOPE_URL = os.environ.get("DASHSCOPE_BASE_URL",
                                "https://dashscope.aliyuncs.com/compatible-mode/v1")

data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)
pdf_file = data_dir / "rag_intro.pdf"

# ── 0. 生成测试 PDF（如果没有）──────────────────
if not pdf_file.exists():
    print("📝 生成测试 PDF...")
    try:
        from fpdf import FPDF
    except ImportError:
        print("   安装 fpdf2...")
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "fpdf2", "-q"])
        from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    # ── 注册中文字体（Windows 自带，无需额外下载）──
    _cn_font_name = "Helvetica"  # 兜底：找不到中文字体时仍用英文
    _cn_font_candidates = [
        ("C:/Windows/Fonts/simhei.ttf", "SimHei"),       # 黑体
        ("C:/Windows/Fonts/msyh.ttc", "MicrosoftYaHei"), # 微软雅黑
        ("C:/Windows/Fonts/simsun.ttc", "SimSun"),       # 宋体
    ]
    for _path, _name in _cn_font_candidates:
        if Path(_path).exists():
            try:
                pdf.add_font(_name, "", _path)
                pdf.add_font(_name, "B", _path)
                _cn_font_name = _name
                print(f"   🔤 使用中文字体：{_path}")
                break
            except Exception:
                continue
    else:
        print("   ⚠️ 未找到系统中文字体，PDF 内容将使用英文")

    pdf.set_font(_cn_font_name, size=12)

    # 中文 PDF 内容
    content = [
        ("RAG（检索增强生成）— 技术概述", True),
        ("", False),
        ("RAG 全称 Retrieval-Augmented Generation（检索增强生成），是一种将大语言模型（LLM）"
         "与外部知识库相结合的技术，能生成更准确、更新及时的答案。", False),
        ("", False),
        ("核心流程 —— 三步走：", True),
        ("", False),
        ("第一步 · 检索（Retrieval）：当用户提问时，系统在向量数据库中搜索最相关的文档片段。"
         "这一步使用 Embedding 模型将文本转换为高维向量，并通过余弦相似度计算语义距离。", False),
        ("", False),
        ("第二步 · 增强（Augmentation）：将检索到的文档片段作为上下文插入 Prompt 中。"
         "这就是「增强」的含义——给 LLM 提供它从未训练过的外部知识。", False),
        ("", False),
        ("第三步 · 生成（Generation）：LLM 基于提供的上下文生成答案，"
         "而非依赖其参数化记忆。这能显著减少虚假生成（幻觉）。", False),
        ("", False),
        ("RAG 的三大核心优势：", True),
        ("1. 实时更新 —— 只需重新索引文档，无需重新训练整个模型。", False),
        ("2. 来源可追溯 —— 每个答案都可以引用具体的文档出处。", False),
        ("3. 数据安全 —— 知识库在本地运行，无需把敏感数据发给 LLM 提供商。", False),
        ("", False),
        ("RAG 架构组件生态：", True),
        ("- 文档加载器：TextLoader、PyPDFLoader、CSVLoader、UnstructuredLoader", False),
        ("- 文本分割器：RecursiveCharacterTextSplitter、SemanticChunker", False),
        ("- Embedding 模型：text-embedding-3、text-embedding-v3、Cohere", False),
        ("- 向量数据库：ChromaDB、FAISS、Pinecone、Weaviate、Milvus", False),
        ("- 大语言模型：GPT-4o、DeepSeek、Qwen、Claude、Gemini", False),
        ("", False),
        ("高级 RAG 技术一览：", True),
        ("- HyDE（假设文档嵌入）：先生成一个假设性答案，再用该答案去检索——提升召回率。", False),
        ("- Multi-Query（多查询）：生成多个查询变体，分别检索后合并结果。", False),
        ("- Reranker（重排序）：用二阶段排序模型对初步检索结果二次排序。", False),
        ("- Self-RAG（自反思检索）：LLM 自行判断每一步是否需要检索。", False),
        ("- Agentic RAG（智能体 RAG）：用 LangGraph 构建多步推理智能体，自主决策检索策略、"
         "工具调用和响应生成。", False),
    ]

    for text, is_title in content:
        if is_title:
            pdf.set_font(_cn_font_name, "B", 14)
        else:
            pdf.set_font(_cn_font_name, "", 12)
        pdf.multi_cell(w=0, h=8, text=text)
        if not text:
            pdf.ln(2)
        else:
            pdf.ln(3)

    pdf.output(str(pdf_file))
    print(f"   ✅ PDF 已生成：{pdf_file}")

# ── 1. 加载 PDF ──────────────────────────────────
loader = PyPDFLoader(str(pdf_file))
documents = loader.load()
print(f"✅ PDF 加载完成，共 {len(documents)} 页，{sum(len(d.page_content) for d in documents)} 字")

# ── 2. 文本切片 ──────────────────────────────────
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
chunks = splitter.split_documents(documents)
print(f"✅ 切片完成，共 {len(chunks)} 块 (chunk_size=500, overlap=80)")

# ── 3. 向量化 ────────────────────────────────────
# 避免新旧数据混在一起：每次重建均清空旧的向量库
import shutil
_persist_dir = "./.chroma_pdf_demo"
if Path(_persist_dir).exists():
    shutil.rmtree(_persist_dir)
    print("🧹 已清空旧的向量库")

embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key=DASHSCOPE_KEY,
)
vectorstore = Chroma.from_documents(
    chunks, embeddings,
    persist_directory=_persist_dir,
)
print("✅ 向量化完成（阿里 text-embedding-v3）")

# ── 4. 构建 RAG 链 ──────────────────────────────
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=DASHSCOPE_KEY,
    base_url=DASHSCOPE_URL,
    temperature=0.1,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

prompt = PromptTemplate(
    template="基于以下已知信息回答问题。\n"
             "已知信息：\n{context}\n\n"
             "问题：{question}\n\n"
             "回答：",
    input_variables=["context", "question"],
)

rag_chain = (
    {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)),
     "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# ── 5. 提问 ──────────────────────────────────────
questions = [
    "RAG 的核心流程有哪三步？",
    "RAG 相比直接问 LLM 有哪些优势？",
    "高级 RAG 技术有哪些？",
]

for q in questions:
    answer = rag_chain.invoke(q)
    print(f"\n{'─' * 50}")
    print(f"❓ 提问：{q}")
    print(f"🤖 回答：{answer[:300]}")

    docs = retriever.invoke(q)
    for i, doc in enumerate(docs):
        print(f"   📎 来源{i+1}：第{doc.metadata.get('page', '?')}页 | {doc.page_content[:60]}...")
