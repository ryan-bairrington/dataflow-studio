/**
 * Configuration panel for the selected node.
 * 
 * Shows node-specific configuration fields based on the node type.
 */
import React, { useState, useCallback } from 'react';
import { Node } from 'reactflow';
import { NODE_DEFINITIONS_MAP } from '../config/nodeTypes';
import { ConfigField, UploadedFile, NodeConfig } from '../types';

interface ConfigPanelProps {
  selectedNode: Node | null;
  onUpdateConfig: (nodeId: string, config: NodeConfig) => void;
  onDelete: (nodeId: string) => void;
  onUploadFile: (file: File) => Promise<UploadedFile>;
  uploads: UploadedFile[];
  availableColumns: string[];
}

export function ConfigPanel({
  selectedNode,
  onUpdateConfig,
  onDelete,
  onUploadFile,
  uploads,
  availableColumns,
}: ConfigPanelProps) {
  const [uploading, setUploading] = useState(false);

  if (!selectedNode) {
    return (
      <aside className="config-panel" role="complementary" aria-label="Node configuration">
        <div className="config-empty">
          <h3>No Node Selected</h3>
          <p>Click a node on the canvas to configure it</p>
        </div>
      </aside>
    );
  }

  const nodeType = selectedNode.data.nodeType;
  const definition = NODE_DEFINITIONS_MAP.get(nodeType);
  const config = selectedNode.data.config || {};

  if (!definition) {
    return (
      <aside className="config-panel">
        <div className="config-error">Unknown node type: {nodeType}</div>
      </aside>
    );
  }

  const handleFieldChange = (fieldName: string, value: unknown) => {
    onUpdateConfig(selectedNode.id, {
      ...config,
      [fieldName]: value,
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const uploaded = await onUploadFile(file);
      handleFieldChange('upload_id', uploaded.uploadId);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = () => {
    if (confirm('Delete this node?')) {
      onDelete(selectedNode.id);
    }
  };

  return (
    <aside className="config-panel" role="complementary" aria-label="Node configuration">
      <div className="config-header">
        <h3>{definition.label}</h3>
        <p className="config-description">{definition.description}</p>
      </div>

      <form className="config-form" onSubmit={(e) => e.preventDefault()}>
        {definition.configFields.map((field) => (
          <ConfigFieldInput
            key={field.name}
            field={field}
            value={config[field.name]}
            onChange={(value) => handleFieldChange(field.name, value)}
            onFileUpload={handleFileUpload}
            uploading={uploading}
            uploads={uploads}
            availableColumns={availableColumns}
          />
        ))}
      </form>

      <div className="config-actions">
        <button
          type="button"
          className="btn btn-danger"
          onClick={handleDelete}
          aria-label="Delete node"
        >
          🗑️ Delete Node
        </button>
      </div>

      <div className="config-node-id">
        <small>Node ID: {selectedNode.id}</small>
      </div>
    </aside>
  );
}

interface ConfigFieldInputProps {
  field: ConfigField;
  value: unknown;
  onChange: (value: unknown) => void;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  uploading: boolean;
  uploads: UploadedFile[];
  availableColumns: string[];
}

function ConfigFieldInput({
  field,
  value,
  onChange,
  onFileUpload,
  uploading,
  uploads,
  availableColumns,
}: ConfigFieldInputProps) {
  const id = `field-${field.name}`;

  switch (field.type) {
    case 'text':
    case 'expression':
      return (
        <div className="form-group">
          <label htmlFor={id}>{field.label}</label>
          <input
            type="text"
            id={id}
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            className={field.type === 'expression' ? 'expression-input' : ''}
            aria-describedby={field.type === 'expression' ? `${id}-hint` : undefined}
          />
          {field.type === 'expression' && (
            <small id={`${id}-hint`} className="field-hint">
              Use column names directly (e.g., age &gt; 18)
            </small>
          )}
        </div>
      );

    case 'number':
      return (
        <div className="form-group">
          <label htmlFor={id}>{field.label}</label>
          <input
            type="number"
            id={id}
            value={(value as number) ?? ''}
            onChange={(e) => onChange(Number(e.target.value))}
            required={field.required}
          />
        </div>
      );

    case 'select':
      return (
        <div className="form-group">
          <label htmlFor={id}>{field.label}</label>
          <select
            id={id}
            value={(value as string) || field.default || ''}
            onChange={(e) => onChange(e.target.value)}
            required={field.required}
          >
            <option value="">Select...</option>
            {field.options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      );

    case 'multiselect':
      const selectedValues = (value as string[]) || [];
      const columns = availableColumns.length > 0 ? availableColumns : ['(run workflow to see columns)'];
      
      return (
        <div className="form-group">
          <label>{field.label}</label>
          <div className="multiselect" role="group" aria-label={field.label}>
            {columns.map((col) => (
              <label key={col} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedValues.includes(col)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      onChange([...selectedValues, col]);
                    } else {
                      onChange(selectedValues.filter((c) => c !== col));
                    }
                  }}
                  disabled={col.startsWith('(')}
                />
                {col}
              </label>
            ))}
          </div>
        </div>
      );

    case 'upload':
      const selectedUpload = uploads.find((u) => u.uploadId === value);
      
      return (
        <div className="form-group">
          <label htmlFor={id}>{field.label}</label>
          
          {/* File upload button */}
          <div className="upload-section">
            <input
              type="file"
              id={id}
              accept=".csv"
              onChange={onFileUpload}
              disabled={uploading}
              className="file-input"
            />
            <label htmlFor={id} className="file-label">
              {uploading ? 'Uploading...' : '📁 Choose CSV File'}
            </label>
          </div>

          {/* Or select from uploads */}
          {uploads.length > 0 && (
            <div className="upload-select">
              <small>Or select existing:</small>
              <select
                value={(value as string) || ''}
                onChange={(e) => onChange(e.target.value)}
                aria-label="Select uploaded file"
              >
                <option value="">Select file...</option>
                {uploads.map((u) => (
                  <option key={u.uploadId} value={u.uploadId}>
                    {u.filename} ({u.rows} rows)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Show selected file info */}
          {selectedUpload && (
            <div className="upload-info">
              <strong>{selectedUpload.filename}</strong>
              <br />
              {selectedUpload.rows} rows, {selectedUpload.columns.length} columns
            </div>
          )}
        </div>
      );

    default:
      return null;
  }
}
