from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportColumn(BaseModel):
    key: str
    label: str
    type: str


class DynamicReportResponse(BaseModel):
    workflow_key: str
    workflow_title: str
    active_version: int
    total_submissions: int
    columns: List[ReportColumn]
    metrics: Dict[str, Any] = Field(default_factory=dict)
    recent_submissions: List[Dict[str, Any]] = Field(default_factory=list)


class CreateSubmissionRequest(BaseModel):
    data: Dict[str, Any]
    submitted_by: Optional[str] = "anonymous"

