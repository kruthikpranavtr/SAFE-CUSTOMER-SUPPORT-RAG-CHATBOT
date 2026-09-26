import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertCircle, RefreshCw, CheckCircle2, ShieldAlert, FileCode2, Layers } from 'lucide-react';
import { api } from '../services/api';
import { RiskItem } from '../types';

export const RiskRegisterPage: React.FC = () => {
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const fetchRisks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRiskRegister();
      setRisks(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch risk register items');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRisks();
  }, []);

  const categories = ['all', ...Array.from(new Set(risks.map((r) => r.category)))];

  const filteredRisks = selectedCategory === 'all'
    ? risks
    : risks.filter((r) => r.category === selectedCategory);

  const mitigatedCount = risks.filter((r) => r.status === 'Mitigated').length;
  const partialCount = risks.filter((r) => r.status === 'Partially Mitigated').length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <div className="p-2 bg-rose-50 text-rose-600 rounded-xl">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">AI Safety & Governance Risk Register</h1>
              <p className="text-xs text-slate-500">
                Systematic risk matrix tracking human-AI safety, cognitive bias mitigations, and reliability controls
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchRisks}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-4 py-2 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Matrix</span>
        </button>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Monitored Risks</div>
          <div className="text-2xl font-bold text-slate-900">{risks.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">Core cognitive & system risks</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-1">Mitigated</div>
          <div className="text-2xl font-bold text-emerald-700">{mitigatedCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">Full architectural guardrails</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-1">Partially Mitigated</div>
          <div className="text-2xl font-bold text-amber-700">{partialCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">Monitored via telemetry & A/B testing</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">Test Verification</div>
          <div className="text-2xl font-bold text-blue-700">100%</div>
          <div className="text-[11px] text-slate-400 mt-1">Automated scenario & live tests</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1">
        <span className="text-xs text-slate-500 font-medium mr-2 flex items-center gap-1">
          <Layers className="w-3.5 h-3.5" /> Category:
        </span>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
              selectedCategory === cat
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {cat === 'all' ? 'All Risks' : cat}
          </button>
        ))}
      </div>

      {/* Risk Register Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
            <p className="text-xs">Loading safety risk matrix...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600">
            <AlertCircle className="w-6 h-6 mx-auto mb-2" />
            <p className="text-xs">{error}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Risk Item</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-6">Mitigation Architecture</th>
                  <th className="py-3 px-4">Verification & Test Coverage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {filteredRisks.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-4 font-semibold text-slate-800">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-slate-400 text-[11px]">{item.id}</span>
                        <span>{item.risk}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700">
                        {item.category}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                        item.status === 'Mitigated'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {item.status === 'Mitigated' ? (
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <ShieldCheck className="w-3 h-3 text-amber-600" />
                        )}
                        {item.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-slate-600 max-w-md">
                      {item.mitigation}
                    </td>
                    <td className="py-4 px-4 text-slate-500 max-w-xs">
                      <div className="flex items-start space-x-1.5">
                        <FileCode2 className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                        <span className="text-[11px]">{item.test_coverage}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
