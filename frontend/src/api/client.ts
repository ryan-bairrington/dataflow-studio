/**
 * API client for communicating with the DataFlow Studio backend.
 */
import { UploadResponse, Workflow, RunWorkflowResponse } from '../types';

const API_BASE = '/api';

/**
 * Upload a CSV file to the server.
 */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Run a workflow and get results.
 */
export async function runWorkflow(
  workflow: Workflow,
  uploads: string[] = []
): Promise<RunWorkflowResponse> {
  const response = await fetch(`${API_BASE}/run-workflow`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ workflow, uploads }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Workflow execution failed');
  }

  return response.json();
}

/**
 * Download a result file.
 */
export function getDownloadUrl(fileId: string): string {
  return `${API_BASE}/download/${fileId}`;
}

/**
 * Get information about an uploaded file.
 */
export async function getUploadInfo(uploadId: string): Promise<UploadResponse> {
  const response = await fetch(`${API_BASE}/uploads/${uploadId}`);

  if (!response.ok) {
    throw new Error('Failed to get upload info');
  }

  return response.json();
}

/**
 * Delete an uploaded file.
 */
export async function deleteUpload(uploadId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/uploads/${uploadId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete upload');
  }
}

/**
 * Get available node types from the server.
 */
export async function getNodeTypes(): Promise<unknown[]> {
  const response = await fetch(`${API_BASE}/nodes`);

  if (!response.ok) {
    throw new Error('Failed to get node types');
  }

  return response.json();
}
