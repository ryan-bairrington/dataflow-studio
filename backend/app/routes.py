"""FastAPI routes for the DataFlow Studio API."""
import uuid
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import pandas as pd

from .models import (
    UploadResponse, 
    RunWorkflowRequest, 
    RunWorkflowResponse,
    NodeOutput,
)
from .engine import WorkflowExecutor
from .engine.executor import WorkflowError
from .engine.nodes import NODE_REGISTRY

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api")

# Storage directories (relative to app root)
DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create executor instance
executor = WorkflowExecutor(UPLOAD_DIR, OUTPUT_DIR)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file for use in workflows.
    
    Args:
        file: The CSV file to upload
        
    Returns:
        Upload ID and file metadata
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=400, 
            detail="Only CSV files are supported"
        )
    
    # Generate unique ID for this upload
    upload_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{upload_id}.csv"
    
    try:
        # Read file content
        content = await file.read()
        
        # Save to disk
        file_path.write_bytes(content)
        
        # Parse to get metadata and preview
        df = pd.read_csv(file_path)
        
        preview = df.head(10).to_dict(orient='records')
        
        logger.info(f"Uploaded file {file.filename} as {upload_id}")
        
        return UploadResponse(
            upload_id=upload_id,
            filename=file.filename,
            rows=len(df),
            columns=list(df.columns),
            preview=preview
        )
        
    except pd.errors.EmptyDataError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")
    except Exception as e:
        file_path.unlink(missing_ok=True)
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.post("/run-workflow", response_model=RunWorkflowResponse)
async def run_workflow(request: RunWorkflowRequest):
    """Execute a workflow and return results.
    
    Args:
        request: Workflow definition and upload references
        
    Returns:
        Execution status and per-node outputs
    """
    workflow_dict = request.workflow.model_dump(by_alias=True)
    
    logger.info(
        f"Running workflow with {len(request.workflow.nodes)} nodes, "
        f"{len(request.workflow.edges)} edges"
    )
    
    try:
        results = executor.execute(workflow_dict)
    except WorkflowError as e:
        logger.error(f"Workflow error: {e}")
        return RunWorkflowResponse(
            status="error",
            node_outputs={},
            errors=[str(e)]
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return RunWorkflowResponse(
            status="error",
            node_outputs={},
            errors=[f"Internal error: {e}"]
        )
    
    # Build response
    node_outputs: dict[str, NodeOutput] = {}
    errors: list[str] = []
    final_output_url: str | None = None
    
    for node_id, result in results.items():
        node_outputs[node_id] = NodeOutput(
            node_id=node_id,
            success=result.success,
            rows=result.rows,
            columns=result.columns,
            preview=result.preview(100),  # Max 100 rows for preview
            error=result.error
        )
        
        if not result.success and result.error:
            errors.append(f"{node_id}: {result.error}")
        
        # Check for Output node with file
        if result.success and result.metadata.get('file_id'):
            file_id = result.metadata['file_id']
            final_output_url = f"/api/download/{file_id}"
    
    # Determine overall status
    if errors:
        status = "partial" if any(r.success for r in results.values()) else "error"
    else:
        status = "success"
    
    return RunWorkflowResponse(
        status=status,
        node_outputs=node_outputs,
        final_output_url=final_output_url,
        errors=errors
    )


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download a generated output file.
    
    Args:
        file_id: The unique file identifier
        
    Returns:
        The CSV file as a download
    """
    # Validate file_id format (should be UUID)
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID format")
    
    file_path = OUTPUT_DIR / f"{file_id}.csv"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=f"output-{file_id[:8]}.csv",
        media_type="text/csv"
    )


@router.get("/nodes")
async def get_available_nodes() -> list[dict[str, Any]]:
    """Get list of available node types with metadata.
    
    Returns:
        List of node type definitions
    """
    return executor.get_node_info()


@router.get("/uploads/{upload_id}")
async def get_upload_info(upload_id: str):
    """Get information about an uploaded file.
    
    Args:
        upload_id: The upload identifier
        
    Returns:
        File metadata and preview
    """
    try:
        uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload ID format")
    
    file_path = UPLOAD_DIR / f"{upload_id}.csv"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Upload not found")
    
    try:
        df = pd.read_csv(file_path)
        return {
            "upload_id": upload_id,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(10).to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")


@router.delete("/uploads/{upload_id}")
async def delete_upload(upload_id: str):
    """Delete an uploaded file.
    
    Args:
        upload_id: The upload identifier
        
    Returns:
        Deletion confirmation
    """
    try:
        uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload ID format")
    
    file_path = UPLOAD_DIR / f"{upload_id}.csv"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Upload not found")
    
    file_path.unlink()
    return {"status": "deleted", "upload_id": upload_id}
