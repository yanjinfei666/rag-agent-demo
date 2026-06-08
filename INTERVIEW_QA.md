# RAG Agent 面试题积累

> 每天学完更新。按 Day 分类。
> **优先级标注：** ⭐⭐⭐＝必问  ⭐⭐＝高频  ⭐＝了解

---

## ✅ Day 1：基础 RAG Demo

| 优先级 | # | 问题 | 回答要点 |
|-------|---|------|---------|
| ⭐⭐⭐ | 1 | **RAG 和直接问 LLM 有什么区别？** | 直接问 LLM 靠训练时记住的知识，知识截止于训练日期、可能幻觉。RAG 先检索外部知识库，再让 LLM 基于检索内容回答，可追溯、实时更新、减少幻觉 |
| ⭐⭐⭐ | 2 | **为什么需要文本切片？切片策略有哪些？** | LLM 上下文窗口有限。三种策略：① RecursiveCharacterTextSplitter（按 `\n\n`→句号→字符逐级切）② 按段落切 ③ 语义切分。我用了第一种 |
| ⭐⭐⭐ | 3 | **向量检索怎么工作的？similarity search 原理？** | 文本→embedding 转高维向量→用户问题也转向量→搜余弦距离最近的 k 个向量→返回对应文本 |
| ⭐⭐⭐ | 4 | **chunk_size / k / temperature 各影响什么？** | chunk_size 控制每块信息量；k 控制召回块数；temperature 控制输出随机性。RAG 场景设低 temperature（0.1） |
| ⭐⭐ | 5 | **你用的什么 embedding 模型？为什么选它？** | 阿里 DashScope text-embedding-v3。因为 DeepSeek 无原生 embedding，阿里中文效果好，API 兼容 OpenAI 格式 |
| ⭐ | 6 | **LangChain 的 Document 是什么结构？** | 包含 `page_content`（正文）和 `metadata`（来源路径、页码等元信息）。切片、检索都基于这个对象 |

---

## ✅ Day 2：参数理解

| 优先级 | # | 问题 | 回答要点 |
|-------|---|------|---------|
| ⭐⭐⭐ | 1 | **chunk_size 设多大合适？** | 中文 200-500，英文 500-1000。取决于文档类型，短文档设小，长文档设大 |
| ⭐⭐ | 2 | **chunk_overlap 有什么用？设多少？** | 防止关键信息被切在边界上。一般设 chunk_size 的 10-20% |
| ⭐⭐⭐ | 3 | **k 值太大或太小有什么问题？** | 太小可能漏掉相关文档；太大会引入噪音，浪费 token。典型值 3-5 |
| ⭐⭐ | 4 | **temperature 为什么 RAG 场景设低？** | RAG 核心是准确检索+回答，不是创意生成。temperature 高会导致幻觉（编造事实） |
| ⭐⭐ | 5 | **PromptTemplate 是什么？推荐用什么？** | 填空模板。推荐 ChatPromptTemplate（system/human 角色消息，更适合对话模型） |

---

## ✅ Day 3：PDF 加载

| 优先级 | # | 问题 | 回答要点 |
|-------|---|------|---------|
| ⭐⭐ | 1 | **PyPDFLoader 和 TextLoader 的区别？** | PyPDFLoader 输入 PDF，每页一个 Document，metadata 带页码；TextLoader 输入 txt，整篇一个 Document |
| ⭐⭐ | 2 | **PDF 加载有什么潜在问题？怎么解决？** | ① **扫描件 PDF 本质是图片**→需 OCR（Tesseract）② **表格/双栏排版**提取乱序→可引入 LlamaParse ③ **页眉页脚干扰**→清洗 |
| ⭐ | 3 | **什么是"扫描件 PDF 没有文字层"？** | 电子 PDF 内部存字符编码，可选中/复制/搜索；扫描件 PDF 内部是一张图片 |
| ⭐⭐ | 4 | **为什么向量库要清空重建？** | Chroma 的 `from_documents` 默认**追加写入**。生产环境按文档版本号/ID 做 upsert |
| ⭐ | 5 | **Chroma 追加写入是 bug 吗？** | 不是，是设计特性——真实场景需要增量导入新文档 |
| ⭐⭐⭐ | 6 | **chunk_size 和 k 怎么配合？** | 先定 chunk_size 决定总块数，k 取总块数的 30-50% |
| ⭐ | 7 | **中文 PDF 生成怎么处理字体？** | fpdf2 内置字体不支持中文。用 Windows 系统字体自动检测 + 三级回退 |
| ⭐⭐⭐ | 8 | **为什么不用 DeepSeek embedding？** | DeepSeek 没有原生 embedding 模型 |

