"""
FastAPI 后端 —— RAG 问答服务

启动：uvicorn main:app --reload
接口文档：http://127.0.0.1:8000/docs
"""
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_engine import RAGEngine

# ── Windows 终端 UTF-8 兼容 ──
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── 全局引擎实例（单例，跨请求复用 embedding/LLM）──
engine = RAGEngine()

# ── FastAPI 应用 ──
app = FastAPI(
    title="RAG Agent 问答服务",
    description="上传 PDF 文档，基于 RAG 进行智能问答。",
    version="0.1.0",
)

# CORS：允许 Streamlit 前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求/响应模型 ──
class ChatRequest(BaseModel):
    question: str

class FeedbackRequest(BaseModel):
    message:str
    score: int

class ChatResponse(BaseModel):
    answer: str
    sources: list


class UploadResponse(BaseModel):
    message: str
    pages: int
    chars: int
    chunks: int

class StatusResponse(BaseModel):
    has_doc: bool
    filename: str | None = None
    pages: int = 0
    chunks: int = 0
    chars: int = 0


# ── 路由 ──

@app.get("/")
def root():
    return {
        "service": "RAG Agent 问答服务",
        "status": "running",
        "docs": "/docs",
        "upload": "POST /upload  (multipart/form-data, file=your.pdf)",
        "chat": "POST /chat  (JSON: {\"question\": \"...\"})",
    }


@app.get("/status", response_model=StatusResponse)
def get_status():
    """查询引擎状态——是否已上传 PDF"""
    return StatusResponse(
        has_doc=engine.qa_chain is not None,
        filename=engine.filename,
        pages=engine.doc_count,
        chunks=engine.chunk_count,
        chars=engine.total_chars,
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    上传 PDF 文件 → 引擎自动加载、切片、向量化

    - **file**: PDF 文件（.pdf 格式）
    """
    # 校验文件类型
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, detail="仅支持 PDF 文件")

    # 保存上传文件到临时路径
    suffix = ".pdf"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = engine.load_and_index(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(500, detail=f"处理 PDF 失败：{str(e)}")

    # 清理临时文件
    os.unlink(tmp_path)

    # 记录文件名（engine 拿到的临时路径不是原名）
    engine.filename = file.filename

    return UploadResponse(
        message=f"✅ 已上传「{file.filename}」",
        pages=result["pages"],
        chars=result["chars"],
        chunks=result["chunks"],
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    提问（需先上传 PDF）

    - **question**: 你的问题
    """
    if not request.question.strip():
        raise HTTPException(400, detail="问题不能为空")

    try:
        result = engine.ask(request.question)
    except RuntimeError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"问答失败：{str(e)}")

    return ChatResponse(answer=result["answer"], sources=result["sources"])

@app.post("/feedback")
async def feedback(request: FeedbackRequest):
    return{"status": "ok",
           "received":request.message}

# ── 启动入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
