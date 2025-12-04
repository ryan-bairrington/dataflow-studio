/**
 * Node type definitions for the workflow canvas.
 * 
 * Each node type has metadata about its appearance, inputs/outputs,
 * and configuration options.
 */
import { NodeDefinition } from '../types';

export const NODE_DEFINITIONS: NodeDefinition[] = [
  // === Input Nodes ===
  {
    type: 'ReadCSV',
    label: 'Read CSV',
    description: 'Load data from a CSV file',
    category: 'input',
    inputs: 0,
    outputs: 1,
    color: '#4CAF50',
    configFields: [
      {
        name: 'upload_id',
        label: 'CSV File',
        type: 'upload',
        required: true,
      },
      {
        name: 'header',
        label: 'First Row is Header',
        type: 'select',
        options: [
          { value: 'true', label: 'Yes' },
          { value: 'false', label: 'No' },
        ],
        default: 'true',
      },
      {
        name: 'sep',
        label: 'Delimiter',
        type: 'select',
        options: [
          { value: ',', label: 'Comma (,)' },
          { value: ';', label: 'Semicolon (;)' },
          { value: '\t', label: 'Tab' },
          { value: '|', label: 'Pipe (|)' },
        ],
        default: ',',
      },
    ],
  },

  // === Transform Nodes ===
  {
    type: 'Filter',
    label: 'Filter',
    description: 'Filter rows based on a condition',
    category: 'transform',
    inputs: 1,
    outputs: 1,
    color: '#2196F3',
    configFields: [
      {
        name: 'expression',
        label: 'Filter Expression',
        type: 'expression',
        placeholder: 'e.g., age > 18 and status == "active"',
        required: true,
      },
    ],
  },
  {
    type: 'Select',
    label: 'Select Columns',
    description: 'Choose which columns to keep',
    category: 'transform',
    inputs: 1,
    outputs: 1,
    color: '#2196F3',
    configFields: [
      {
        name: 'columns',
        label: 'Columns to Keep',
        type: 'multiselect',
        required: true,
      },
    ],
  },
  {
    type: 'Sort',
    label: 'Sort',
    description: 'Sort rows by column values',
    category: 'transform',
    inputs: 1,
    outputs: 1,
    color: '#2196F3',
    configFields: [
      {
        name: 'columns',
        label: 'Sort By Columns',
        type: 'multiselect',
        required: true,
      },
      {
        name: 'ascending',
        label: 'Order',
        type: 'select',
        options: [
          { value: 'true', label: 'Ascending (A-Z, 0-9)' },
          { value: 'false', label: 'Descending (Z-A, 9-0)' },
        ],
        default: 'true',
      },
    ],
  },
  {
    type: 'Formula',
    label: 'Formula',
    description: 'Create a calculated column',
    category: 'transform',
    inputs: 1,
    outputs: 1,
    color: '#9C27B0',
    configFields: [
      {
        name: 'newCol',
        label: 'New Column Name',
        type: 'text',
        placeholder: 'e.g., total_amount',
        required: true,
      },
      {
        name: 'expression',
        label: 'Formula',
        type: 'expression',
        placeholder: 'e.g., quantity * unit_price',
        required: true,
      },
    ],
  },

  // === Combine Nodes ===
  {
    type: 'Join',
    label: 'Join',
    description: 'Combine two datasets by matching keys',
    category: 'combine',
    inputs: 2,
    outputs: 1,
    color: '#FF9800',
    configFields: [
      {
        name: 'leftKey',
        label: 'Left Key Column',
        type: 'text',
        placeholder: 'Column from first input',
        required: true,
      },
      {
        name: 'rightKey',
        label: 'Right Key Column',
        type: 'text',
        placeholder: 'Column from second input',
        required: true,
      },
      {
        name: 'how',
        label: 'Join Type',
        type: 'select',
        options: [
          { value: 'inner', label: 'Inner (matching rows only)' },
          { value: 'left', label: 'Left (keep all from first)' },
          { value: 'right', label: 'Right (keep all from second)' },
          { value: 'outer', label: 'Outer (keep all rows)' },
        ],
        default: 'inner',
      },
    ],
  },
  {
    type: 'Aggregate',
    label: 'Aggregate',
    description: 'Group data and calculate summaries',
    category: 'combine',
    inputs: 1,
    outputs: 1,
    color: '#FF9800',
    configFields: [
      {
        name: 'groupBy',
        label: 'Group By Columns',
        type: 'multiselect',
        required: true,
      },
      {
        name: 'aggregations',
        label: 'Aggregations',
        type: 'text', // Will be handled specially in the UI
        placeholder: 'Configure in detail panel',
      },
    ],
  },

  // === Output Nodes ===
  {
    type: 'Output',
    label: 'Output',
    description: 'Export results as CSV',
    category: 'output',
    inputs: 1,
    outputs: 0,
    color: '#F44336',
    configFields: [
      {
        name: 'format',
        label: 'Output Format',
        type: 'select',
        options: [
          { value: 'csv', label: 'CSV File' },
        ],
        default: 'csv',
      },
    ],
  },
];

// Quick lookup map
export const NODE_DEFINITIONS_MAP = new Map(
  NODE_DEFINITIONS.map(def => [def.type, def])
);

// Get category color
export const CATEGORY_COLORS: Record<string, string> = {
  input: '#4CAF50',
  transform: '#2196F3',
  combine: '#FF9800',
  output: '#F44336',
};
