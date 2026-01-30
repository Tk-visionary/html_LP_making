import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

class HistoryManager:
    def __init__(self, base_path: str = "history"):
        # Base path defaults to "history" relative to the backend directory
        # Assuming this file is imported from backend/routes/generate_code.py,
        # we might need to adjust relative path if it's running from backend root.
        # Let's use absolute path relative to this file to be safe? 
        # Or standard "process working dir" which is usually backend/
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def create_session(self, params: Dict[str, Any]) -> str:
        """
        Creates a new session directory and saves the prompt metadata.
        Returns the session_id (which acts as the directory name).
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        unique_id = str(uuid.uuid4())[:8]
        
        session_id = f"{time_str}_{unique_id}"
        
        # specific directory for today's date
        daily_path = os.path.join(self.base_path, date_str)
        os.makedirs(daily_path, exist_ok=True)
        
        # specific directory for this session
        session_path = os.path.join(daily_path, session_id)
        os.makedirs(session_path, exist_ok=True)
        
        
        # Save prompt metadata
        
        # Inherit title from parent session if exists
        try:
             parent_id = params.get("parent_session_id")
             if parent_id:
                 parent_path = self.find_session_path(parent_id)
                 if parent_path:
                     parent_meta_path = os.path.join(parent_path, "prompt.json")
                     if os.path.exists(parent_meta_path):
                         with open(parent_meta_path, "r", encoding="utf-8") as f:
                             parent_meta = json.load(f)
                             if "title" in parent_meta:
                                 params["title"] = parent_meta["title"]
        except Exception as e:
            print(f"Error inheriting title: {e}")

        meta_path = os.path.join(session_path, "prompt.json")
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                # Filter out huge fields if necessary, but saving full prompt is good for history
                # Avoid saving base64 images to JSON if possible, or truncate them?
                # User asked for "input image preservation" to be optional/maybe not needed,
                # but "thought" must be saved. 
                # Let's save the params as provided.
                json.dump(params, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving prompt metadata: {e}")
            
        return os.path.join(date_str, session_id)

    def append_thought(self, session_path_rel: str, variant_index: int, content: str):
        """
        Appends thinking content to the thought file.
        """
        if not session_path_rel:
            return

        full_path = os.path.join(self.base_path, session_path_rel, f"variant_{variant_index}_thought.md")
        
        try:
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error appending thought: {e}")

    def save_code(self, session_path_rel: str, variant_index: int, code: str):
        """
        Saves the generated code to a file.
        """
        if not session_path_rel:
            return

        full_path = os.path.join(self.base_path, session_path_rel, f"variant_{variant_index}_code.html")
        
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            print(f"Error saving code: {e}")

    def get_latest_thought(self) -> Optional[str]:
        """
        Retrieves the thought process from the most recent session.
        Useful for "continue conversation" context.
        """
        # Find latest date directory
        try:
            dates = sorted([d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))], reverse=True)
            if not dates:
                return None
            
            latest_date = dates[0]
            date_dir = os.path.join(self.base_path, latest_date)
            
            # Find latest session in that date
            sessions = sorted([s for s in os.listdir(date_dir) if os.path.isdir(os.path.join(date_dir, s))], reverse=True)
            if not sessions:
                return None
            
            latest_session = sessions[0]
            session_dir = os.path.join(date_dir, latest_session)
            
            # Find thought files
            # Just grab variant_0_thought.md for simplicity or combine all?
            # User request: "past thought history". Let's grab the first one we find.
            thought_file = os.path.join(session_dir, "variant_0_thought.md")
            if os.path.exists(thought_file):
                with open(thought_file, "r", encoding="utf-8") as f:
                    return f.read()
            
            return None
        except Exception as e:
            print(f"Error reading latest thought: {e}")
            return None
    def get_history_list(self) -> List[Dict[str, Any]]:
        """
        Returns a sorted list of all history sessions.
        """
        history_list = []
        
        if not os.path.exists(self.base_path):
            return []

        # Iterate over date directories
        for date_str in os.listdir(self.base_path):
            date_path = os.path.join(self.base_path, date_str)
            if not os.path.isdir(date_path):
                continue
                
            # Iterate over session directories
            for session_id in os.listdir(date_path):
                session_path = os.path.join(date_path, session_id)
                if not os.path.isdir(session_path):
                    continue
                    
                # Read metadata
                meta_path = os.path.join(session_path, "prompt.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            
                            # Extract useful info for the list
                            prompt_text = ""
                            custom_title = meta.get("title")
                            
                            if custom_title:
                                prompt_text = custom_title
                            elif "prompt" in meta:
                                if isinstance(meta["prompt"], dict):
                                    prompt_text = meta["prompt"].get("text", "")
                                elif isinstance(meta["prompt"], str):
                                    prompt_text = meta["prompt"]
                            
                            # Construct a displayable item
                            history_list.append({
                                "id": session_id,
                                "date": date_str,
                                "timestamp": session_id.split("_")[0] if "_" in session_id else "",
                                "prompt": prompt_text[:100] + "..." if len(prompt_text) > 100 and not custom_title else prompt_text,
                                "input_mode": meta.get("input_mode", "unknown"),
                                "url": f"/history/{date_str}/{session_id}",
                                "parent_session_id": meta.get("parent_session_id")
                            })
                    except Exception as e:
                        print(f"Error reading metadata for {session_id}: {e}")
                        
        # Sort by date and timestamp descending (newest first)
        history_list.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
        
        # Filter out sessions that are parents of other sessions (to group by conversation)
        # 1. Collect all parent_session_ids
        parent_ids = set()
        for item in history_list:
            if item.get("parent_session_id"):
                parent_ids.add(item["parent_session_id"])
        
        # 2. Keep only sessions that are NOT in parent_ids
        # Construct full ID "date/session_id" to match parent_session_id format
        final_list = []
        for item in history_list:
            full_id = f"{item['date']}/{item['id']}"
            if full_id not in parent_ids:
                final_list.append(item)
                
        return final_list

    def get_session(self, date_str: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full details for a specific session.
        """
        session_path = os.path.join(self.base_path, date_str, session_id)
        if not os.path.exists(session_path):
            return None
            
        result = {}
        
        # Load prompt metadata
        meta_path = os.path.join(session_path, "prompt.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    result["params"] = json.load(f)
            except Exception:
                pass
                
        # Load variants
        # Scan for variant_{i}_code.html and variant_{i}_thought.md
        variants = []
        i = 0
        while True:
            code_path = os.path.join(session_path, f"variant_{i}_code.html")
            thought_path = os.path.join(session_path, f"variant_{i}_thought.md")
            
            if not os.path.exists(code_path) and not os.path.exists(thought_path):
                break
                
            variant_data = {"index": i}
            
            if os.path.exists(code_path):
                with open(code_path, "r", encoding="utf-8") as f:
                    variant_data["code"] = f.read()
                    
            if os.path.exists(thought_path):
                with open(thought_path, "r", encoding="utf-8") as f:
                    variant_data["thought"] = f.read()
                    
            variants.append(variant_data)
            i += 1
            
        try:
            # Create a simplified object for the current session to avoid circular reference
            current_session_data = {
                "id": session_id,
                "date": date_str,
                "params": result.get("params"),
                "variants": variants
            }

            if result.get("params") and result["params"].get("parent_session_id"):
                 parent_id = result["params"]["parent_session_id"]
                 parent_path = self.find_session_path(parent_id)
                 if parent_path:
                    # Extract date from path to call get_session
                    parent_dir = os.path.dirname(parent_path)
                    parent_date = os.path.basename(parent_dir)
                    
                    parent_sess_id = os.path.basename(parent_path)
                    
                    parent_data = self.get_session(parent_date, parent_sess_id)
                    if parent_data:
                        # Append parent's history stack to ours
                        parent_stack = parent_data.get("stack", [])
                        if not parent_stack:
                            parent_stack = [parent_data]
                        
                        result["stack"] = parent_stack + [current_session_data]
                    else:
                        result["stack"] = [current_session_data]
                 else:
                     result["stack"] = [current_session_data]
            else:
                 result["stack"] = [current_session_data]
        except Exception as e:
            print(f"Error fetching parent session: {e}")
            result["stack"] = [result]

        result["variants"] = variants
        return result
        
    def find_session_path(self, session_id: str) -> Optional[str]:
        """Finds the path of a session by ID, searching all date directories."""
        # If session_id contains a date (e.g. "2024-03-01/session_id"), handle it
        if "/" in session_id:
            date_str, sess_id = session_id.split("/", 1)
            path = os.path.join(self.base_path, date_str, sess_id)
            if os.path.exists(path):
                return path
            return None
        
        # Otherwise, search all date directories
        date_dirs = sorted(os.listdir(self.base_path), reverse=True)
        for date_dir in date_dirs:
            full_date_path = os.path.join(self.base_path, date_dir)
            if not os.path.isdir(full_date_path):
                continue
            
            candidate = os.path.join(full_date_path, session_id)
            if os.path.exists(candidate):
                return candidate
        return None
    def delete_session(self, date_str: str, session_id: str) -> bool:
        """
        Deletes a specific session directory.
        Returns True if deleted, False if not found.
        """
        session_path = os.path.join(self.base_path, date_str, session_id)
        if not os.path.exists(session_path):
            return False
            
        try:
            import shutil
            shutil.rmtree(session_path)
            
            # Check if date directory is empty, if so delete it too
            date_dir = os.path.dirname(session_path)
            if not os.listdir(date_dir):
                os.rmdir(date_dir)
                
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    def update_session_title(self, date_str: str, session_id: str, title: str) -> bool:
        """
        Updates the title of a specific session.
        """
        session_path = os.path.join(self.base_path, date_str, session_id)
        if not os.path.exists(session_path):
            return False
            
        meta_path = os.path.join(session_path, "prompt.json")
        # create meta file if not exists ? No, should exist.
        
        try:
            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            
            meta["title"] = title
            
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Error updating session title: {e}")
            return False
