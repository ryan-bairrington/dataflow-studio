"""Unit tests for workflow nodes."""
import pytest
import pandas as pd

from app.engine.nodes import (
    ReadCSVNode, FilterNode, SelectNode, SortNode, 
    FormulaNode, JoinNode, AggregateNode, OutputNode
)
from app.engine.nodes.io_nodes import ReadCSVNode as ReadCSVNodeClass


class TestFilterNode:
    """Tests for the FilterNode."""
    
    def test_filter_basic(self, sample_df):
        """Test basic filtering."""
        node = FilterNode("filter-1", {"expression": "age > 30"})
        result = node.execute([sample_df])
        
        assert result.success
        assert result.rows == 3  # Charlie, David, Eve
        assert all(result.data['age'] > 30)
    
    def test_filter_string_equality(self, sample_df):
        """Test filtering with string comparison."""
        node = FilterNode("filter-2", {"expression": "department == 'Sales'"})
        result = node.execute([sample_df])
        
        assert result.success
        assert result.rows == 2  # Alice, Charlie
    
    def test_filter_and_condition(self, sample_df):
        """Test filtering with AND condition."""
        node = FilterNode("filter-3", {
            "expression": "age > 30 and department == 'Engineering'"
        })
        result = node.execute([sample_df])
        
        assert result.success
        assert result.rows == 1  # David
    
    def test_filter_invalid_expression(self, sample_df):
        """Test that invalid expressions are rejected."""
        node = FilterNode("filter-4", {"expression": "exec('malicious')"})
        result = node.execute([sample_df])
        
        assert not result.success
        assert "forbidden" in result.error.lower() or "failed" in result.error.lower()
    
    def test_filter_empty_expression(self, sample_df):
        """Test that empty expression passes through all data."""
        node = FilterNode("filter-5", {"expression": ""})
        result = node.execute([sample_df])
        
        assert result.success
        assert result.rows == len(sample_df)


class TestSelectNode:
    """Tests for the SelectNode."""
    
    def test_select_columns(self, sample_df):
        """Test selecting specific columns."""
        node = SelectNode("select-1", {"columns": ["name", "salary"]})
        result = node.execute([sample_df])
        
        assert result.success
        assert result.columns == ["name", "salary"]
        assert result.rows == len(sample_df)
    
    def test_select_missing_column(self, sample_df):
        """Test error when selecting non-existent column."""
        node = SelectNode("select-2", {"columns": ["name", "nonexistent"]})
        result = node.execute([sample_df])
        
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_select_empty_list(self, sample_df):
        """Test that empty column list returns all columns."""
        node = SelectNode("select-3", {"columns": []})
        result = node.execute([sample_df])
        
        assert result.success
        assert result.columns == list(sample_df.columns)


class TestSortNode:
    """Tests for the SortNode."""
    
    def test_sort_ascending(self, sample_df):
        """Test sorting in ascending order."""
        node = SortNode("sort-1", {"columns": ["age"], "ascending": True})
        result = node.execute([sample_df])
        
        assert result.success
        assert list(result.data['age']) == [25, 30, 35, 40, 45]
    
    def test_sort_descending(self, sample_df):
        """Test sorting in descending order."""
        node = SortNode("sort-2", {"columns": ["salary"], "ascending": False})
        result = node.execute([sample_df])
        
        assert result.success
        assert list(result.data['salary']) == [80000, 75000, 60000, 55000, 50000]
    
    def test_sort_multiple_columns(self, sample_df):
        """Test sorting by multiple columns."""
        node = SortNode("sort-3", {
            "columns": ["department", "age"],
            "ascending": [True, False]
        })
        result = node.execute([sample_df])
        
        assert result.success


