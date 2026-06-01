"""
backend/src/app/firestore_db.py
-------------------------------
Handles storing and retrieving user profiles, chat sessions, and messages in Google Firestore.
Provides persistence across deployments.
"""
from __future__ import annotations

import os
from datetime import datetime
from google.cloud import firestore
import firebase_admin
from firebase_admin import firestore as admin_firestore

_db = None

def get_db():
    global _db
    if _db is None:
        if not firebase_admin._apps:
            # This should have been initialized in auth.py
            # But we provide a fallback just in case
            print("⚠️ Firestore calling initialize_app (fallback)")
            firebase_admin.initialize_app()
        _db = admin_firestore.client()
    return _db

# ── User Profile Operations ───────────────────────────────────────────────────

def get_user_profile(uid: str) -> dict | None:
    db = get_db()
    doc = db.collection("user_profiles").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_user_profile(uid: str, profile_data: dict):
    db = get_db()
    
    # Merge with existing data if any
    existing = get_user_profile(uid)
    if existing:
        updated_data = {**existing, **profile_data}
    else:
        updated_data = {**profile_data, "uid": uid, "created_at": datetime.utcnow()}
    
    # Convert any nested dicts or objects if needed, but Firestore handles dicts well.
    db.collection("user_profiles").document(uid).set(updated_data)
    return updated_data

# ── Chat Session Operations ──────────────────────────────────────────────────

def create_chat_session(user_uid: str, title: str) -> dict:
    db = get_db()
    session_id = f"sess_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
    session_data = {
        "id": session_id,
        "user_uid": user_uid,
        "title": title,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    db.collection("chat_sessions").document(session_id).set(session_data)
    return session_data

def get_user_sessions(user_uid: str) -> list[dict]:
    db = get_db()
    docs = db.collection("chat_sessions").where("user_uid", "==", user_uid).stream()
    
    sessions = []
    for doc in docs:
        sessions.append(doc.to_dict())
    return sessions

def get_session(session_id: str, user_uid: str) -> dict | None:
    db = get_db()
    doc = db.collection("chat_sessions").document(session_id).get()
    if doc.exists:
        data = doc.to_dict()
        if data.get("user_uid") == user_uid:
            return data
    return None

# ── Message Operations ───────────────────────────────────────────────────────

def add_chat_message(session_id: str, role: str, content: str):
    db = get_db()
    msg_id = f"msg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
    message_data = {
        "id": msg_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    }
    db.collection("chat_history").document(msg_id).set(message_data)
    
    # Update session's updated_at
    db.collection("chat_sessions").document(session_id).update({
        "updated_at": datetime.utcnow()
    })
    return message_data

def get_chat_history(session_id: str) -> list[dict]:
    db = get_db()
    docs = db.collection("chat_history").where("session_id", "==", session_id).stream()
    
    messages = []
    for doc in docs:
        messages.append(doc.to_dict())
        
    # Sort in memory to avoid needing a composite index in Firestore
    messages.sort(key=lambda x: x.get("created_at"))
    return messages
