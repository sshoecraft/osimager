/**
 * Simplified WebSocket hook for testing connectivity.
 */

import { useEffect, useState } from 'react';
import { useAppStore } from '@/stores/app-store';

export function useWebSocket() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const { isConnected, setConnected } = useAppStore();

  useEffect(() => {
    // Create WebSocket connection with dynamic host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/backend/builds/ws`;
    console.log('🔌 Attempting WebSocket connection to:', wsUrl);
    
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('✅ WebSocket connected');
      setConnected(true);
      setWs(websocket);
    };
    
    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('📨 WebSocket message:', message);
        
        // Handle heartbeat
        if (message.type === 'heartbeat') {
          websocket.send(JSON.stringify({ type: 'pong' }));
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error);
      }
    };
    
    websocket.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      setConnected(false);
      setWs(null);
    };
    
    websocket.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setConnected(false);
    };

    // Cleanup on unmount
    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, [setConnected]);

  const reconnect = () => {
    if (ws) {
      ws.close();
    }
    // The useEffect will handle reconnection
  };

  return {
    isConnected,
    reconnect,
  };
}
