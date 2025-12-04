/**
 * Tests for the Palette component.
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Palette } from '../components/Palette';

describe('Palette', () => {
  const mockOnDragStart = jest.fn();

  beforeEach(() => {
    mockOnDragStart.mockClear();
  });

  it('renders all node categories', () => {
    render(<Palette onDragStart={mockOnDragStart} />);

    expect(screen.getByText(/Input/i)).toBeInTheDocument();
    expect(screen.getByText(/Transform/i)).toBeInTheDocument();
    expect(screen.getByText(/Combine/i)).toBeInTheDocument();
    expect(screen.getByText(/Output/i)).toBeInTheDocument();
  });

  it('renders all node types', () => {
    render(<Palette onDragStart={mockOnDragStart} />);

    expect(screen.getByText('Read CSV')).toBeInTheDocument();
    expect(screen.getByText('Filter')).toBeInTheDocument();
    expect(screen.getByText('Select Columns')).toBeInTheDocument();
    expect(screen.getByText('Join')).toBeInTheDocument();
    expect(screen.getByText('Aggregate')).toBeInTheDocument();
    expect(screen.getByText('Output')).toBeInTheDocument();
  });

  it('renders node descriptions', () => {
    render(<Palette onDragStart={mockOnDragStart} />);

    expect(screen.getByText('Load data from a CSV file')).toBeInTheDocument();
    expect(screen.getByText('Filter rows based on a condition')).toBeInTheDocument();
  });

  it('calls onDragStart when dragging a node', () => {
    render(<Palette onDragStart={mockOnDragStart} />);

    const readCSVNode = screen.getByText('Read CSV').closest('.palette-node');
    expect(readCSVNode).toBeInTheDocument();

    if (readCSVNode) {
      fireEvent.dragStart(readCSVNode);
      expect(mockOnDragStart).toHaveBeenCalled();
    }
  });

  it('has correct aria labels for accessibility', () => {
    render(<Palette onDragStart={mockOnDragStart} />);

    expect(screen.getByRole('complementary', { name: /node palette/i })).toBeInTheDocument();
  });
});
