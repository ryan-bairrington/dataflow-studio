/**
 * Core types for the DataFlow Studio frontend.
 */

// === Node Types ===

export interface NodeConfig {
  [key: string]: unknown;
}

export interface WorkflowNode {
  id: string;
  type: string;
  config: NodeConfig;
  position: { x: number; y: number };
}

export interface WorkflowEdge {
  fromNodeId: string;
  fromPort: string;
  toNodeId: string;
  toPort: string;
}

export interface Workflow {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

// === Node Definitions ===

export type FieldType = 'text' | 'number' | 'select' | 'multiselect' | 'expression' | 'upload';

export interface ConfigField {
  name: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  required?: boolean;
  default?: unknown;
  options?: { value: string; label: string }[];
}

export interface NodeDefinition {
  type: string;
  label: string;
  description: string;
  category: 'input' | 'transform' | 'combine' | 'output';
  inputs: number;
  outputs: number;
  configFields: ConfigField[];
  color?: string;
}

// === API Types ===

export interface UploadResponse {
  upload_id: string;
  filename: string;
  rows: number;
  columns: string[];
  preview: Record<string, unknown>[];
}

export interface NodeOutput {
  node_id: string;
  success: boolean;
  rows: number;
  columns: string[];
  preview: Record<string, unknown>[];
  error?: string;
}

export interface RunWorkflowResponse {
  status: 'success' | 'partial' | 'error';
  node_outputs: Record<string, NodeOutput>;
  final_output_url?: string;
  errors: string[];
}

// === UI State ===

export interface UploadedFile {
  uploadId: string;
  filename: string;
  rows: number;
  columns: string[];
}

export type ExecutionStatus = 'idle' | 'running' | 'success' | 'error';

export interface NodeExecutionState {
  status: ExecutionStatus;
  rows?: number;
  columns?: string[];
  preview?: Record<string, unknown>[];
  error?: string;
}
