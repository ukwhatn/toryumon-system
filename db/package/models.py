from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime, BigInteger

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
