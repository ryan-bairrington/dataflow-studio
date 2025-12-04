/**
 * Main canvas component using React Flow.
 * 
 * Handles drag-and-drop, node connections, and the visual workflow.
 */
import React, { useCallback, useRef, useState, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowInstance,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { WorkflowNode } from './WorkflowNode';
import { useWorkflowContext } from '../context/WorkflowContext';
import { NODE_DEFINITIONS_MAP, CATEGORY_COLORS } from '../config/nodeTypes';

// Register custom node types
const nodeTypes: NodeTypes = {
  workflowNode: WorkflowNode,
};

interface CanvasProps {
  onNodeSelect: (nodeId: string | null) => void;
  selectedNodeId: string | null;
}

export function Canvas({ onNodeSelect, selectedNodeId }: CanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  
  const {
    nodes,
    edges,
    nodeStates,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
  } = useWorkflowContext();

  // Inject execution state into node data
  const nodesWithState = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        executionState: nodeStates[node.id],
        selected: node.id === selectedNodeId,
      },
    }));
  }, [nodes, nodeStates, selectedNodeId]);

  // Handle drop from palette
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const nodeType = event.dataTransfer.getData('application/dataflow-node');
      if (!nodeType || !reactFlowInstance || !reactFlowWrapper.current) {
        return;
      }

      // Calculate position relative to the canvas
      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNodeId = addNode(nodeType, position);
      onNodeSelect(newNodeId);
    },
    [reactFlowInstance, addNode, onNodeSelect]
  );

  // Handle node selection
  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: { id: string }) => {
      onNodeSelect(node.id);
    },
    [onNodeSelect]
  );

  // Handle background click (deselect)
  const handlePaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  // MiniMap color function
  const getNodeColor = (node: { data: { nodeType: string } }) => {
    const definition = NODE_DEFINITIONS_MAP.get(node.data.nodeType);
    return definition?.color || CATEGORY_COLORS[definition?.category || 'transform'] || '#888';
  };

  return (
    <div className="canvas-container" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodesWithState}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: true,
        }}
        proOptions={{ hideAttribution: true }}
        aria-label="Workflow canvas"
      >
        <Background gap={15} color="#e0e0e0" />
        <Controls aria-label="Canvas controls" />
        <MiniMap
          nodeColor={getNodeColor}
          nodeStrokeWidth={3}
          zoomable
          pannable
          aria-label="Workflow minimap"
        />
      </ReactFlow>
      
      {/* Empty state hint */}
      {nodes.length === 0 && (
        <div className="canvas-empty-hint">
          <p>👈 Drag nodes from the palette to get started</p>
        </div>
      )}
    </div>
  );
}
