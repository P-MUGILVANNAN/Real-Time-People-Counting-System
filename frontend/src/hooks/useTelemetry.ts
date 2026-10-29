import { useState, useEffect, useRef } from 'react';
import { TelemetryStats, AlertItem } from '../types';
import { apiService, WS_BASE_URL } from '../services/api';

const defaultStats: TelemetryStats = {
  is_running: false,
  is_paused: false,
  source: 'none',
  frame_index: 0,
  source_fps: 0,
  processing_fps: 0,
  latency_ms: 0,
  frame_detection_count: 0,
  active_tracked_count: 0,
  cumulative_unique_count: 0,
  density_count: 0,
  hybrid_count: 0,
  crowd_status: 'normal',
  occlusion_index: 0,
  difficulty_category: 'low',
  lines: {},
  regions: {}
};

export function useTelemetry() {
  const [stats, setStats] = useState<TelemetryStats>(defaultStats);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let pollTimer: any = null;

    const connectWebSocket = () => {
      try {
        const socket = new WebSocket(`${WS_BASE_URL}/ws/analytics`);
        wsRef.current = socket;

        socket.onopen = () => {
          setIsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.stats) setStats(parsed.stats);
            if (parsed.alerts) setAlerts(parsed.alerts);
            if (parsed.session_id) setSessionId(parsed.session_id);
          } catch (e) {
            console.error('Error parsing telemetry payload:', e);
          }
        };

        socket.onclose = () => {
          setIsConnected(false);
          // Try reconnecting in 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch (err) {
        setIsConnected(false);
      }
    };

    connectWebSocket();

    // Fallback polling ticker every 2 seconds
    pollTimer = setInterval(async () => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        try {
          const res = await apiService.getCurrentAnalytics();
          if (res.data && res.data.data) {
            setStats(res.data.data);
            if (res.data.recent_alerts) setAlerts(res.data.recent_alerts);
            if (res.data.current_session_id) setSessionId(res.data.current_session_id);
          }
        } catch (e) {
          // backend may be idle
        }
      }
    }, 2000);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pollTimer) clearInterval(pollTimer);
    };
  }, []);

  return { stats, alerts, sessionId, isConnected };
}
