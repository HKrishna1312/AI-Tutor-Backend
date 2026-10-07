from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text
)
from sqlalchemy.dialects import mysql
from app.core.connect_db import Base


class ResumeVectorTable(Base):
    __tablename__ = "resume_vectors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    vector_id = Column(String(64), nullable=False, index=True)
    filename = Column(String(255))
    index_name = Column(String(100), nullable=False)
    namespace = Column(String(100), nullable=False)
    chunk_count = Column(Integer, default=0)
    profile = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_resume_vectors_user_created", "user_id", "created_at"),
    )
