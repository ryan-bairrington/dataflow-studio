"""Integration tests for the API endpoints."""
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestUploadEndpoint:
    """Tests for /api/upload endpoint."""
    
    def test_upload_csv(self, client):
        """Test successful CSV upload."""
        csv_content = b"name,age,city\nAlice,30,NYC\nBob,25,LA\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert data["filename"] == "test.csv"
        assert data["rows"] == 2
        assert data["columns"] == ["name", "age", "city"]
    
    def test_upload_invalid_file_type(self, client):
        """Test rejection of non-CSV files."""
        files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        assert "CSV" in response.json()["detail"]


class TestRunWorkflowEndpoint:
    """Tests for /api/run-workflow endpoint."""
    
    def test_run_simple_workflow(self, client):
        """Test running a simple workflow end-to-end."""
        # First upload a file
        csv_content = b"id,name,age,score\n1,Alice,30,85\n2,Bob,25,90\n3,Charlie,35,75\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        upload_response = client.post("/api/upload", files=files)
        upload_id = upload_response.json()["upload_id"]
        
        # Run a workflow
        workflow = {
            "workflow": {
                "nodes": [
                    {"id": "read", "type": "ReadCSV", "config": {"upload_id": upload_id}},
                    {"id": "filter", "type": "Filter", "config": {"expression": "age > 25"}},
                    {"id": "output", "type": "Output", "config": {"format": "csv"}}
                ],
                "edges": [
                    {"fromNodeId": "read", "toNodeId": "filter"},
                    {"fromNodeId": "filter", "toNodeId": "output"}
                ]
            },
            "uploads": [upload_id]
        }
        
        response = client.post("/api/run-workflow", json=workflow)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "read" in data["node_outputs"]
        assert "filter" in data["node_outputs"]
        assert "output" in data["node_outputs"]
        
        # Check filter results
        filter_output = data["node_outputs"]["filter"]
        assert filter_output["success"]
        assert filter_output["rows"] == 2  # Alice (30) and Charlie (35)
        
        # Check download URL is present
        assert data["final_output_url"] is not None
    
    def test_run_workflow_with_aggregate(self, client):
        """Test workflow with join and aggregation."""
        # Upload data
        csv_content = b"dept,emp,salary\nSales,Alice,50000\nSales,Bob,55000\nEng,Charlie,70000\n"
        files = {"file": ("employees.csv", io.BytesIO(csv_content), "text/csv")}
        upload_response = client.post("/api/upload", files=files)
        upload_id = upload_response.json()["upload_id"]
        
        workflow = {
            "workflow": {
                "nodes": [
                    {"id": "read", "type": "ReadCSV", "config": {"upload_id": upload_id}},
                    {"id": "agg", "type": "Aggregate", "config": {
                        "groupBy": ["dept"],
                        "aggregations": [
                            {"col": "salary", "op": "sum", "as": "total_salary"},
                            {"col": "emp", "op": "count", "as": "headcount"}
                        ]
                    }}
                ],
                "edges": [
                    {"fromNodeId": "read", "toNodeId": "agg"}
                ]
            }
        }
        
        response = client.post("/api/run-workflow", json=workflow)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        agg_output = data["node_outputs"]["agg"]
        assert agg_output["success"]
        assert agg_output["rows"] == 2  # 2 departments
        assert "total_salary" in agg_output["columns"]
        assert "headcount" in agg_output["columns"]


class TestDownloadEndpoint:
    """Tests for /api/download endpoint."""
    
    def test_download_output(self, client):
        """Test downloading workflow output."""
        # Upload and run workflow with output
        csv_content = b"x,y\n1,2\n3,4\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        upload_response = client.post("/api/upload", files=files)
        upload_id = upload_response.json()["upload_id"]
        
        workflow = {
            "workflow": {
                "nodes": [
                    {"id": "read", "type": "ReadCSV", "config": {"upload_id": upload_id}},
                    {"id": "output", "type": "Output", "config": {"format": "csv"}}
                ],
                "edges": [
                    {"fromNodeId": "read", "toNodeId": "output"}
                ]
            }
        }
        
        run_response = client.post("/api/run-workflow", json=workflow)
        download_url = run_response.json()["final_output_url"]
        
        # Download the file
        download_response = client.get(download_url)
        
        assert download_response.status_code == 200
        assert "text/csv" in download_response.headers["content-type"]
    
    def test_download_nonexistent(self, client):
        """Test 404 for non-existent file."""
        response = client.get("/api/download/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    def test_download_invalid_id(self, client):
        """Test 400 for invalid file ID."""
        response = client.get("/api/download/not-a-uuid")
        assert response.status_code == 400


class TestNodesEndpoint:
    """Tests for /api/nodes endpoint."""
    
    def test_get_nodes(self, client):
        """Test getting available node types."""
        response = client.get("/api/nodes")
        
        assert response.status_code == 200
        nodes = response.json()
        
        assert isinstance(nodes, list)
        assert len(nodes) >= 8  # We have 8 node types
        
        # Check structure
        node_types = {n["type"] for n in nodes}
        assert "ReadCSV" in node_types
        assert "Filter" in node_types
        assert "Join" in node_types
        assert "Aggregate" in node_types
        assert "Output" in node_types
