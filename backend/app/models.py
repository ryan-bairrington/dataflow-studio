"""Pydantic models for API and workflow definitions."""
from typing import Any, Literal
from pydantic import BaseModel, Field


# === Workflow Models ===

class NodeConfig(BaseModel):
    """Base configuration for a workflow node."""
    pass


class ReadCSVConfig(BaseModel):
    """Configuration for ReadCSV node."""
    upload_id: str
    header: bool = True
    sep: str = ","


class FilterConfig(BaseModel):
    """Configuration for Filter node."""
    expression: str = Field(..., description="Pandas-compatible filter expression")


class SelectConfig(BaseModel):
    """Configuration for Select node."""
    columns: list[str]


class JoinConfig(BaseModel):
    """Configuration for Join node."""
    left_key: str = Field(..., alias="leftKey")
    right_key: str = Field(..., alias="rightKey")
    how: Literal["inner", "left", "right", "outer"] = "inner"

    class Config:
        populate_by_name = True


class AggregationSpec(BaseModel):
    """Single aggregation specification."""
    col: str
    op: Literal["sum", "mean", "count", "min", "max", "first", "last"]
    alias: str = Field(..., alias="as")

    class Config:
        populate_by_name = True


class AggregateConfig(BaseModel):
    """Configuration for Aggregate node."""
    group_by: list[str] = Field(..., alias="groupBy")
    aggregations: list[AggregationSpec]

    class Config:
        populate_by_name = True


class SortConfig(BaseModel):
    """Configuration for Sort node."""
    columns: list[str]
    ascending: bool | list[bool] = True


class FormulaConfig(BaseModel):
    """Configuration for Formula node."""
    new_col: str = Field(..., alias="newCol")
    expression: str

    class Config:
        populate_by_name = True


class OutputConfig(BaseModel):
    """Configuration for Output node."""
    format: Literal["csv"] = "csv"


# === Workflow Structure ===

class WorkflowNode(BaseModel):
    """A node in the workflow graph."""
    id: str
    type: str
    config: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] | None = None  # For UI positioning


class WorkflowEdge(BaseModel):
    """An edge connecting two nodes."""
    from_node_id: str = Field(..., alias="fromNodeId")
    from_port: str = Field(default="out", alias="fromPort")
    to_node_id: str = Field(..., alias="toNodeId")
    to_port: str = Field(default="in", alias="toPort")

    class Config:
        populate_by_name = True


class Workflow(BaseModel):
    """Complete workflow definition."""
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]


# === API Models ===

class UploadResponse(BaseModel):
    """Response from file upload."""
    upload_id: str
    filename: str
    rows: int
    columns: list[str]
    preview: list[dict[str, Any]]


class RunWorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    workflow: Workflow
    uploads: list[str] = Field(default_factory=list)


class NodeOutput(BaseModel):
    """Output from a single node."""
    node_id: str
    success: bool
    rows: int = 0
    columns: list[str] = Field(default_factory=list)
    preview: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class RunWorkflowResponse(BaseModel):
    """Response from workflow execution."""
    status: Literal["success", "partial", "error"]
    node_outputs: dict[str, NodeOutput]
    final_output_url: str | None = None
    errors: list[str] = Field(default_factory=list)
