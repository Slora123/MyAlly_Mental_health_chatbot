"""
app.py
───────
MyAlly - Empathetic Student Mental-Health Chatbot
Entry-point. All implementation lives in src/.

Usage:
    python app.py
    (build the vector index first with: python build_rag_index.py)
"""

import uvicorn

if __name__ == "__main__":
    import os
    import subprocess
    from pathlib import Path
    
    db_path = Path(__file__).resolve().parents[1] / "database" / "chroma_db"
    
    def needs_rebuild():
        if not db_path.exists() or not any(db_path.iterdir()):
            return True
        # Even if folder exists, check for sqlite file size
        sqlite_db = db_path / "chroma.sqlite3"
        if sqlite_db.exists() and sqlite_db.stat().st_size < 1000: # Less than 1KB is likely empty
            return True
        return False

    if needs_rebuild():
        print("⚠️  Vector database missing or empty! Bootstrapping RAG index...")
        
        # Reconstruct knowledge dataset from chunks if needed
        data_dir = Path(__file__).resolve().parents[1] / "database" / "data" / "processed"
        parts = sorted(data_dir.glob("knowledge_part_*"))
        if parts and not (data_dir / "knowledge_documents.jsonl").exists():
            print("Combining knowledge dataset parts...")
            with open(data_dir / "knowledge_documents.jsonl", "wb") as outfile:
                for part in parts:
                    with open(part, "rb") as infile:
                        outfile.write(infile.read())
            
        import sys
        build_script = Path(__file__).resolve().parents[1] / "database" / "build_rag_index.py"
        subprocess.run([sys.executable, str(build_script)], check=False)
        print("✅  RAG index bootstrap complete.")

    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 MyAlly is starting on 0.0.0.0:{port}")
    uvicorn.run("src.app.chat_api:app", host="0.0.0.0", port=port, reload=False)
