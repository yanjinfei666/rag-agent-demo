# RAG Agent 面试题积累

> 每天学完更新。按 Day 分类，前面打 ✅ 表示已掌握。

---

## ✅ Day 1：基础 RAG Demo

| # | 问题 | 回答要点 |
|---|------|---------|
| 1 | **RAG 和直接问 LLM 有什么区别？** | 直接问 LLM 靠训练时记住的知识，知识截止于训练日期、可能幻觉。RAG 先检索外部知识库，再让 LLM 基于检索内容回答，可追溯、实时更新、减少幻觉 |
| 2 | **为什么需要文本切片？切片策略有哪些？** | LLM 上下文窗口有限。三种策略：① RecursiveCharacterTextSplitter（按 `\n\n`→句号→字符逐级切）② 按段落切 ③ 语义切分。我用了第一种 |
| 3 | **向量检索怎么工作的？similarity search 原理？** | 文本→embedding 转高维向量→用户问题也转向量→搜余弦距离最近的 k 个向量→返回对应文本 |
| 4 | **chunk_size / k / temperature 各影响什么？** | chunk_size 控制每块信息量；k 控制召回块数；temperature 控制输出随机性。RAG 场景设低 temperature（0.1） |
| 5 | **你用的什么 embedding 模型？为什么选它？** | 阿里 DashScope text-embedding-v3。因为 DeepSeek 无原生 embedding，阿里中文效果好，API 兼容 OpenAI 格式 |
| 6 | **LangChain 的 Document 是什么结构？** | 包含 `page_content`（正文）和 `metadata`（来源路径、页码等元信息）。切片、检索都基于这个对象 |

---

## ✅ Day 2：参数理解

| # | 问题 | 回答要点 |
|---|------|---------|
| 1 | **chunk_size 设多大合适？** | 中文 200-500，英文 500-1000。取决于文档类型，短文档设小，长文档设大 |
| 2 | **chunk_overlap 有什么用？设多少？** | 防止关键信息被切在边界上。一般设 chunk_size 的 10-20% |
| 3 | **k 值太大或太小有什么问题？** | 太小可能漏掉相关文档；太大会引入噪音，浪费 token。典型值 3-5 |
| 4 | **temperature 为什么 RAG 场景设低？** | RAG 核心是准确检索+回答，不是创意生成。temperature 高会导致幻觉（编造事实） |
| 5 | **PromptTemplate 是什么？推荐用什么？** | 填空模板。把 context+question 拼成固定格式发给 LLM。推荐 ChatPromptTemplate（system/human 角色消息，更适合对话模型） |

---

## ✅ Day 3：PDF 加载

| # | 问题 | 回答要点 |
|---|------|---------|
| 1 | **PyPDFLoader 和 TextLoader 的区别？** | PyPDFLoader 输入 PDF，每页一个 Document，metadata 带页码；TextLoader 输入 txt，整篇一个 Document。加载 PDF 后可以追溯回答来源在哪一页 |
| 2 | **PDF 加载有什么潜在问题？怎么解决？** | ① **扫描件 PDF 本质是图片**，PyPDFLoader 提取为空→需 OCR（Tesseract）② **表格/双栏排版**提取乱序→可引入 LlamaParse ③ **页眉页脚干扰**→清洗 |
| 3 | **什么是"扫描件 PDF 没有文字层"？** | 电子 PDF 内部存字符编码，可选中/复制/搜索；扫描件 PDF 内部是一张图片，看着有文字但实际不可选中、Ctrl+F 搜不到、PyPDFLoader 读出来是空字符串 |
| 4 | **为什么向量库要清空重建？** | Chroma 的 `from_documents` 默认**追加写入**。多次跑不同版本的内容会混入新旧数据，导致检索结果矛盾。生产环境按文档版本号/ID 做 upsert，不是每次都清空 |
| 5 | **Chroma 追加写入是 bug 吗？** | 不是，是设计特性——真实场景需要增量导入新文档。Demo 阶段因为反复改同一份文档内容才需要清空。生产环境用 upsert（存在即更新，不存在即插入） |
| 6 | **chunk_size 和 k 怎么配合？** | 先定 chunk_size 决定总块数，k 取总块数的 30-50%。例如 993 字 chunk_size=500 切出 3 块，k=2~3 就够；5000 字切出 10 块，k=3~5。**块少 k 不超总块数，块多 k 不超 5-8** |
| 7 | **中文 PDF 生成怎么处理字体？** | fpdf2 内置字体不支持中文。用 Windows 系统字体（simhei/msyh/simsun）自动检测 + 三级回退，全找不到则用 Helvetica 英文兜底 |
| 8 | **为什么不用 DeepSeek embedding？** | DeepSeek 没有原生 embedding 模型 |

---

## ✅ Day 3 拓展：RAG 深度概念

| # | 问题 | 回答要点 |
|---|------|---------|
| 1 | **Ragas 是什么？为什么需要它？** | RAG 评估框架。你改参数/加 Reranker 后，说"我感觉变好了"没用，必须有数据。Ragas 算四个核心指标：**Faithfulness（忠实度）**、**Context Precision（上下文精度）**、**Context Recall（上下文召回）**、**Answer Relevancy（答案相关性）** |
| 2 | **Reranker 是什么？为什么需要它？** | 向量搜索（余弦相似度）只是粗排，"跟 RAG 有关"的内容都离得近，会混入噪音。Reranker 用 Cross-Encoder 对检索结果逐条打分，去噪音后排前 3-5 块给 LLM。流程：**粗排（embedding 搜 10 块）→ 精排（Reranker 打分取前 3）** |
| 3 | **Reranker 和普通向量搜索比优缺点？** | 向量搜索快（毫秒级），但精度一般；Reranker 精度更高，但慢一点（每块几十毫秒）。所以**先粗排再精排**是标准方案 |
| 4 | **怎么证明你的优化有效？** | 用 Ragas 建 20 个测试 QA 对，跑分对比。比如基础 RAG 的 Faithfulness 0.65，加 Reranker 后升到 0.82。面试官看到数据直接点头 |
| 5 | **LangChain 的 Document 结构具体是什么样的？** | `Document(page_content="文本内容", metadata={"source": "xxx.pdf", "page": 1})`。切片后每个小块仍然是 Document，继承原来的 metadata（页码保留） |

---

## 📅 待学：Day 4 — FastAPI 后端抽离

*学完更新*

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

> 📌 每天学完一个 Day，我自动更新这个文件，新增当天的面试题+答案。