---

## ✅ Day 3 拓展：RAG 深度概念

| 优先级 | # | 问题 | 回答要点 |
|-------|---|------|---------|
| ⭐⭐⭐ | 1 | **Ragas 是什么？为什么需要它？** | RAG 评估框架。四指标：**Faithfulness**、**Context Precision**、**Context Recall**、**Answer Relevancy** |
| ⭐⭐⭐ | 2 | **Reranker 是什么？为什么需要它？** | 粗排（embedding）→ 精排（Cross-Encoder 逐条打分）→ 去噪音取前 3 |
| ⭐⭐ | 3 | **Reranker 和普通向量搜索比优缺点？** | 向量搜索快但精度一般；Reranker 精度高但慢。**先粗排再精排**是标准方案 |
| ⭐⭐ | 4 | **怎么证明你的优化有效？** | 用 Ragas 建 20 个测试 QA 对，跑分对比优化前后的 Faithfulness |
| ⭐ | 5 | **LangChain 的 Document 结构具体是什么样的？** | `Document(page_content="文本", metadata={"source": "xxx.pdf", "page": 1})` |

---

## ✅ Day 4：FastAPI 后端抽离

| 优先级 | # | 问题 | 回答要点 |
|-------|---|------|---------|
| ⭐⭐⭐ | 1 | **为什么要把 RAG 逻辑从脚本抽离成 RAGEngine 类？** | ① 可复用（同一引擎给 FastAPI/Streamlit/CLI 用）② 状态管理（embedding/LLM 跨请求复用）③ 可测试 ④ 解耦 |
| ⭐⭐⭐ | 2 | **FastAPI 相比 Flask 有什么优势？** | ① 异步原生 ② 自动 API 文档（Swagger UI）③ Pydantic 校验 ④ 性能（基于 Starlette） |
| ⭐⭐ | 3 | **为什么 engine 设计成全局单例？** | embedding 和 LLM 客户端是重量级对象，内部维护连接池和 tokenizer。全局单例跨请求复用 |
| ⭐⭐⭐ | 4 | **/upload 和 /chat 为什么设计成两步？路由职责怎么分的？** | **/upload**：写操作（接收 PDF→切片→向量化→建索引）。**/chat**：读操作（接收问题→检索→LLM 生成→返回答案+来源）。职责分离 |
| ⭐⭐ | 5 | **上传文件用 NamedTemporaryFile 有什么注意事项？** | ① `delete=False` 需要手动删 ② 必须校验后缀防恶意文件 ③ try/finally 保证清理 |
| ⭐⭐ | 6 | **CORS 是什么？为什么设 `allow_origins=["*"]`？** | 跨域资源共享——不同端口的前端不能调后端 API。设 `["*"]` 因为 Streamlit 在 8501 端口 |
| ⭐⭐ | 7 | **Pydantic 模型在这里起了什么作用？** | ① 请求校验 ② 响应格式化 ③ 自动生成 API 文档 |
| ⭐ | 8 | **FastAPI 怎么启动？接口文档在哪？** | `uvicorn main:app --reload` → `http://127.0.0.1:8000/docs` |
| ⭐ | 9 | **为什么持久化目录分`.chroma_demo`/`.chroma_pdf_demo`/`.chroma_rag`？** | 每个阶段用独立目录，避免向量库互相污染 |
| ⭐⭐ | 10 | **`_build_chain` 为什么每次 upload 都要重新构建？** | upload 后 vectorstore 和 retriever 都变了，LCEL 链引用了 retriever 对象，必须重建 |

---

## 📅 待学：Day 5 — Streamlit 对接

*学完更新*

---

## 📅 待学：Day 7 — Reranker

*学完更新*

---

## 📅 待学：Day 8 — HyDE

*学完更新*

---

## 📅 待学：Day 9-11 — LangGraph

*学完更新*

---

## 📅 待学：Day 12-14 — Agent 工具

*学完更新*

---

## 📅 待学：Day 15-16 — Memory

*学完更新*

---

## 📅 待学：Day 20-22 — 部署 + README

*学完更新*

---

> 📌 每天学完更新。⭐ 标注根据 JD 要求和面试高频度动态调整。
> **复习建议：** 优先掌握 ⭐⭐⭐ 和 ⭐⭐ 的题目，⭐ 的题有时间再看。
