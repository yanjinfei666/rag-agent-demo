"""
Day 11 LangGraph Memory —— 多轮对话记忆
Agent 能记住用户之前说了什么
"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
import requests, uuid

llm = ChatOpenAI(
    model="qwen-max",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1,
)

API_BASE = "http://127.0.0.1:8000"

# ── 工具 ──
@tool
def search_knowledge_base(query: str) -> str:
    """从知识库搜索信息"""
    try:
        resp = requests.post(f"{API_BASE}/chat", json={"question": query}, timeout=5)
        return f"知识库：{resp.json().get('answer', '无结果')[:400]}" if resp.ok else "搜索失败"
    except: return "知识库未连接"

@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    allowed = set("0123456789+-*/()., ")
    if not all(c in allowed for c in expression): return "非法字符"
    return f"结果：{eval(expression)}"

tools = [search_knowledge_base, calculator]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = SystemMessage(content="你是中文助手。每个工具最多用一次。记住用户说过的话。")


# ── Annotated State ── 通过 add_messages 追加，而非覆盖
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# ── 函数 ──
def call_model(state: AgentState) -> AgentState:
    resp = llm_with_tools.invoke(state["messages"])
    return {"messages": [resp]}

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last = state["messages"][-1]
    return "tools" if (hasattr(last, "tool_calls") and last.tool_calls) else "end"

def execute_tools(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    for tc in last.tool_calls:
        fn = {t.name: t for t in tools}.get(tc["name"])
        if fn: state["messages"].append(ToolMessage(content=fn.invoke(tc["args"]), tool_call_id=tc["id"]))
    return state

# ── 编译 ──
wf = StateGraph(AgentState)
wf.add_node("agent", call_model)
wf.add_node("tools", execute_tools)
wf.add_edge(START, "agent")
wf.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
wf.add_edge("tools", "agent")
app = wf.compile(checkpointer=MemorySaver())


# ── 对话 ──
def chat(question: str, thread_id: str):
    print(f"\n❓ {question}")
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 8}
    result = app.invoke({"messages": [HumanMessage(content=question)]}, config=cfg)
    ans = result["messages"][-1].content
    print(f"🤖 {ans}")
    return ans


# ── 测试 ──
if __name__ == "__main__":
    sid = "session-001"

    # 第一轮：告诉 Agent 名字
    chat("我叫小明，是一名程序员", sid)
    # 第二轮：问名字
    chat("我叫什么名字？", sid)
    # 第三轮：问职业
    chat("我的职业是什么？", sid)
    # 第四轮：计算
    chat("1+2乘以3等于几？", sid)
    # 第五轮：问刚才算的什么
    chat("刚才你算的表达式是什么？", sid)

    # 新会话：不记得
    print(f"\n{'='*40}\n新会话：")
    chat("我叫什么名字？", "session-002")
