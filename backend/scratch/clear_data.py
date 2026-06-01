import os
import json
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# 1. Clear SQL Database (Chat Sessions & Messages)
DB_PATH = Path(__file__).resolve().parents[1] / "myally.db"
if DB_PATH.exists():
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Delete messages first due to foreign key
        if "chat_messages" in metadata.tables:
            messages = metadata.tables["chat_messages"]
            db.execute(messages.delete())
        
        if "chat_sessions" in metadata.tables:
            sessions = metadata.tables["chat_sessions"]
            db.execute(sessions.delete())
            
        db.commit()
        print("✅ Cleared chat_messages and chat_sessions tables.")
    except Exception as e:
        print(f"❌ Error clearing SQL tables: {e}")
        db.rollback()
    finally:
        db.close()
else:
    print("ℹ️ No sqlite database found to clear.")

# 2. Clear Crisis Alerts JSON
ALERTS_FILE = Path(__file__).resolve().parents[2] / "database" / "crisis_alerts.json"
if ALERTS_FILE.exists():
    try:
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        print("✅ Cleared crisis_alerts.json.")
    except Exception as e:
        print(f"❌ Error clearing alerts file: {e}")
else:
    print("ℹ️ No alerts file found to clear.")

print("\n✨ Database has been reset. You can start fresh now!")
