/**
 * Tests for node type definitions.
 */
import { NODE_DEFINITIONS, NODE_DEFINITIONS_MAP } from '../config/nodeTypes';

describe('Node Definitions', () => {
  it('should have all required node types', () => {
    const requiredTypes = [
      'ReadCSV',
      'Filter',
      'Select',
      'Sort',
      'Formula',
      'Join',
      'Aggregate',
      'Output',
    ];

    requiredTypes.forEach((type) => {
      expect(NODE_DEFINITIONS_MAP.has(type)).toBe(true);
    });
  });

  it('should have valid structure for each node', () => {
    NODE_DEFINITIONS.forEach((def) => {
      expect(def.type).toBeTruthy();
      expect(def.label).toBeTruthy();
      expect(def.description).toBeTruthy();
      expect(['input', 'transform', 'combine', 'output']).toContain(def.category);
      expect(typeof def.inputs).toBe('number');
      expect(typeof def.outputs).toBe('number');
      expect(Array.isArray(def.configFields)).toBe(true);
    });
  });

  it('should have ReadCSV with 0 inputs and 1 output', () => {
    const readCSV = NODE_DEFINITIONS_MAP.get('ReadCSV');
    expect(readCSV?.inputs).toBe(0);
    expect(readCSV?.outputs).toBe(1);
  });

  it('should have Join with 2 inputs', () => {
    const join = NODE_DEFINITIONS_MAP.get('Join');
    expect(join?.inputs).toBe(2);
    expect(join?.outputs).toBe(1);
  });

  it('should have Output with 0 outputs', () => {
    const output = NODE_DEFINITIONS_MAP.get('Output');
    expect(output?.inputs).toBe(1);
    expect(output?.outputs).toBe(0);
  });

  it('should have valid config fields', () => {
    const filter = NODE_DEFINITIONS_MAP.get('Filter');
    expect(filter?.configFields.length).toBeGreaterThan(0);
    
    const expressionField = filter?.configFields.find((f) => f.name === 'expression');
    expect(expressionField).toBeTruthy();
    expect(expressionField?.type).toBe('expression');
    expect(expressionField?.required).toBe(true);
  });
});
