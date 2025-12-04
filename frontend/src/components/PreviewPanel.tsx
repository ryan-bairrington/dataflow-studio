/**
 * Preview panel showing node output data.
 * 
 * Displays a data table with the selected node's output.
 */
import React from 'react';
import { NodeExecutionState } from '../types';

interface PreviewPanelProps {
  nodeId: string | null;
  nodeLabel: string;
  state: NodeExecutionState | null;
  downloadUrl: string | null;
  onClose: () => void;
}

export function PreviewPanel({ nodeId, nodeLabel, state, downloadUrl, onClose }: PreviewPanelProps) {
  if (!nodeId || !state) {
    return null;
  }

  return (
    <div className="preview-panel" role="dialog" aria-labelledby="preview-title">
      <div className="preview-header">
        <h3 id="preview-title">
          🔍 Preview: {nodeLabel}
          <span className="preview-meta">
            {state.rows?.toLocaleString()} rows × {state.columns?.length} columns
          </span>
        </h3>
        <button
          className="btn-close"
          onClick={onClose}
          aria-label="Close preview"
        >
          ✕
        </button>
      </div>

      {state.error ? (
        <div className="preview-error" role="alert">
          <h4>❌ Error</h4>
          <pre>{state.error}</pre>
        </div>
      ) : state.preview && state.preview.length > 0 ? (
        <div className="preview-table-container">
          <table className="preview-table" role="grid">
            <thead>
              <tr>
                <th className="row-num">#</th>
                {state.columns?.map((col) => (
                  <th key={col} scope="col">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {state.preview.map((row, idx) => (
                <tr key={idx}>
                  <td className="row-num">{idx + 1}</td>
                  {state.columns?.map((col) => (
                    <td key={col}>{formatCellValue(row[col])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {state.rows && state.rows > state.preview.length && (
            <div className="preview-truncated">
              Showing {state.preview.length} of {state.rows.toLocaleString()} rows
            </div>
          )}
        </div>
      ) : (
        <div className="preview-empty">No data to preview</div>
      )}

      {downloadUrl && (
        <div className="preview-actions">
          <a
            href={downloadUrl}
            download
            className="btn btn-primary"
          >
            ⬇️ Download CSV
          </a>
        </div>
      )}
    </div>
  );
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  if (typeof value === 'number') {
    // Format numbers nicely
    if (Number.isInteger(value)) {
      return value.toLocaleString();
    }
    return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
  }
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }
  return String(value);
}
