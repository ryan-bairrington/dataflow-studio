"""Pytest fixtures for DataFlow Studio tests."""
import tempfile
from pathlib import Path

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.engine import WorkflowExecutor
from app.engine.nodes.io_nodes import ReadCSVNode, OutputNode


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for uploads and outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        upload_dir = tmppath / "uploads"
        output_dir = tmppath / "outputs"
        upload_dir.mkdir()
        output_dir.mkdir()
        
        yield upload_dir, output_dir


@pytest.fixture
def executor(temp_dirs):
    """Create a WorkflowExecutor with temporary directories."""
    upload_dir, output_dir = temp_dirs
    return WorkflowExecutor(upload_dir, output_dir)


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'department': ['Sales', 'Engineering', 'Sales', 'Engineering', 'Marketing'],
        'salary': [50000, 75000, 55000, 80000, 60000]
    })


@pytest.fixture
def sample_csv_file(temp_dirs, sample_df):
    """Create a sample CSV file in the upload directory."""
    upload_dir, _ = temp_dirs
    file_id = "test-upload-123"
    file_path = upload_dir / f"{file_id}.csv"
    sample_df.to_csv(file_path, index=False)
    
    # Configure ReadCSVNode to use this directory
    ReadCSVNode.upload_dir = upload_dir
    
    return file_id, file_path
