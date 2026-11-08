from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# Defines standard visualization formats supported by dynamic reporting widgets.
class ChartType(str, Enum):
    STAT_CARD = "stat_card"
    BAR_CHART = "bar_chart"
    DONUT_CHART = "donut_chart"
    LINE_CHART = "line_chart"


# Represents a table column projected from the active workflow schema.
class ReportColumn(BaseModel):
    key: str
    label: str
    type: str
    reportable: bool = True


# Represents a single rendered analytics widget on the reporting dashboard.
class ReportWidget(BaseModel):
    id: str
    field_key: str
    title: str
    chart_type: ChartType
    summary: str = ""
    data: Any


# Encapsulates dynamic analytics metrics, chart widgets, and recent submission rows for a workflow.
class DynamicReportResponse(BaseModel):
    workflow_key: str
    workflow_title: str
    active_version: int
    total_submissions: int
    columns: List[ReportColumn]
    widgets: List[ReportWidget] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    recent_submissions: List[Dict[str, Any]] = Field(default_factory=list)


# Validates an incoming form submission payload against the active workflow version.
class CreateSubmissionRequest(BaseModel):
    data: Dict[str, Any]
    submitted_by: Optional[str] = "anonymous"
