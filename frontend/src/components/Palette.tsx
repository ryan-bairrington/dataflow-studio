/**
 * Node palette sidebar - drag nodes onto the canvas.
 */
import React from 'react';
import { NODE_DEFINITIONS, CATEGORY_COLORS } from '../config/nodeTypes';
import { NodeDefinition } from '../types';

interface PaletteProps {
  onDragStart: (nodeType: string) => void;
}

const categoryLabels: Record<string, string> = {
  input: '📥 Input',
  transform: '🔧 Transform',
  combine: '🔗 Combine',
  output: '📤 Output',
};

function NodeCard({ definition, onDragStart }: { definition: NodeDefinition; onDragStart: () => void }) {
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('application/dataflow-node', definition.type);
    e.dataTransfer.effectAllowed = 'move';
    onDragStart();
  };

  return (
    <div
      className="palette-node"
      draggable
      onDragStart={handleDragStart}
      style={{ borderLeftColor: definition.color || CATEGORY_COLORS[definition.category] }}
      role="button"
      aria-label={`Drag ${definition.label} node`}
      tabIndex={0}
    >
      <div className="palette-node-label">{definition.label}</div>
      <div className="palette-node-description">{definition.description}</div>
      <div className="palette-node-ports">
        {definition.inputs > 0 && <span className="port-badge input">{definition.inputs} in</span>}
        {definition.outputs > 0 && <span className="port-badge output">{definition.outputs} out</span>}
      </div>
    </div>
  );
}

export function Palette({ onDragStart }: PaletteProps) {
  // Group nodes by category
  const groupedNodes = NODE_DEFINITIONS.reduce((acc, node) => {
    if (!acc[node.category]) {
      acc[node.category] = [];
    }
    acc[node.category].push(node);
    return acc;
  }, {} as Record<string, NodeDefinition[]>);

  const categories = ['input', 'transform', 'combine', 'output'];

  return (
    <aside className="palette" role="complementary" aria-label="Node palette">
      <h2 className="palette-title">Nodes</h2>
      <p className="palette-hint">Drag nodes to the canvas</p>
      
      {categories.map((category) => (
        <div key={category} className="palette-category">
          <h3 className="palette-category-title">{categoryLabels[category]}</h3>
          <div className="palette-nodes">
            {groupedNodes[category]?.map((node) => (
              <NodeCard
                key={node.type}
                definition={node}
                onDragStart={() => onDragStart(node.type)}
              />
            ))}
          </div>
        </div>
      ))}
    </aside>
  );
}
