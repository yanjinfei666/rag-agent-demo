"""
第1天 RAG Demo —— 5 秒跑通检索增强生成！

跑法：python demo_01_basic_rag.py
"""
import os

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

# ── 配置：阿里云 DashScope（通义千问）────────
DASHSCOPE_KEY = os.environ["DASHSCOPE_API_KEY"]
DASHSCOPE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# ── 1. 加载文档 ──────────────────────────────────
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)
sample_file = data_dir / "sample.txt"
sample_file.write_text(
    "DeepSeek 是一家中国 AI 公司，专注于大语言模型研发。"
    "DeepSeek-V3 是一款 671B 参数的 MoE 模型，训练成本仅 557 万美元。"
    "RAG（检索增强生成）是给 LLM 外接知识库的技术。"
    "LangChain 是构建 LLM 应用最流行的 Python 框架。"
    "ChromaDB 是一个轻量级的开源向量数据库。"
    "DeepSeek API 兼容 OpenAI 接口，开发者可以无缝切换。",
    encoding="utf-8",
)
loader = TextLoader(str(sample_file), encoding="utf-8")
documents = loader.load()
print(f"✅ 文档加载完成，{len(documents)} 篇")

# ── 2. 文本切片 ──────────────────────────────────
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=40)
chunks = splitter.split_documents(documents)
print(f"✅ 文档切片完成，共 {len(chunks)} 块")

# ── 3. 向量化 ────────────────────────────────────
# 阿里云通义千问嵌入模型（支持中文，效果好）
embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key=DASHSCOPE_KEY,
)
vectorstore = Chroma.from_documents(
    chunks, embeddings,
    persist_directory="./.chroma_demo",
)
print("✅ 向量化完成（阿里 text-embedding-v3）")

# ── 4. 构建 RAG 链 ──────────────────────────────
llm = ChatOpenAI(
    model="qwen-plus",          # 通义千问 qwen-plus，你也可换 qwen-turbo（更快）
    api_key=DASHSCOPE_KEY,
    base_url=DASHSCOPE_URL,
    temperature=0.9,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

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

# ── 5. 提问！ ──────────────────────────────────
questions = [
    "DeepSeek 是什么？",
    "RAG 是什么意思？",
    "DeepSeek-V3 有多少参数？",
]

for q in questions:
    answer = rag_chain.invoke(q)
    print(f"\n{'─' * 50}")
    print(f"❓ 提问：{q}")
    print(f"🤖 回答：{answer[:300]}")

    docs = retriever.invoke(q)
    for i, doc in enumerate(docs):
        print(f"   📎 来源{i+1}：{doc.page_content[:80]}...")