class TestFormulaNode:
    """Tests for the FormulaNode."""
    
    def test_formula_arithmetic(self, sample_df):
        """Test arithmetic formula."""
        node = FormulaNode("formula-1", {
            "newCol": "salary_with_bonus",
            "expression": "salary * 1.1"
        })
        result = node.execute([sample_df])
        
        assert result.success
        assert "salary_with_bonus" in result.columns
        assert result.data['salary_with_bonus'].iloc[0] == 55000.0  # 50000 * 1.1
    
    def test_formula_column_reference(self, sample_df):
        """Test formula referencing multiple columns."""
        node = FormulaNode("formula-2", {
            "newCol": "age_salary_ratio",
            "expression": "age * 1000 + salary / 1000"
        })
        result = node.execute([sample_df])
        
        assert result.success
        assert "age_salary_ratio" in result.columns
    
    def test_formula_invalid_expression(self, sample_df):
        """Test that invalid expressions are rejected."""
        node = FormulaNode("formula-3", {
            "newCol": "hacked",
            "expression": "__import__('os').system('rm -rf /')"
        })
        result = node.execute([sample_df])
        
        assert not result.success


class TestJoinNode:
    """Tests for the JoinNode."""
    
    def test_inner_join(self):
        """Test inner join."""
        left_df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        right_df = pd.DataFrame({
            'user_id': [2, 3, 4],
            'score': [85, 90, 75]
        })
        
        node = JoinNode("join-1", {
            "leftKey": "id",
            "rightKey": "user_id",
            "how": "inner"
        })
        result = node.execute([left_df, right_df])
        
        assert result.success
        assert result.rows == 2  # Only IDs 2 and 3 match
    
    def test_left_join(self):
        """Test left join."""
        left_df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        right_df = pd.DataFrame({
            'user_id': [2, 3, 4],
            'score': [85, 90, 75]
        })
        
        node = JoinNode("join-2", {
            "leftKey": "id",
            "rightKey": "user_id",
            "how": "left"
        })
        result = node.execute([left_df, right_df])
        
        assert result.success
        assert result.rows == 3  # All left rows preserved
    
    def test_join_missing_inputs(self):
        """Test error when join has insufficient inputs."""
        left_df = pd.DataFrame({'id': [1, 2, 3]})
        
        node = JoinNode("join-3", {
            "leftKey": "id",
            "rightKey": "id",
            "how": "inner"
        })
        result = node.execute([left_df])  # Only one input
        
        assert not result.success
        assert "2 inputs" in result.error


class TestAggregateNode:
    """Tests for the AggregateNode."""
    
    def test_aggregate_sum(self, sample_df):
        """Test sum aggregation."""
        node = AggregateNode("agg-1", {
            "groupBy": ["department"],
            "aggregations": [
                {"col": "salary", "op": "sum", "as": "total_salary"}
            ]
        })
        result = node.execute([sample_df])
        
        assert result.success
        assert "total_salary" in result.columns
        assert result.rows == 3  # 3 departments
    
    def test_aggregate_multiple_ops(self, sample_df):
        """Test multiple aggregations."""
        node = AggregateNode("agg-2", {
            "groupBy": ["department"],
            "aggregations": [
                {"col": "salary", "op": "sum", "as": "total_salary"},
                {"col": "salary", "op": "mean", "as": "avg_salary"},
                {"col": "age", "op": "count", "as": "employee_count"}
            ]
        })
        result = node.execute([sample_df])
        
        assert result.success
        assert set(result.columns) == {
            "department", "total_salary", "avg_salary", "employee_count"
        }
    
    def test_aggregate_invalid_column(self, sample_df):
        """Test error with non-existent column."""
        node = AggregateNode("agg-3", {
            "groupBy": ["nonexistent"],
            "aggregations": [
                {"col": "salary", "op": "sum", "as": "total"}
            ]
        })
        result = node.execute([sample_df])
        
        assert not result.success


class TestReadCSVNode:
    """Tests for ReadCSVNode."""
    
    def test_read_csv(self, sample_csv_file):
        """Test reading a CSV file."""
        file_id, _ = sample_csv_file
        
        node = ReadCSVNode("read-1", {"upload_id": file_id})
        result = node.execute([])
        
        assert result.success
        assert result.rows == 5
        assert "name" in result.columns
    
    def test_read_csv_missing_file(self, temp_dirs):
        """Test error when file doesn't exist."""
        upload_dir, _ = temp_dirs
        ReadCSVNodeClass.upload_dir = upload_dir
        
        node = ReadCSVNode("read-2", {"upload_id": "nonexistent-id"})
        result = node.execute([])
        
        assert not result.success
        assert "not found" in result.error.lower()
