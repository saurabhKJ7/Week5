import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface UseWebSocketProps {
  url: string;
  onOutput: (output: string) => void;
  onError: (error: string) => void;
  onExplanation: (explanation: string) => void;
}

export const useWebSocket = ({
  url,
  onOutput,
  onError,
  onExplanation,
}: UseWebSocketProps) => {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    const connectSocket = () => {
      if (reconnectAttempts.current >= maxReconnectAttempts) {
        onError('Maximum reconnection attempts reached. Please refresh the page.');
        return;
      }

      // Initialize socket connection
      socketRef.current = io(url, {
        path: '/socket.io',
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        timeout: 20000,
        forceNew: true,
        withCredentials: true,
        autoConnect: true
      });

      // Set up event listeners
      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
      });

      socketRef.current.on('connect_error', (error: Error) => {
        console.error('Connection error:', error);
        setIsConnected(false);
        reconnectAttempts.current += 1;
        onError(`Connection error: ${error.message}`);

        if (reconnectAttempts.current < maxReconnectAttempts) {
          setTimeout(() => {
            console.log('Attempting to reconnect...');
            socketRef.current?.connect();
          }, 2000 * Math.pow(2, reconnectAttempts.current)); // Exponential backoff
        }
      });

      socketRef.current.on('output', (data: string) => {
        console.log('Received output:', data);
        onOutput(data);
      });

      socketRef.current.on('error', (error: string) => {
        console.error('Server error:', error);
        onError(error);
      });

      socketRef.current.on('explanation', (data: string) => {
        console.log('Received explanation:', data);
        onExplanation(data);
      });

      socketRef.current.on('disconnect', (reason: string) => {
        console.log('WebSocket disconnected:', reason);
        setIsConnected(false);

        if (reason === 'io server disconnect' || reason === 'transport close') {
          setTimeout(() => {
            if (socketRef.current) {
              console.log('Attempting to reconnect after disconnect...');
              socketRef.current.connect();
            }
          }, 1000);
        }
      });
    };

    connectSocket();

    // Cleanup on unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      reconnectAttempts.current = 0;
    };
  }, [url, onOutput, onError, onExplanation, maxReconnectAttempts]);

  const executeCode = useCallback(
    (code: string, language: string) => {
      if (!socketRef.current?.connected) {
        onError('Not connected to server. Please wait for reconnection...');
        return;
      }

      try {
        console.log('Executing code:', { code, language });
        socketRef.current.emit('execute', { code, language });
      } catch (error) {
        console.error('Execute error:', error);
        onError(`Failed to execute code: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    },
    [onError]
  );

  const requestExplanation = useCallback(
    (code: string, output: string) => {
      if (!socketRef.current?.connected) {
        onError('Not connected to server. Please wait for reconnection...');
        return;
      }

      try {
        console.log('Requesting explanation:', { code, output });
        socketRef.current.emit('explain', { code, output });
      } catch (error) {
        console.error('Explanation error:', error);
        onError(`Failed to request explanation: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    },
    [onError]
  );

  return {
    executeCode,
    requestExplanation,
    isConnected,
  };
};

export default useWebSocket; 