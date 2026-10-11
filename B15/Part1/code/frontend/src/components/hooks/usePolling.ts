import { useRef, useCallback } from 'react';

interface UsePollingOptions<T> {
  pollFunction: () => Promise<T>;
  onSuccess: (data: T) => void;
  onError: (error: string) => void;
  onProgress?: (message: string) => void;
  maxAttempts?: number;
  getInterval?: (attempt: number) => number;
  initialDelay?: number;
}

interface UsePollingReturn {
  startPolling: () => void;
  stopPolling: () => void;
  isPolling: boolean;
}

export function usePolling<T>({
  pollFunction,
  onSuccess,
  onError,
  onProgress,
  maxAttempts = 30,
  getInterval = (attempt: number) => {
    if (attempt <= 3) return 10000; // First 3 attempts: 10 seconds
    if (attempt <= 6) return 15000; // Next 3 attempts: 15 seconds
    if (attempt <= 10) return 20000; // Next 4 attempts: 20 seconds
    return 30000; // After that: 30 seconds
  },
  initialDelay = 15000,
}: UsePollingOptions<T>): UsePollingReturn {
  const pollingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
      pollingTimeoutRef.current = null;
    }
    isPollingRef.current = false;
    onProgress?.('');
  }, [onProgress]);

  const startPolling = useCallback(() => {
    // Prevent multiple polling loops
    if (isPollingRef.current) {
      console.log('Polling already in progress, skipping...');
      return;
    }

    // Clear any existing timeout
    stopPolling();

    isPollingRef.current = true;
    let pollAttempts = 0;

    const checkResult = async () => {
      // Check if polling was cancelled
      if (!isPollingRef.current) {
        return;
      }

      try {
        onProgress?.(
          `Checking for results... (attempt ${pollAttempts + 1}/${maxAttempts})`
        );
        const result = await pollFunction();
        onProgress?.('');
        onSuccess(result);
        isPollingRef.current = false; // Stop polling
      } catch {
        pollAttempts++;

        if (pollAttempts >= maxAttempts || !isPollingRef.current) {
          onProgress?.('');
          onError(
            'Operation is taking longer than expected. Please refresh to check status.'
          );
          isPollingRef.current = false;
          return;
        }

        const nextInterval = getInterval(pollAttempts);
        const nextCheckTime = Math.round(nextInterval / 1000);
        onProgress?.(
          `Next check in ${nextCheckTime} seconds... (attempt ${pollAttempts}/${maxAttempts})`
        );

        // Store timeout reference for cleanup
        pollingTimeoutRef.current = setTimeout(checkResult, nextInterval);
      }
    };

    // Start checking after initial delay
    onProgress?.(
      `Starting operation... will check in ${Math.round(
        initialDelay / 1000
      )} seconds`
    );
    pollingTimeoutRef.current = setTimeout(checkResult, initialDelay);
  }, [
    pollFunction,
    onSuccess,
    onError,
    onProgress,
    maxAttempts,
    getInterval,
    initialDelay,
    stopPolling,
  ]);

  return {
    startPolling,
    stopPolling,
    isPolling: isPollingRef.current,
  };
}
