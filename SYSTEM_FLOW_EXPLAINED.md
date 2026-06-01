# MyAlly Complete System Flow Explained

## Overview
MyAlly is an **AI-powered empathetic chatbot for Indian students** using **RAG (Retrieval-Augmented Generation)** combined with **empathy-based responses** and safety checks. It's a full-stack application with a React frontend and Python FastAPI backend.

---

## Part 1: What is RAG?

### RAG = Retrieval-Augmented Generation

**RAG** is an AI technique that combines:
- **Retrieval**: Searching a database for relevant information
- **Augmented**: Adding that information to the AI prompt
- **Generation**: Using LLM to generate a response informed by the retrieved data

**Without RAG**: LLM generates based only on its training data (hallucinations, outdated info)
**With RAG**: LLM generates based on actual retrieved context (accurate, grounded, source-aware)

### MyAlly's RAG Architecture

```
Vector Database (Chroma) 
    ↓
┌────────────────────────────────┐
│  Empathy Collection (6 examples) │
│  - Real student emotions        │
│  - Coping mechanisms            │
│  - Validation strategies        │
└────────────────────────────────┘

┌────────────────────────────────┐
│  Knowledge Collection (3 facts)  │
│  - Mental health facts          │
│  - Treatment information        │
│  - Coping techniques            │
└────────────────────────────────┘
```

---

## Part 2: What is Empathy in MyAlly?

### Empathy = Understanding + Validation + Support

MyAlly uses **empathy retrieval** to:

1. **Find similar emotional experiences** from a database of 600+ student support dialogues
2. **Retrieve context on how others coped** with the same emotions
3. **Use that to make AI responses feel human** - not robotic

### Empathy vs. Knowledge
- **Empathy**: "I get it, others felt this way too, here's how they dealt..."
- **Knowledge**: "Depression is characterized by... here's the treatment..."

MyAlly uses BOTH together, kept separate in the prompt so the LLM knows which to use when.

---

## Part 3: User Input → Frontend Capture

### Step 1: User Interaction in Browser

```jsx
// File: frontend/src/App.jsx
1. User types in the input field
   └─ "I feel so stressed with exams..."

2. User presses Enter or clicks Send button
   └─ handleSendMessage() is triggered

3. Message is stored in React state
   └─ setMessages([...prev, userMsg])

4. Input field is cleared
   └─ setInputText('')

5. Theme detection runs
   └─ detectThemeFromText(text)  // Changes UI theme based on emotion
```

### Code Example:
```javascript
const handleSendMessage = async (textOverride) => {
  const text = textOverride || inputText;
  
  // Add user message to chat UI immediately
  const userMsg = { role: 'user', text: text, time: new Date() };
  setMessages((prev) => [...prev, userMsg]);
  setInputText('');
  setIsTyping(true);  // Show typing indicator
  
  // Send to backend
  const response = await fetch('/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`  // User's auth token
    },
    body: JSON.stringify({ 
      message: text,           // User's message
      session_id: sessionId     // Which conversation
    }),
  });
  
  // Wait for bot response...
  const data = await response.json();
  const botMsg = { role: 'bot', text: data.reply };
  setMessages((prev) => [...prev, botMsg]);
  setIsTyping(false);
};
```

### Frontend → Backend Flow:
```
User Input
    ↓
handleSendMessage()
    ↓
fetch('/chat', POST)
    ├─ Headers: Authorization Bearer token
    ├─ Body: { message: "...", session_id: "..." }
    ↓
Backend API Receives Request
```

---

## Part 4: Backend Receives & Processes Message

### Step 2: FastAPI Endpoint Receives Message

```python
# File: backend/src/app/chat_api.py

