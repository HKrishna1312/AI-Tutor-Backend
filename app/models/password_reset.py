# from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
# from sqlalchemy.orm import relationship
# from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()


# class PasswordResetToken(Base):
#     __tablename__ = "password_reset_tokens"

#     id = Column(Integer, primary_key=True, index=True)

#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

#     token = Column(String(255), unique=True, nullable=False)

#     created_at = Column(DateTime, nullable=False)

#     expires_at = Column(DateTime, nullable=False)

#     used = Column(Boolean, default=False)

#     user = relationship("UserTable")



from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()
from app.core.connect_db import Base

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    token = Column(String(255), unique=True, nullable=False)

    created_at = Column(DateTime, nullable=False)

    expires_at = Column(DateTime, nullable=False)

    used = Column(Boolean, default=False)