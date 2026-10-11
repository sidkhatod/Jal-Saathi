import React, { useState, useEffect } from 'react';
import { Language } from './Navbar';

interface WaterSection {
  action: string;
  amount_mm: number;
  method: string;
  depletion_mm: number;
  raw_mm: number;
  taw_mm: number;
  norm_depletion: number;
  advice: string;
  reason_key: string;
  confidence: number;
}

interface ProtectSection {
  status: string;
  disease_predicted?: string;
  advice: string;
  weather_window: string;
  reason_key: string;
  confidence: number;
}

interface NourishSection {
  status: string;
  advice: string;
  soil_context?: {
    level_used: string;
    year_used: string;
    district: string;
    dominant_ratings: Record<string, string>;
  };
  reason_key: string;
  confidence: number;
}

interface AdvisoryData {
  plot_id: string;
  as_of_date: string;
  crop: string;
  district: string;
  water: WaterSection;
  protect: ProtectSection;
  nourish: NourishSection;
  overall_confidence: number;
}

interface ThisWeekAdvisoryProps {
  lang: Language;
  setLang: (lang: Language) => void;
}

export const ThisWeekAdvisory: React.FC<ThisWeekAdvisoryProps> = ({ lang, setLang }) => {
  const [data, setData] = useState<AdvisoryData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const filename = lang === 'hi' ? '/demo/advisory_hi.json' : '/demo/advisory_en.json';
    fetch(filename)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: AdvisoryData) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load advisory:', err);
        setError('Failed to fetch advisory demo payload.');
        setLoading(false);
      });
  }, [lang]);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p>{lang === 'en' ? 'Loading this week advisory...' : 'साप्ताहिक सलाह लोड हो रही है...'}</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-red-400">
        <p>{error || 'No advisory data found.'}</p>
      </div>
    );
  }

  const overallPct = Math.round(data.overall_confidence * 100);

  return (
    <div className="space-y-6">
      {/* Header with Title and Language Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
            <span>📅 {data.as_of_date}</span>
            <span>•</span>
            <span>📍 {data.district}</span>
            <span>•</span>
            <span>🌾 {data.crop}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            {lang === 'en' ? 'Farmer Weekly Action Card' : 'किसान साप्ताहिक कार्य-सलाह'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            {lang === 'en'
              ? 'Multi-objective advisory combining root-zone physics, foliage health, and soil nutrients.'
              : 'जड़-क्षेत्र भौतिकी, फसल स्वास्थ्य और मृदा परीक्षण का संयुक्त 3-स्तंभीय परामर्श।'}
          </p>
        </div>

        {/* Right side: Language Toggle and Overall Confidence */}
        <div className="flex items-center space-x-3 self-start sm:self-auto">
          {/* Overall Confidence Badge */}
          <div className="glass-panel px-3.5 py-1.5 rounded-xl border border-emerald-500/30 flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block leading-tight">
                {lang === 'en' ? 'Model Confidence' : 'विश्वसनीयता'}
              </span>
              <span className="text-sm font-black text-emerald-300 font-mono">
                {overallPct}% Verified
              </span>
            </div>
          </div>

          {/* Quick Toggle Button */}
          <button
            onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}
            className="px-3 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center space-x-1"
          >
            <span>🌐</span>
            <span>{lang === 'en' ? 'हिन्दी में देखें' : 'Switch to English'}</span>
          </button>
        </div>
      </div>

      {/* 3 Pillars Grid: WATER, LEAVES, FEED */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Pillar 1: WATER (सिंचाई) */}
        <div className="glass-panel p-6 rounded-2xl border-t-4 border-t-cyan-400 flex flex-col justify-between space-y-4 glow-cyan">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center space-x-1.5">
                <span>💧</span>
                <span>{lang === 'en' ? 'Water Decision' : 'सिंचाई निर्णय'}</span>
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-bold">
                {data.water.method}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20">
              <div className="text-2xl font-black text-white font-mono flex items-baseline space-x-1">
                <span>{data.water.action.toUpperCase()}</span>
                <span className="text-cyan-400 text-lg">({data.water.amount_mm} mm)</span>
              </div>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {data.water.advice}
              </p>
            </div>

            {/* Metrics Breakdown */}
            <div className="space-y-1.5 text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              <div className="flex justify-between">
                <span className="text-slate-400">{lang === 'en' ? 'Current Depletion:' : 'वर्तमान नमी कमी:'}</span>
                <span className="font-mono font-bold text-white">{data.water.depletion_mm} mm</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">{lang === 'en' ? 'Trigger RAW:' : 'सिंचाई सीमा (RAW):'}</span>
                <span className="font-mono text-amber-300">{data.water.raw_mm} mm</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">{lang === 'en' ? 'Total Available (TAW):' : 'कुल धारिता (TAW):'}</span>
                <span className="font-mono text-slate-400">{data.water.taw_mm} mm</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Reason: <span className="font-mono text-slate-300">{data.water.reason_key}</span></span>
            <span className="font-mono text-cyan-400 font-semibold">{Math.round(data.water.confidence * 100)}% Conf.</span>
          </div>
        </div>

        {/* Pillar 2: LEAVES (पत्तियां / फसल सुरक्षा) */}
        <div className="glass-panel p-6 rounded-2xl border-t-4 border-t-amber-400 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center space-x-1.5">
                <span>🍃</span>
                <span>{lang === 'en' ? 'Foliage & Protection' : 'पत्तियां व फसल सुरक्षा'}</span>
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20 font-bold">
                {data.protect.status.toUpperCase()}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/20">
              <div className="text-lg font-black text-amber-300">
                ⚠️ {data.protect.disease_predicted || 'Foliage Condition'}
              </div>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {data.protect.advice}
              </p>
            </div>

            {/* Weather spray window alert */}
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                {lang === 'en' ? 'Weather & Spray Window' : 'मौसम व छिड़काव उपयुक्तता'}
              </span>
              <p className="text-xs text-amber-300/90 font-medium">
                🌦️ {data.protect.weather_window}
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Reason: <span className="font-mono text-slate-300">{data.protect.reason_key}</span></span>
            <span className="font-mono text-amber-400 font-semibold">{Math.round(data.protect.confidence * 100)}% Conf.</span>
          </div>
        </div>

        {/* Pillar 3: FEED (मृदा पोषण / खाद) */}
        <div className="glass-panel p-6 rounded-2xl border-t-4 border-t-emerald-400 flex flex-col justify-between space-y-4 glow-emerald">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-1.5">
                <span>🌱</span>
                <span>{lang === 'en' ? 'Soil Health & Nutrition' : 'मृदा स्वास्थ्य व पोषण'}</span>
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-bold">
                {data.nourish.status}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20">
              <div className="text-lg font-black text-emerald-300">
                🧪 {data.nourish.advice}
              </div>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {lang === 'en'
                  ? 'No guesswork chemical dosing. Real soil ratings retrieved from Soil Health Card portal.'
                  : 'बिना अनुमान के सटीक सलाह। मृदा स्वास्थ्य कार्ड पोर्टल से प्राप्त वास्तविक रेटिंग।'}
              </p>
            </div>

            {/* Soil Health Ratings from Parquet API */}
            {data.nourish.soil_context && (
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 text-xs">
                <div className="flex justify-between text-slate-400 text-[11px]">
                  <span>SHC Level: <strong className="text-white">{data.nourish.soil_context.level_used}</strong></span>
                  <span>Year: <strong className="text-white">{data.nourish.soil_context.year_used}</strong></span>
                </div>
                <div className="grid grid-cols-3 gap-1.5 text-center font-mono">
                  {Object.entries(data.nourish.soil_context.dominant_ratings).map(([nut, val]) => (
                    <div key={nut} className="p-1 rounded bg-slate-800/80 border border-slate-700/60">
                      <div className="text-[10px] text-slate-400">{nut}</div>
                      <div className={`font-bold text-[11px] ${
                        val.toLowerCase().includes('low') || val.toLowerCase().includes('कम')
                          ? 'text-red-400'
                          : val.toLowerCase().includes('high') || val.toLowerCase().includes('अधिक')
                          ? 'text-cyan-400'
                          : 'text-amber-400'
                      }`}>
                        {val}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Reason: <span className="font-mono text-slate-300">{data.nourish.reason_key}</span></span>
            <span className="font-mono text-emerald-400 font-semibold">{Math.round(data.nourish.confidence * 100)}% Conf.</span>
          </div>
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-400 flex items-center space-x-3">
        <span className="text-lg">🛡️</span>
        <p>
          <strong className="text-slate-200">Agronomic Safety Guarantee: </strong>
          {lang === 'en'
            ? 'Jal-Saathi never outputs proprietary brand names or unverified chemical doses. All protect recommendations require weather-window label checks, and fertilizer guidance confirms with your local Krishi Vigyan Kendra (KVK).'
            : 'जल-साथी कभी भी किसी कंपनी के उत्पाद या बिना सत्यापन की खुराक नहीं बताता। दवा प्रयोग से पहले मौसम व लेबल जांचें, और खाद की मात्रा के लिए नजदीकी KVK से पुष्टि करें।'}
        </p>
      </div>
    </div>
  );
};
