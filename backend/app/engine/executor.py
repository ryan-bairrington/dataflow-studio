"""Workflow execution engine.

This module handles the execution of workflow graphs:
1. Parses workflow JSON into a DAG
2. Performs topological sort to determine execution order
3. Executes each node in order, passing data between them
4. Handles errors and provides per-node status

Key Design Decisions:
- Nodes are executed lazily (only when their outputs are needed)
- Intermediate results are cached for efficiency
- Each node receives copies of input DataFrames to prevent mutation issues
"""
from collections import defaultdict
from pathlib import Path
from typing import Any
import logging

import pandas as pd

from .nodes import NODE_REGISTRY, BaseNode, NodeResult
from .nodes.io_nodes import ReadCSVNode, OutputNode

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Base exception for workflow execution errors."""
    pass


class CycleDetectedError(WorkflowError):
    """Raised when a cycle is detected in the workflow graph."""
    pass


class NodeNotFoundError(WorkflowError):
    """Raised when a referenced node doesn't exist."""
    pass


class WorkflowExecutor:
    """Execute workflow graphs.
    
    Usage:
        executor = WorkflowExecutor(upload_dir, output_dir)
        results = executor.execute(workflow_json)
    """
    
    def __init__(self, upload_dir: Path, output_dir: Path):
        """Initialize the executor.
        
        Args:
            upload_dir: Directory where uploaded files are stored
            output_dir: Directory where output files will be written
        """
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        
        # Set class-level directories for I/O nodes
        ReadCSVNode.upload_dir = self.upload_dir
        OutputNode.output_dir = self.output_dir
    
    def execute(
        self, 
        workflow: dict[str, Any]
    ) -> dict[str, NodeResult]:
        """Execute a complete workflow.
        
        Args:
            workflow: Workflow definition with 'nodes' and 'edges'
            
        Returns:
            Dictionary mapping node IDs to their execution results
            
        Raises:
            WorkflowError: If workflow is invalid or execution fails
        """
        nodes_config = workflow.get('nodes', [])
        edges_config = workflow.get('edges', [])
        
        if not nodes_config:
            raise WorkflowError("Workflow has no nodes")
        
        # Build the graph
        nodes, adjacency, reverse_adj = self._build_graph(nodes_config, edges_config)
        
        # Topological sort to get execution order
        execution_order = self._topological_sort(nodes, adjacency)
        
        logger.info(f"Execution order: {execution_order}")
        
        # Execute nodes in order
        results: dict[str, NodeResult] = {}
        outputs: dict[str, pd.DataFrame] = {}  # Cache of node outputs
        
        for node_id in execution_order:
            node = nodes[node_id]
            
            # Gather inputs from upstream nodes
            inputs = self._gather_inputs(node_id, reverse_adj, outputs, edges_config)
            
            # Execute the node
            logger.info(f"Executing node: {node_id} ({node.node_type})")
            
            try:
                result = node.execute(inputs)
                results[node_id] = result
                
                if result.success and result.data is not None:
                    outputs[node_id] = result.data
                    logger.info(
                        f"Node {node_id} succeeded: {result.rows} rows, "
                        f"{len(result.columns)} columns"
                    )
                else:
                    logger.warning(f"Node {node_id} failed: {result.error}")
                    # Don't stop on error - continue with other branches
                    
            except Exception as e:
                logger.error(f"Node {node_id} raised exception: {e}")
                results[node_id] = NodeResult(success=False, error=str(e))
        
        return results
    
    def _build_graph(
        self,
        nodes_config: list[dict[str, Any]],
        edges_config: list[dict[str, Any]]
    ) -> tuple[
        dict[str, BaseNode],
        dict[str, list[str]],
        dict[str, list[tuple[str, str, str]]]
    ]:
        """Build the workflow graph from configuration.
        
        Args:
            nodes_config: List of node definitions
            edges_config: List of edge definitions
            
        Returns:
            Tuple of:
            - nodes: Dict of node_id -> BaseNode instance
            - adjacency: Dict of node_id -> list of downstream node_ids
            - reverse_adj: Dict of node_id -> list of (upstream_id, from_port, to_port)
        """
        nodes: dict[str, BaseNode] = {}
        adjacency: dict[str, list[str]] = defaultdict(list)
        reverse_adj: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        
        # Create node instances
        for node_def in nodes_config:
            node_id = node_def['id']
            node_type = node_def['type']
            config = node_def.get('config', {})
            
            if node_type not in NODE_REGISTRY:
                raise WorkflowError(f"Unknown node type: {node_type}")
            
            node_class = NODE_REGISTRY[node_type]
            nodes[node_id] = node_class(node_id, config)
        
        # Build adjacency lists from edges
        for edge in edges_config:
            from_node = edge.get('fromNodeId', edge.get('from_node_id'))
            to_node = edge.get('toNodeId', edge.get('to_node_id'))
            from_port = edge.get('fromPort', edge.get('from_port', 'out'))
            to_port = edge.get('toPort', edge.get('to_port', 'in'))
            
            if from_node not in nodes:
                raise NodeNotFoundError(f"Edge references unknown node: {from_node}")
            if to_node not in nodes:
                raise NodeNotFoundError(f"Edge references unknown node: {to_node}")
            
            adjacency[from_node].append(to_node)
            reverse_adj[to_node].append((from_node, from_port, to_port))
        
        return nodes, dict(adjacency), dict(reverse_adj)
    
    def _topological_sort(
        self,
        nodes: dict[str, BaseNode],
        adjacency: dict[str, list[str]]
    ) -> list[str]:
        """Perform topological sort using Kahn's algorithm.
        
        Args:
            nodes: All nodes in the graph
            adjacency: Forward adjacency list
            
        Returns:
            List of node IDs in execution order
            
        Raises:
            CycleDetectedError: If the graph contains a cycle
        """
        # Calculate in-degrees
        in_degree: dict[str, int] = {node_id: 0 for node_id in nodes}
        for source, targets in adjacency.items():
            for target in targets:
                in_degree[target] += 1
        
        # Start with nodes that have no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort for deterministic ordering
            queue.sort()
            node_id = queue.pop(0)
            result.append(node_id)
            
            # Reduce in-degree of downstream nodes
            for downstream in adjacency.get(node_id, []):
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    queue.append(downstream)
        
        if len(result) != len(nodes):
            raise CycleDetectedError("Workflow contains a cycle")
        
        return result
    
    def _gather_inputs(
        self,
        node_id: str,
        reverse_adj: dict[str, list[tuple[str, str, str]]],
        outputs: dict[str, pd.DataFrame],
        edges_config: list[dict[str, Any]]
    ) -> list[pd.DataFrame]:
        """Gather input DataFrames for a node.
        
        Args:
            node_id: ID of the node needing inputs
            reverse_adj: Reverse adjacency list with port info
            outputs: Cached outputs from executed nodes
            edges_config: Original edge definitions (for port ordering)
            
        Returns:
            List of input DataFrames, ordered by input port
        """
        upstream_nodes = reverse_adj.get(node_id, [])
        
        if not upstream_nodes:
            return []  # Source node with no inputs
        
        # Sort inputs by port name to ensure consistent ordering
        # Convention: 'in' or 'in_0' is first, 'in_1' is second, etc.
        sorted_inputs = sorted(upstream_nodes, key=lambda x: x[2])  # Sort by to_port
        
        inputs = []
        for upstream_id, from_port, to_port in sorted_inputs:
            if upstream_id in outputs:
                # Create a copy to prevent mutation issues
                inputs.append(outputs[upstream_id].copy())
            else:
                # Upstream node didn't produce output (likely failed)
                logger.warning(f"Missing output from {upstream_id} for {node_id}")
        
        return inputs
    
    def get_node_info(self) -> list[dict[str, Any]]:
        """Get information about available node types.
        
        Returns:
            List of dicts with node type metadata
        """
        return [
            {
                'type': node_type,
                'displayName': cls.display_name,
                'description': cls.description,
                'inputCount': cls("temp", {}).input_count,
                'outputCount': cls("temp", {}).output_count,
            }
            for node_type, cls in NODE_REGISTRY.items()
        ]
