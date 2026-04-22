from typing import Literal

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .config import get_llm
from .state import AgentState
from .tools import get_tools

SYSTEM_PROMPT = """\
You are a helpful flight planner assistant. Your goal is to help users find flights
that best match their preferences for CO₂ emissions, price, and comfort level.

Available airports (IATA codes): CDG, LHR, JFK, LAX, AMS, FRA, BCN, MAD, DXB, SIN.

You have tools to:
- Search flights between airports
- Get details for a specific flight
- Compare and rank flights by price | co2 | comfort | balanced
- Look up users and their preferences
- Get personalized recommendations for a user
- Update a user's preferences

When presenting options to the user:
- Always mention price (€), CO₂ (kg), and comfort score (1–10) for each flight.
- Highlight direct vs connecting flights and explain the environmental trade-off.
- If you know the user's ID, fetch their preferences first to give tailored recommendations.
- Keep your answers concise and structured — a simple table or bullet list works well.
"""


def _should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "__end__"


def build_graph(api_base_url: str, provider: str = "anthropic"):
    """Compile a ReAct LangGraph agent wired to the flight planner API."""
    tools = get_tools(api_base_url)
    llm = get_llm(provider)
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def agent_node(state: AgentState) -> dict:
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return {"messages": [llm_with_tools.invoke(messages)]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue)
    graph.add_edge("tools", "agent")

    return graph.compile()
