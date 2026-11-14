import React, { useState } from 'react';
import { X, Save, Check } from 'lucide-react';
import type { SystemConfig } from '../types';

interface SettingsModalProps {
  config: SystemConfig;
  isOpen: boolean;
  onClose: () => void;
  onSave: (newConfig: SystemConfig) => Promise<void>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  config,
  isOpen,
  onClose,
  onSave,
}) => {
  const [cameraIdx, setCameraIdx] = useState<number>(config.camera_idx);
  const [threshold, setThreshold] = useState<number>(config.conf_threshold);
  const [autoLog, setAutoLog] = useState<boolean>(config.auto_log);
  const [saveSnapshots, setSaveSnapshots] = useState<boolean>(config.save_snapshots);
  const [saved, setSaved] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave({
      camera_idx: cameraIdx,
      conf_threshold: threshold,
      auto_log: autoLog,
      save_snapshots: saveSnapshots,
    });
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-100">
          <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-800">
            Configuration Système & Capteur
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-5">
          {/* Camera Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase font-mono mb-2">
              Index Caméra Video
            </label>
            <select
              value={cameraIdx}
              onChange={(e) => setCameraIdx(Number(e.target.value))}
              className="w-full px-3 py-2 text-xs font-mono rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Caméra 0 (Par défaut / Webcam intégrée)</option>
              <option value={1}>Caméra 1 (Externe / Périphérique USB)</option>
              <option value={2}>Caméra 2 (Secondaire)</option>
            </select>
          </div>

          {/* Confidence Slider */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-700 uppercase font-mono">
                Seuil de Sensibilité Détection
              </label>
              <span className="text-xs font-mono font-bold text-blue-600">
                {(threshold * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0.20"
              max="0.85"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="w-full accent-blue-600 h-2 bg-slate-100 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Recommandé : 0.60 - 0.65 pour filtrer les reflets et visages en arrière-plan.
            </p>
          </div>

          {/* Toggles */}
          <div className="flex flex-col gap-3 pt-2 border-t border-slate-100">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-xs font-medium text-slate-700">
                Journalisation automatique SQLite
              </span>
              <input
                type="checkbox"
                checked={autoLog}
                onChange={(e) => setAutoLog(e.target.checked)}
                className="w-4 h-4 rounded text-blue-600 accent-blue-600 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-xs font-medium text-slate-700">
                Archiver les captures optiques (.jpg)
              </span>
              <input
                type="checkbox"
                checked={saveSnapshots}
                onChange={(e) => setSaveSnapshots(e.target.checked)}
                className="w-4 h-4 rounded text-blue-600 accent-blue-600 cursor-pointer"
              />
            </label>
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold font-mono bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors"
            >
              {saved ? (
                <>
                  <Check className="w-3.5 h-3.5" /> Enregistré !
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" /> Sauvegarder
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
