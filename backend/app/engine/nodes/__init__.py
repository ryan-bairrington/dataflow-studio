"""Node implementations for the workflow engine."""
from .base import BaseNode, NodeResult
from .io_nodes import ReadCSVNode, OutputNode
from .transform_nodes import FilterNode, SelectNode, SortNode, FormulaNode
from .combine_nodes import JoinNode, AggregateNode

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    "ReadCSV": ReadCSVNode,
    "Filter": FilterNode,
    "Select": SelectNode,
    "Join": JoinNode,
    "Aggregate": AggregateNode,
    "Sort": SortNode,
    "Formula": FormulaNode,
    "Output": OutputNode,
}

__all__ = [
    "BaseNode",
    "NodeResult",
    "NODE_REGISTRY",
    "ReadCSVNode",
    "FilterNode",
    "SelectNode",
    "JoinNode",
    "AggregateNode",
    "SortNode",
    "FormulaNode",
    "OutputNode",
]
