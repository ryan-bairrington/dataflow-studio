"""Transformation nodes for filtering, selecting, and modifying data."""
from typing import Any

import pandas as pd

from .base import BaseNode, NodeResult
from ..parser import SafeExpressionParser, ExpressionError


class FilterNode(BaseNode):
    """Filter rows based on an expression.
    
    Config:
        expression (str): Filter expression (e.g., "age > 18 and status == 'active'")
    """
    
    node_type = "Filter"
    display_name = "Filter"
    description = "Filter rows based on a condition"
    
    def __init__(self, node_id: str, config: dict[str, Any]):
        super().__init__(node_id, config)
        self.parser = SafeExpressionParser()
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Filter DataFrame based on expression."""
        if not inputs:
            return NodeResult(success=False, error="No input data to filter")
        
        df = inputs[0]
        expression = self.config.get('expression', '')
        
        if not expression:
            # No filter = pass through
            return NodeResult(success=True, data=df)
        
        try:
            result = self.parser.evaluate_filter(df, expression)
            return NodeResult(
                success=True,
                data=result,
                metadata={'expression': expression, 'filtered_rows': len(df) - len(result)}
            )
        except ExpressionError as e:
            return NodeResult(success=False, error=str(e))
        except Exception as e:
            return NodeResult(success=False, error=f"Filter failed: {e}")
    
    def validate_config(self) -> tuple[bool, str | None]:
        expression = self.config.get('expression')
        if expression:
            is_valid, error = self.parser.validate(expression)
            if not is_valid:
                return False, error
        return True, None


class SelectNode(BaseNode):
    """Select specific columns from the data.
    
    Config:
        columns (list[str]): List of column names to select
    """
    
    node_type = "Select"
    display_name = "Select Columns"
    description = "Choose which columns to keep"
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Select specified columns."""
        if not inputs:
            return NodeResult(success=False, error="No input data")
        
        df = inputs[0]
        columns = self.config.get('columns', [])
        
        if not columns:
            return NodeResult(success=True, data=df)  # No columns specified = all columns
        
        # Validate columns exist
        missing = [c for c in columns if c not in df.columns]
        if missing:
            return NodeResult(
                success=False, 
                error=f"Columns not found: {', '.join(missing)}"
            )
        
        try:
            result = df[columns].copy()
            return NodeResult(
                success=True,
                data=result,
                metadata={'selected_columns': columns}
            )
        except Exception as e:
            return NodeResult(success=False, error=f"Select failed: {e}")
    
    def validate_config(self) -> tuple[bool, str | None]:
        columns = self.config.get('columns')
        if columns is not None and not isinstance(columns, list):
            return False, "columns must be a list"
        return True, None


class SortNode(BaseNode):
    """Sort data by specified columns.
    
    Config:
        columns (list[str]): Columns to sort by
        ascending (bool | list[bool]): Sort direction(s)
    """
    
    node_type = "Sort"
    display_name = "Sort"
    description = "Sort rows by column values"
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Sort DataFrame by specified columns."""
        if not inputs:
            return NodeResult(success=False, error="No input data")
        
        df = inputs[0]
        columns = self.config.get('columns', [])
        ascending = self.config.get('ascending', True)
        
        if not columns:
            return NodeResult(success=True, data=df)  # Nothing to sort
        
        # Validate columns
        missing = [c for c in columns if c not in df.columns]
        if missing:
            return NodeResult(
                success=False,
                error=f"Sort columns not found: {', '.join(missing)}"
            )
        
        try:
            result = df.sort_values(by=columns, ascending=ascending).reset_index(drop=True)
            return NodeResult(
                success=True,
                data=result,
                metadata={'sort_columns': columns, 'ascending': ascending}
            )
        except Exception as e:
            return NodeResult(success=False, error=f"Sort failed: {e}")


class FormulaNode(BaseNode):
    """Create a new column using a formula expression.
    
    Config:
        newCol (str): Name of the new column to create
        expression (str): Formula expression (e.g., "price * quantity")
    """
    
    node_type = "Formula"
    display_name = "Formula"
    description = "Create a calculated column"
    
    def __init__(self, node_id: str, config: dict[str, Any]):
        super().__init__(node_id, config)
        self.parser = SafeExpressionParser()
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Add new calculated column to DataFrame."""
        if not inputs:
            return NodeResult(success=False, error="No input data")
        
        df = inputs[0]
        new_col = self.config.get('newCol', self.config.get('new_col'))
        expression = self.config.get('expression', '')
        
        if not new_col:
            return NodeResult(success=False, error="newCol is required")
        
        if not expression:
            return NodeResult(success=False, error="expression is required")
        
        try:
            result = self.parser.evaluate_formula(df, expression, new_col)
            return NodeResult(
                success=True,
                data=result,
                metadata={'new_column': new_col, 'expression': expression}
            )
        except ExpressionError as e:
            return NodeResult(success=False, error=str(e))
        except Exception as e:
            return NodeResult(success=False, error=f"Formula failed: {e}")
    
    def validate_config(self) -> tuple[bool, str | None]:
        new_col = self.config.get('newCol', self.config.get('new_col'))
        if not new_col:
            return False, "newCol is required"
        
        expression = self.config.get('expression')
        if expression:
            is_valid, error = self.parser.validate(expression)
            if not is_valid:
                return False, error
        else:
            return False, "expression is required"
        
        return True, None
