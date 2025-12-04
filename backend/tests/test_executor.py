"""Tests for the workflow executor."""
import pytest
import pandas as pd

from app.engine import WorkflowExecutor
from app.engine.executor import CycleDetectedError, WorkflowError
from app.engine.nodes.io_nodes import ReadCSVNode


class TestWorkflowExecutor:
    """Tests for WorkflowExecutor."""
    
    def test_simple_workflow(self, executor, sample_csv_file):
        """Test a simple read -> filter -> select workflow."""
        file_id, _ = sample_csv_file
        
        workflow = {
            "nodes": [
                {"id": "read", "type": "ReadCSV", "config": {"upload_id": file_id}},
                {"id": "filter", "type": "Filter", "config": {"expression": "age > 30"}},
                {"id": "select", "type": "Select", "config": {"columns": ["name", "age"]}}
            ],
            "edges": [
                {"fromNodeId": "read", "toNodeId": "filter"},
                {"fromNodeId": "filter", "toNodeId": "select"}
            ]
        }
        
        results = executor.execute(workflow)
        
        assert "read" in results
        assert "filter" in results
        assert "select" in results
        
        assert results["read"].success
        assert results["filter"].success
        assert results["select"].success
        
        # Check final output
        final = results["select"]
        assert final.rows == 3  # Charlie, David, Eve (age > 30)
        assert final.columns == ["name", "age"]
    
    def test_workflow_with_join(self, executor, temp_dirs):
        """Test a workflow with a join node."""
        upload_dir, _ = temp_dirs
        ReadCSVNode.upload_dir = upload_dir
        
        # Create two CSV files
        employees = pd.DataFrame({
            'emp_id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        salaries = pd.DataFrame({
            'employee_id': [1, 2, 3],
            'salary': [50000, 60000, 70000]
        })
        
        employees.to_csv(upload_dir / "emp.csv", index=False)
        salaries.to_csv(upload_dir / "sal.csv", index=False)
        
        workflow = {
            "nodes": [
                {"id": "read-emp", "type": "ReadCSV", "config": {"upload_id": "emp"}},
                {"id": "read-sal", "type": "ReadCSV", "config": {"upload_id": "sal"}},
                {"id": "join", "type": "Join", "config": {
                    "leftKey": "emp_id",
                    "rightKey": "employee_id",
                    "how": "inner"
                }}
            ],
            "edges": [
                {"fromNodeId": "read-emp", "toNodeId": "join", "toPort": "in"},
                {"fromNodeId": "read-sal", "toNodeId": "join", "toPort": "in_1"}
            ]
        }
        
        results = executor.execute(workflow)
        
        assert results["join"].success
        assert results["join"].rows == 3
        assert "name" in results["join"].columns
        assert "salary" in results["join"].columns
    
    def test_workflow_with_aggregate(self, executor, sample_csv_file):
        """Test workflow with aggregation."""
        file_id, _ = sample_csv_file
        
        workflow = {
            "nodes": [
                {"id": "read", "type": "ReadCSV", "config": {"upload_id": file_id}},
                {"id": "agg", "type": "Aggregate", "config": {
                    "groupBy": ["department"],
                    "aggregations": [
                        {"col": "salary", "op": "sum", "as": "total_salary"},
                        {"col": "age", "op": "mean", "as": "avg_age"}
                    ]
                }}
            ],
            "edges": [
                {"fromNodeId": "read", "toNodeId": "agg"}
            ]
        }
        
        results = executor.execute(workflow)
        
        assert results["agg"].success
        assert results["agg"].rows == 3  # 3 departments
        assert "total_salary" in results["agg"].columns
        assert "avg_age" in results["agg"].columns
    
    def test_cycle_detection(self, executor):
        """Test that cycles in the workflow are detected."""
        workflow = {
            "nodes": [
                {"id": "a", "type": "Filter", "config": {"expression": ""}},
                {"id": "b", "type": "Filter", "config": {"expression": ""}},
                {"id": "c", "type": "Filter", "config": {"expression": ""}}
            ],
            "edges": [
                {"fromNodeId": "a", "toNodeId": "b"},
                {"fromNodeId": "b", "toNodeId": "c"},
                {"fromNodeId": "c", "toNodeId": "a"}  # Creates cycle
            ]
        }
        
        with pytest.raises(CycleDetectedError):
            executor.execute(workflow)
    
    def test_empty_workflow(self, executor):
        """Test error on empty workflow."""
        workflow = {"nodes": [], "edges": []}
        
        with pytest.raises(WorkflowError, match="no nodes"):
            executor.execute(workflow)
    
    def test_unknown_node_type(self, executor):
        """Test error on unknown node type."""
        workflow = {
            "nodes": [{"id": "x", "type": "UnknownNode", "config": {}}],
            "edges": []
        }
        
        with pytest.raises(WorkflowError, match="Unknown node type"):
            executor.execute(workflow)
