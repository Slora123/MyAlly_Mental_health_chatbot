# RAG Guide For An Empathetic Student Mental-Health Chatbot

## 1. What Was Wrong In The Old Setup

The old `app.py` and `rag_chatbot_colab.ipynb` had four main issues:

1. They retrieved only one document from one collection.
2. They did not separate empathy examples from factual mental-health knowledge.
3. They could accidentally retrieve poor Reddit replies because empathy level `0` rows were not filtered out.
4. They used retrieved text as a loose "friend style" example instead of a structured support pipeline.

That makes the chatbot sound warm sometimes, but it does not make it reliably empathetic or properly grounded.

## 2. Correct Role Of Each Dataset

### Empathy-Mental-Health Reddit

Use it for:

- empathy mechanisms
- supportive response patterns
- rationale-based examples

Do not use:

- low-empathy rows (`level = 0`)
- direct copying of raw replies

Recommended rule:

- keep only `level >= 1`
- prefer `level = 2` results during retrieval

### EmpatheticDialogues

Use it for:

- conversational flow
- emotion labels
- natural empathetic follow-up replies

Do not use it as clinical knowledge.

### MHQA

Use it for:

- mental-health educational grounding
- question-answer style retrieval
- topic routing such as depression, anxiety, trauma, and OCD

Do not use it as a diagnosis engine.

## 3. Best RAG Architecture

Use two collections, not one:

1. `student_support_empathy`
2. `student_support_knowledge`

### Collection 1: empathy

Store documents like:

```text
Support-seeking message: ...
Empathetic response: ...
Empathy mechanism: emotional_reaction / interpretation / exploration
Empathy evidence: ...
```

and

```text
Emotion label: sentimental
Situation prompt: ...
Speaker message: ...
Empathetic reply: ...
```

This collection teaches the model how to respond.

### Collection 2: knowledge

Store documents like:

```text
Topic: Depression
Question type: Preventive
Question: ...
Correct answer: ...
Options: ...
```

This collection helps the model answer factual or psychoeducational questions.

## 4. Inference Flow

For each user message:

1. Detect crisis or immediate danger.
2. Detect whether the user needs emotional support, factual information, or both.
3. Retrieve top empathy examples.
4. Retrieve MHQA snippets only when the message looks knowledge-seeking.
5. Generate the answer with a prompt that forces:
   - validation first
   - careful factual language
   - no diagnosis
   - one practical next step
   - one gentle follow-up question

## 5. Prompt Pattern That Works Better

Your prompt should tell the model:

- the user is a student
- empathy examples are for tone, not copying
- MHQA snippets are for cautious educational grounding
- response must begin with emotional acknowledgment
- no diagnosis, no overclaiming, no robotic disclaimers

The current updated `app.py` follows this structure.

## 6. Why This Accommodates Empathy Better

This design improves empathy because it separates:

- `how to respond` from empathy datasets
- `what factual content may help` from MHQA

That matters because empathy is not the same as knowledge. A chatbot can be factually correct and still feel cold, or warm and still be factually weak. Good RAG for mental-health support needs both layers.

## 7. Practical Build Steps

### Step A: keep only true dataset files

Recommended keep list:

- `dataset reddit/emotional-reactions-reddit.csv`
- `dataset reddit/interpretations-reddit.csv`
- `dataset reddit/explorations-reddit.csv`
- `empatheticdialogues/train.csv`
- `empatheticdialogues/valid.csv`
- `empatheticdialogues/test.csv`
- `mhqa-main/datasets/mhqa.csv`
- `mhqa-main/datasets/mhqa-b.csv`

### Step B: build the vector DB

```bash
python build_rag_index.py
```

### Step C: run the app

```bash
python app.py
```

## 8. What To Do Next If You Want Even Better Results

### Add reranking

After vector search, rerank with:

- empathy level
- topic match
- emotion match

### Add response scoring

Create an internal check for:

- empathy
- safety
- factual caution

If the draft fails, regenerate once.

### Add visible grounding

Show a small UI card:

- empathy source type
- MHQA topic
- confidence note

### Add student-specific safety policy

Include rules for:

- exam stress
- loneliness
- homesickness
- bullying
- self-harm risk

## 9. Important Limitation

MHQA is useful for grounding, but it is still a benchmark-style QA dataset, not a therapy manual. So it should support psychoeducation, not replace professional guidance or crisis care.