@app.post("/chat")
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Receives user message and returns bot reply
    """
    # 1. Authenticate user
    user_id = user["uid"]
    
    # 2. Create or get chat session
    if not req.session_id:
        # First message - create new session
        session = vector_db.create_chat_session(user_id, title="Chat: ...")
        session_id = session["id"]
    else:
        session_id = req.session_id
    
    # 3. Save user message to database
    vector_db.add_chat_message(session_id, role="user", content=req.message)
    
    # 4. Get chat history (all previous user-bot exchanges)
    full_history = vector_db.get_chat_history(session_id)
    
    # 5. Call the RAG pipeline
    reply = chat_logic(
        req.message,           # Current user message
        history_pairs,         # List of [user, bot] pairs
        user_profile=user,     # User's profile (name, preferences)
        today=datetime.utcnow()
    )
    
    # 6. Save bot reply to database
    vector_db.add_chat_message(session_id, role="bot", content=reply)
    
    # 7. Return to frontend
    return {"reply": reply, "session_id": session_id}
```

---

## Part 5: RAG & Empathy Pipeline Execution

### Step 3: RAG Pipeline - The Heart of MyAlly

```python
# File: backend/src/app/service.py

def chat_logic(user_message: str, history: list, user_profile, today) -> str:
    """
    The complete RAG pipeline:
    1. Safety check (pre-generation)
    2. Intent classification
    3. Empathy retrieval
    4. Knowledge retrieval (conditional)
    5. Prompt assembly
    6. LLM generation
    7. Safety check (post-generation)
    8. Logging
    """
```

### Detailed Pipeline Steps:

#### **STEP 1: Pre-Generation Safety Check**
```python
# File: backend/src/rag/safety.py

is_safe, _ = safety.check_pre_generation(user_message)
intent = router.classify_intent(user_message)

# Check for crisis keywords: "kill myself", "suicide", "self harm", etc.
# If HIGH RISK detected:
#   ├─ Escalate to crisis protocol
#   ├─ Evaluate severity with LLM
#   ├─ Save crisis alert for counselor
#   └─ Return immediate support response
#
# If SAFE:
#   └─ Continue to retrieval step
```

#### **STEP 2: Intent Classification**
```python
# File: backend/src/rag/router.py

intent = router.classify_intent(user_message)
# Returns one of:
# - "high_risk"      → Suicide/self-harm signals
# - "knowledge_seeking" → "What is depression?" type questions
# - "mixed"          → "I'm stressed AND want tips on coping"
# - "support_only"   → "I feel so alone and overwhelmed..."

# This determines what to retrieve:
if intent in ["support_only", "mixed"]:
    retriever.retrieve_empathy_snippets()  # Get empathy examples

if intent in ["knowledge_seeking", "mixed"]:
    retriever.retrieve_knowledge_snippets() # Get facts
```

#### **STEP 3: Empathy Retrieval** ⭐ (Key to MyAlly's warmth)
```python
# File: backend/src/rag/retriever.py

# Vector Database Setup:
empathy_collection = chromadb.get_collection("student_support_empathy")
knowledge_collection = chromadb.get_collection("student_support_knowledge")

# EMPATHY RETRIEVAL PROCESS:
# ─────────────────────────

candidates = query_collection(
    collection=empathy_collection,
    query_text=user_message,
    n_results=6  # Get top 6 candidates
)
# How it works:
# 1. User message is converted to vector using embedding model
# 2. Model: all-MiniLM-L6-v2 (sentence transformer)
# 3. Search Chroma for 6 most similar empathy examples
# 4. Each result includes:
#    - Document: The actual support text
#    - Metadata: { source, mechanism, emotion, quality_score }
#    - Distance: How semantically similar (lower = better)

# RERANKING (Step 9.4 - Advanced):
# ────────────────────────────────
selected = _rerank_empathy(candidates, top_n=3)
# Reranking scores by:
# 1. quality_score (higher = better)
# 2. semantic distance (lower = better)
# 3. Source diversity (max 2 from same source)
# Returns: Top 3 BEST empathy examples

# EXAMPLE RETRIEVED EMPATHY BLOCK:
"""
1. [Reddit | Validation] I understand you feel overwhelmed...
2. [EmpatheticDialogues | Active listening] That sounds really tough...
3. [Student Support | Coping mechanism] Have you tried taking breaks...
"""
```

#### **STEP 4: Knowledge Retrieval** (Conditional)
```python
# File: backend/src/rag/retriever.py

if intent in ["knowledge_seeking", "mixed"]:
    knowledge_snippets = retrieve_knowledge_snippets(
        collection=knowledge_collection,
        query_text=user_message,
        n_results=3  # Get top 3 facts
    )
    # Returns mental health facts, treatments, coping strategies
    # Kept SEPARATE from empathy in prompt (important!)
```

#### **STEP 5: Prompt Assembly**
```python
# File: backend/src/rag/prompt_builder.py

# Build the message list for the LLM:

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT  # See below
    },
    {
        "role": "user",
        "content": f"""
        User's message: {user_message}
        
        EMPATHY CONTEXT (how others felt & coped):
        {render_empathy_context(empathy_examples)}
        
        KNOWLEDGE CONTEXT (mental health facts):
        {render_knowledge_context(knowledge_examples)}
        
        Conversation history: {history}
        User profile: {user_profile}
        """
    }
]

# SYSTEM PROMPT (Makes AI sound like a real friend):
"""
You are MyAlly -- a warm, genuine, and chill friend for Indian students.
Your personality:
- You talk like a REAL PERSON, not a therapist or helpdesk
- EMOJIS ARE MANDATORY: 1-2 emojis per message naturally
- LANGUAGE MATCHING: 
  * English input → reply in PURE English (no mixing)
  * Marathi Minglish → reply in Marathi Minglish (e.g., "kasa ahes?")
  * Hindi/Hinglish → reply in Hindi/Hinglish
