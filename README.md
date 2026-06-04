---
title: MyAlly
emoji: 🛡️
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
---

# MyAlly: A Premium AI Mental-Health Companion 🛡️✨

**MyAlly** is a state-of-the-art, empathy-aware mental health support chatbot designed specifically for students. It utilizes **Retrieval-Augmented Generation (RAG)** to provide grounded, verified support combined with a personalized memory layer and a robust crisis escalation protocol.

---

## 🌟 Key Features

### 🤝 Empathetic Chat Interface
- **Acts like a supportive friend** with a professional, empathetic tone
- **Understands Hinglish/Minglish** and simple English
- **Glassmorphism UI** with mood-based themes that change automatically based on user message keywords

### 🧠 Context Awareness & Memory
- **Dual-layer memory architecture:** Full encrypted chat history in Firestore + high-level semantic memories in ChromaDB for long-term context (RAG)
- **Instant chat loading:** Profile and chat history cached in localStorage for zero-flicker return visits

### 📚 RAG-Based Responses
- **Uses ChromaDB** with verified empathy and knowledge documents to provide accurate and reliable guidance

### 🛡️ Real-time Crisis Escalation
- **Detects high-risk intent** and sends instant alerts to counselors via the web portal
- Crisis alerts are stored in Firestore (`crisis_alerts` collection) and persist across server restarts

### 🔒 Secure Authentication & Encryption
- **Firebase + JWT-based login** ensuring user privacy and secure access
- **AES-256 chat encryption:** All messages are encrypted server-side using Fernet (AES-128-CBC + HMAC-SHA256) before being stored in Firestore. The frontend never sees raw ciphertext.

---

## 🏗️ Architecture

```
┌──────────────────────┐       ┌─────────────────────────┐
│  Vercel (Frontend)   │──────▶│  HF Spaces (Backend)    │
│  React + Vite        │  API  │  FastAPI + Uvicorn       │
└──────────────────────┘       └───────────┬─────────────┘
                                           │
                    ┌──────────────────────┼─────────────────────┐
                    ▼                      ▼                     ▼
           ┌──────────────┐      ┌──────────────────┐   ┌──────────────┐
           │   Firestore  │      │    ChromaDB       │   │  HF Inference│
           │  (Encrypted  │      │  (RAG / Semantic  │   │  API (Qwen   │
           │  Chat Logs)  │      │   Memory)         │   │  2.5 7B)     │
           └──────────────┘      └──────────────────┘   └──────────────┘
```

---

## 🛠️ Technology Stack

| Layer          | Technology                                          |
|----------------|-----------------------------------------------------|
| **Frontend**   | React + Vite, Vanilla CSS, React Router             |
| **Backend**    | FastAPI (Python), Uvicorn                           |
| **LLM**        | HuggingFace Inference API (Qwen 2.5 7B Instruct)   |
| **Auth**       | Firebase Authentication (Google OAuth + JWT)        |
| **Primary DB** | Google Firestore (encrypted persistent chat logs)   |
| **RAG / Memory** | ChromaDB (local vector embeddings)               |
| **Encryption** | AES-256 Fernet (cryptography library)               |
| **Deployment** | Vercel (frontend) + HF Spaces via Docker (backend)  |

---

## 🚀 Running Locally

### 1. Prerequisites
- Python 3.9+
- Node.js & npm

### 2. Clone & Install

**Backend:**
```bash
cd /path/to/MyAlly
/Library/Developer/CommandLineTools/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Configuration (`.env`)
Create a **single `.env` file** in the project root:

```env
# AI Brain
HUGGINGFACE_TOKEN=your_hf_token

# Firebase (Frontend)
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...

# Firebase Admin (Backend)
FIREBASE_CREDENTIALS_PATH=firebase-key.json
DEBUG_AUTH=false

# Encryption Key for Chat History (AES-256 Fernet)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
CHAT_ENCRYPTION_KEY=your_generated_key
```

### 4. Running the App

**Option A — One command (recommended for testing):**
```bash
bash start.sh
```
Builds the frontend and starts the backend at **http://localhost:8000**.

**Option B — Separate processes (recommended for development, hot-reload):**

Terminal 1 (Backend):
```bash
source .venv/bin/activate
PYTHONPATH=backend uvicorn src.app.chat_api:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```
Frontend available at **http://localhost:5173**, API proxied to port 8000.

---

## ☁️ Deployment

| Component  | Platform      | Notes                                                                |
|------------|---------------|----------------------------------------------------------------------|
| Frontend   | Vercel        | Auto-deploys from `main` branch. No backend secrets needed.         |
| Backend    | HF Spaces     | Docker-based. Add `CHAT_ENCRYPTION_KEY` as a **Secret** in Space settings (Settings → Variables and secrets). |

---

## 🧑‍💼 Admin Mode
To access the **Counselor Dashboard**, navigate to `/admin` in your browser. This panel allows professional counselors to monitor flagged crisis situations in real-time. Crisis alerts are stored persistently in Firestore and survive server restarts.

---

## 🔒 Security & Privacy
- **End-to-end encrypted storage:** All chat messages are encrypted with AES-256 before being stored in Firestore. The encryption key lives only in backend environment secrets — never in source code or the frontend.
- **Privacy First:** Counselors cannot see your private chats unless a high-risk crisis situation is detected by the AI.
- **Support-Only:** MyAlly is a support tool, not a clinical diagnosis or therapy service. Always consult a professional for medical advice.
