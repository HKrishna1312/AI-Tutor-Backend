from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship

from app.core.connect_db import Base


class InterviewSessionTable(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="Interview practice")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    attempts = relationship(
        "InterviewAttemptTable",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_interview_sessions_user_created", "user_id", "created_at"),
    )


class InterviewAttemptTable(Base):
    __tablename__ = "interview_attempts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=False)
    concept = Column(String(120), nullable=False, index=True)
    answer = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=False)
    score = Column(Integer, nullable=False)
    strengths = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=False)
    improvements = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=False)
    feedback = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("InterviewSessionTable", back_populates="attempts")

    __table_args__ = (
        Index("ix_interview_attempts_session_created", "session_id", "created_at"),
    )
