"""
src/app/chat_api.py
────────────────────
FastAPI backend for MyAlly chat.
Serves the static HTML/CSS/JS frontend and exposes a /chat POST endpoint.
"""
from __future__ import annotations

from pathlib import Path

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
from typing import Optional

from src.app.service import chat_logic
from src.app.auth import get_current_user, get_admin_user
from . import vector_db, firestore_db
from .encryption import encrypt_text, decrypt_text

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="MyAlly Mental-Health Support", lifespan=lifespan)

# Serve everything inside frontend/dist
_STATIC_DIR = Path(__file__).resolve().parents[3] / "frontend" / "dist"

class OnboardingRequest(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    preferred_tone: Optional[str] = None
    support_style: Optional[str] = None
    lifestyle_patterns: Optional[str] = None
    support_network: Optional[str] = None
    education: Optional[str] = None
    avatar_url: Optional[str] = None
    bot_avatar_url: Optional[str] = None

    class Config:
        extra = "allow"



from src.app.auth import _firebase_ready

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "firebase_initialized": _firebase_ready,
        "firestore_connected": firestore_db._db is not None
    }

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None # If None, creates a new session

# ── User API ──────────────────────────────────────────────────────────────
@app.get("/api/user/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return user

@app.post("/api/user/onboarding")
async def save_onboarding(req: OnboardingRequest, user: dict = Depends(get_current_user)):
    profile_data = req.model_dump(exclude_unset=True)
    updated_user = firestore_db.save_user_profile(user["uid"], profile_data)
    # Also save to vector_db for RAG context (local/ephemeral but useful for current session)
    vector_db.save_user_profile(user["uid"], profile_data)
    return {"status": "success", "user": updated_user}

# ── Chat API ──────────────────────────────────────────────────────────────

@app.get("/api/chats")
async def get_chat_sessions(user: dict = Depends(get_current_user)):
    sessions = firestore_db.get_user_sessions(user["uid"])
    # Sort descending by updated_at
    # Firestore timestamps need to be handled
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    return {"sessions": sessions}

@app.get("/api/chats/all")
async def get_all_chats(user: dict = Depends(get_current_user)):
    sessions = firestore_db.get_user_sessions(user["uid"])
    all_messages = []
    latest_session_id = None
    
    # Sort sessions by updated_at to find the latest
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    if sessions:
        latest_session_id = sessions[0]["id"]
        
    for s in sessions:
        msgs = firestore_db.get_chat_history(s["id"])
        # Decrypt each message before adding to the response
        decrypted_msgs = [
            {**m, "content": decrypt_text(m["content"])}
            for m in msgs
        ]
        all_messages.extend(decrypted_msgs)
        
    # Sort all messages chronologically
    all_messages.sort(key=lambda x: x["created_at"])
    
    return {
        "session_id": latest_session_id,
        "messages": all_messages
    }

@app.get("/api/chats/{session_id}")
async def get_chat_history(session_id: str, user: dict = Depends(get_current_user)):
    session = firestore_db.get_session(session_id, user["uid"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    raw_messages = firestore_db.get_chat_history(session_id)
    # Decrypt each message before sending to the frontend
    messages = [
        {**m, "content": decrypt_text(m["content"])}
        for m in raw_messages
    ]
    return {"session_id": session_id, "title": session["title"], "messages": messages}

@app.post("/chat")
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    print(f"📥 Received chat request: {req}")
    try:
        if not req.session_id:
            # Create new session
            title = "Chat: " + req.message[:20] + "..." if len(req.message) > 20 else "Chat: " + req.message
            session = firestore_db.create_chat_session(user["uid"], title)
            session_id = session["id"]
            # Mirror in vector_db
            vector_db.create_chat_session(user["uid"], title, session_id=session_id)
        else:
            session_id = req.session_id
            session = firestore_db.get_session(session_id, user["uid"])
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

        # Save user message to Firestore (PRIMARY, encrypted) and ChromaDB (RAG, plaintext for semantic search)
        firestore_db.add_chat_message(session_id, role="user", content=encrypt_text(req.message))
        vector_db.add_chat_message(session_id, role="user", content=req.message)

        # Build history format expected by logic: list of [user_msg, bot_msg] pairs
        # We use Firestore for the chat history context to be robust
        full_history = [
            {**m, "content": decrypt_text(m["content"])}
            for m in firestore_db.get_chat_history(session_id)
        ]
        
        history_pairs: list[list[str | None]] = []
        current_pair: list[str | None] = [None, None]
        # Exclude the message we just added for the 'history' argument to chat_logic
        for m in full_history[:-1]: 
            if m["role"] == "user":
                if current_pair[0] is not None:
                    history_pairs.append(current_pair)
                    current_pair = [None, None]
                current_pair[0] = m["content"]
            elif m["role"] == "bot":
                current_pair[1] = m["content"]
                history_pairs.append(current_pair)
                current_pair = [None, None]
        if current_pair[0] is not None or current_pair[1] is not None:
            history_pairs.append(current_pair)

        # Call logic
        reply = chat_logic(req.message, history_pairs, user_profile=user, today=datetime.now(timezone.utc))
        
        # Save bot message to Firestore (encrypted) and ChromaDB (plaintext for RAG)
        firestore_db.add_chat_message(session_id, role="bot", content=encrypt_text(reply))
        vector_db.add_chat_message(session_id, role="bot", content=reply)
        
        return {"reply": reply, "session_id": session_id}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        # TEMPORARY DEBUG: Return the actual error as the bot reply so we can see what crashed!
        return {"reply": f"🤖 CRASH LOG: {str(exc)}", "session_id": req.session_id or "error"}


# ── Admin/Counselor Endpoints ──────────────────────────────────────────────

@app.get("/api/admin/alerts")
async def get_alerts(admin: dict = Depends(get_admin_user)):
    """Fetches all crisis alerts for the counselor. Requires authorised counselor login."""
    from src.app import counselor_service
    alerts = counselor_service.get_all_alerts()
    return {"alerts": alerts}


@app.post("/api/admin/resolve/{alert_id}")
async def resolve_alert(alert_id: str, admin: dict = Depends(get_admin_user)):
    """Marks a crisis alert as resolved. Requires authorised counselor login."""
    from src.app import counselor_service
    success = counselor_service.resolve_alert(alert_id)
    if success:
        return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Alert not found"})


# Serve frontend/dist files
@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    # Try to serve specific file (like login-mockup.png)
    full_path = _STATIC_DIR / file_path
    if full_path.exists() and full_path.is_file():
        return FileResponse(str(full_path))
    
    # Otherwise fallback to index.html (SPA support)
    return FileResponse(str(_STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)