- MAX 2 sentences + 1 emoji (SHORT replies like real texting)
- DO NOT over-empathize or ask multiple follow-up questions
- When stressed: 1 validation + 1 actionable task + emoji

Example:
  User (English): "I'm so stressed with exams"
  You: "Yaar, exams are tough but you've got this 💪 Take a break, grab some chai, and come back fresh 🍵"
"""
```

#### **STEP 6: LLM Generation** 🤖
```python
# File: backend/src/app/service.py

client = InferenceClient(
    model="Qwen/Qwen2.5-7B-Instruct",
    token=HUGGINGFACE_TOKEN
)

response = client.text_generation(
    prompt=formatted_prompt,
    max_new_tokens=256,
    temperature=0.7,  # Balanced: creative but consistent
)

bot_reply = response  # E.g., "Yaar, I hear you... 😔"
```

**What the LLM sees:**
```
[System]: You are MyAlly, a warm Indian friend...

[User Context]:
- Their message: "I feel so alone"
- Empathy examples: 3 real cases where others felt alone + how they coped
- Knowledge facts: info on loneliness, coping techniques
- History: past conversation context
- Profile: their name, preferences, support style

[Generate response using ALL this context]
```

#### **STEP 7: Post-Generation Safety Check**
```python
# File: backend/src/rag/safety.py

is_safe, issues = safety.check_post_generation(bot_reply)

# Blocks if bot tries to:
# ✗ Diagnose: "you have depression"
# ✗ Prescribe meds: "stop your medication"
# ✗ Be dismissive: "just get over it"
# ✗ Make false certainty: "this will definitely cure you"
# ✗ Unsafe advice: "you don't need a therapist"

# If unsafe patterns detected:
#   └─ Regenerate with safety guardrails enforced
```

#### **STEP 8: Logging & Database**
```python
# Save for analytics:
app_logging.append_log({
    "user_query": user_message,
    "ai_response": bot_reply,
    "intent": intent,
    "retrieved_empathy_ids": [...],
    "retrieved_knowledge_ids": [...],
    "timestamp": datetime.now()
})

# Store in message history for context in future conversations
vector_db.add_chat_message(session_id, role="bot", content=bot_reply)
```

---

## Part 6: Response Returns to User

### Step 4: Backend Returns Reply to Frontend

```python
# Backend sends back:
return {
    "reply": "Yaar, I hear you 😔 Take a 5-min break & grab some tea ☕",
    "session_id": "abc123xyz"
}
```

### Step 5: Frontend Displays Response

```javascript
// Frontend receives the response
const data = await response.json();

// Create bot message object
const botMsg = {
    role: 'bot',
    text: data.reply,
    time: new Date().toISOString()
};

// Add to chat messages state
setMessages((prev) => [...prev, botMsg]);

// Hide typing indicator
setIsTyping(false);

// Message automatically appears in chat UI via MessageBubble component
// Theme updates if emotion detected
// Chat scrolls to bottom automatically
```

### Frontend Display:
```
┌─────────────────────────────────┐
│         MyAlly Chat             │
├─────────────────────────────────┤
│                                 │
│  👤 I feel so stressed...       │
│                                 │
│              🤖 Yaar, I hear you!│
│                 Take a break ☕ │
│                                 │
│  [Input field] [Send button]    │
└─────────────────────────────────┘
```

---

## Complete Flow Diagram

```
FRONTEND                          BACKEND
─────────────────────────────────────────────────────────────

User Input
   ↓
React State: setMessages
   ↓
fetch('/chat', POST)
   ├─ Headers: Auth Bearer token
   ├─ Body: { message, session_id }
   │
   └──────────────────→ FastAPI @app.post("/chat")
                             ↓
                        1. Authenticate user
                             ↓
                        2. Save user message to DB
                             ↓
                        3. Classify intent (router)
                             ├─ "high_risk" → Crisis protocol
                             ├─ "knowledge_seeking"
                             ├─ "mixed"
                             └─ "support_only"
                             ↓
                        4. PRE-GEN SAFETY CHECK
                             ↓
                        5. RETRIEVE EMPATHY (top 6 → rerank → top 3)
                             ├─ Query Chroma with embedding
                             ├─ Get similar student experiences
                             └─ Apply quality/diversity filters
                             ↓
                        6. RETRIEVE KNOWLEDGE (top 3, conditional)
                             ├─ Mental health facts
                             └─ Treatment information
                             ↓
                        7. BUILD PROMPT
                             ├─ System: "You are MyAlly..."
                             ├─ User message + empathy context
                             ├─ Knowledge context
                             ├─ Chat history
                             └─ User profile
                             ↓
                        8. LLM GENERATION (Qwen 7B)
                             └─ "Yaar, I hear you 😔..."
                             ↓
                        9. POST-GEN SAFETY CHECK
                             └─ Block diagnoses, meds, dismissiveness
                             ↓
                        10. LOG & SAVE
                             └─ Store bot reply in DB
                             ↓
   ← ← ← ← ← ← ← ← ← ← {"reply": "Yaar...", "session_id": "..."}
   ↓
Receive response JSON
   ↓
Create botMsg object
   ↓
setMessages([...prev, botMsg])
   ↓
MessageBubble renders reply
   ↓
User sees response in chat UI
   ↓
[Ready for next message]
```

---

## Key Architecture Components

### Database Schema
```
Chroma Vector Database (3 collections):
│
├─ student_support_empathy
│  └─ 600+ documents from:
│     ├─ Reddit mental health threads
│     ├─ EmpatheticDialogues dataset
│     └─ Student support logs
│     └─ Each with: emotion, mechanism, quality_score, source
│
├─ student_support_knowledge
│  └─ Mental health FAQs
│     ├─ Topic: depression, anxiety, etc.
│     └─ Question_type: symptoms, treatment, coping
│
└─ user_profiles (Firebase)
   └─ nickname, gender, support_style, lifestyle_patterns, etc.
```

### Request/Response Flow
```
Frontend (React)
    │
    └─→ FastAPI Backend
            │
            ├─→ Vector DB (Chroma)
            │   └─ Embedding model: all-MiniLM-L6-v2
            │
            ├─→ Safety Layer
            │   └─ Crisis detection + post-gen validation
            │
            ├─→ Intent Router
            │   └─ Classify support need
            │
            ├─→ LLM (Qwen 7B via HuggingFace)
            │   └─ Generate response with context
            │
            └─→ User DB (Firebase)
                └─ Store messages, profiles, alerts
```

---

## Why This Architecture is Special

### 1. **Empathy-Driven**
Real student experiences inform every response, not just generic advice.

### 2. **Bilingual/Trilingual**
Detects and matches language (English, Marathi Minglish, Hindi/Hinglish).

### 3. **Safe by Design**
- Pre-generation checks stop high-risk content
- Post-generation validation blocks harmful advice
- Crisis escalation to counselor dashboard

### 4. **Conversational, Not Robotic**
- Mandatory emojis
- Short, natural replies (max 2 sentences)
- Talks like a real friend, not a therapist

### 5. **Context-Aware**
- Keeps empathy and knowledge separate
- Uses full conversation history
- Considers user profile preferences

### 6. **Verifiable & Debuggable**
- All responses logged with retrieved sources
- Counselor can see what context informed each reply
- Audit trail for transparency

---

## Summary

**User Input** → **Frontend Captures** → **Backend Receives** → **Intent Classified** → **Empathy Retrieved** → **Knowledge Retrieved** → **Prompt Built** → **LLM Generates** → **Safety Validated** → **Logged & Saved** → **Response Returned** → **Frontend Displays** → **User Sees Warm, Empathetic Reply**

Every response is **grounded in real student experiences** (empathy RAG) + **mental health facts** (knowledge RAG) + **safety guardrails**, all **in the student's own language**, with the **personality of a supportive friend** 🤖💚
