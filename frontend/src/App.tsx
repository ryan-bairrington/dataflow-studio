/**
 * Main application component.
 * 
 * Orchestrates the layout and manages selected node state.
 */
import React, { useState, useCallback, useMemo } from 'react';
import { ReactFlowProvider } from 'reactflow';

import { WorkflowProvider, useWorkflowContext } from './context/WorkflowContext';
import { Toolbar, Palette, Canvas, ConfigPanel, PreviewPanel } from './components';
import { NODE_DEFINITIONS_MAP } from './config/nodeTypes';

function AppContent() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [previewNodeId, setPreviewNodeId] = useState<string | null>(null);
  const [draggedNodeType, setDraggedNodeType] = useState<string | null>(null);

  const {
    nodes,
    edges,
    executionStatus,
    nodeStates,
    lastResult,
    uploads,
    updateNodeConfig,
    deleteNode,
    uploadFile,
    runWorkflow,
    clearWorkflow,
    getAvailableColumns,
  } = useWorkflowContext();

  // Find selected node
  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) || null,
    [nodes, selectedNodeId]
  );

  // Get available columns for selected node
  const availableColumns = useMemo(
    () => (selectedNodeId ? getAvailableColumns(selectedNodeId) : []),
    [selectedNodeId, getAvailableColumns]
  );

  // Handle node selection
  const handleNodeSelect = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId);
    // Also show preview if node has been executed
    if (nodeId && nodeStates[nodeId]) {
      setPreviewNodeId(nodeId);
    }
  }, [nodeStates]);

  // Handle node deletion
  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      deleteNode(nodeId);
      if (selectedNodeId === nodeId) {
        setSelectedNodeId(null);
      }
      if (previewNodeId === nodeId) {
        setPreviewNodeId(null);
      }
    },
    [deleteNode, selectedNodeId, previewNodeId]
  );

  // Get preview state and info
  const previewState = previewNodeId ? nodeStates[previewNodeId] : null;
  const previewNode = previewNodeId ? nodes.find((n) => n.id === previewNodeId) : null;
  const previewLabel = previewNode
    ? NODE_DEFINITIONS_MAP.get(previewNode.data.nodeType)?.label || previewNode.data.nodeType
    : '';

  // Get download URL for Output nodes
  const downloadUrl = useMemo(() => {
    if (!previewNodeId || !previewNode) return null;
    if (previewNode.data.nodeType !== 'Output') return null;
    return lastResult?.final_output_url || null;
  }, [previewNodeId, previewNode, lastResult]);

  return (
    <div className="app">
      <Toolbar
        status={executionStatus}
        onRun={runWorkflow}
        onClear={clearWorkflow}
        nodeCount={nodes.length}
        edgeCount={edges.length}
      />

      <div className="app-body">
        <Palette onDragStart={setDraggedNodeType} />

        <main className="app-main">
          <Canvas
            onNodeSelect={handleNodeSelect}
            selectedNodeId={selectedNodeId}
          />

          {previewState && (
            <PreviewPanel
              nodeId={previewNodeId}
              nodeLabel={previewLabel}
              state={previewState}
              downloadUrl={downloadUrl}
              onClose={() => setPreviewNodeId(null)}
            />
          )}
        </main>

        <ConfigPanel
          selectedNode={selectedNode}
          onUpdateConfig={updateNodeConfig}
          onDelete={handleDeleteNode}
          onUploadFile={uploadFile}
          uploads={uploads}
          availableColumns={availableColumns}
        />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <WorkflowProvider>
        <AppContent />
      </WorkflowProvider>
    </ReactFlowProvider>
  );
}
