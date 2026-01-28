from fastapi import APIRouter, HTTPException
from history_manager import HistoryManager

router = APIRouter()
history_manager = HistoryManager()

@router.get("/history/list")
async def get_history_list():
    try:
        return history_manager.get_history_list()
    except Exception as e:
        print(f"Error getting history list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/history/{date_str}/{session_id}")
async def get_session(date_str: str, session_id: str):
    session = history_manager.get_session(date_str, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
@router.delete("/history/{date_str}/{session_id}")
async def delete_session(date_str: str, session_id: str):
    success = history_manager.delete_session(date_str, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or could not be deleted")
    return {"status": "success"}

from pydantic import BaseModel

class SessionTitleUpdate(BaseModel):
    date_str: str
    session_id: str
    title: str

@router.post("/history/title")
async def update_session_title(request: SessionTitleUpdate):
    success = history_manager.update_session_title(request.date_str, request.session_id, request.title)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or name could not be updated")
    return {"status": "success"}
