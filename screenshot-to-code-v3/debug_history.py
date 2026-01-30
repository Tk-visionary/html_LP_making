import sys
import os
import traceback

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from history_manager import HistoryManager

def debug_get_session(date_str, session_id):
    print(f"Attempting to load session: {date_str}/{session_id}")
    hm = HistoryManager(base_path="backend/history")
    try:
        session = hm.get_session(date_str, session_id)
        print("Session loaded successfully.")
        # print(session.keys())
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    # stored session from curl output
    debug_get_session("2026-01-28", "15-03-04_512254cc")
