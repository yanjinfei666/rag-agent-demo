"""
RAG 引擎 —— 封装加载/索引/问答逻辑，供 FastAPI / Streamlit 调用
"""
import os
import shutil
from pathlib import Path
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


class RAGEngine:
    """RAG 引擎：上传 PDF → 索引 → 问答"""

    def __init__(self):
        # ── 配置 ──
        self.dashscope_key = os.environ.get("DASHSCOPE_API_KEY")
        if not self.dashscope_key:
            raise RuntimeError("请在 .env 中配置 DASHSCOPE_API_KEY")
        self.dashscope_url = os.environ.get(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        # ── Embedding 模型（复用，不每次重建）──
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v3",
            dashscope_api_key=self.dashscope_key,
        )

        # ── LLM（复用）──
        self.llm = ChatOpenAI(
            model="qwen-plus",
            api_key=self.dashscope_key,
            base_url=self.dashscope_url,
            temperature=0.1,
        )

        # ── 状态（每次 upload 更新）──
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        self.doc_count = 0
        self.chunk_count = 0
        self.persist_dir = "./.chroma_rag"

    def load_and_index(self, pdf_path: str) -> dict:
        """
        加载 PDF → 切片 → 向量化 → 建检索器
        返回：{"pages": N, "chars": N, "chunks": N}
        """
        # 1. 加载 PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        pages = len(documents)
        chars = sum(len(d.page_content) for d in documents)

        # 2. 切片
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
        chunks = splitter.split_documents(documents)

        # 3. 清空旧向量库（避免新旧混合）
        if Path(self.persist_dir).exists():
            shutil.rmtree(self.persist_dir)

        # 4. 向量化
        self.vectorstore = Chroma.from_documents(
            chunks, self.embeddings,
            persist_directory=self.persist_dir,
        )

        # 5. 建检索器 + RAG 链
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        self._build_chain()

        # 6. 记录
        self.doc_count = pages
        self.chunk_count = len(chunks)

        return {"pages": pages, "chars": chars, "chunks": len(chunks)}

    def _build_chain(self):
        """构建 RAG 链（每次重建索引后更新）"""
        prompt = PromptTemplate(
            template="基于以下已知信息回答问题。\n"
                     "已知信息：\n{context}\n\n"
                     "问题：{question}\n\n"
                     "回答：",
            input_variables=["context", "question"],
        )
        self.rag_chain = (
            {"context": self.retriever
             | (lambda docs: "\n\n".join(d.page_content for d in docs)),
             "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def ask(self, question: str) -> dict:
        """
        问答
        返回：{"answer": str, "sources": [{"page": N, "content": str}, ...]}
        """
        if not self.rag_chain:
            raise RuntimeError("请先上传 PDF 文件")

        answer = self.rag_chain.invoke(question)

        docs = self.retriever.invoke(question)
        sources = [
            {
                "page": d.metadata.get("page", "?"),
                "content": d.page_content[:200],
            }
            for d in docs
        ]

        return {"answer": answer, "sources": sources}

    def clear(self):
        """清空索引"""
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        self.doc_count = 0
        self.chunk_count = 0
        if Path(self.persist_dir).exists():
            shutil.rmtree(self.persist_dir)
