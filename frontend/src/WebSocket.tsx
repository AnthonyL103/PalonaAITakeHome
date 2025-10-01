import { useState, useEffect, useRef} from 'react';

interface WebSocketMessage {
  type: string;
  content?: any;
  message?: string;
  [key: string]: any;
}

export const useWebSocket = (onMessage?: (message: WebSocketMessage) => void) => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const isConnectingRef = useRef<boolean>(false);
  const onMessageRef = useRef(onMessage); 

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    const connect = () => {
      if (isConnectingRef.current || socketRef.current?.readyState === WebSocket.OPEN) {
        return;
      }

      isConnectingRef.current = true;
      console.log('Attempting WebSocket connection...');

      const ws = new WebSocket('ws://localhost:8000/ws');
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('Connected to localhost:8000');
        setIsConnected(true);
        isConnectingRef.current = false;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          onMessageRef.current?.(message);
        } catch (error) {
          console.error('Failed to parse message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code} ${event.reason}`);
        setIsConnected(false);
        isConnectingRef.current = false;
        socketRef.current = null;
        
        if (event.code !== 1000) {
          console.log(' Scheduling reconnection in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        isConnectingRef.current = false;
      };
    };

    connect();

    return () => {
      console.log('Cleaning up WebSocket...');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close(1000, 'Component unmounting');
        socketRef.current = null;
      }
      isConnectingRef.current = false;
    };
  }, []); 

  return { isConnected };
};

