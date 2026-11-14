import React, { useEffect, useState } from 'react';
import { Download, Trash2, RefreshCw } from 'lucide-react';
import type { DetectionEvent, StatsData } from '../types';

export const AnalyticsDashboard: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [detections, setDetections] = useState<DetectionEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterMaterial, setFilterMaterial] = useState<string>('all');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resStats, resDets] = await Promise.all([
        fetch('/api/stats'),
        fetch('/api/detections?limit=100'),
      ]);
      const dataStats = await resStats.json();
      const dataDets = await resDets.json();
      setStats(dataStats);
      setDetections(dataDets);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleClearDb = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir purger le registre SQLite ?')) {
      await fetch('/api/detections/clear', { method: 'POST' });
      fetchData();
    }
  };

  const filteredDetections = detections.filter((d) => {
    if (filterMaterial !== 'all' && d.display_name !== filterMaterial) return false;
    return true;
  });

  const uniqueMaterials = Array.from(new Set(detections.map((d) => d.display_name)));

  const recyclableCount =
    stats?.by_nature
      .filter((n) => n.name.toLowerCase().includes('recyclable'))
      .reduce((sum, n) => sum + n.count, 0) || 0;
  const rateRecyclable =
    stats && stats.total_detections > 0
      ? ((recyclableCount / stats.total_detections) * 100).toFixed(1)
      : '0.0';

  return (
    <div className="flex flex-col gap-6">
      {/* 4 KPI Top Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="font-mono text-[11px] text-slate-500 uppercase tracking-wider mb-1">
            Total Unités Traitées
          </div>
          <div className="text-3xl font-extrabold text-slate-900 leading-tight">
            {stats?.total_detections ?? 0}
          </div>
          <div className="text-xs text-emerald-600 font-semibold mt-1">Registre SQLite Actif</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="font-mono text-[11px] text-slate-500 uppercase tracking-wider mb-1">
            Matière Majoritaire
          </div>
          <div className="text-2xl font-extrabold text-slate-900 leading-tight truncate">
            {stats?.most_common_waste ? stats.most_common_waste.toUpperCase() : '--'}
          </div>
          <div className="text-xs text-slate-500 font-medium mt-1">Fréquence la plus élevée</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="font-mono text-[11px] text-slate-500 uppercase tracking-wider mb-1">
            Score Moyen IA
          </div>
          <div className="text-3xl font-extrabold text-slate-900 leading-tight">
            {stats ? `${(stats.avg_confidence * 100).toFixed(1)}%` : '-- %'}
          </div>
          <div className="text-xs text-blue-600 font-semibold mt-1">Certitude de détection</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="font-mono text-[11px] text-slate-500 uppercase tracking-wider mb-1">
            Taux Recyclabilité
          </div>
          <div className="text-3xl font-extrabold text-slate-900 leading-tight">
            {rateRecyclable}%
          </div>
          <div className="text-xs text-emerald-600 font-semibold mt-1">Filière valorisable</div>
        </div>
      </div>

      {/* Material Breakdown */}
      {stats && stats.by_material.length > 0 && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-700">
              Distribution par Type de Matière
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              {stats.total_detections} unités au total
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {stats.by_material.map((mat) => {
              const pct = ((mat.count / stats.total_detections) * 100).toFixed(1);
              return (
                <div key={mat.name} className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="flex justify-between text-xs font-bold mb-1">
                    <span className="text-slate-900">{mat.name}</span>
                    <span className="text-blue-600 font-mono">
                      {mat.count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden mt-2">
                    <div className="h-full bg-blue-600 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Events Table & Action Buttons */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
          <div>
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-700">
              Registre d'Inspection SQL
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Historique complet des détections confirmées et enregistrées
            </p>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <select
              value={filterMaterial}
              onChange={(e) => setFilterMaterial(e.target.value)}
              className="px-3 py-1.5 text-xs font-mono font-medium rounded-lg border border-slate-200 bg-white text-slate-700"
            >
              <option value="all">Toutes les matières</option>
              {uniqueMaterials.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>

            <a
              href="/api/export-csv"
              download
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-mono font-bold transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> CSV
            </a>

            <button
              onClick={handleClearDb}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-mono font-bold transition-colors"
              title="Purger le registre"
            >
              <Trash2 className="w-3.5 h-3.5" /> Purger
            </button>

            <button
              onClick={fetchData}
              disabled={loading}
              className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
              title="Actualiser"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-100">
          <table className="w-full text-left font-mono text-xs divide-y divide-slate-100">
            <thead className="bg-slate-50 text-slate-600 uppercase text-[11px] font-bold">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Horodatage</th>
                <th className="px-4 py-3">Matière</th>
                <th className="px-4 py-3">Certitude</th>
                <th className="px-4 py-3">Bac Destination</th>
                <th className="px-4 py-3">Filière</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {filteredDetections.length > 0 ? (
                filteredDetections.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-2.5 font-bold text-slate-400">#{row.id}</td>
                    <td className="px-4 py-2.5 text-slate-500">{row.timestamp}</td>
                    <td className="px-4 py-2.5 font-bold text-slate-900">{row.display_name}</td>
                    <td className="px-4 py-2.5 font-bold text-blue-600">
                      {(row.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-2.5">{row.bin_label}</td>
                    <td className="px-4 py-2.5 text-slate-500">{row.waste_nature}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Aucun enregistrement ne correspond au filtre.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
