import { useState } from 'react';
import { Status } from '../../../../../Alert';

type OperationType =
  | 'idle'
  | 'generating'
  | 'publishing'
  | 'updating'
  | 'unpublishing'
  | 'checking';

interface UseSTACOperationsReturn {
  currentOperation: OperationType;
  status: Status | null;
  pollingStatus: string;
  setCurrentOperation: (operation: OperationType) => void;
  setStatus: (status: Status | null) => void;
  setPollingStatus: (status: string) => void;
  isOperationActive: (operation: OperationType) => boolean;
  isLoading: boolean;
}

export function useSTACOperations(): UseSTACOperationsReturn {
  const [currentOperation, setCurrentOperation] =
    useState<OperationType>('idle');
  const [status, setStatus] = useState<Status | null>(null);
  const [pollingStatus, setPollingStatus] = useState<string>('');

  const isOperationActive = (operation: OperationType) =>
    currentOperation === operation;
  const isLoading = currentOperation !== 'idle';

  return {
    currentOperation,
    status,
    pollingStatus,
    setCurrentOperation,
    setStatus,
    setPollingStatus,
    isOperationActive,
    isLoading,
  };
}
