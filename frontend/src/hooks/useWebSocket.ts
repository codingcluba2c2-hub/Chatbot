import { useState, useEffect, useRef, useCallback } from 'react';
import { MessageProps } from '@/components/chat/ChatMessage';

export function useWebSocket(
  url: string, 
  onMessageReceived: (data: any) => void,
  onStatusChange: (status: 'online' | 'offline') => void
) {
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 10;

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      onStatusChange('online');
      reconnectAttempts.current = 0;
      
      // Start ping heartbeat
      const pingInterval = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send('ping');
        } else {
          clearInterval(pingInterval);
        }
      }, 20000);
      
      // Store interval to clear on close
      (ws.current as any)._pingInterval = pingInterval;
    };

    ws.current.onmessage = (event) => {
      if (event.data === 'pong') return;
      try {
        const data = JSON.parse(event.data);
        onMessageReceived(data);
      } catch (e) {
        console.error('Invalid WS message', e);
      }
    };

    ws.current.onclose = () => {
      if ((ws.current as any)?._pingInterval) {
        clearInterval((ws.current as any)._pingInterval);
      }
      onStatusChange('offline');
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        setTimeout(() => {
          reconnectAttempts.current += 1;
          connect();
        }, timeout);
      }
    };

    ws.current.onerror = (error) => {
      // Browsers often fire a generic Event that logs as {}
      console.error('WebSocket Error encountered.');
      ws.current?.close();
    };
  }, [url, onMessageReceived, onStatusChange]);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  return { sendMessage };
}
