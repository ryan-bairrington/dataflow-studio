/**
 * Custom hook for managing workflow state.
 * 
 * Handles nodes, edges, execution, and file uploads.
 */
import { useState, useCallback, useMemo } from 'react';
import {
  Node,
  Edge,
  Connection,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
} from 'reactflow';
import { uploadFile, runWorkflow as apiRunWorkflow } from '../api/client';
import {
  Workflow,
  WorkflowNode,
  WorkflowEdge,
  NodeConfig,
  UploadedFile,
  ExecutionStatus,
  NodeExecutionState,
  RunWorkflowResponse,
} from '../types';

let nodeIdCounter = 1;

function generateNodeId(): string {
  return `node-${nodeIdCounter++}`;
}

export interface WorkflowState {
  // React Flow state
  nodes: Node[];
  edges: Edge[];
  
  // Execution state
  executionStatus: ExecutionStatus;
  nodeStates: Record<string, NodeExecutionState>;
  lastResult: RunWorkflowResponse | null;
  
  // Uploads
  uploads: UploadedFile[];
}

export function useWorkflow() {
  // React Flow nodes and edges
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  
  // Execution state
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>('idle');
  const [nodeStates, setNodeStates] = useState<Record<string, NodeExecutionState>>({});
  const [lastResult, setLastResult] = useState<RunWorkflowResponse | null>(null);
  
  // Uploaded files
  const [uploads, setUploads] = useState<UploadedFile[]>([]);

  // Handle node changes (position, selection, etc.)
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  // Handle edge changes
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  // Handle new connections
  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            type: 'smoothstep',
            animated: true,
          },
          eds
        )
      );
    },
    []
  );

  // Add a new node to the canvas
  const addNode = useCallback((nodeType: string, position: { x: number; y: number }) => {
    const newNode: Node = {
      id: generateNodeId(),
      type: 'workflowNode',
      position,
      data: {
        nodeType,
        config: {},
      },
    };
    setNodes((nds) => [...nds, newNode]);
    return newNode.id;
  }, []);

  // Update a node's configuration
  const updateNodeConfig = useCallback((nodeId: string, config: NodeConfig) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, config } }
          : node
      )
    );
  }, []);

  // Delete a node and its edges
  const deleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) =>
      eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
    );
  }, []);

  // Upload a file
  const handleUploadFile = useCallback(async (file: File): Promise<UploadedFile> => {
    const response = await uploadFile(file);
    const uploadedFile: UploadedFile = {
      uploadId: response.upload_id,
      filename: response.filename,
      rows: response.rows,
      columns: response.columns,
    };
    setUploads((prev) => [...prev, uploadedFile]);
    return uploadedFile;
  }, []);

  // Convert React Flow state to API workflow format
  const buildWorkflow = useCallback((): Workflow => {
    const workflowNodes: WorkflowNode[] = nodes.map((node) => ({
      id: node.id,
      type: node.data.nodeType,
      config: node.data.config,
      position: node.position,
    }));

    const workflowEdges: WorkflowEdge[] = edges.map((edge, index) => {
      // Determine port based on edge handle or index
      const targetPorts = edges
        .filter((e) => e.target === edge.target)
        .map((e, i) => ({ id: e.id, port: i === 0 ? 'in' : `in_${i}` }));
      
      const thisPort = targetPorts.find((p) => p.id === edge.id);
      
      return {
        fromNodeId: edge.source,
        fromPort: edge.sourceHandle || 'out',
        toNodeId: edge.target,
        toPort: thisPort?.port || 'in',
      };
    });

    return { nodes: workflowNodes, edges: workflowEdges };
  }, [nodes, edges]);

  // Run the workflow
  const runWorkflow = useCallback(async () => {
    setExecutionStatus('running');
    setLastResult(null);
    
    // Set all nodes to running
    const initialStates: Record<string, NodeExecutionState> = {};
    nodes.forEach((node) => {
      initialStates[node.id] = { status: 'running' };
    });
    setNodeStates(initialStates);

    try {
      const workflow = buildWorkflow();
      const uploadIds = uploads.map((u) => u.uploadId);
      const result = await apiRunWorkflow(workflow, uploadIds);
      
      // Update node states from result
      const newStates: Record<string, NodeExecutionState> = {};
      Object.entries(result.node_outputs).forEach(([nodeId, output]) => {
        newStates[nodeId] = {
          status: output.success ? 'success' : 'error',
          rows: output.rows,
          columns: output.columns,
          preview: output.preview,
          error: output.error,
        };
      });
      setNodeStates(newStates);
      setLastResult(result);
      setExecutionStatus(result.status === 'error' ? 'error' : 'success');
    } catch (error) {
      setExecutionStatus('error');
      console.error('Workflow execution failed:', error);
    }
  }, [nodes, uploads, buildWorkflow]);

  // Clear the canvas
  const clearWorkflow = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setNodeStates({});
    setExecutionStatus('idle');
    setLastResult(null);
  }, []);

  // Get columns available for a node (from upstream nodes)
  const getAvailableColumns = useCallback(
    (nodeId: string): string[] => {
      // Find upstream nodes
      const incomingEdges = edges.filter((e) => e.target === nodeId);
      const upstreamNodeIds = incomingEdges.map((e) => e.source);
      
      // Get columns from node states
      const columns = new Set<string>();
      upstreamNodeIds.forEach((id) => {
        const state = nodeStates[id];
        if (state?.columns) {
          state.columns.forEach((col) => columns.add(col));
        }
      });
      
      // Also check uploads for ReadCSV nodes
      upstreamNodeIds.forEach((id) => {
        const node = nodes.find((n) => n.id === id);
        if (node?.data.nodeType === 'ReadCSV' && node.data.config.upload_id) {
          const upload = uploads.find((u) => u.uploadId === node.data.config.upload_id);
          if (upload) {
            upload.columns.forEach((col) => columns.add(col));
          }
        }
      });
      
      return Array.from(columns);
    },
    [edges, nodes, nodeStates, uploads]
  );

  return {
    // State
    nodes,
    edges,
    executionStatus,
    nodeStates,
    lastResult,
    uploads,
    
    // Actions
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    updateNodeConfig,
    deleteNode,
    uploadFile: handleUploadFile,
    runWorkflow,
    clearWorkflow,
    getAvailableColumns,
    buildWorkflow,
  };
}
