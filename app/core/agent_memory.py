import json
import time
import logging
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.models.agent_session import AgentSession, AgentToolLog

logger = logging.getLogger(__name__)


def load_session(
    session_id : str,
    user_id : int,
    agent_name : str,
    db : Session,
) -> dict:
    
    try:
        session = db.query(AgentSession).filter(AgentSession.session_id == session_id).first()
        
        if session:
            return {
                "history" : session.history or [],
                "farmer_profile" : session.farmer_profile or [],
                "turn_count" : session.turn_count,
                "is_new" : False,
            }
            
        else:
            new_session = AgentSession(
            session_id = session_id,
            agent_name = agent_name,
            user_id = user_id,
            history = [],
            farmer_profile = {},
            turn_count = 0,
        )
        
        
            db.add(new_session)
            db.flush()
        
            return {
             "history" : [],
             "farmer_profile" : [],
             "turn_count" : 0,
             "is_new" : True,  
        }
            
    except Exception as e:
        logger.error(f"Failed to load session {session_id}: {e}")
        
        return {
            "history" : [],
            "farmer_profile" : {},
            "turn_count" : 0,
            "is_new" : True,
        }
        
        


def save_session(session_id : str, agent_name : str, user_id : int, history: list, farmer_profile : dict, turn_count : int, db : Session,) -> bool:
    
    
    try:
        session = db.query(AgentSession).filter(AgentSession.session_id == session_id).first()
        
        if session:
            session.history = history
            session.farmer_profile = farmer_profile
            session.turn_count = turn_count
            
        else:
            session = AgentSession(
                session_id = session_id,
                agent_name = agent_name,
                user_id = user_id,
                history = history,
                farmer_profile = farmer_profile,
                turn_count = turn_count,
            )
            
            db.add(session)
            
        db.flush()
        return True
    
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")
        
        


def log_tool_call(session_id : str, agent_name : str, node_name : str, db : Session, tool_name : Optional[str] = None, input_summary : Optional[str] = None, output_summary : Optional[str] = None, success : bool = True, error_message : Optional[str] = None, duration_ms :Optional[float] = None,) -> None:
    
    try:
        log = AgentToolLog(
            session_id_ref = session_id,
            agent_name = agent_name,
            node_name = node_name,
            tool_name = tool_name,
            input_summary = (input_summary or "")[:500],
            output_summary = (output_summary or "")[:500],
            success = success,
            error_message = error_message,
            duration_ms = duration_ms,
        )
        
        db.add(log)
        db.flush()
        
    except Exception as e:
        logger.error(f"failed to write tool log for session {session_id}: {e}")
        
        
def build_history_context(history : list, max_turns: int = 10) -> str:
    
    
    if not history:
        return ""
    
    recent = history[-(max_turns * 2):]
    lines = []
    
    
    for msg in recent:
        role = "Farmer" if msg.get("role") == "human" else "AgriAI"
        content = msg.get("content", "").script()
        lines.append(f"{role}:{content}")
        
        
    return "\n".join(lines)