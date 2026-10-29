export interface TelemetryStats {
  is_running: boolean;
  is_paused: boolean;
  source: string;
  frame_index: number;
  source_fps: number;
  processing_fps: number;
  latency_ms: number;
  frame_detection_count: number;
  active_tracked_count: number;
  cumulative_unique_count: number;
  density_count: number;
  density_weights_ready?: boolean;
  hybrid_count: number;
  crowd_status: 'normal' | 'moderate' | 'high' | 'critical';
  occlusion_index: number;
  difficulty_category: 'low' | 'moderate' | 'high' | 'severe';
  lines: Record<string, {
    line_id: string;
    name: string;
    count_in: number;
    count_out: number;
    net_flow: number;
  }>;
  regions: Record<string, {
    region_id: string;
    name: string;
    count: number;
    density_per_10k_px: number;
    status: 'normal' | 'moderate' | 'high' | 'critical';
    area_pixels: number;
  }>;
}

export interface AlertItem {
  alert_id: string;
  session_id?: string;
  severity: 'moderate' | 'high' | 'critical';
  message: string;
  source: string;
  metric_value: number;
  threshold_value: number;
  timestamp: number;
  acknowledged: boolean;
  acknowledged_at?: number;
}

export interface AnalyticsSnapshot {
  timestamp: number;
  frame_index: number;
  detection_count: number;
  active_tracked_count: number;
  cumulative_unique_count: number;
  density_estimate: number;
  hybrid_estimate: number;
  processing_fps: number;
  latency_ms: number;
  occlusion_index: number;
  difficulty_category: string;
}

export interface SessionItem {
  session_id: string;
  source_type: string;
  source_path: string;
  model_name: string;
  tracker_type: string;
  start_time: number;
  end_time?: number;
  total_frames: number;
  peak_count: number;
  avg_count: number;
  status: string;
}

export interface ExperimentItem {
  experiment_id: string;
  name: string;
  dataset_name: string;
  model_type: string;
  tracker_type: string;
  confidence_thresh: number;
  iou_thresh: number;
  crowding_group: string;
  sample_count: number;
  mae: number;
  rmse: number;
  mape: number;
  precision: number;
  recall: number;
  f1: number;
  ap50: number;
  mean_latency_ms: number;
  fps: number;
  created_at: number;
  status: string;
  results?: any;
}

export interface ModelsStatus {
  detector: {
    loaded: boolean;
    model_name: string;
    device: string;
    confidence_threshold: number;
    iou_threshold: number;
    last_fps: number;
  };
  density_model: {
    architecture: string;
    status: string;
    has_valid_weights: boolean;
    device: string;
  };
  tracker: {
    tracker_type: string;
    track_buffer: number;
    active_tracks_count: number;
    cumulative_unique_count: number;
  };
}
