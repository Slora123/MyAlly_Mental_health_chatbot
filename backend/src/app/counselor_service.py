"""
backend/src/app/counselor_service.py
────────────────────────────────────
Handles storing and retrieving crisis alerts for the counselor dashboard.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Path to the internal alerts database
DB_DIR = Path(__file__).resolve().parents[3] / "database"
ALERTS_FILE = DB_DIR / "crisis_alerts.json"

def _ensure_db_exists():
    """Ensure the database directory and alerts file exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if not ALERTS_FILE.exists():
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def save_crisis_alert(summary: str, user_info: str, trigger_message: str):
    """
    Saves a crisis alert to the internal JSON database.
    
    Parameters
    ----------
    summary         : The AI-generated crisis summary.
    user_info       : The user's name and contact details.
    trigger_message : The specific user message that triggered the alert.
    """
    _ensure_db_exists()
    
    alert_entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "timestamp": datetime.now().isoformat(),
        "user_info": user_info,
        "summary": summary,
        "trigger_message": trigger_message,
        "status": "unread", # read, unread, resolved
        "severity": "high_risk"
    }
    
    try:
        with open(ALERTS_FILE, "r+", encoding="utf-8") as f:
            alerts = json.load(f)
            alerts.insert(0, alert_entry) # Add to the top
            f.seek(0)
            json.dump(alerts, f, indent=4)
            f.truncate()
        print(f"✅ Crisis alert saved internally for {user_info}")
    except Exception as e:
        print(f"❌ Failed to save internal crisis alert: {e}")

def get_all_alerts():
    """Returns all crisis alerts from the database."""
    _ensure_db_exists()
    try:
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def resolve_alert(alert_id: str):
    """Marks an alert as resolved."""
    _ensure_db_exists()
    try:
        with open(ALERTS_FILE, "r+", encoding="utf-8") as f:
            alerts = json.load(f)
            for alert in alerts:
                if alert["id"] == alert_id:
                    alert["status"] = "resolved"
                    break
            f.seek(0)
            json.dump(alerts, f, indent=4)
            f.truncate()
        return True
    except Exception:
        return False
