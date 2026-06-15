"""
Day 9 LangGraph 入门 —— 最简单的"思考→回答"循环

跑法：python demo_03_langgraph_basic.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


# ── 配置 LLM（复用你已有的阿里云 DashScope）──
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1,
)


# ═══════════════════════════════════════════════════
# 1. 定义状态（State）
# ═══════════════════════════════════════════════════
class AgentState(TypedDict):
    """Agent 的"脑子"——所有节点共享的数据"""
    question: str      # 用户输入的问题
    answer: str        # LLM 生成的回答
    steps: list        # 执行记录（用来打印过程）


# ═══════════════════════════════════════════════════
# 2. 定义节点（Node）
# ═══════════════════════════════════════════════════
def think_node(state: AgentState) -> AgentState:
    """节点1：思考——调 LLM 生成回答"""
    print(f"🤔  思考中... 问题：{state['question']}")
    response = llm.invoke([HumanMessage(content=state["question"])])
    answer = response.content
    return {
        "answer": answer,
        "steps": state["steps"] + [f"LLM 思考完成，生成了 {len(answer)} 字的回答"],
    }

def end_node(state: AgentState) -> AgentState:
    """节点2：结束——整理结果"""
    print(f"✅  回答完成")
    # 不做任何修改，直接返回当前状态
    return state


# ═══════════════════════════════════════════════════
# 3. 构建图（Graph）
# ═══════════════════════════════════════════════════
# 创建图，指定状态结构
workflow = StateGraph(AgentState)

# 注册两个节点
workflow.add_node("think", think_node)    # 思考节点
workflow.add_node("end", end_node)        # 结束节点

# 设置入口：第一个执行的节点
workflow.set_entry_point("think")

# 设置边：think → end（思考完就结束）
workflow.add_edge("think", "end")

# 编译成可执行的应用
app = workflow.compile()


# ═══════════════════════════════════════════════════
# 4. 运行
# ═══════════════════════════════════════════════════
questions = [
    "LangGraph 是什么？用一句话解释",
    "1+1 等于几？",
]

for q in questions:
    print(f"\n{'='*50}")
    print(f"❓ 问题：{q}")

    result = app.invoke({
        "question": q,
        "answer": "",
        "steps": [],
    })

    print(f"🤖 回答：{result['answer'][:200]}")
    print(f"📋 执行记录：")
    for i, step in enumerate(result["steps"], 1):
        print(f"   {i}. {step}")
