import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Skeleton } from '../components/ui/Skeleton';
import {
  Play,
  Pause,
  RotateCcw,
  BarChart2,
} from 'lucide-react';

interface StrategyDay {
  depletion_mm: number;
  action_mm: number;
  cumulative_water: number;
  stress: boolean;
}

interface ReplayDay {
  day: number;
  date: string;
  stage: string;
  rain_mm: number;
  etc: number;
  ppo: StrategyDay;
  threshold: StrategyDay;
  fixed_interval: StrategyDay;
}

interface ReplaySummaryItem {
  total_water_mm: number;
  irrigations: number;
  stress_days: number;
  water_saved_vs_fixed_pct?: number;
  water_saved_vs_thresh_pct?: number;
}

interface ReplayData {
  district: string;
  crop: string;
  sowing_date: string;
  total_days: number;
  taw_mm: number;
  raw_mm: number;
  summary: {
    ppo: ReplaySummaryItem;
    threshold: ReplaySummaryItem;
    fixed_interval: ReplaySummaryItem;
  };
  days: ReplayDay[];
}

export const Impact: React.FC = () => {
  const [data, setData] = useState<ReplayData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentDayIndex, setCurrentDayIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeStrategy, setActiveStrategy] = useState<'ppo' | 'threshold' | 'fixed_interval'>('ppo');

  useEffect(() => {
    document.title = 'Jal-Saathi - Season Replay & Impact';
  }, []);

  useEffect(() => {
    let mounted = true;
    fetch('./data/replay/wheat_Karnal.json')
      .then((res) => {
        if (!res.ok) throw new Error('Replay not found');
        return res.json();
      })
      .then((d) => {
        if (mounted) {
          setData(d);
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Playback timer
  useEffect(() => {
    let interval: any = null;
    if (isPlaying && data) {
      interval = setInterval(() => {
        setCurrentDayIndex((prev) => {
          if (prev >= data.days.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 120);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, data]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 max-w-5xl mx-auto py-8">
        <Skeleton className="h-28 rounded-3xl" />
        <Skeleton className="h-80 rounded-3xl" />
      </div>
    );
  }

  if (!data || !data.days || data.days.length === 0) {
    return null; // As per prompt rule: if missing, remove page
  }

  const currentDay = data.days[currentDayIndex] || data.days[0];
  const strategyData = currentDay[activeStrategy];

  const taw = data.taw_mm || 75.0;
  const raw = data.raw_mm || 37.5;
  const currentDepletion = strategyData.depletion_mm;

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto w-full py-4 sm:py-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E1EFE4] text-[#1E3A28] border border-[#6B9E7A]/25 text-xs font-bold mb-3">
          <BarChart2 className="w-4 h-4" />
          <span>Season Replay</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#26362F] tracking-tight">
          Historical Season Impact Replay
        </h1>
        <p className="text-sm sm:text-base text-[#5F6F68] mt-1.5">
          Evaluating irrigation strategies on historical weather in Karnal ({data.crop}, 120 days).
        </p>
      </div>

      {/* Main Interactive Replay Dashboard */}
      <Card elevated className="flex flex-col gap-6">
        {/* Playback Controls & Timeline Slider */}
        <div className="flex flex-col gap-4 border-b border-[#26362F]/10 pb-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={isPlaying ? 'secondary' : 'primary'}
                onClick={() => setIsPlaying(!isPlaying)}
                leftIcon={isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              >
                {isPlaying ? 'Pause' : 'Play Replay'}
              </Button>

              <button
                type="button"
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentDayIndex(0);
                }}
                className="p-2.5 rounded-full text-[#5F6F68] hover:bg-[#26362F]/5 transition-colors cursor-pointer"
                aria-label="Reset replay"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>

            {/* Strategy Pill Selector */}
            <div className="flex items-center gap-1.5 p-1 rounded-full bg-[#26362F]/8">
              {[
                { id: 'ppo', label: 'RL Policy' },
                { id: 'threshold', label: 'Threshold Rule' },
                { id: 'fixed_interval', label: 'Fixed Interval' },
              ].map((strat) => (
                <button
                  key={strat.id}
                  type="button"
                  onClick={() => setActiveStrategy(strat.id as any)}
                  className={`px-3 py-1.5 text-xs font-bold rounded-full transition-all cursor-pointer ${
                    activeStrategy === strat.id
                      ? 'bg-white text-[#26362F] shadow-xs'
                      : 'text-[#5F6F68] hover:text-[#26362F]'
                  }`}
                >
                  {strat.label}
                </button>
              ))}
            </div>

            {/* Current Day Info */}
            <div className="text-right">
              <span className="text-sm font-extrabold text-[#26362F]">
                Day {currentDay.day} of {data.total_days}
              </span>
              <span className="text-xs text-[#5F6F68] block">
                {currentDay.date} • {currentDay.stage}
              </span>
            </div>
          </div>

          {/* Scrub Slider */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-[#5F6F68]">Day 0</span>
            <input
              type="range"
              min="0"
              max={data.days.length - 1}
              value={currentDayIndex}
              onChange={(e) => {
                setIsPlaying(false);
                setCurrentDayIndex(parseInt(e.target.value));
              }}
              className="w-full accent-[#6B9E7A] cursor-pointer"
            />
            <span className="text-xs font-semibold text-[#5F6F68]">Day {data.days.length - 1}</span>
          </div>
        </div>

        {/* Moisture & Daily Physics Display */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Soil Moisture Depletion Gauge Bar */}
          <div className="md:col-span-6 flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#26362F]">Root-zone Depletion</span>
              <span className="font-semibold text-[#5F6F68]">
                {currentDepletion.toFixed(1)} mm / {taw} mm TAW
              </span>
            </div>

            {/* Horizontal Bar with RAW Threshold Line */}
            <div className="relative w-full h-7 rounded-full bg-[#26362F]/10 overflow-hidden">
              {/* RAW Mark Indicator (37.5 mm) */}
              <div
                className="absolute top-0 bottom-0 w-[2px] bg-[#C86047] z-10"
                style={{ left: `${(raw / taw) * 100}%` }}
                title="RAW threshold line"
              />

              {/* Depletion Level */}
              <div
                className={`h-full transition-all duration-150 ${
                  currentDepletion > raw ? 'bg-[#EBA896]' : 'bg-[#6B9E7A]'
                }`}
                style={{ width: `${Math.min(100, (currentDepletion / taw) * 100)}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-[#5F6F68]">
              <span>0 mm (Field Capacity)</span>
              <span className="text-[#C86047] font-semibold">RAW Line ({raw} mm)</span>
              <span>{taw} mm (Wilting Point)</span>
            </div>
          </div>

          {/* Daily Water Inflow / Outflow Tiles */}
          <div className="md:col-span-6 grid grid-cols-3 gap-3 text-center">
            <div className="p-3 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8">
              <span className="text-[11px] text-[#5F6F68] block">Daily ETc</span>
              <strong className="text-base text-[#26362F]">{currentDay.etc.toFixed(2)} mm</strong>
            </div>

            <div className="p-3 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8">
              <span className="text-[11px] text-[#5F6F68] block">Rainfall</span>
              <strong className="text-base text-[#13384A]">{currentDay.rain_mm.toFixed(1)} mm</strong>
            </div>

            <div className="p-3 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8">
              <span className="text-[11px] text-[#5F6F68] block">Irrigation</span>
              <strong className="text-base text-[#1E3A28]">
                {strategyData.action_mm > 0 ? `${strategyData.action_mm} mm` : '0 mm'}
              </strong>
            </div>
          </div>
        </div>

        {/* Mandatory Simulation Caption */}
        <p className="text-xs text-center text-[#5F6F68] italic pt-4 border-t border-[#26362F]/10">
          Replay of the 2022-23 season on historical weather. Simulated irrigation.
        </p>
      </Card>

      {/* KPI Comparison Tiles */}
      <div>
        <h3 className="font-extrabold text-xl text-[#26362F] mb-4">
          Strategy Comparison (Full Season)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* PPO RL Policy */}
          <Card
            className={`p-6 border transition-all ${
              activeStrategy === 'ppo'
                ? 'bg-[#E1EFE4] border-[#6B9E7A]/50 ring-2 ring-[#6B9E7A]/30'
                : 'bg-white/80 border-[#26362F]/10'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-extrabold text-base text-[#1E3A28]">RL Policy (PPO)</h4>
              <Chip label="Trained Policy" variant="leaf" size="sm" />
            </div>

            <div className="flex flex-col gap-2.5 text-xs text-[#26362F]">
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Total Water:</span>
                <strong>{data.summary.ppo.total_water_mm.toFixed(1)} mm</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Irrigations:</span>
                <strong>{data.summary.ppo.irrigations} applications</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Stress Days:</span>
                <strong>{data.summary.ppo.stress_days.toFixed(1)} days</strong>
              </div>
            </div>
          </Card>

          {/* Threshold Rule */}
          <Card
            className={`p-6 border transition-all ${
              activeStrategy === 'threshold'
                ? 'bg-[#FAF0D7] border-[#EBCB8B]/60 ring-2 ring-[#EBCB8B]/40'
                : 'bg-white/80 border-[#26362F]/10'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-extrabold text-base text-[#473612]">Threshold Rule</h4>
              <Chip label="Agronomic Baseline" variant="sand" size="sm" />
            </div>

            <div className="flex flex-col gap-2.5 text-xs text-[#26362F]">
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Total Water:</span>
                <strong>{data.summary.threshold.total_water_mm.toFixed(1)} mm</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Irrigations:</span>
                <strong>{data.summary.threshold.irrigations} applications</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Stress Days:</span>
                <strong>{data.summary.threshold.stress_days.toFixed(1)} days</strong>
              </div>
            </div>
          </Card>

          {/* Fixed Interval */}
          <Card
            className={`p-6 border transition-all ${
              activeStrategy === 'fixed_interval'
                ? 'bg-[#FCE8E2] border-[#EBA896]/60 ring-2 ring-[#EBA896]/40'
                : 'bg-white/80 border-[#26362F]/10'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-extrabold text-base text-[#5C1D13]">Fixed Interval</h4>
              <Chip label="Traditional Practice" variant="alert" size="sm" />
            </div>

            <div className="flex flex-col gap-2.5 text-xs text-[#26362F]">
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Total Water:</span>
                <strong>{data.summary.fixed_interval.total_water_mm.toFixed(1)} mm</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Irrigations:</span>
                <strong>{data.summary.fixed_interval.irrigations} applications</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5F6F68]">Stress Days:</span>
                <strong>{data.summary.fixed_interval.stress_days.toFixed(1)} days</strong>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
