import chromadb
from pathlib import Path

# Paths
DB_PATH = str(Path(__file__).resolve().parents[2] / "database" / "chroma_db")

def reset_chats():
    print(f"Connecting to ChromaDB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Collections to clear
    collections_to_clear = ["chat_sessions", "chat_history"]
    
    for col_name in collections_to_clear:
        try:
            print(f"Clearing collection: {col_name}...")
            # Deleting and recreating the collection is the most effective way to clear all data
            client.delete_collection(col_name)
            print(f"✅ Successfully cleared {col_name}.")
        except Exception as e:
            if "does not exist" in str(e).lower():
                print(f"ℹ️ Collection {col_name} already empty or doesn't exist.")
            else:
                print(f"❌ Error clearing {col_name}: {e}")

    print("\n✨ All chat history for all users has been deleted.")

if __name__ == "__main__":
    reset_chats()
