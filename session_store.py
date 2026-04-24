"""
Persistent session storage using SQLite via SQLAlchemy.
Stores and retrieves SharedState between sessions.
"""

import json
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Text, DateTime
)
from sqlalchemy.orm import DeclarativeBase, Session
from config import SESSION_DB_PATH


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    __tablename__ = "sessions"

    session_id    = Column(String, primary_key=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    last_updated  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job_role      = Column(String, nullable=True)
    industry      = Column(String, nullable=True)
    state_json    = Column(Text, nullable=False)   # Full SharedState serialized


class SessionStore:

    def __init__(self) -> None:
        self.engine = create_engine(f"sqlite:///{SESSION_DB_PATH}", echo=False)
        Base.metadata.create_all(self.engine)

    def save_session(self, state) -> None:
        """Persist the full SharedState object to SQLite."""
        record = SessionRecord(
            session_id   = state.session_id,
            created_at   = datetime.fromisoformat(state.created_at),
            last_updated = datetime.utcnow(),
            job_role     = state.target_job_role,
            industry     = state.target_industry,
            state_json   = json.dumps(state.to_dict(), ensure_ascii=False),
        )
        with Session(self.engine) as session:
            existing = session.get(SessionRecord, state.session_id)
            if existing:
                existing.last_updated = datetime.utcnow()
                existing.state_json   = record.state_json
            else:
                session.add(record)
            session.commit()

    def load_session(self, session_id: str) -> dict | None:
        """Retrieve a previous session by ID."""
        with Session(self.engine) as session:
            record = session.get(SessionRecord, session_id)
            if record:
                return json.loads(record.state_json)
            return None

    def list_sessions(self) -> list[dict]:
        """List all stored sessions (summary only)."""
        with Session(self.engine) as session:
            records = session.query(SessionRecord).all()
            return [
                {
                    "session_id":   r.session_id,
                    "created_at":   r.created_at.isoformat(),
                    "last_updated": r.last_updated.isoformat(),
                    "job_role":     r.job_role,
                    "industry":     r.industry,
                }
                for r in records
            ]

    def delete_session(self, session_id: str) -> bool:
        with Session(self.engine) as session:
            record = session.get(SessionRecord, session_id)
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
