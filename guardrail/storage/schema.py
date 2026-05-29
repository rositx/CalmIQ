# guardrail/storage/schema.py
# SQLAlchemy declarative models for PostgreSQL persistence

from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SessionLog(Base):
    """Permanent session analytics log table."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    peak_irritation_score = Column(Float, default=0.0)
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    resolution_type = Column(String, nullable=True)  # 'ai_resolved' | 'human_resolved' | 'abandoned'
    coupon_issued = Column(Boolean, default=False)
    turn_count = Column(Integer, default=0)

    turns = relationship("SessionTurnLog", back_populates="session")
    escalations = relationship("EscalationEventLog", back_populates="session")


class SessionTurnLog(Base):
    """Granular turn-by-turn chat history logging."""
    __tablename__ = "session_turns"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    role = Column(String, nullable=False)  # 'user' | 'ai'
    message = Column(String, nullable=False)
    sentiment_score = Column(Float, default=0.0)
    irritation_score_at_turn = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionLog", back_populates="turns")


class EscalationEventLog(Base):
    """Detailed escalation alerts and human agent connection timings."""
    __tablename__ = "escalation_events"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    score_at_trigger = Column(Float, nullable=False)
    threshold_at_trigger = Column(Float, nullable=False)
    primary_signal = Column(Column(String, nullable=True))
    agent_id = Column(String, nullable=True)
    time_to_agent_seconds = Column(Integer, nullable=True)

    session = relationship("SessionLog", back_populates="escalations")
