import React, { useEffect, useState } from 'react';
import { Camera, Upload, BarChart3 } from 'lucide-react';
import { Navbar } from './components/Navbar';
import { LiveInspection } from './components/LiveInspection';
import { UploadInspection } from './components/UploadInspection';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { SettingsModal } from './components/SettingsModal';
import type { SystemConfig, TelemetryData } from './types';

const defaultTelemetry: TelemetryData = {
  state: 'IDLE',
  stability: 0.0,
  fps: 0.0,
  active_object: null,
  detections: [],
  recent_logs: [],
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'live' | 'upload' | 'analytics'>('live');
  const [telemetry, setTelemetry] = useState<TelemetryData>(defaultTelemetry);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamKey, setStreamKey] = useState<number>(Date.now());
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [config, setConfig] = useState<SystemConfig>({
    camera_idx: 0,
    conf_threshold: 0.35,
    auto_log: true,
    save_snapshots: false,
  });

  // Fetch initial system status & configuration
  useEffect(() => {
    fetch('/api/status')
      .then((res) => res.json())
      .then((data) => {
        if (data.threshold !== undefined) {
          setConfig({
            camera_idx: data.camera?.index ?? 0,
            conf_threshold: data.threshold,
            auto_log: data.auto_log ?? true,
            save_snapshots: false,
          });
        }
      })
      .catch((err) => console.error('Status fetch error:', err));

    fetch('/api/camera/status')
      .then((res) => res.json())
      .then((data) => {
        setIsStreaming(Boolean(data.is_running));
      })
      .catch(() => {});
  }, []);

  const handleToggleStream = async () => {
    try {
      if (isStreaming) {
        await fetch('/api/camera/stop', { method: 'POST' });
        setIsStreaming(false);
      } else {
        await fetch('/api/camera/start', { method: 'POST' });
        setIsStreaming(true);
        setStreamKey(Date.now());
      }
    } catch (err) {
      console.error('Camera toggle error:', err);
    }
  };


  // Connect to WebSocket Telemetry Stream
  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollInterval: any = null;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setTelemetry(data);
        } catch (e) {
          console.error('Telemetry parse error:', e);
        }
      };

      ws.onerror = () => {
        // Fallback polling if WS fails
        if (!pollInterval) {
          pollInterval = setInterval(async () => {
            try {
              const res = await fetch('/api/telemetry');
              const data = await res.json();
              setTelemetry(data);
            } catch {}
          }, 100);
        }
      };

      ws.onclose = () => {
        setTimeout(connectWebSocket, 2000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  const handleSaveConfig = async (newConfig: SystemConfig) => {
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig),
      });
      if (res.ok) {
        setConfig(newConfig);
      }
    } catch (err) {
      console.error('Config save error:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 px-4 sm:px-8 py-6 max-w-7xl mx-auto">
      {/* Top Navbar */}
      <Navbar fps={telemetry.fps} onOpenSettings={() => setIsSettingsOpen(true)} />

      {/* Navigation Tabs Bar */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-200/70 border border-slate-300/60 rounded-xl w-fit mb-6 shadow-2xs">
        <button
          onClick={() => setActiveTab('live')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'live'
              ? 'bg-white text-blue-600 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Camera className="w-3.5 h-3.5" />
          <span>Poste Direct</span>
        </button>

        <button
          onClick={() => setActiveTab('upload')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'upload'
              ? 'bg-white text-blue-600 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Analyse d'Image Fixe</span>
        </button>

        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'analytics'
              ? 'bg-white text-blue-600 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Tableau de Bord & Analytique</span>
        </button>
      </div>

      {/* Active Tab View */}
      <main>
        {activeTab === 'live' && (
          <LiveInspection
            telemetry={telemetry}
            isStreaming={isStreaming}
            streamKey={streamKey}
            onToggleStream={handleToggleStream}
          />
        )}
        {activeTab === 'upload' && <UploadInspection />}
        {activeTab === 'analytics' && <AnalyticsDashboard />}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        config={config}
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSave={handleSaveConfig}
      />
    </div>
  );
};

export default App;
