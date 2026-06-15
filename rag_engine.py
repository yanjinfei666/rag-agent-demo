"""
RAG 引擎 —— 封装加载/索引/问答逻辑，供 FastAPI / Streamlit 调用

Day 7 升级：加入 BGE Reranker（Cross-Encoder 精排）
"""
import os
import shutil
from pathlib import Path

# HF 国内镜像（下载 BGE 模型用）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
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

        # ── Reranker 配置 ──
        self.use_reranker = True
        self.recall_k = 8              # 粗召回数量（给 reranker 更大的候选池）
        self.final_k = 3               # 精排后保留数量
        self.reranker_model = None     # 懒加载，第一次 upload 时才下载

        # ── 状态（每次 upload 更新）──
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
        self.filename = None
        self.doc_count = 0
        self.chunk_count = 0
        self.total_chars = 0
        self.persist_dir = ""

    # ════════════════════════════════════════════════════
    # Reranker 懒加载（首次使用才下载模型 ~300MB）
    # ════════════════════════════════════════════════════
    def _get_reranker(self):
        """懒加载 BGE Reranker 模型（Cross-Encoder）"""
        if self.reranker_model is None and self.use_reranker:
            from sentence_transformers import CrossEncoder
            self.reranker_model = CrossEncoder(
                "BAAI/bge-reranker-base",
                automodel_args={"torch_dtype": "float32"},
            )
        return self.reranker_model

    # ════════════════════════════════════════════════════
    # 索引
    # ════════════════════════════════════════════════════
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

        # 3. 每次用唯一目录，避免 Windows SQLite 文件锁
        import uuid
        self.persist_dir = f"./.chroma_rag/{uuid.uuid4().hex[:12]}"
        self.vectorstore = Chroma.from_documents(
            chunks, self.embeddings,
            persist_directory=self.persist_dir,
        )

        # 5. 建检索器（recall_k 不能超过总块数）
        retrieve_k = self.recall_k if self.use_reranker else self.final_k
        retrieve_k = min(retrieve_k, len(chunks))
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": retrieve_k}
        )

        # 6. 构建 QA 链（不含检索器，检索在 ask() 里做）
        self._build_chain()

        # 7. 触发 Reranker 模型下载（首次上传时）
        if self.use_reranker:
            self._get_reranker()

        # 8. 记录
        self.filename = Path(pdf_path).name
        self.doc_count = pages
        self.chunk_count = len(chunks)
        self.total_chars = chars

        return {"pages": pages, "chars": chars, "chunks": len(chunks)}

    def _build_chain(self):
        """构建 QA 链（输入 {context, question} → 输出 answer）"""
        prompt = PromptTemplate(
            template="基于以下已知信息回答问题。\n"
                     "已知信息：\n{context}\n\n"
                     "问题：{question}\n\n"
                     "回答：",
            input_variables=["context", "question"],
        )
        self.qa_chain = (
            prompt | self.llm | StrOutputParser()
        )

    # ════════════════════════════════════════════════════
    # 问答（Day 7 核心：检索 → 精排 → 生成）
    # ════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════
    # HyDE：先生成假设答案，再用假设答案去检索
    # ════════════════════════════════════════════════════
    def _generate_hypothetical(self, question: str) -> str:
        """用 LLM 生成一个假设性的理想答案"""
        hyde_prompt = PromptTemplate.from_template(
            "你是一位领域专家。请针对以下问题，写一段详细的、专业的回答。\n"
            "要求：回答要尽可能完整、包含具体细节、使用专业术语。\n"
            "注意：你不需要检索任何资料，直接基于你的知识写一段假设性的回答。\n\n"
            "问题：{question}\n\n"
            "假设性回答："
        )
        chain = hyde_prompt | self.llm | StrOutputParser()
        return chain.invoke({"question": question})

    # ════════════════════════════════════════════════════
    # 问答（Day 7 核心：检索 → 精排 → 生成）
    # ════════════════════════════════════════════════════
    def ask(self, question: str) -> dict:
        """
        问答（含 HyDE + Reranker）

        流程：
          ① 生成假设答案（HyDE）
          ② 用假设答案进行向量检索 → 粗召回 N 块
          ③ Cross-Encoder 打分 → 精排取 top K
          ④ 拼成 context → LLM 生成回答
        """
        if not self.qa_chain:
            raise RuntimeError("请先上传 PDF 文件")

        # ── ① HyDE：生成假设答案 → 用假设答案检索（比原始问题召回更准）──
        hyde_query = self._generate_hypothetical(question)

        # ── ② 向量检索（粗召回）──
        docs = self.retriever.invoke(hyde_query)

        # ── ② Reranker 精排（可选）──
        if self.use_reranker and self.reranker_model and len(docs) > self.final_k:
            # 构造 (question, doc) 对
            pairs = [(question, d.page_content) for d in docs]
            # Cross-Encoder 逐对打分
            scores = self.reranker_model.predict(pairs)
            # 按分数降序排列
            scored = sorted(
                zip(scores, docs),
                key=lambda x: x[0],
                reverse=True,
            )
            # 取 top K
            docs = [d for _, d in scored[:self.final_k]]

        # ── ③ 拼 context → 生成 ──
        context = "\n\n".join(d.page_content for d in docs)
        answer = self.qa_chain.invoke({"context": context, "question": question})

        # ── ④ 构建来源信息 ──
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
        self.qa_chain = None
        self.filename = None
        self.doc_count = 0
        self.chunk_count = 0
        self.total_chars = 0
        if Path(self.persist_dir).exists():
            shutil.rmtree(self.persist_dir)
