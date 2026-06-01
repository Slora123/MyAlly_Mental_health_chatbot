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
- **Remembers past conversations** and maintains chat history for personalized, human-like interactions

### 📚 RAG-Based Responses
- **Uses ChromaDB** with verified resources to provide accurate and reliable guidance

### 🛡️ Real-time Crisis Escalation
- **Detects high-risk intent** and sends instant alerts to counselors via the web portal

### 🔒 Secure Authentication
- **Firebase + JWT-based login** ensuring user privacy and secure access

---

## 🛠️ Technology Stack

- **Backend:** FastAPI (Python), Uvicorn
- **Frontend:** React + Vite, CSS3 (Vanilla), React Router
- **AI/LLM:** HuggingFace Inference API (Qwen 2.5 7B Instruct)
- **Primary Database:** Google Firestore (Persistence)
- **RAG / Vector DB:** ChromaDB (Persistence & Memory)
- **Auth:** Firebase Authentication

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- Node.js & npm

### 2. Installation

**Backend Setup:**
```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
```

**Frontend Setup:**
```bash
cd frontend
npm install
```

### 3. Configuration (`.env`)
Create a **single `.env` file** in the project root with the following keys:

```env
# AI Brain
HUGGINGFACE_TOKEN="your_hf_token"

# Firebase (Frontend)
VITE_FIREBASE_API_KEY="..."
VITE_FIREBASE_AUTH_DOMAIN="..."
VITE_FIREBASE_PROJECT_ID="..."

# Firebase Admin (Backend)
FIREBASE_CREDENTIALS_PATH="firebase-key.json"
```

### 4. Build the RAG Index
Before running the app, index the empathy and knowledge datasets:
```bash
cd backend
python build_rag_index.py
```

### 5. Running the App
**Start Backend:**
```bash
cd backend
python -m src.app.chat_api
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

---

## 🧑‍💼 Admin Mode
To access the **Counselor Dashboard**, navigate to `/admin` in your browser. This panel allows professional counselors to monitor flagged crisis situations in real-time.

---

## 🔒 Security & Privacy
- **Privacy First:** The counselor cannot see your private chats unless a high-risk situation is detected by the AI.
- **Support-Only:** MyAlly is a support tool, not a clinical diagnosis or therapy service. Always consult a professional for medical advice.
