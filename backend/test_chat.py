from src.app.service import chat_logic
try:
    print(chat_logic("hi", []))
except Exception as e:
    import traceback
    traceback.print_exc()
