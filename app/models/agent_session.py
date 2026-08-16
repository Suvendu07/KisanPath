from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base




class AgentSession(Base):
    
    __tablename__ = "agent_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), ondelete="SET NULL")
    
    history = Column(JSON, default=dict)
    
    turn_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    
    user = relationship("User", foreign_keys=[user_id])
    tool_logs = relationship("AgentToolLog", back_populates="session", cascade="all, delete")
    
    
    def __repr__(self):
        return (
            f"<AgentSession id={self.id} "
            f"agent={self.agent_name} "
            f"session={self.session_id} "
            f"turns={self.turn_count}>"
        )
    
    
    
    
class AgentToolLog(Base):
    
    __tablename__ = "agent_tool_logs"
    
    id = Column(Integer, primary_key=True, index= True)
    
    session_id_ref = Column(String(100), ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    
    agent_name = Column(String(50), nullable=False)
    node_name = Column(String(100), nullable=False)
    tool_name = Column(String(100), nullable=True)
    
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    duration_ms = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    session = relationship("AgentSession", back_populates="tool_logs")
    
    def __repr__(self):
        return (
            f"<AgentToolLog id={self.id} "
            f"node={self.node_name} "
            f"success={self.success}>"
        )
 