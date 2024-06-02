from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from .connection import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String, nullable=False)
    univ_name = Column(String, nullable=True)
    discord_account_id = Column(BigInteger, nullable=False)

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC))
    deleted_at = Column(DateTime, nullable=True)


class ProgressAsk(Base):
    __tablename__ = "progress_asks"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, nullable=False)
    ask_channel_id = Column(BigInteger, nullable=False)
    ask_message_id = Column(BigInteger, nullable=False)
    summary_channel_id = Column(BigInteger, nullable=False)
    summary_message_id = Column(BigInteger, nullable=False)

    contents = relationship("ProgressAskContents", back_populates="progress_ask")
    roles = relationship("ProgressAskRoles", back_populates="progress_ask")

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC))
    deleted_at = Column(DateTime, nullable=True)


class ProgressAskContents(Base):
    __tablename__ = "progress_ask_contents"

    id = Column(Integer, primary_key=True, index=True)
    progress_ask_id = Column(Integer, ForeignKey("progress_asks.id"))
    progress_ask = relationship("ProgressAsk", back_populates="contents")

    content = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC))
    deleted_at = Column(DateTime, nullable=True)


class ProgressAskRoles(Base):
    __tablename__ = "progress_ask_roles"

    id = Column(Integer, primary_key=True, index=True)
    progress_ask_id = Column(Integer, ForeignKey("progress_asks.id"))
    progress_ask = relationship("ProgressAsk", back_populates="roles")

    role_id = Column(BigInteger, nullable=False)

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC))
    deleted_at = Column(DateTime, nullable=True)
