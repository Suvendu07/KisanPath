
from fastapi import APIRouter, Depends, Query
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
 
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user_model import User
from app.agent.scheme.service import (
    run_scheme_agent,
    get_session_history,
    clear_session,
)
 
router = APIRouter()
 
 
 
class SchemeAgentRequest(BaseModel):
    message: str
    session_id: Optional[str] = None    # None = start new session
 
 
class SchemeAgentResponse(BaseModel):
    reply: str
    session_id: str        # frontend stores and sends back next time
    intent: str
    steps_taken: list
    needs_clarification: bool
    eligible_schemes_count:  int
    confidence_score: float
    hallucination_flags: list
 
 
  
@router.post(
    "/scheme/chat",
    response_model = SchemeAgentResponse,
    summary = "Government Scheme Agent — ask about agriculture schemes",
)
def scheme_agent_chat(
    payload: SchemeAgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Main chat endpoint for the Government Scheme Agent.
 
    The agent:
    1. Understands the farmer's intent
    2. Extracts farmer profile (state, land size, crop types etc.)
    3. Asks clarifying questions if needed (max 2 rounds)
    4. Retrieves relevant schemes from knowledge base (RAG)
    5. Filters by eligibility based on farmer's profile
    6. Verifies information to prevent hallucination
    7. Generates a personalized, cited response
 
    Frontend must:
    - Store the returned session_id
    - Send it back on every subsequent message in the same conversation
    - When session_id is null/empty, a new session is created automatically
    """
    return run_scheme_agent(
        user_id = current_user.id,
        user_role  = current_user.role.value,
        message = payload.message,
        session_id = payload.session_id,
        db = db,
    )
 
 
@router.get(
    "/scheme/history/{session_id}",
    summary = "Get conversation history for a scheme agent session",
)
def scheme_session_history(
    session_id:   str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the full conversation history and extracted farmer profile
    for a specific session. Useful for resuming a conversation.
    """
    return get_session_history(session_id, current_user.id, db)
 
 
@router.delete(
    "/scheme/history/{session_id}",
    summary = "Clear a scheme agent session (start fresh)",
)
def clear_scheme_session(
    session_id: str,
    current_user: User    = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clears all memory for a session. The farmer will need to provide
    their details again on the next message.
    """
    return clear_session(session_id, current_user.id, db)