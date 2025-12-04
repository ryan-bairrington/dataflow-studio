# DataFlow Studio - Developer Guide

This document covers the internal architecture and how to extend the system.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│  React Frontend │◄───►│  FastAPI Backend │
│  (react-flow)   │     │  (Python/Pandas) │
└─────────────────┘     └───────┬─────────┘
                               │
                    ┌─────────┴─────────┐
                    │ WorkflowExecutor  │
                    └─────────┬─────────┘
                              │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────┴──────┐  ┌─────┴───────┐ ┌─────┴────────┐
    │  I/O Nodes  │  │ Transform  │ │ Combine     │
    │  (ReadCSV,  │  │ Nodes      │ │ Nodes       │
    │   Output)   │  │ (Filter,   │ │ (Join,      │
    └─────────────┘  │  Select)   │ │  Aggregate) │
                    └─────────────┘ └──────────────┘
```

## Adding a New Node Type

### Step 1: Create the Node Class

Create a new file or add to an existing nodes module:

```python
# backend/app/engine/nodes/my_nodes.py
from typing import Any
import pandas as pd
from .base import BaseNode, NodeResult


class DeduplicateNode(BaseNode):
    """Remove duplicate rows from the dataset.
    
    Config:
        columns (list[str], optional): Columns to check for duplicates.
            If not provided, checks all columns.
        keep (str): Which duplicate to keep: 'first', 'last', or 'none'
    """
    
    # Required class attributes
    node_type = "Deduplicate"  # Must match frontend node type
    display_name = "Remove Duplicates"
    description = "Remove duplicate rows based on column values"
    
    def execute(self, inputs: list[pd.DataFrame]) -> NodeResult:
        """Execute the deduplication."""
        if not inputs:
            return NodeResult(success=False, error="No input data")
        
        df = inputs[0]
        columns = self.config.get('columns')  # None = all columns
        keep = self.config.get('keep', 'first')
        
        try:
            result = df.drop_duplicates(
                subset=columns, 
                keep=keep if keep != 'none' else False
            )
            return NodeResult(
                success=True,
                data=result,
                metadata={
                    'duplicates_removed': len(df) - len(result)
                }
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))
    
    def validate_config(self) -> tuple[bool, str | None]:
        """Optional: validate configuration before execution."""
        keep = self.config.get('keep', 'first')
        if keep not in ('first', 'last', 'none'):
            return False, f"Invalid keep value: {keep}"
        return True, None
```

### Step 2: Register the Node

Add to `backend/app/engine/nodes/__init__.py`:

```python
from .my_nodes import DeduplicateNode

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    # ... existing nodes ...
    "Deduplicate": DeduplicateNode,
}
```

### Step 3: Add Frontend Node Definition

Add to `frontend/src/config/nodeTypes.ts`:

```typescript
export const NODE_DEFINITIONS: NodeDefinition[] = [
  // ... existing nodes ...
  {
    type: 'Deduplicate',
    label: 'Remove Duplicates',
    description: 'Remove duplicate rows',
    category: 'transform',
    inputs: 1,
    outputs: 1,
    configFields: [
      {
        name: 'columns',
        label: 'Columns (optional)',
        type: 'multiselect',
        placeholder: 'Leave empty for all columns'
      },
      {
        name: 'keep',
        label: 'Keep',
        type: 'select',
        options: [
          { value: 'first', label: 'First occurrence' },
          { value: 'last', label: 'Last occurrence' },
          { value: 'none', label: 'Remove all duplicates' }
        ],
        default: 'first'
      }
    ]
  }
];
```

### Step 4: Write Tests

```python
# backend/tests/test_nodes.py
def test_deduplicate_basic(self):
    df = pd.DataFrame({'a': [1, 1, 2], 'b': ['x', 'x', 'y']})
    node = DeduplicateNode("dedup-1", {})
    result = node.execute([df])
    
    assert result.success
    assert result.rows == 2  # One duplicate removed
