from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db import init_db

app = FastAPI(title="EdgeIQ API")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routes import props, ev, chat, bets  # noqa: E402
app.include_router(props.router)
app.include_router(ev.router)
app.include_router(chat.router)
app.include_router(bets.router)
