/**
 * React Context for sharing workflow state across components.
 */
import React, { createContext, useContext, ReactNode } from 'react';
import { useWorkflow } from '../hooks/useWorkflow';

type WorkflowContextType = ReturnType<typeof useWorkflow>;

const WorkflowContext = createContext<WorkflowContextType | null>(null);

export function WorkflowProvider({ children }: { children: ReactNode }) {
  const workflow = useWorkflow();
  
  return (
    <WorkflowContext.Provider value={workflow}>
      {children}
    </WorkflowContext.Provider>
  );
}

export function useWorkflowContext(): WorkflowContextType {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflowContext must be used within a WorkflowProvider');
  }
  return context;
}
