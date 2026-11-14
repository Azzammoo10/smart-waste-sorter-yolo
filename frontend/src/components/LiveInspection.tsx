import React from 'react';
import { Camera, VideoOff, CheckCircle2, Clock } from 'lucide-react';
import type { TelemetryData } from '../types';

interface LiveInspectionProps {
  telemetry: TelemetryData;
  isStreaming: boolean;
  streamKey: number;
  onToggleStream: () => void;
}

const DIRECTIVES: Record<string, string> = {
  cardboard: "Aplatir la boîte ou brique d'emballage. Déposer dans le Bac Jaune (Recyclable Sec).",
  plastic: "Vider le liquide. Maintenir le bouchon vissé. Déposer dans le Bac Jaune (Recyclable Sec).",
  metal: "Vider la canette ou conserve métallique. Déposer directement dans le Bac Jaune.",
  glass: "Déposer dans le Bac Vert. Retirer les couvercles métalliques (à placer dans le bac jaune).",
  paper: "Déposer propre et sec sans film plastique dans le Bac Jaune / Bleu.",
  biodegradable: "Déposer dans le Bac Marron / Composteur organique.",
};

export const LiveInspection: React.FC<LiveInspectionProps> = ({
  telemetry,
  isStreaming,
  streamKey,
  onToggleStream,
}) => {
  const active = telemetry.active_object;
  const isTracking = telemetry.state === 'TRACKING' && active !== null;
  const binColor = active?.bin_color || '#2563EB';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* ── Left Column : Video Viewport ─────────────────────────────────── */}
      <div className="lg:col-span-7 flex flex-col gap-3">
        <div className="flex justify-between items-center bg-white px-4 py-2.5 rounded-xl border border-slate-200">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-ping" />
            <span className="text-xs font-bold text-slate-700 font-mono uppercase tracking-wider">
              Flux Caméra DirectShow
            </span>
          </div>

          <button
            onClick={onToggleStream}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm ${
              isStreaming
                ? 'bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isStreaming ? (
              <>
                <VideoOff className="w-3.5 h-3.5" /> Arrêter la Caméra
              </>
            ) : (
              <>
                <Camera className="w-3.5 h-3.5" /> Activer l'Acquisition Vidéo
              </>
            )}
          </button>
        </div>

        {/* Video Viewport */}
        <div className="relative aspect-4/3 w-full bg-slate-950 rounded-2xl overflow-hidden border border-slate-200 shadow-md flex items-center justify-center">
          {isStreaming ? (
            <img
              src={`/api/video_feed?t=${streamKey}`}
              alt="Live Camera Feed"
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="text-center p-8 text-slate-400">
              <Camera className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm font-semibold text-slate-300">Acquisition vidéo en pause</p>
              <p className="text-xs text-slate-500 mt-1">
                Cliquez sur "Activer l'Acquisition Vidéo" pour lancer la détection en direct.
              </p>
            </div>
          )}

          {/* Real-time Telemetry Tag on bottom left of video */}
          {isStreaming && (
            <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 text-white font-mono text-[11px] flex items-center gap-3">
              <span className="text-emerald-400 font-bold">{telemetry.fps.toFixed(1)} FPS</span>
              <span className="text-slate-400">|</span>
              <span className="text-slate-300">YOLO 640x480</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Right Column : Live Decision & Telemetry ─────────────────────── */}
      <div className="lg:col-span-5 flex flex-col gap-4">
        {/* Dynamic Decision Banner */}
        <div
          className="rounded-2xl p-6 bg-white border border-slate-200 shadow-sm transition-all duration-200"
          style={{
            borderLeftWidth: '8px',
            borderLeftColor: isTracking ? binColor : '#94A3B8',
          }}
        >
          <div className="flex justify-between items-center mb-1">
            <span
              className="font-mono text-xs font-bold uppercase tracking-wider"
              style={{ color: isTracking ? binColor : '#64748B' }}
            >
              {isTracking ? 'DÉTECTION DIRECTE CONFIRMÉE' : 'CAPTEUR EN ATTENTE'}
            </span>
            {isTracking && (
              <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3 h-3" /> STABILISÉ
              </span>
            )}
          </div>

          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight my-2">
            {isTracking ? active.display_name.toUpperCase() : 'POSTE DE TRI PRÊT'}
          </h2>

          <div
            className="inline-block text-xs font-mono font-bold px-3.5 py-1.5 rounded-md text-white mb-3 shadow-xs tracking-wide"
            style={{ backgroundColor: isTracking ? binColor : '#64748B' }}
          >
            {isTracking
              ? `DESTINATION : ${active.bin_label.toUpperCase()}`
              : 'ZONE LIBRE // EN ATTENTE D\'OBJET'}
          </div>

          <div className="bg-slate-50 border-l-4 border-slate-300 p-3.5 rounded-r-lg text-xs font-medium text-slate-700 mt-2 leading-relaxed">
            {isTracking
              ? DIRECTIVES[active.class_name] ||
                'Déposer dans le bac prescrit en respectant les consignes de tri.'
              : 'Présentez un emballage devant l\'objectif pour une reconnaissance immédiate et fluide.'}
          </div>
        </div>

        {/* 2 KPI Mini Metric Boxes */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="font-mono text-[11px] text-slate-500 uppercase tracking-wider mb-1">
              Matière Active
            </div>
            <div
              className="text-xl font-extrabold truncate"
              style={{ color: isTracking ? binColor : '#0F172A' }}
            >
              {isTracking ? active.display_name : '--'}
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="font-mono text-[11px] text-slate-500 uppercase tracking-wider mb-1">
              Certitude IA
            </div>
            <div className="text-xl font-extrabold text-slate-900">
              {isTracking ? `${(active.confidence * 100).toFixed(1)}%` : '-- %'}
            </div>
          </div>
        </div>

        {/* Live Stability Gauge */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-center font-mono text-[11px] font-bold text-slate-600 mb-2">
            <span>STABILITÉ DU SIGNAL</span>
            <span>{isTracking ? `${Math.round(telemetry.stability * 100)}%` : '0%'}</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-150"
              style={{ width: `${isTracking ? Math.round(telemetry.stability * 100) : 0}%` }}
            />
          </div>
        </div>

        {/* Recent Detections Log Feed */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <h3 className="text-xs font-bold text-slate-600 uppercase font-mono tracking-wider">
              Derniers Dépôts Validés (SQLite)
            </h3>
          </div>

          <div className="flex flex-col divide-y divide-slate-100 text-xs font-mono">
            {telemetry.recent_logs && telemetry.recent_logs.length > 0 ? (
              telemetry.recent_logs.map((log) => (
                <div key={log.id} className="py-2 flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">{log.display_name}</span>
                    <span className="text-blue-600 text-[11px]">
                      [{(log.confidence * 100).toFixed(0)}%]
                    </span>
                  </div>
                  <span className="text-slate-500 text-[11px]">{log.timestamp.slice(-8)}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-3 text-center">
                Aucun dépôt enregistré pour le moment.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
