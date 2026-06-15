"""
Day 10 LangGraph Agent —— 3 个工具：知识库搜索 + 联网搜索 + 计算器

跑法：
  先启动 FastAPI 后端（给 Agent 提供知识库搜索）：uvicorn main:app --reload
  再跑这个脚本：python demo_04_langgraph_tools.py
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
import requests


# ── 配置 LLM ──
llm = ChatOpenAI(
    model="qwen-max",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1,
)

API_BASE = "http://127.0.0.1:8000"


# ═══════════════════════════════════════════════════
# 1. 定义三个工具（Tool）
# ═══════════════════════════════════════════════════

@tool
def search_knowledge_base(query: str) -> str:
    """从已上传的知识库中搜索与问题相关的信息"""
    try:
        resp = requests.post(f"{API_BASE}/chat", json={"question": query})
        if resp.status_code == 200:
            data = resp.json()
            # 把答案和来源拼成一段文字返回给 Agent
            sources_text = ""
            for src in data.get("sources", []):
                sources_text += f"\n[第{src['page']}页] {src['content'][:150]}"
            return f"知识库回答：{data['answer'][:500]}\n参考来源：{sources_text[:500]}"
        else:
            return f"知识库搜索失败：{resp.text}"
    except requests.exceptions.ConnectionError:
        return "错误：无法连接到知识库后端，请先启动 uvicorn"


@tool
def search_web(query: str) -> str:
    """搜索互联网上的最新信息"""
    try:
        import warnings
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            raw = ddgs.text(query, max_results=3)
            results = list(raw)
        if not results:
            return "未找到相关结果"
        text = ""
        for r in results:
            text += f"\n【{r.get('title', '')}】\n{r.get('href', '')}\n{r.get('body', '')[:200]}\n"
        return text[:1500]
    except ImportError:
        return "错误：未安装 duckduckgo_search，请运行 pip install duckduckgo_search"
    except Exception as e:
        return f"联网搜索失败：{str(e)}"


@tool
def calculator(expression: str) -> str:
    """计算数学表达式，如 '1 + 2 * 3'"""
    try:
        # 只允许数字和运算符，防止恶意代码
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return "错误：表达式包含非法字符"
        result = eval(expression)
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算失败：{str(e)}"


# 收集所有工具
tools = [search_knowledge_base, search_web, calculator]

# 给 LLM 绑定工具
from langchain_core.messages import SystemMessage

# 系统指令：每个工具最多用一次，用完直接回答
TOOL_SYSTEM_PROMPT = SystemMessage(content=(
    '你是中文助手。严格遵循以下规则：\n'
    '1. 每个工具最多调用一次，不要重复调用同一个工具\n'
    '2. 拿到工具返回的结果后，直接基于结果回答用户\n'
    '3. 如果工具返回空结果或错误，直接告诉用户暂时找不到相关信息'
))

llm_with_tools = llm.bind_tools(tools)


# ═══════════════════════════════════════════════════
# 2. 定义 State
# ═══════════════════════════════════════════════════
class AgentState(TypedDict):
    messages: list      # 对话历史（HumanMessage / AIMessage）
    steps: list         # 执行记录（用于展示）


# ═══════════════════════════════════════════════════
# 3. 定义节点（Node）
# ═══════════════════════════════════════════════════
def call_model(state: AgentState) -> AgentState:
    """LLM 思考：决定直接回答还是调用工具"""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)

    # 记录 LLM 的决定
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_names = [t["name"] for t in response.tool_calls]
        step_log = f"🔧 LLM 决定调用工具：{', '.join(tool_names)}"
    else:
        step_log = f"💬 LLM 决定直接回答"

    return {
        "messages": messages + [response],
        "steps": state["steps"] + [step_log],
    }


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """判断：LLM 想要调用工具还是直接结束"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"    # 有工具调用 → 去执行工具
    return "end"          # 没有工具调用 → 直接结束


def execute_tools(state: AgentState) -> AgentState:
    """执行 LLM 请求的工具调用"""
    last_message = state["messages"][-1]
    tool_map = {t.name: t for t in tools}

    for tc in last_message.tool_calls:
        fn = tool_map.get(tc["name"])
        if not fn:
            continue
        result = fn.invoke(tc["args"])

        # 手动构造 ToolMessage，确保 tool_call_id 正确
        state["messages"].append(ToolMessage(
            content=result,
            tool_call_id=tc["id"],
        ))
        state["steps"].append(f"🔨 执行 {tc['name']} 完成")

    return state


# ═══════════════════════════════════════════════════
# 4. 构建图
# ═══════════════════════════════════════════════════
workflow = StateGraph(AgentState)

# 注册节点
workflow.add_node("agent", call_model)          # Agent 思考节点
workflow.add_node("tools", execute_tools)       # 手动工具执行节点

# 设置入口
workflow.set_entry_point("agent")

# 条件边：Agent 决定下一步
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END},
)

# 执行完工具后回到 Agent 继续思考
workflow.add_edge("tools", "agent")

# 编译（限制最多 5 步，防止死循环）
app = workflow.compile()
app.recursion_limit = 5


# ═══════════════════════════════════════════════════
# 5. 测试
# ═══════════════════════════════════════════════════
def ask(question: str):
    """提问并显示 Agent 的思考过程"""
    print(f"\n{'='*60}")
    print(f"❓ 用户：{question}")
    print(f"{'='*60}")

    try:
        result = app.invoke(
            {"messages": [TOOL_SYSTEM_PROMPT, HumanMessage(content=question)], "steps": []},
            config={"recursion_limit": 8},
        )
    except Exception as e:
        print(f"\n❌ 执行出错：{str(e)[:200]}")
        return

    print(f"\n📋 执行记录：")
    for s in result["steps"]:
        print(f"   {s}")

    final_answer = result["messages"][-1].content
    print(f"\n🤖 Agent 回答：{final_answer}")


if __name__ == "__main__":
    # 先装依赖
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("安装 duckduckgo_search...")
        os.system("pip install duckduckgo_search -q")
        print("安装完成\n")

    # 测试三个场景
    ask("计算 1 + 2 乘以 3 等于多少？")
    ask("你的名字叫什么？你是谁开发的？")
    ask("Python 的列表和元组有什么区别？")
