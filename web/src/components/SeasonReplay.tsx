import React, { useState, useEffect, useRef } from 'react';
import { Language } from './Navbar';

interface DayStrategyData {
  depletion_mm: number;
  action_mm: number;
  cumulative_water: number;
  stress: boolean;
}

interface DayRecord {
  day: number;
  date: string;
  stage: string;
  rain_mm: number;
  etc: number;
  ppo: DayStrategyData;
  threshold: DayStrategyData;
  fixed_interval: DayStrategyData;
}

interface StrategySummary {
  total_water_mm: number;
  irrigations: number;
  stress_days: number;
  water_saved_vs_fixed_pct: number;
  water_saved_vs_thresh_pct?: number;
}

interface SeasonData {
  district: string;
  crop: string;
  sowing_date: string;
  total_days: number;
  taw_mm: number;
  raw_mm: number;
  summary: {
    ppo: StrategySummary;
    threshold: StrategySummary;
    fixed_interval: StrategySummary;
  };
  days: DayRecord[];
}

interface SeasonReplayProps {
  lang: Language;
}

export const SeasonReplay: React.FC<SeasonReplayProps> = ({ lang }) => {
  const [seasonData, setSeasonData] = useState<SeasonData | null>(null);
  const [currentDay, setCurrentDay] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [selectedStrategy, setSelectedStrategy] = useState<'ppo' | 'threshold' | 'fixed_interval'>('ppo');
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    fetch('/replay/wheat_Karnal.json')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: SeasonData) => {
        setSeasonData(data);
      })
      .catch((err) => {
        console.error('Failed to load replay data:', err);
        setError('Could not load season replay data.');
      });
  }, []);

  useEffect(() => {
    if (isPlaying) {
      const interval = 250 / playbackSpeed;
      timerRef.current = window.setInterval(() => {
        setCurrentDay((prev) => {
          if (!seasonData || prev >= seasonData.total_days - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, interval);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, seasonData]);

  if (error) {
    return (
      <div className="p-8 text-center text-red-400">
        <p>{error}</p>
      </div>
    );
  }

  if (!seasonData) {
    return (
      <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p>{lang === 'en' ? 'Loading season simulation...' : 'सीजन सिमुलेशन लोड हो रहा है...'}</p>
      </div>
    );
  }

  const dayInfo = seasonData.days[currentDay] || seasonData.days[0];
  const stratInfo = dayInfo[selectedStrategy];
  const taw = seasonData.taw_mm;
  const raw = seasonData.raw_mm;
  const currentDepletion = stratInfo.depletion_mm;
  const depletionPct = Math.min(100, Math.max(0, (currentDepletion / taw) * 100));
  const rawPct = (raw / taw) * 100;

  // Cumulative stats up to current day
  const cumWater = stratInfo.cumulative_water;
  const cumIrrigations = seasonData.days
    .slice(0, currentDay + 1)
    .filter((d) => d[selectedStrategy].action_mm > 0).length;
  const cumStressDays = seasonData.days
    .slice(0, currentDay + 1)
    .filter((d) => d[selectedStrategy].stress).length;

  return (
    <div className="space-y-6">
      {/* Permanent Required Disclaimer Label */}
      <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs sm:text-sm">
        <div className="flex items-center space-x-2">
          <span className="text-base">⚠️</span>
          <span className="font-semibold tracking-wide">
            {lang === 'en'
              ? 'Simulated on historical weather (held-out season). Not field-validated.'
              : 'ऐतिहासिक मौसम (परीक्षण वर्ष) पर सिमुलेट किया गया। वास्तविक खेत-सत्यापित नहीं।'}
          </span>
        </div>
        <span className="text-[11px] text-amber-400/80 hidden md:inline">
          Karnal 2023-24 Winter Wheat (FAO-56 Dual Balance)
        </span>
      </div>

      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs text-emerald-400 font-semibold uppercase tracking-wider mb-1">
            <span>🌾 {seasonData.crop}</span>
            <span>•</span>
            <span>📍 {seasonData.district}, Haryana</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {lang === 'en' ? 'Interactive 120-Day Season Replay' : '120-दिवसीय इंटरएक्टिव सीजन रीप्ले'}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {lang === 'en'
              ? 'Watch Reinforcement Learning optimize water applications versus traditional calendar and threshold irrigation.'
              : 'देखें कैसे रीइन्फोर्समेंट लर्निंग पारंपरिक समय-सारणी के मुकाबले जल की बचत करती है।'}
          </p>
        </div>

        {/* Strategy Switcher */}
        <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 self-start md:self-auto">
          <button
            onClick={() => setSelectedStrategy('ppo')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              selectedStrategy === 'ppo'
                ? 'bg-emerald-500 text-slate-950 shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            ⭐ RL Policy (PPO)
          </button>
          <button
            onClick={() => setSelectedStrategy('threshold')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              selectedStrategy === 'threshold'
                ? 'bg-slate-700 text-slate-100 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Threshold (RAW)
          </button>
          <button
            onClick={() => setSelectedStrategy('fixed_interval')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              selectedStrategy === 'fixed_interval'
                ? 'bg-slate-700 text-slate-100 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Fixed (20-Day)
          </button>
        </div>
      </div>

      {/* Main Player & Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Replay Gauge & Timeline */}
        <div className="lg:col-span-2 glass-panel p-5 sm:p-6 rounded-2xl space-y-6">
          {/* Day & Stage Header */}
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div>
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                {lang === 'en' ? 'Current Day of Season' : 'सीजन का दिन'}
              </span>
              <div className="flex items-baseline space-x-2 mt-0.5">
                <span className="text-3xl font-black text-white font-mono">Day {dayInfo.day}</span>
                <span className="text-xs text-slate-400">({dayInfo.date})</span>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                {lang === 'en' ? 'Growth Stage' : 'फसल अवस्था'}
              </span>
              <div className="text-sm sm:text-base font-bold text-emerald-400 mt-0.5">
                {dayInfo.stage}
              </div>
            </div>
          </div>

          {/* Root-Zone Soil Depletion Meter */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-medium text-slate-300">
              <span>{lang === 'en' ? 'Root-Zone Moisture Depletion' : 'जड़-क्षेत्र नमी कमी'}</span>
              <span className="font-mono text-emerald-400 font-bold">
                {currentDepletion.toFixed(1)} mm / {taw} mm ({depletionPct.toFixed(0)}%)
              </span>
            </div>

            {/* Visual Depletion Bar */}
            <div className="relative h-7 w-full bg-slate-900 rounded-xl overflow-hidden border border-slate-800 shadow-inner">
              {/* Field Capacity (0mm) Indicator */}
              <div
                className="h-full bg-gradient-to-r from-cyan-500 via-emerald-500 to-amber-500 transition-all duration-300 ease-out"
                style={{ width: `${depletionPct}%` }}
              ></div>

              {/* RAW Marker (Readily Available Water Boundary) */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-red-400 z-10"
                style={{ left: `${rawPct}%` }}
              >
                <span className="absolute -top-5 -left-6 text-[9px] font-mono text-red-400 font-bold uppercase tracking-wider">
                  RAW (37.5mm)
                </span>
              </div>
            </div>

            <div className="flex justify-between text-[11px] text-slate-500 font-mono">
              <span>0 mm (Field Capacity)</span>
              <span className="text-amber-400/80">37.5 mm (Stress Threshold)</span>
              <span>75 mm (Wilting Point)</span>
            </div>
          </div>

          {/* Daily Weather & Action Event Cards */}
          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-center">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider">
                {lang === 'en' ? 'Crop ETc' : 'वाष्पोत्सर्जन'}
              </span>
              <div className="text-lg font-bold text-slate-100 font-mono mt-1">
                {dayInfo.etc.toFixed(1)} <span className="text-xs text-slate-500">mm/day</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-center">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider">
                {lang === 'en' ? 'Rainfall' : 'वर्षा'}
              </span>
              <div className="text-lg font-bold text-cyan-400 font-mono mt-1">
                {dayInfo.rain_mm > 0 ? `+${dayInfo.rain_mm.toFixed(1)}` : '0.0'}{' '}
                <span className="text-xs text-slate-500">mm</span>
              </div>
            </div>
            <div className={`p-3 rounded-xl border text-center transition-all ${
              stratInfo.action_mm > 0
                ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300 glow-emerald'
                : 'bg-slate-900/70 border-slate-800/80 text-slate-400'
            }`}>
              <span className="text-[11px] uppercase tracking-wider">
                {lang === 'en' ? 'Today Action' : 'सिंचाई आदेश'}
              </span>
              <div className="text-lg font-extrabold font-mono mt-1 text-slate-100">
                {stratInfo.action_mm > 0 ? (
                  <span className="text-emerald-400">💧 +{stratInfo.action_mm} mm</span>
                ) : (
                  <span className="text-slate-500">Skip (0 mm)</span>
                )}
              </div>
            </div>
          </div>

          {/* Playback Controls & Slider */}
          <div className="space-y-4 pt-2">
            {/* Slider */}
            <div className="space-y-1">
              <input
                type="range"
                min={0}
                max={seasonData.total_days - 1}
                value={currentDay}
                onChange={(e) => setCurrentDay(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>Nov 15 (Sowing)</span>
                <span>Jan 15 (Mid-Season)</span>
                <span>Mar 15 (Harvest)</span>
              </div>
            </div>

            {/* Buttons Bar */}
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 shadow-md ${
                    isPlaying
                      ? 'bg-amber-500 hover:bg-amber-400 text-slate-950'
                      : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950'
                  }`}
                >
                  <span>{isPlaying ? '⏸️ Pause' : '▶️ Play Replay'}</span>
                </button>
                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentDay(0);
                  }}
                  className="px-3 py-2 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  ⏮️ Reset
                </button>
              </div>

              {/* Speed Buttons */}
              <div className="flex items-center space-x-1 p-1 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-500 px-1 font-semibold uppercase">Speed:</span>
                {[1, 2, 5].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setPlaybackSpeed(spd)}
                    className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                      playbackSpeed === spd
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Live Cumulative KPI Cards & Comparison */}
        <div className="space-y-4">
          {/* Live Cumulative Water Counter */}
          <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-cyan-400 space-y-2">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
              {lang === 'en' ? 'Cumulative Water Applied' : 'कुल सिंचित जल'}
            </span>
            <div className="text-3xl sm:text-4xl font-black text-white font-mono tracking-tight">
              {cumWater.toFixed(0)}{' '}
              <span className="text-base text-slate-400 font-sans font-medium">mm</span>
            </div>
            {selectedStrategy === 'ppo' && (
              <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <span>💧</span>
                <span>Saves 46.7% vs Fixed (140 mm saved)</span>
              </div>
            )}
          </div>

          {/* Cumulative Irrigations Counter */}
          <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-emerald-400 space-y-1">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
              {lang === 'en' ? 'Irrigation Events Run' : 'सिंचाई चक्र'}
            </span>
            <div className="text-3xl font-black text-white font-mono">
              {cumIrrigations}{' '}
              <span className="text-sm text-slate-400 font-normal">
                {lang === 'en' ? 'applications' : 'बार'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {selectedStrategy === 'ppo' ? 'Optimized pre-monsoon timing' : 'Preset scheduled events'}
            </p>
          </div>

          {/* Cumulative Stress Days Counter */}
          <div className={`glass-panel p-5 rounded-2xl border-l-4 space-y-1 transition-all ${
            cumStressDays > 0 ? 'border-l-red-500 bg-red-950/20' : 'border-l-slate-700'
          }`}>
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
              {lang === 'en' ? 'Water Stress Days' : 'जल तनाव दिवस'}
            </span>
            <div className={`text-3xl font-black font-mono ${
              cumStressDays > 0 ? 'text-red-400' : 'text-slate-100'
            }`}>
              {cumStressDays}{' '}
              <span className="text-sm font-normal text-slate-400">
                {lang === 'en' ? 'days' : 'दिन'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {cumStressDays === 0
                ? '✅ Zero moisture deficit penalty'
                : '⚠️ Foliage stress detected above RAW'}
            </p>
          </div>

          {/* Full Season Comparison Table */}
          <div className="glass-panel p-4 rounded-2xl space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              {lang === 'en' ? '120-Day Season Total Comparison' : '120-दिवसीय पूर्ण तुलना'}
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <span className="font-bold text-emerald-400">⭐ RL PPO</span>
                <span className="font-mono font-bold text-white">160 mm (4 irrs, 0 stress)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-300">Threshold</span>
                <span className="font-mono text-slate-400">240 mm (6 irrs, 0 stress)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-300">Fixed Interval</span>
                <span className="font-mono text-slate-400">300 mm (6 irrs, 3 stress)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
