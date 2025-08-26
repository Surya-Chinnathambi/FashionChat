from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from database import get_db
from services.chat_service import ChatService
from schemas import ChatMessage, ChatResponse
from routers.auth import get_current_user
from models import User

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """Send message to chatbot"""
    try:
        # Try to get current user if authenticated (optional)
        try:
            current_user = await get_current_user()
        except:
            current_user = None
        
        chat_service = ChatService(db)
        
        response = await chat_service.process_message(
            message=message.message,
            session_id=message.session_id,
            user_id=current_user.id if current_user else None
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get chat history for a session"""
    try:
        chat_service = ChatService(db)
        history = await chat_service.get_chat_history(session_id, limit)
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")

@router.get("/sessions")
async def get_user_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat sessions"""
    from models import ChatSession
    
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).limit(10).all()
    
    return [
        {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat() if session.updated_at else None
        }
        for session in sessions
    ]
