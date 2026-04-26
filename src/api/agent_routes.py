import asyncio
import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import BaseModel

router = APIRouter(prefix="/agent", tags=["agent"])

# Lazy-initialised singleton so the graph and checkpointer survive across requests.
_checkpointer: Optional[MemorySaver] = None
_graph: Any = None

# Per-thread resume signals: set by POST /agent/{thread_id}/resume
_resume_events: dict[str, asyncio.Event] = {}
_resume_values: dict[str, Any] = {}


def _get_graph():
    global _checkpointer, _graph
    if _graph is None:
        import os
        from src.agent.graph import build_graph
        _checkpointer = MemorySaver()
        _graph = build_graph(
            api_base_url="http://localhost:8000",
            provider=os.getenv("AGENT_PROVIDER", "huggingface"),
            checkpointer=_checkpointer,
        )
    return _graph


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AgentRunRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    thread_id: Optional[str] = None


class ResumeRequest(BaseModel):
    approved: bool = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/run")
async def run_agent(request: AgentRunRequest):
    """Start or continue an agent thread and stream its execution as Server-Sent Events."""
    thread_id = request.thread_id or str(uuid.uuid4())
    return StreamingResponse(
        _stream_agent(thread_id, request.query, request.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/{thread_id}/resume")
async def resume_agent(thread_id: str, request: ResumeRequest):
    """Signal the waiting SSE stream to resume after a human-review checkpoint."""
    if thread_id not in _resume_events:
        return {"error": "Thread not found or not currently paused"}
    _resume_values[thread_id] = {"approved": request.approved}
    _resume_events[thread_id].set()
    return {"status": "resumed", "thread_id": thread_id}


# ---------------------------------------------------------------------------
# SSE streaming logic
# ---------------------------------------------------------------------------

def _sse(event_type: str, data: Any) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _stream_agent(thread_id: str, query: str, user_id: Optional[str]):
    graph = _get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    # Tell the client its thread_id so it can call /resume later.
    yield _sse("start", {"thread_id": thread_id})

    user_content = query
    if user_id:
        user_content = f"[User context: user_id={user_id}]\n{query}"

    input_data: Any = {"messages": [HumanMessage(content=user_content)], "user_id": user_id}

    while True:
        try:
            async for event in graph.astream_events(input_data, config=config, version="v2"):
                payload = _convert_event(event)
                if payload:
                    yield _sse(payload["type"], payload)
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})
            return

        # After the stream ends, check whether the graph paused on an interrupt.
        state = await graph.aget_state(config)
        pending = [
            intr.value
            for task in state.tasks
            for intr in task.interrupts
        ]

        if pending:
            # Notify client of the checkpoint.
            yield _sse("interrupt", {"thread_id": thread_id, "checkpoints": pending})

            # Park the SSE connection until the client calls /resume.
            evt = asyncio.Event()
            _resume_events[thread_id] = evt
            await evt.wait()
            _resume_events.pop(thread_id, None)
            resume_val = _resume_values.pop(thread_id, {"approved": True})

            # Next iteration resumes the graph from the checkpoint.
            input_data = Command(resume=resume_val)
        else:
            # Graph ran to completion.
            break

    yield _sse("done", {"thread_id": thread_id})


def _convert_event(event: dict) -> Optional[dict]:
    """Map a LangGraph astream_events payload to a simplified SSE payload."""
    kind = event.get("event", "")
    name = event.get("name", "")
    data = event.get("data", {})

    if kind == "on_tool_start":
        return {
            "type": "tool_start",
            "tool": name,
            "input": data.get("input", {}),
        }

    if kind == "on_tool_end":
        output = data.get("output", "")
        if hasattr(output, "content"):
            output = output.content
        return {
            "type": "tool_end",
            "tool": name,
            "output": str(output)[:1000],
        }

    if kind == "on_chat_model_stream":
        chunk = data.get("chunk")
        if chunk and hasattr(chunk, "content") and chunk.content:
            return {"type": "token", "content": chunk.content}

    return None
