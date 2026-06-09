"""SQLAlchemy ORM models for the database."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    Float,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Task execution status."""
    PENDING = "pending"
    PARSING = "parsing"
    INFERRING = "inferring"
    STRATIFYING = "stratifying"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    """Main task table for questionnaire filling jobs."""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)  # UUID
    url = Column(String(512), nullable=False, index=True)
    total_count = Column(Integer, nullable=False)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)

    # Progress tracking
    current_step = Column(String(50), nullable=True)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Questionnaire data
    questionnaire_data = Column(JSON, nullable=True)  # Parsed questionnaire structure
    constraints_l1 = Column(JSON, nullable=True)  # L1 AI-inferred constraints
    constraints_l2 = Column(JSON, nullable=True)  # L2 user-specified constraints
    stratification_plan = Column(JSON, nullable=True)  # SubagentGroup allocation

    # Configuration
    execution_config = Column(JSON, nullable=True)  # Speed preset, intervals, etc.
    redemption_code = Column(String(32), nullable=True, index=True)  # L2 unlock code

    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Relationships
    subagent_results = relationship("SubagentResult", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, url={self.url[:50]}, status={self.status})>"


class RedemptionCodeStatus(str, enum.Enum):
    """Redemption code status."""
    UNUSED = "unused"
    ACTIVATED = "activated"
    CONSUMED = "consumed"
    EXPIRED = "expired"


class RedemptionCode(Base):
    """Redemption codes for L2 feature unlock."""
    __tablename__ = "redemption_codes"

    code = Column(String(32), primary_key=True, index=True)
    status = Column(SQLEnum(RedemptionCodeStatus), nullable=False, default=RedemptionCodeStatus.UNUSED, index=True)

    # Usage tracking
    activated_at = Column(DateTime, nullable=True)
    used_count = Column(Integer, default=0)
    max_uses = Column(Integer, default=1)  # 1 for one-time, >1 for subscription

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)  # Admin user or system
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RedemptionCode(code={self.code}, status={self.status}, uses={self.used_count}/{self.max_uses})>"


class SubagentResult(Base):
    """Results from individual subagent execution."""
    __tablename__ = "subagent_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    subagent_id = Column(String(20), nullable=False)  # e.g., "SA-1"

    # Subagent configuration
    quota = Column(Integer, nullable=False)
    persona = Column(JSON, nullable=False)  # Gender, age, city, occupation, income
    hard_constraints = Column(JSON, nullable=True)
    answer_biases = Column(JSON, nullable=True)

    # Execution results
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="subagent_results")

    def __repr__(self):
        return f"<SubagentResult(id={self.id}, task_id={self.task_id}, subagent_id={self.subagent_id}, success={self.success_count}/{self.quota})>"
