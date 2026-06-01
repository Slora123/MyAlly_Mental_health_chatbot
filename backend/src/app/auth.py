import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from . import vector_db, firestore_db

# Load Firebase credentials
from dotenv import load_dotenv
from pathlib import Path

root_env = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=root_env)

firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
firebase_cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

if not firebase_admin._apps:
    if firebase_cred_json:
        # Use JSON string directly from env variable (Good for Render)
        import json
        import base64
        try:
            # Check if it's base64 encoded; if not, load normally
            try:
                decoded_json = base64.b64decode(firebase_cred_json).decode('utf-8')
                cred_dict = json.loads(decoded_json)
            except Exception:
                cred_dict = json.loads(firebase_cred_json)
                
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("🔐 Initialized Firebase using FIREBASE_CREDENTIALS_JSON")
            firebase_cred_path = "env_json" # Mark as configured
        except Exception as e:
            print(f"❌ Error parsing FIREBASE_CREDENTIALS_JSON: {e}")
    
    elif firebase_cred_path:
        # Resolve path
        if not os.path.isabs(firebase_cred_path):
            # Try root of project first
            root_path = Path(__file__).resolve().parents[2]
            possible_path = root_path / firebase_cred_path
            if possible_path.exists():
                firebase_cred_path = str(possible_path)
            else:
                # Try relative to current file's parent's parent (backend/)
                firebase_cred_path = os.path.join(root_path, firebase_cred_path)
        
        if os.path.exists(firebase_cred_path):
            print(f"🔐 Initializing Firebase with file: {firebase_cred_path}")
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred)
        else:
            print(f"⚠️ WARNING: Firebase credentials file NOT found at: {firebase_cred_path}")
            firebase_cred_path = None
    else:
        print("⚠️ WARNING: No Firebase configuration found (Path or JSON)")

security = HTTPBearer()

_firebase_ready = bool(firebase_admin._apps)

if _firebase_ready:
    print("✅ Firebase Admin SDK is initialized. Real token verification is ACTIVE.")
else:
    print("❌ CRITICAL: Firebase Admin SDK is NOT initialized.")
    print("   ➡ Per-user chat isolation will NOT work.")
    print("   ➡ Fix: Download firebase-key.json from Firebase Console → Project Settings → Service Accounts.")
    print("   ➡ Place it at the project root and ensure FIREBASE_CREDENTIALS_PATH=firebase-key.json in .env")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Hard DEBUG_AUTH bypass (must be explicitly set to "true")
    if os.getenv("DEBUG_AUTH", "false").lower() == "true":
        print("⚠️  DEBUG_AUTH is ENABLED - Bypassing authentication! All users are 'debug-user'.")
        return {"uid": "debug-user", "email": "debug@example.com", "name": "Debug User"}

    # Reject immediately if Firebase is not initialized
    if not firebase_admin._apps:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Firebase Admin SDK is not initialized on the server. "
                "Place firebase-key.json in the project root and restart."
            ),
        )

    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token, clock_skew_seconds=60)
        uid = decoded_token["uid"]
        print(f"✅ Auth verified for uid: {uid} ({decoded_token.get('email', 'no email')})")

        user = firestore_db.get_user_profile(uid)
        if not user:
            # First-time login: create a profile for this user
            email = decoded_token.get("email", "")
            name = decoded_token.get("name", "Anonymous")
            print(f"👤 New user detected. Creating profile for: {email}")
            user = firestore_db.save_user_profile(uid, {"uid": uid, "email": email, "name": name})

        return user
    except auth.InvalidIdTokenError as e:
        print(f"🔐 Invalid Token Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
        )
    except Exception as e:
        print(f"💥 Internal Server Error during auth profile creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch or create user profile: {str(e)}",
        )
