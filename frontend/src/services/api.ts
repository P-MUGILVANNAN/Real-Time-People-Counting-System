import axios from 'axios';
import {
  TelemetryStats,
  AlertItem,
  AnalyticsSnapshot,
  SessionItem,
  ExperimentItem,
  ModelsStatus
} from '../types';

export const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8000';
export const WS_BASE_URL = (import.meta as any).env?.VITE_WS_URL || 'ws://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health & Models
  getHealth: () => client.get('/api/health'),
  getModelsStatus: () => client.get<ModelsStatus>('/api/models'),
  getSystemStatus: () => client.get('/api/system/status'),

  // Camera
  startCamera: (cameraIndex: number = 0, trackerType: string = 'bytetrack', confThresh?: number) =>
    client.post('/api/camera/start', {
      camera_index: cameraIndex,
      tracker_type: trackerType,
      confidence_thresh: confThresh
    }),
  stopCamera: () => client.post('/api/camera/stop'),
  toggleDisplay: (key: string, value: boolean) =>
    client.post('/api/camera/toggle', { key, value }),
  captureScreenshot: () => client.post<{ status: string; file_path: string }>('/api/camera/screenshot'),
  toggleRecording: (enable: boolean) => client.post('/api/camera/record', null, { params: { enable } }),

  // Video
  getVideoFiles: () => client.get<{ count: number; videos: any[] }>('/api/video/files'),
  uploadVideo: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/api/video/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  startVideo: (videoFilename: string, trackerType: string = 'bytetrack', confThresh?: number) =>
    client.post('/api/video/start', {
      video_filename: videoFilename,
      tracker_type: trackerType,
      confidence_thresh: confThresh
    }),
  stopVideo: () => client.post('/api/video/stop'),
  pauseVideo: () => client.post('/api/video/pause'),
  resumeVideo: () => client.post('/api/video/resume'),
  getVideoStatus: () => client.get<TelemetryStats>('/api/video/status'),

  // Analytics & History
  getCurrentAnalytics: () => client.get<{ status: string; data: TelemetryStats; recent_alerts: AlertItem[]; current_session_id: string }>('/api/analytics/current'),
  getAnalyticsHistory: (sessionId?: string, limit: number = 100) =>
    client.get<{ count: number; snapshots: AnalyticsSnapshot[] }>('/api/analytics/history', {
      params: { session_id: sessionId, limit }
    }),
  getSessions: (limit: number = 20) => client.get<{ count: number; sessions: SessionItem[] }>('/api/analytics/sessions', { params: { limit } }),
  getAlerts: (limit: number = 50) => client.get<{ count: number; alerts: AlertItem[] }>('/api/analytics/alerts', { params: { limit } }),
  acknowledgeAlert: (alertId: string) => client.post('/api/analytics/alerts/ack', { alert_id: alertId }),
  getRegions: () => client.get('/api/analytics/regions'),
  createRegion: (region: any) => client.post('/api/analytics/regions', region),
  createLine: (line: any) => client.post('/api/analytics/lines', line),
  updateThresholds: (thresholds: any) => client.post('/api/analytics/thresholds', thresholds),

  // Reports
  getReportsSummary: () => client.get('/api/reports/summary'),
  getExportCsvUrl: (sessionId?: string) => `${API_BASE_URL}/api/reports/export/csv${sessionId ? `?session_id=${sessionId}` : ''}`,
  getExportJsonUrl: (sessionId?: string) => `${API_BASE_URL}/api/reports/export/json${sessionId ? `?session_id=${sessionId}` : ''}`,

  // Experiments
  getExperiments: () => client.get<{ count: number; experiments: ExperimentItem[] }>('/api/experiments'),
  runExperiment: (config: any) => client.post('/api/experiments/run', config),
  getExperimentById: (id: string) => client.get<ExperimentItem>(`/api/experiments/${id}`),

  // Video Stream URL
  getVideoStreamUrl: () => `${API_BASE_URL}/api/video/stream`
};
