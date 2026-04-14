import anthropic
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.config import ANTHROPIC_API_KEY
from backend.ai.prompt import build_system_prompt, build_suggested_chips

router = APIRouter(prefix="/chat", tags=["chat"])
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ChatRequest(BaseModel):
    message: str
    prop_context: dict
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]


class ChipsRequest(BaseModel):
    prop_context: dict


@router.post("/chips")
def get_chips(payload: ChipsRequest):
    return {"chips": build_suggested_chips(payload.prop_context)}


@router.post("")
def stream_chat(payload: ChatRequest):
    system = build_system_prompt(payload.prop_context)
    # Filter out empty-content messages (e.g. from failed prior streams) to
    # avoid Anthropic rejecting the request with a 400 invalid_request_error.
    clean_history = [m for m in payload.history if m.get("content", "").strip()]
    messages = [*clean_history, {"role": "user", "content": payload.message}]

    def generate():
        try:
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {text}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {e}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
