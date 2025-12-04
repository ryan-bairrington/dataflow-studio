"""Nodes for combining and aggregating data."""
from typing import Any

import pandas as pd

from .base import BaseNode, NodeResult


class JoinNode(BaseNode):
    """Join two DataFrames together.
    
    Config:
        leftKey (str): Column name for left side of join
        rightKey (str): Column name for right side of join
        how (str): Join type - 'inner', 'left', 'right', 'outer'
    
    Inputs:
        - First input (index 0): Left DataFrame
        - Second input (index 1): Right DataFrame
    """
    
    node_type = "Join"
    display_name = "Join"
    description = "Combine two datasets based on matching keys"
    
    @property
    def input_count(self) -> int:
        return 2  # Requires two inputs
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Join two DataFrames."""
        if len(inputs) < 2:
            return NodeResult(
                success=False, 
                error=f"Join requires 2 inputs, got {len(inputs)}"
            )
        
        left_df = inputs[0]
        right_df = inputs[1]
        
        left_key = self.config.get('leftKey', self.config.get('left_key'))
        right_key = self.config.get('rightKey', self.config.get('right_key'))
        how = self.config.get('how', 'inner')
        
        if not left_key:
            return NodeResult(success=False, error="leftKey is required")
        if not right_key:
            return NodeResult(success=False, error="rightKey is required")
        
        # Validate keys exist
        if left_key not in left_df.columns:
            return NodeResult(
                success=False,
                error=f"Left key '{left_key}' not found in left dataset. Available: {list(left_df.columns)}"
            )
        if right_key not in right_df.columns:
            return NodeResult(
                success=False,
                error=f"Right key '{right_key}' not found in right dataset. Available: {list(right_df.columns)}"
            )
        
        # Validate join type
        valid_joins = {'inner', 'left', 'right', 'outer'}
        if how not in valid_joins:
            return NodeResult(
                success=False,
                error=f"Invalid join type: {how}. Must be one of: {valid_joins}"
            )
        
        try:
            # Handle column name conflicts by adding suffixes
            result = pd.merge(
                left_df, 
                right_df,
                left_on=left_key,
                right_on=right_key,
                how=how,
                suffixes=('_left', '_right')
            )
            
            return NodeResult(
                success=True,
                data=result,
                metadata={
                    'left_key': left_key,
                    'right_key': right_key,
                    'join_type': how,
                    'left_rows': len(left_df),
                    'right_rows': len(right_df),
                    'result_rows': len(result)
                }
            )
        except Exception as e:
            return NodeResult(success=False, error=f"Join failed: {e}")
    
    def validate_config(self) -> tuple[bool, str | None]:
        left_key = self.config.get('leftKey', self.config.get('left_key'))
        right_key = self.config.get('rightKey', self.config.get('right_key'))
        
        if not left_key:
            return False, "leftKey is required"
        if not right_key:
            return False, "rightKey is required"
        
        how = self.config.get('how', 'inner')
        if how not in {'inner', 'left', 'right', 'outer'}:
            return False, f"Invalid join type: {how}"
        
        return True, None


class AggregateNode(BaseNode):
    """Aggregate data by grouping columns.
    
    Config:
        groupBy (list[str]): Columns to group by
        aggregations (list[dict]): List of aggregation specs:
            - col (str): Column to aggregate
            - op (str): Operation - 'sum', 'mean', 'count', 'min', 'max', 'first', 'last'
            - as (str): Alias for result column
    """
    
    node_type = "Aggregate"
    display_name = "Aggregate"
    description = "Group data and calculate summaries"
    
    VALID_OPS = {'sum', 'mean', 'count', 'min', 'max', 'first', 'last', 'std', 'var'}
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Aggregate DataFrame by groups."""
        if not inputs:
            return NodeResult(success=False, error="No input data")
        
        df = inputs[0]
        group_by = self.config.get('groupBy', self.config.get('group_by', []))
        aggregations = self.config.get('aggregations', [])
        
        if not group_by:
            return NodeResult(success=False, error="groupBy columns are required")
        if not aggregations:
            return NodeResult(success=False, error="At least one aggregation is required")
        
        # Validate group columns
        missing_groups = [c for c in group_by if c not in df.columns]
        if missing_groups:
            return NodeResult(
                success=False,
                error=f"Group columns not found: {', '.join(missing_groups)}"
            )
        
        # Build aggregation dict for pandas
        agg_dict = {}
        rename_map = {}
        
        for agg in aggregations:
            col = agg.get('col')
            op = agg.get('op')
            alias = agg.get('as', agg.get('alias', f"{col}_{op}"))
            
            if not col:
                return NodeResult(success=False, error="Aggregation missing 'col'")
            if not op:
                return NodeResult(success=False, error="Aggregation missing 'op'")
            
            if op not in self.VALID_OPS:
                return NodeResult(
                    success=False,
                    error=f"Invalid aggregation op: {op}. Valid: {self.VALID_OPS}"
                )
            
            if col not in df.columns:
                return NodeResult(
                    success=False,
                    error=f"Aggregation column not found: {col}"
                )
            
            # Handle count specially (can be applied to any column)
            agg_key = (col, op)
            agg_dict[alias] = (col, op)
        
        try:
            # Use named aggregation syntax
            grouped = df.groupby(group_by, as_index=False)
            result = grouped.agg(**{alias: (col, op) for alias, (col, op) in agg_dict.items()})
            
            return NodeResult(
                success=True,
                data=result,
                metadata={
                    'group_by': group_by,
                    'aggregations': aggregations,
                    'unique_groups': len(result)
                }
            )
        except Exception as e:
            return NodeResult(success=False, error=f"Aggregation failed: {e}")
    
    def validate_config(self) -> tuple[bool, str | None]:
        group_by = self.config.get('groupBy', self.config.get('group_by', []))
        if not group_by:
            return False, "groupBy is required"
        
        aggregations = self.config.get('aggregations', [])
        if not aggregations:
            return False, "At least one aggregation is required"
        
        for agg in aggregations:
            if not agg.get('col'):
                return False, "Each aggregation needs a 'col'"
            if not agg.get('op'):
                return False, "Each aggregation needs an 'op'"
            if agg.get('op') not in self.VALID_OPS:
                return False, f"Invalid op: {agg.get('op')}"
        
        return True, None
