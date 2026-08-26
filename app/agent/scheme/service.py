import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.agent.scheme.state import create_initial_state
from app.agent.scheme.graph import build_scheme_agent_graph
from app.models.agent_session import AgentSession




logger = logging.getLogger(__name__)


_compiled_graph = None
_graph_db = None



def _get_or_build_graph(db : Session):
    """
    Returns the compiled LangGraph, building it if it hasn't been built yet.
    Thread-safe for single-process deployments (standard uvicorn setup).
    """
    
    global _compiled_graph, _graph_db
    
    if _compiled_graph is None or _graph_db is not db:
        logger.info("Building Goverment Scheme Agent graph....")
        _compiled_graph = build_scheme_agent_graph(db)
        _graph_db = db

        
    return _compiled_graph



def run_scheme_agent(user_id : int, user_role : str, mesasge : str, session_id : Optional[str], db : Session) -> dict:
    
    """
    Runs the Government Scheme Agent for one user message.
 
    Args:
        user_id:    from JWT (injected by FastAPI dependency)
        user_role:  "farmer", "user", "vendor" — affects profile loading
        message:    the farmer's current message
        session_id: UUID string — if None, a new session is created
        db:         SQLAlchemy session
 
    Returns:
        {
          "reply":          str,      # the agent's response
          "session_id":     str,      # pass back to frontend for next message
          "intent":         str,      # what the agent understood
          "steps_taken":    list,     # nodes that ran (for transparency/debug)
          "needs_clarification": bool,# True if agent asked a follow-up question
          "eligible_schemes_count": int,
          "confidence_score": float,
        }
    """
    
    
    if not session_id:
        session_id = f"scheme-{uuid.uuid4().hex}"
        
    try:
        
        initial_state = create_initial_state(
            user_id= user_id,
            user_role= user_role, 
            session_id= session_id,
            current_query= mesasge,
        )
        
        compiled_graph = _get_or_build_graph(db)
        
        final_state = compiled_graph.invoke(
            initial_state,
            config = {"recursion_limit" : 20},
        )
        
        reply = final_state.get("final_response") or (
            "I'm sorry, I couldn't generate a response."
            "Please try again or contact your neares KVk."
        )
        
        
        return {
            "reply": reply,
            "session_id": session_id,
            "intent": final_state.get("intent", "unknown"),
            "steps_taken": final_state.get("steps_taken", []),
            "needs_clarification": final_state.get("needs_clarification", False),
            "eligible_schemes_count": len(final_state.get("eligible_schemes", [])),
            "confidence_score": final_state.get("confidence_score", 0.0),
            "hallucination_flags":    final_state.get("hallucination_flags", []),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail= str(e)
        )
        
    except Exception as e:
        logger.error(f"run_scheme_agent failed for user = {user_id} : {e}")
        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= "Agent encountered an error. Please try again."
        )
        
        
def get_session_history(session_id : str, user_id : int, db : Session) -> dict:
    """
    Returns the conversation history for a session.
    Only returns history belonging to the requesting user.
    """
    
    session = db.query(AgentSession).filter(
        AgentSession.session_id == session_id, AgentSession.user_id == user_id,
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404, detail= "Session not found"
        )
        
    return {
        "session_id" : session_id,
        "agent_name" : session.agent_name,
        "turn_count" : session.turn_count,
        "history" : session.history or [],
        "farmer_profile" : session.farmer_profile or {},
        "created_at" : session.created_at,
        "updated_at" : session.updated_at,
    }
    
    
def clear_session(session_id : str, user_id : int, db : Session) -> dict:
    """
    Clears a session — useful for testing or when farmer wants to start fresh.
    """
    session = db.query(AgentSession).filter(
        AgentSession.session_id == session_id,
        AgentSession.user_id == user_id,
    ).first()
 
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
 
    db.delete(session)
    db.commit()
 
    return {"message": f"Session {session_id} cleared successfully."}