```

## Workflow Execution Engine

### How Execution Works

1. **Parse Workflow**: Convert JSON to internal graph representation
2. **Topological Sort**: Determine execution order using Kahn's algorithm
3. **Execute Nodes**: Process each node in order, caching outputs
4. **Return Results**: Collect per-node results and final outputs

```
Workflow JSON → Build Graph → Topological Sort → Execute → Results
```

### Execution Order Example

```
ReadCSV_1 ─────┐
                ├───► Join ──► Filter ──► Output
ReadCSV_2 ─────┘
```

Topological order: `[ReadCSV_1, ReadCSV_2, Join, Filter, Output]`

### Handling Multi-Input Nodes

For nodes like `Join` that need multiple inputs:

```python
# Inputs are ordered by the 'toPort' field in edges
# Default port: 'in' (first input)
# Additional ports: 'in_1', 'in_2', etc.

edges = [
    {"fromNodeId": "left", "toNodeId": "join", "toPort": "in"},    # First input
    {"fromNodeId": "right", "toNodeId": "join", "toPort": "in_1"}  # Second input
]
```

## Expression Parser Security

### How Sandboxing Works

The `SafeExpressionParser` provides security through:

1. **Pattern Blocking**: Regex patterns block dangerous constructs
2. **AST Validation**: Parse expressions to validate syntax
3. **Restricted Evaluation**: Use `pandas.eval()` with limited namespace

### Blocked Patterns

```python
DANGEROUS_PATTERNS = [
    r'\b__\w+__\b',      # Dunders
    r'\bexec\s*\(',       # exec()
    r'\beval\s*\(',       # eval()
    r'\bimport\s',        # imports
    r'\bos\.\w+',         # os module
    # ... more
]
```

### Adding Safe Functions

To allow new functions in expressions:

```python
# backend/app/engine/parser.py

ALLOWED_FUNCTIONS = {
    # Existing functions...
    'my_func': lambda x: x.apply(custom_operation),
}
```

### Extending for Advanced Use

For more complex expressions, consider:

1. **Whitelisting Approach**: Only allow specific operations
2. **AST Transformation**: Transform AST to safe equivalent
3. **Sandbox Process**: Execute in isolated subprocess

## Frontend Architecture

### Component Hierarchy

```
App
├── Toolbar
├── Sidebar (Palette)
├── Canvas (react-flow)
│   ├── WorkflowNode (custom node component)
│   └── Edges
├── ConfigPanel
└── PreviewPanel
```

### State Management

We use React Context + hooks for simplicity:

```typescript
// useWorkflow.ts - manages workflow state
const { nodes, edges, addNode, removeNode, updateConfig, runWorkflow } = useWorkflow();

// useSelection.ts - manages selected node
const { selectedNode, selectNode } = useSelection();
```

## API Design Decisions

### Why Base64 Previews?

We return preview data as JSON (list of dicts) rather than base64 CSV because:
- Easier to display in React tables
- Smaller payload for typical previews
- Can be extended with type hints

### File Storage Strategy

MVP uses filesystem storage:
- Uploads: `data/uploads/{uuid}.csv`
- Outputs: `data/outputs/{uuid}.csv`

For production, replace with:
- S3/Azure Blob for uploads
- Add TTL-based cleanup
- Consider streaming for large files

## Performance Considerations

### Large Files

- Preview is capped at 100 rows
- Consider chunked processing for files > 100MB
- Add progress callbacks for long operations

### Caching

- Intermediate results are cached during execution
- Node outputs can be persisted for re-execution

## Testing Strategy

```
tests/
├── test_nodes.py      # Unit tests for each node type
├── test_executor.py   # Workflow execution tests
├── test_parser.py     # Expression parser security tests
└── test_api.py        # Integration tests for endpoints
```

Run tests:
```bash
cd backend
pytest -v
pytest -v --cov=app --cov-report=html  # With coverage
```
