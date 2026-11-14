export interface ActiveObject {
  box: [number, number, number, number];
  class_name: string;
  confidence: number;
  display_name: string;
  bin_label: string;
  bin_color: string;
  waste_nature: string;
  stability?: number;
}

export interface DetectionEvent {
  id: number;
  timestamp: string;
  source: string;
  class_name: string;
  display_name: string;
  confidence: number;
  bin_label: string;
  waste_nature: string;
}

export interface TelemetryData {
  state: 'IDLE' | 'TRACKING';
  stability: number;
  fps: number;
  active_object: ActiveObject | null;
  detections: ActiveObject[];
  recent_logs: DetectionEvent[];
}

export interface StatsData {
  total_detections: number;
  avg_confidence: number;
  most_common_waste: string;
  by_material: { name: string; count: number }[];
  by_nature: { name: string; count: number; color: string }[];
}

export interface SystemConfig {
  camera_idx: number;
  conf_threshold: number;
  auto_log: boolean;
  save_snapshots: boolean;
}

