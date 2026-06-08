"""
Day 6：FastAPI 基础
实现 GET/POST 路由、路径参数、查询参数、Pydantic 数据校验
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uvicorn

# ============ 1. 创建 FastAPI 应用 ============
app = FastAPI(
    title="学生管理系统 API",
    description="Day 6 FastAPI 学习项目",
    version="1.0.0"
)


# ============ 2. Pydantic 数据模型 ============
class StudentCreate(BaseModel):
    """创建学生的请求体模型"""
    name: str = Field(..., min_length=1, max_length=20, description="学生姓名")
    age: int = Field(..., ge=15, le=30, description="年龄（15-30）")
    grade: str = Field(..., description="年级")
    score: float = Field(default=0.0, ge=0, le=100, description="分数（0-100）")
    
    # 示例数据（会显示在Swagger UI中）
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "张三",
                    "age": 20,
                    "grade": "大三",
                    "score": 90.5
                }
            ]
        }
    }


class StudentResponse(BaseModel):
    """学生信息响应模型"""
    id: int
    name: str
    age: int
    grade: str
    score: float
    level: str
    create_time: str


class APIResponse(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


# ============ 3. 模拟数据库 ============
students_db: List[dict] = []
student_id_counter = 0


def get_level(score):
    """根据分数计算等级"""
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 60:
        return "及格"
    return "不及格"


# ============ 4. API 路由 ============

@app.get("/")
async def root():
    """根路径 - 服务信息"""
    return {
        "service": "学生管理系统",
        "version": "1.0.0",
        "docs": "http://127.0.0.1:8000/docs"
    }


@app.get("/students", response_model=List[StudentResponse])
async def get_students(
    min_score: Optional[float] = Query(None, ge=0, le=100, description="最低分数筛选"),
    grade: Optional[str] = Query(None, description="按年级筛选"),
    limit: int = Query(10, ge=1, le=100, description="返回条数限制")
):
    """
    获取学生列表
    - 支持按最低分数筛选
    - 支持按年级筛选
    - 支持限制返回条数
    """
    result = students_db.copy()
    
    # 按分数筛选
    if min_score is not None:
        result = [s for s in result if s["score"] >= min_score]
    
    # 按年级筛选
    if grade:
        result = [s for s in result if s["grade"] == grade]
    
    # 限制条数
    result = result[:limit]
    
    return result


@app.get("/students/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int):
    """
    根据ID获取单个学生信息
    - student_id: 路径参数，学生ID
    """
    for student in students_db:
        if student["id"] == student_id:
            return student
    
    raise HTTPException(status_code=404, detail=f"学生ID {student_id} 不存在")


@app.post("/students", response_model=APIResponse)
async def create_student(student: StudentCreate):
    """
    创建新学生
    - 请求体：StudentCreate 模型
    - 自动校验数据格式
    """
    global student_id_counter
    student_id_counter += 1
    
    new_student = {
        "id": student_id_counter,
        "name": student.name,
        "age": student.age,
        "grade": student.grade,
        "score": student.score,
        "level": get_level(student.score),
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    students_db.append(new_student)
    
    return APIResponse(
        code=201,
        message="创建成功",
        data=new_student
    )


@app.delete("/students/{student_id}", response_model=APIResponse)
async def delete_student(student_id: int):
    """删除学生"""
    for i, student in enumerate(students_db):
        if student["id"] == student_id:
            deleted = students_db.pop(i)
            return APIResponse(
                message=f"已删除学生: {deleted['name']}",
                data=deleted
            )
    
    raise HTTPException(status_code=404, detail=f"学生ID {student_id} 不存在")


@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    if not students_db:
        return {"message": "暂无学生数据"}
    
    scores = [s["score"] for s in students_db]
    return {
        "总人数": len(students_db),
        "平均分": round(sum(scores) / len(scores), 1),
        "最高分": max(scores),
        "最低分": min(scores),
        "及格率": f"{sum(1 for s in scores if s >= 60) / len(scores) * 100:.1f}%"
    }


# ============ 5. 启动配置 ============
if __name__ == "__main__":
    # 启动服务
    # host="127.0.0.1" 只允许本机访问
    # port=8000 端口号
    # reload=True 代码修改后自动重载
    uvicorn.run(
        "day6_fastapi_basic:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
