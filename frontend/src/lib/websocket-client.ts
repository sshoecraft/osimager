/**
 * WebSocket client for real-time build monitoring.
 * 
 * Provides real-time updates for build status, progress, and logs.
 */

import type {
  WebSocketMessage,
  InitialStatusMessage,
  BuildStatusMessage,
  BuildLogMessage,
  BuildProgressMessage,
} from '@/types/api';

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

export interface WebSocketOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export class OSImagerWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number;
  private maxReconnectAttempts: number;
  private heartbeatInterval: number;
  private reconnectAttempts = 0;
  private isConnecting = false;
  private shouldReconnect = true;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private generalHandlers: Set<WebSocketEventHandler> = new Set();

  constructor(options: WebSocketOptions = {}) {
    this.url = options.url || this.getWebSocketURL();
    this.reconnectInterval = options.reconnectInterval || 2000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 20;
    this.heartbeatInterval = options.heartbeatInterval || 25000;
  }

  private getWebSocketURL(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/backend/builds/ws`;
  }

  /**
   * Connect to the WebSocket server.
   */
  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    // Cancel any pending reconnection
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.isConnecting = true;
    this.shouldReconnect = true;

    try {
      // Close any existing connection first
      if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
        this.ws.close();
      }

      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

      // Wait for connection
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, 10000);

        this.ws!.onopen = (event) => {
          clearTimeout(timeout);
          this.handleOpen(event);
          resolve();
        };

        this.ws!.onerror = (event) => {
          clearTimeout(timeout);
          this.handleError(event);
          reject(new Error('WebSocket connection failed'));
        };
      });
    } catch (error) {
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * Disconnect from the WebSocket server.
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.clearTimers();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check if WebSocket is connected.
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Send a message to the server.
   */
  send(message: any): void {
    if (!this.isConnected) {
      console.warn('WebSocket not connected, cannot send message:', message);
      return;
    }

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  /**
   * Manually trigger a reconnection attempt.
   */
  reconnect(): void {
    console.log('Manual reconnection triggered');
    this.disconnect();
    this.reconnectAttempts = 0; // Reset attempts for manual reconnect
    this.shouldReconnect = true;
    this.connect().catch(error => {
      console.error('Manual reconnect failed:', error);
    });
  }

  /**
   * Subscribe to a specific build for updates.
   */
  subscribeToBuild(buildId: string): void {
    this.send({
      type: 'subscribe_build',
      build_id: buildId,
    });
  }

  /**
   * Add event handler for specific message type.
   */
  on(eventType: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler);
  }

  /**
   * Remove event handler for specific message type.
   */
  off(eventType: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(eventType);
      }
    }
  }

  /**
   * Add general event handler for all messages.
   */
  onMessage(handler: WebSocketEventHandler): void {
    this.generalHandlers.add(handler);
  }

  /**
   * Remove general event handler.
   */
  offMessage(handler: WebSocketEventHandler): void {
    this.generalHandlers.delete(handler);
  }

  private handleOpen(event: Event): void {
    console.log('WebSocket connected');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.startHeartbeat();

    // Notify handlers
    this.emitEvent({
      type: 'connection',
      data: { connected: true },
    });
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      console.debug('WebSocket message received:', message.type);
      
      // Handle heartbeat from server
      if (message.type === 'heartbeat') {
        this.send({ type: 'pong' });
        return;
      }
      
      this.emitEvent(message);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnecting = false;
    this.clearTimers();

    // Notify handlers
    this.emitEvent({
      type: 'connection',
      data: { connected: false },
    });

    // Attempt reconnection if appropriate (but not for intentional close codes)
    if (this.shouldReconnect && 
        this.reconnectAttempts < this.maxReconnectAttempts &&
        event.code !== 1000) { // 1000 = normal closure
      console.log(`Scheduling reconnect (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
      this.scheduleReconnect();
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('Max reconnection attempts reached');
      this.emitEvent({
        type: 'error',
        data: { error: 'Max reconnection attempts reached' },
      });
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.isConnecting = false;
    
    // Notify handlers
    this.emitEvent({
      type: 'error',
      data: { error: 'WebSocket connection error' },
    });
  }

  private emitEvent(message: WebSocketMessage): void {
    // Call specific handlers
    const specificHandlers = this.eventHandlers.get(message.type);
    if (specificHandlers) {
      specificHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }

    // Call general handlers
    this.generalHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in general WebSocket handler:', error);
      }
    });
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, this.heartbeatInterval);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    const delay = Math.min(
      this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts), // Gentler backoff
      15000 // Max 15 seconds
    );

    console.log(`Scheduling WebSocket reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect().catch(error => {
        console.error('WebSocket reconnect failed:', error);
        // Continue trying to reconnect unless we've hit the max
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      });
    }, delay);
  }

  private clearTimers(): void {
    this.clearHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

// Create and export singleton instance
export const wsClient = new OSImagerWebSocketClient();

// Export typed event handlers for convenience
export const createInitialStatusHandler = (
  handler: (data: InitialStatusMessage['data']) => void
): WebSocketEventHandler => {
  return (message) => {
    if (message.type === 'initial_status') {
      handler((message as InitialStatusMessage).data);
    }
  };
};

export const createBuildStatusHandler = (
  handler: (buildId: string, build: BuildStatusMessage['data']) => void
): WebSocketEventHandler => {
  return (message) => {
    if (message.type === 'build_status' && message.build_id) {
      handler(message.build_id, (message as BuildStatusMessage).data);
    }
  };
};

export const createBuildLogHandler = (
  handler: (buildId: string, logEntry: BuildLogMessage['data']) => void
): WebSocketEventHandler => {
  return (message) => {
    if (message.type === 'build_log' && message.build_id) {
      handler(message.build_id, (message as BuildLogMessage).data);
    }
  };
};

export const createBuildProgressHandler = (
  handler: (buildId: string, progress: BuildProgressMessage['data']) => void
): WebSocketEventHandler => {
  return (message) => {
    if (message.type === 'build_progress' && message.build_id) {
      handler(message.build_id, (message as BuildProgressMessage).data);
    }
  };
};

export default OSImagerWebSocketClient;
