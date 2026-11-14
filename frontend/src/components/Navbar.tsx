import React from 'react';
import { SlidersHorizontal } from 'lucide-react';

interface NavbarProps {
  fps: number;
  onOpenSettings: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ fps, onOpenSettings }) => {
  return (
    <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center px-6 py-4 bg-white/90 backdrop-blur-md border border-slate-200 rounded-2xl shadow-sm mb-6 gap-4">
      <div className="flex items-center gap-4">
        <div className="bg-slate-900 text-white font-mono text-xs font-bold px-3 py-1.5 rounded-lg tracking-widest shadow-sm">
          ECOVISION ST-04
        </div>
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight leading-snug">
            Système Industriel de Tri & Contrôle Optique
          </h1>
          <p className="text-xs text-slate-500 font-medium">
            Acquisition vidéo 60 FPS, stabilisation YOLO & télémesure SQLite
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 self-end sm:self-auto">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full font-mono text-xs font-bold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
          <span>STATION ACTIVE // {fps > 0 ? `${fps.toFixed(1)} FPS` : 'DIRECTSHOW'}</span>
        </div>

        <button
          onClick={onOpenSettings}
          className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl border border-slate-200 transition-colors"
          title="Paramètres Capteur & Modèle"
        >
          <SlidersHorizontal className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
