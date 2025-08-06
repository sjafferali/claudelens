import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

export interface DeletionProgressEvent extends WebSocketMessage {
  type: 'deletion_progress';
  project_id: string;
  stage: string;
  progress: number;
  message: string;
  completed: boolean;
  error?: string;
  timestamp: string;
}

export interface WebSocketOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  send: (message: unknown) => void;
  close: () => void;
  reconnect: () => void;
  lastMessage: WebSocketMessage | null;
}

const DEFAULT_OPTIONS: Required<
  Omit<WebSocketOptions, 'onConnect' | 'onDisconnect' | 'onError' | 'onMessage'>
> = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
};

export function useWebSocket(
  url: string | null,
  options: WebSocketOptions = {}
): UseWebSocketReturn {
  const optionsRef = useRef({ ...DEFAULT_OPTIONS, ...options });
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const shouldConnectRef = useRef(true);

  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = { ...DEFAULT_OPTIONS, ...options };
  }, [options]);

  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
    }

    heartbeatTimeoutRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() })
        );
        startHeartbeat(); // Schedule next heartbeat
      }
    }, optionsRef.current.heartbeatInterval);
  }, []);

  const connect = useCallback(() => {
    if (!url || !shouldConnectRef.current) return;

    setIsConnecting(true);
    setError(null);

    try {
      // Determine WebSocket URL
      const wsUrl =
        url.startsWith('ws://') || url.startsWith('wss://')
          ? url
          : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${url}`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectAttemptsRef.current = 0;
        optionsRef.current.onConnect?.();
        startHeartbeat();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          setLastMessage(message);
          optionsRef.current.onMessage?.(message);
        } catch (err) {
          console.warn('Failed to parse WebSocket message:', event.data);
        }
      };

      wsRef.current.onclose = (event) => {
        setIsConnected(false);
        setIsConnecting(false);
        clearTimeouts();
        optionsRef.current.onDisconnect?.();

        // Only attempt to reconnect if not closed intentionally and we haven't exceeded max attempts
        if (
          shouldConnectRef.current &&
          event.code !== 1000 &&
          reconnectAttemptsRef.current < optionsRef.current.maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current++;
          setError(
            `Connection lost. Reconnecting... (${reconnectAttemptsRef.current}/${optionsRef.current.maxReconnectAttempts})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, optionsRef.current.reconnectInterval);
        } else if (
          reconnectAttemptsRef.current >=
          optionsRef.current.maxReconnectAttempts
        ) {
          setError('Connection failed. Maximum reconnection attempts reached.');
        }
      };

      wsRef.current.onerror = (event) => {
        setError('WebSocket error occurred');
        optionsRef.current.onError?.(event);
      };
    } catch (err) {
      setIsConnecting(false);
      setError(`Failed to create WebSocket connection: ${err}`);
    }
  }, [url, startHeartbeat, clearTimeouts]);

  const close = useCallback(() => {
    shouldConnectRef.current = false;
    clearTimeouts();

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client closing connection');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    setError(null);
    reconnectAttemptsRef.current = 0;
  }, [clearTimeouts]);

  const send = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const messageStr =
          typeof message === 'string' ? message : JSON.stringify(message);
        wsRef.current.send(messageStr);
      } catch (err) {
        console.error('Failed to send WebSocket message:', err);
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message);
    }
  }, []);

  const reconnect = useCallback(() => {
    close();
    shouldConnectRef.current = true;
    reconnectAttemptsRef.current = 0;
    connect();
  }, [close, connect]);

  // Connect when URL changes or component mounts
  useEffect(() => {
    if (url) {
      shouldConnectRef.current = true;
      connect();
    }

    return () => {
      shouldConnectRef.current = false;
      close();
    };
  }, [url, connect, close]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldConnectRef.current = false;
      clearTimeouts();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [clearTimeouts]);

  return {
    isConnected,
    isConnecting,
    error,
    send,
    close,
    reconnect,
    lastMessage,
  };
}

export function useDeletionProgress(
  onProgress?: (event: DeletionProgressEvent) => void
) {
  const { isConnected, lastMessage } = useWebSocket('/api/v1/ws/stats');

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'deletion_progress' && onProgress) {
      onProgress(lastMessage as DeletionProgressEvent);
    }
  }, [lastMessage, onProgress]);

  return {
    isConnected,
  };
}
