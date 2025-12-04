"""Base classes for workflow nodes.

All node implementations inherit from BaseNode and implement the execute() method.
This provides a consistent interface for the workflow executor.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class NodeResult:
    """Result from node execution."""
    success: bool
    data: pd.DataFrame | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def rows(self) -> int:
        """Get row count from result data."""
        if self.data is not None:
            return len(self.data)
        return 0
    
    @property
    def columns(self) -> list[str]:
        """Get column names from result data."""
        if self.data is not None:
            return list(self.data.columns)
        return []
    
    def preview(self, n: int = 100) -> list[dict[str, Any]]:
        """Get preview of data as list of dicts.
        
        Args:
            n: Maximum number of rows to include
            
        Returns:
            List of row dictionaries
        """
        if self.data is None:
            return []
        return self.data.head(n).to_dict(orient='records')


class BaseNode(ABC):
    """Abstract base class for all workflow nodes.
    
    Each node type must implement:
    - execute(): Perform the node's operation and return a NodeResult
    - input_count: Property indicating how many inputs the node expects
    - output_count: Property indicating how many outputs the node produces
    
    Attributes:
        node_id: Unique identifier for this node instance
        config: Node-specific configuration dictionary
    """
    
    # Class-level metadata
    node_type: str = "Base"
    display_name: str = "Base Node"
    description: str = "Base node class"
    
    def __init__(self, node_id: str, config: dict[str, Any]):
        """Initialize the node.
        
        Args:
            node_id: Unique identifier for this node
            config: Node-specific configuration
        """
        self.node_id = node_id
        self.config = config
    
    @property
    def input_count(self) -> int:
        """Number of input connections expected. Override in subclasses."""
        return 1
    
    @property
    def output_count(self) -> int:
        """Number of output connections produced. Override in subclasses."""
        return 1
    
    @abstractmethod
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Execute the node's operation.
        
        Args:
            inputs: List of input DataFrames (from upstream nodes)
            
        Returns:
            NodeResult containing success status and output data
        """
        pass
    
    def validate_config(self) -> tuple[bool, str | None]:
        """Validate the node's configuration.
        
        Override in subclasses for custom validation.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.node_id!r})"
