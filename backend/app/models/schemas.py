"""Pydantic models for API request/response validation."""
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


# Enums matching database models
class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PARSING = "parsing"
    INFERRING = "inferring"
    STRATIFYING = "stratifying"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RedemptionCodeStatus(str, Enum):
    """Redemption code status."""
    UNUSED = "unused"
    ACTIVATED = "activated"
    CONSUMED = "consumed"
    EXPIRED = "expired"


# Request schemas
class ParseRequest(BaseModel):
    """Request to parse questionnaire from URL."""
    url: HttpUrl = Field(..., description="Questionnaire URL from wjx.cn")
    total_count: int = Field(..., ge=1, le=10000, description="Number of responses to generate")
    redemption_code: Optional[str] = Field(None, max_length=32, description="Optional L2 unlock code")


class StratifyRequest(BaseModel):
    """Request to perform demographic stratification."""
    task_id: str = Field(..., description="Task ID from parse step")
    constraints_l2: Optional[Dict[str, Any]] = Field(None, description="User-specified L2 constraints")


class ExecuteRequest(BaseModel):
    """Request to start questionnaire execution."""
    task_id: str = Field(..., description="Task ID from stratify step")
    execution_config: Optional[Dict[str, Any]] = Field(None, description="Speed preset and intervals")


class RedemptionCodeActivateRequest(BaseModel):
    """Request to activate a redemption code."""
    code: str = Field(..., min_length=8, max_length=32, description="Redemption code")


# Response schemas
class TaskResponse(BaseModel):
    """Response with task information."""
    id: str
    url: str
    total_count: int
    status: TaskStatus
    current_step: Optional[str] = None
    completed_count: int = 0
    failed_count: int = 0
    progress_percentage: float = 0.0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class TaskDetailResponse(TaskResponse):
    """Detailed task response including parsed data and plans."""
    questionnaire_data: Optional[Dict[str, Any]] = None
    constraints_l1: Optional[Dict[str, Any]] = None
    constraints_l2: Optional[Dict[str, Any]] = None
    stratification_plan: Optional[Dict[str, Any]] = None
    execution_config: Optional[Dict[str, Any]] = None
    redemption_code: Optional[str] = None

    class Config:
        from_attributes = True


class SubagentResultResponse(BaseModel):
    """Response with subagent execution result."""
    id: int
    task_id: str
    subagent_id: str
    quota: int
    persona: Dict[str, Any]
    success_count: int = 0
    failed_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class RedemptionCodeResponse(BaseModel):
    """Response with redemption code information."""
    code: str
    status: RedemptionCodeStatus
    activated_at: Optional[datetime] = None
    used_count: int
    max_uses: int
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParseResponse(BaseModel):
    """Response from parse endpoint."""
    task_id: str
    message: str = "Parsing started"


class StratifyResponse(BaseModel):
    """Response from stratify endpoint."""
    task_id: str
    message: str = "Stratification completed"
    subagent_count: int


class ExecuteResponse(BaseModel):
    """Response from execute endpoint."""
    task_id: str
    message: str = "Execution started"


class StatusResponse(BaseModel):
    """Real-time status update for WebSocket."""
    task_id: str
    status: TaskStatus
    current_step: Optional[str] = None
    progress_percentage: float = 0.0
    completed_count: int = 0
    failed_count: int = 0
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    task_id: Optional[str] = None


# Persona and constraint schemas
class Persona(BaseModel):
    """Demographic persona for subagent."""
    gender: Optional[str] = None
    age_range: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    occupation: Optional[str] = None
    income_range: Optional[str] = None
    education: Optional[str] = None


class SubagentGroup(BaseModel):
    """Subagent group allocation from stratification."""
    subagent_id: str
    quota: int
    ratio: float
    persona: Persona
    hard_constraints: Optional[Dict[str, Any]] = None
    answer_biases: Optional[Dict[str, Any]] = None
    merged_from: Optional[List[str]] = None
