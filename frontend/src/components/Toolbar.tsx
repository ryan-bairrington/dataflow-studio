/**
 * Top toolbar with workflow actions.
 */
import React from 'react';
import { ExecutionStatus } from '../types';

interface ToolbarProps {
  status: ExecutionStatus;
  onRun: () => void;
  onClear: () => void;
  nodeCount: number;
  edgeCount: number;
}

export function Toolbar({ status, onRun, onClear, nodeCount, edgeCount }: ToolbarProps) {
  const isRunning = status === 'running';

  return (
    <header className="toolbar" role="banner">
      <div className="toolbar-brand">
        <h1>🔄 DataFlow Studio</h1>
      </div>

      <div className="toolbar-stats">
        <span className="stat">
          <span className="stat-icon">📦</span>
          {nodeCount} nodes
        </span>
        <span className="stat">
          <span className="stat-icon">↔️</span>
          {edgeCount} connections
        </span>
      </div>

      <div className="toolbar-actions">
        <button
          className="btn btn-secondary"
          onClick={onClear}
          disabled={isRunning || nodeCount === 0}
          title="Clear the canvas"
        >
          🗑️ Clear
        </button>
        
        <button
          className={`btn btn-primary ${isRunning ? 'btn-loading' : ''}`}
          onClick={onRun}
          disabled={isRunning || nodeCount === 0}
          title="Run the workflow"
        >
          {isRunning ? (
            <>
              <span className="spinner" aria-hidden="true"></span>
              Running...
            </>
          ) : (
            <>▶️ Run Workflow</>
          )}
        </button>
      </div>

      {status !== 'idle' && status !== 'running' && (
        <div className={`toolbar-status status-${status}`} role="status" aria-live="polite">
          {status === 'success' ? '✅ Complete' : '❌ Errors occurred'}
        </div>
      )}
    </header>
  );
}
