"""
hf_backend/src/app/counselor_service.py
────────────────────────────────────────
Handles storing and retrieving crisis alerts for the counselor dashboard.

PRODUCTION FIX:
  Previously used a local 'database/crisis_alerts.json' file, which was wiped
  on every Hugging Face Space restart — causing silent data loss of crisis alerts.

  Now delegates entirely to Firestore via firestore_db module.
  Crisis alerts persist across restarts, survive deployments, and support
  real-time onSnapshot listeners in the counselor dashboard frontend.

  Crisis data is stored UNENCRYPTED in Firestore — counselors must be able
  to read it immediately without any decryption step.
"""
from __future__ import annotations

import logging
from src.app import firestore_db

logger = logging.getLogger(__name__)


def save_crisis_alert(summary: str, user_info: str, trigger_message: str) -> None:
    """
    Save a crisis alert so counselors can act on it.

    Delegates to firestore_db.save_crisis_alert() which writes to the
    Firestore 'crisis_alerts' collection. Survives server restarts.

    Parameters
    ----------
    summary         : AI-generated summary of the crisis severity.
    user_info       : User's name + contact details (for counselor to reach out).
    trigger_message : The exact user message that triggered the crisis detection.
    """
    try:
        alert_id = firestore_db.save_crisis_alert(
            summary=summary,
            user_info=user_info,
            trigger_message=trigger_message,
        )
        logger.info(f"✅ [counselor_service] Crisis alert saved (id={alert_id}) for: {user_info}")
    except Exception as e:
        logger.error(f"❌ [counselor_service] Failed to save crisis alert: {e}")


def get_all_alerts() -> list[dict]:
    """
    Fetch all crisis alerts for the counselor dashboard, newest first.
    Reads from Firestore 'crisis_alerts' collection.
    """
    try:
        return firestore_db.get_all_alerts()
    except Exception as e:
        logger.error(f"❌ [counselor_service] Failed to fetch alerts: {e}")
        return []


def resolve_alert(alert_id: str) -> bool:
    """
    Mark a crisis alert as resolved.
    Updates the Firestore document status to 'resolved'.

    Parameters
    ----------
    alert_id : The Firestore document 'id' field of the alert.

    Returns
    -------
    True if the alert was found and updated, False otherwise.
    """
    try:
        return firestore_db.resolve_alert(alert_id)
    except Exception as e:
        logger.error(f"❌ [counselor_service] Failed to resolve alert {alert_id}: {e}")
        return False
