/**
 * Custom node component for React Flow.
 * 
 * Displays the node with its type, status, and handles.
 */
import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { NODE_DEFINITIONS_MAP, CATEGORY_COLORS } from '../config/nodeTypes';
import { NodeExecutionState } from '../types';

interface WorkflowNodeData {
  nodeType: string;
  config: Record<string, unknown>;
  executionState?: NodeExecutionState;
  selected?: boolean;
}

function getStatusIcon(status?: string): string {
  switch (status) {
    case 'running': return '⏳';
    case 'success': return '✅';
    case 'error': return '❌';
    default: return '';
  }
}

function getStatusClass(status?: string): string {
  switch (status) {
    case 'running': return 'status-running';
    case 'success': return 'status-success';
    case 'error': return 'status-error';
    default: return '';
  }
}

export const WorkflowNode = memo(function WorkflowNode({ data, selected }: NodeProps<WorkflowNodeData>) {
  const definition = NODE_DEFINITIONS_MAP.get(data.nodeType);
  
  if (!definition) {
    return <div className="workflow-node error">Unknown node type: {data.nodeType}</div>;
  }

  const color = definition.color || CATEGORY_COLORS[definition.category];
  const state = data.executionState;
  const statusIcon = getStatusIcon(state?.status);
  const statusClass = getStatusClass(state?.status);

  return (
    <div 
      className={`workflow-node ${statusClass} ${selected ? 'selected' : ''}`}
      style={{ borderColor: color }}
      role="button"
      aria-label={`${definition.label} node`}
    >
      {/* Input handles */}
      {definition.inputs > 0 && (
        <Handle
          type="target"
          position={Position.Left}
          id="in"
          className="node-handle input-handle"
          aria-label="Input connection"
        />
      )}
      {definition.inputs > 1 && (
        <Handle
          type="target"
          position={Position.Left}
          id="in_1"
          className="node-handle input-handle secondary"
          style={{ top: '70%' }}
          aria-label="Secondary input connection"
        />
      )}

      {/* Node content */}
      <div className="node-header" style={{ backgroundColor: color }}>
        <span className="node-icon">{getCategoryIcon(definition.category)}</span>
        <span className="node-label">{definition.label}</span>
        {statusIcon && <span className="node-status" aria-label={`Status: ${state?.status}`}>{statusIcon}</span>}
      </div>
      
      <div className="node-body">
        {state?.rows !== undefined && (
          <div className="node-stat">
            <span className="stat-label">Rows:</span>
            <span className="stat-value">{state.rows.toLocaleString()}</span>
          </div>
        )}
        {state?.columns !== undefined && (
          <div className="node-stat">
            <span className="stat-label">Cols:</span>
            <span className="stat-value">{state.columns.length}</span>
          </div>
        )}
        {state?.error && (
          <div className="node-error" title={state.error}>
            {state.error.substring(0, 50)}{state.error.length > 50 ? '...' : ''}
          </div>
        )}
        {!state && Object.keys(data.config).length > 0 && (
          <div className="node-configured">⚙️ Configured</div>
        )}
      </div>

      {/* Output handles */}
      {definition.outputs > 0 && (
        <Handle
          type="source"
          position={Position.Right}
          id="out"
          className="node-handle output-handle"
          aria-label="Output connection"
        />
      )}
    </div>
  );
});

function getCategoryIcon(category: string): string {
  switch (category) {
    case 'input': return '📥';
    case 'transform': return '🔧';
    case 'combine': return '🔗';
    case 'output': return '📤';
    default: return '📦';
  }
}
