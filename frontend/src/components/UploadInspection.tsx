import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle } from 'lucide-react';
import type { ActiveObject } from '../types';

export const UploadInspection: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<ActiveObject[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResults(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Erreur lors de l'analyse de l'image.");
      }

      const data = await res.json();
      setResults(data.detections);
    } catch (err: any) {
      setError(err.message || 'Une erreur est survenue.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Upload Zone */}
      <div className="lg:col-span-7 flex flex-col gap-4">
        <label className="border-2 border-dashed border-slate-300 hover:border-blue-500 bg-white rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors shadow-xs">
          <UploadCloud className="w-12 h-12 text-slate-400 mb-3" />
          <p className="text-sm font-bold text-slate-700">
            Cliquez pour importer une photo d'emballage
          </p>
          <p className="text-xs text-slate-400 mt-1">Formats acceptés : JPG, PNG, WebP</p>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>

        {previewUrl && (
          <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col items-center">
            <img
              src={previewUrl}
              alt="Preview"
              className="max-h-96 rounded-xl object-contain shadow-xs"
            />
            <button
              onClick={handleUpload}
              disabled={loading}
              className="mt-4 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold font-mono rounded-xl shadow-xs transition-colors disabled:opacity-50"
            >
              {loading ? 'ANALYSE EN COURS...' : 'LANCER L\'INSPECTION OPTIQUE'}
            </button>
          </div>
        )}
      </div>

      {/* Analysis Result */}
      <div className="lg:col-span-5 flex flex-col gap-4">
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <h2 className="text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-4">
            Résultats de l'Inspection
          </h2>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs font-medium">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {results === null && !loading && !error && (
            <div className="text-center py-12 text-slate-400">
              <p className="text-xs">Importez une image pour voir le diagnostic de tri.</p>
            </div>
          )}

          {results !== null && results.length === 0 && (
            <div className="text-center py-8 text-amber-600 bg-amber-50 rounded-xl border border-amber-200 p-4 text-xs font-medium">
              Aucune matière résolue sur ce cliché au seuil actuel.
            </div>
          )}

          {results !== null && results.length > 0 && (
            <div className="flex flex-col gap-3">
              {results.map((d, i) => (
                <div
                  key={i}
                  className="p-4 rounded-xl border bg-white shadow-xs"
                  style={{ borderLeftWidth: '6px', borderLeftColor: d.bin_color }}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-extrabold text-base text-slate-900">
                      {d.display_name.toUpperCase()}
                    </span>
                    <span className="text-xs font-mono font-bold text-blue-600">
                      {(d.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div
                    className="inline-block text-[11px] font-mono font-bold text-white px-2.5 py-1 rounded mt-2"
                    style={{ backgroundColor: d.bin_color }}
                  >
                    {d.bin_label.toUpperCase()}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Filière de traitement : <b>{d.waste_nature}</b>
                  </p>
                </div>
              ))}

              <div className="flex items-center gap-2 p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-medium mt-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Inspection enregistrée avec succès dans la base SQLite.</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
