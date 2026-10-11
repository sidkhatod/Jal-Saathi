import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from '../i18n';
import { backend, Field, PlanData } from '../lib/backend';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Skeleton } from '../components/ui/Skeleton';
import {
  Droplets,
  Sprout,
  ArrowRight,
  Clock,
  MapPin,
  CheckCircle2,
  FileText,
  AlertCircle,
} from 'lucide-react';

interface CropConfig {
  stages: {
    stage_id: string;
    name_en: string;
    name_hi: string;
    days: number;
  }[];
  total_days: number;
}

export const SeasonDashboard: React.FC = () => {
  const { fieldId } = useParams<{ fieldId: string }>();
  const { t, language } = useTranslation();
  const navigate = useNavigate();

  const [field, setField] = useState<Field | null>(null);
  const [currentPlan, setCurrentPlan] = useState<PlanData | null>(null);
  const [pastPlans, setPastPlans] = useState<PlanData[]>([]);
  const [cropsData, setCropsData] = useState<Record<string, CropConfig>>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    // Load crops config for stage timeline
    fetch('./data/crops.json')
      .then((r) => r.json())
      .then((d) => {
        if (mounted) setCropsData(d);
      })
      .catch(() => {});

    // Fetch field details
    const loadFieldAndPlans = async () => {
      try {
        const fields = await backend.farms.getFields();
        const target = fields.find((f) => f.id === fieldId) || fields[0] || null;
        if (!target) {
          if (mounted) setIsLoading(false);
          return;
        }

        if (mounted) setField(target);

        // Fetch current week plan
        const plan = await backend.plans.getPlan(target.id, target.currentWeek);
        if (mounted) setCurrentPlan(plan);

        // Fetch past week plans for history
        const past: PlanData[] = [];
        for (let w = target.currentWeek - 1; w >= 1; w--) {
          const pastP = await backend.plans.getPlan(target.id, w);
          if (pastP) past.push(pastP);
        }
        if (mounted) setPastPlans(past);
      } catch {
        // error handling
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    loadFieldAndPlans();

    return () => {
      mounted = false;
    };
  }, [fieldId]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 max-w-5xl mx-auto py-6">
        <Skeleton className="h-28 rounded-3xl" />
        <Skeleton className="h-64 rounded-3xl" />
        <Skeleton className="h-48 rounded-3xl" />
      </div>
    );
  }

  if (!field) {
    return (
      <Card className="text-center py-12 max-w-xl mx-auto">
        <AlertCircle className="w-10 h-10 text-[#5F6F68] mx-auto mb-3" />
        <h3 className="text-lg font-bold text-[#26362F]">Field not found</h3>
        <Button className="mt-4" onClick={() => navigate('/')}>
          Return Home
        </Button>
      </Card>
    );
  }

  const isCheckinDue = field.currentWeek === 6 || (field.isDemo && field.currentWeek >= 6);
  const cropConfig = cropsData[field.crop];
  const stages = cropConfig?.stages || [];

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto w-full py-4 sm:py-6">
      {/* Top Banner: Field Overview */}
      <Card elevated className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#26362F]">
              {field.name}
            </h1>
            {field.isDemo && (
              <Chip label={t('app.demo_badge')} variant="leaf" size="sm" />
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs sm:text-sm text-[#5F6F68] mt-2">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              {field.district}, Haryana
            </span>
            <span>•</span>
            <span className="capitalize font-semibold text-[#26362F]">{field.crop}</span>
            <span>•</span>
            <span>{field.area} {field.areaUnit}</span>
            <span>•</span>
            <span className="capitalize">{field.irrigationSource}</span>
          </div>
        </div>

        {/* Check-in Status Action */}
        <div className="flex flex-col sm:items-end gap-2">
          {isCheckinDue ? (
            <div className="flex flex-col sm:items-end gap-2">
              <Chip
                label={t('dashboard.checkin_due_badge')}
                variant="alert"
                size="md"
                icon={<Clock className="w-3.5 h-3.5" />}
              />
              <Button
                variant="primary"
                onClick={() => navigate(`/checkin/${field.id}`)}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                {t('dashboard.checkin_open_btn', { week: field.currentWeek })}
              </Button>
            </div>
          ) : (
            <div className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/10 flex items-center gap-2.5 text-xs text-[#5F6F68]">
              <Clock className="w-4 h-4 text-[#6B9E7A]" />
              <span>{t('dashboard.first_checkin_opens_in_7_days')}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Moisture Status Gauge & Summary Card */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left: Moisture Ring Gauge */}
        <Card elevated className="md:col-span-5 flex flex-col justify-between items-center text-center p-6 sm:p-8">
          <div className="w-full text-left">
            <h3 className="font-extrabold text-lg text-[#26362F] flex items-center gap-2">
              <Droplets className="w-5 h-5 text-[#6B9E7A]" />
              <span>{t('dashboard.water_status')}</span>
            </h3>
            <p className="text-xs text-[#5F6F68] mt-0.5">
              {t('dashboard.moisture_gauge_caption')}
            </p>
          </div>

          {/* Soft Circular Gauge */}
          <div className="relative my-6 w-44 h-44 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                cx="50"
                cy="50"
                r="40"
                className="stroke-[#26362F]/10"
                strokeWidth="10"
                fill="none"
              />
              {/* Active progress arc */}
              <circle
                cx="50"
                cy="50"
                r="40"
                className="stroke-[#6B9E7A] transition-all duration-700 ease-out"
                strokeWidth="10"
                strokeDasharray="251.2"
                strokeDashoffset={
                  currentPlan?.water?.action === 'irrigate' ? '75' : '150'
                }
                strokeLinecap="round"
                fill="none"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-2xl font-extrabold text-[#26362F]">
                {currentPlan?.water?.amount_mm ? `${currentPlan.water.amount_mm} mm` : 'Adequate'}
              </span>
              <span className="text-xs font-semibold text-[#5F6F68] capitalize">
                {currentPlan?.water?.action || 'Monitoring'}
              </span>
            </div>
          </div>

          <div className="w-full pt-4 border-t border-[#26362F]/10 text-xs text-[#5F6F68]">
            {currentPlan?.water?.advice || 'Root zone balance maintained within safe thresholds.'}
          </div>
        </Card>

        {/* Right: Stage Timeline */}
        <Card elevated className="md:col-span-7 flex flex-col justify-between p-6 sm:p-8">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-extrabold text-lg text-[#26362F] flex items-center gap-2">
                <Sprout className="w-5 h-5 text-[#6B9E7A]" />
                <span>{t('dashboard.stage_timeline')}</span>
              </h3>
              <span className="text-xs font-semibold text-[#5F6F68]">
                Week {field.currentWeek} of {field.totalWeeks}
              </span>
            </div>

            <div className="flex flex-col gap-3">
              {stages.length > 0 ? (
                stages.map((stg, idx) => {
                  const isCurrent = idx === 0 && field.currentWeek <= 6;
                  const isPast = false;

                  return (
                    <div
                      key={stg.stage_id}
                      className={`p-3.5 rounded-2xl border flex items-center justify-between text-xs transition-all ${
                        isCurrent
                          ? 'bg-[#E1EFE4] border-[#6B9E7A]/40 text-[#1E3A28] font-bold shadow-xs'
                          : isPast
                          ? 'bg-white/60 border-[#26362F]/8 text-[#5F6F68]'
                          : 'bg-white/90 border-[#26362F]/10 text-[#26362F]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px] ${
                            isCurrent
                              ? 'bg-[#6B9E7A] text-white'
                              : 'bg-[#26362F]/10 text-[#5F6F68]'
                          }`}
                        >
                          {idx + 1}
                        </div>
                        <span>
                          {language === 'hi' ? stg.name_hi : stg.name_en}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span>{stg.days} days</span>
                        {isCurrent && (
                          <Chip label={t('dashboard.stage_active')} variant="leaf" size="sm" />
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-4 text-xs text-[#5F6F68]">
                  Crop stage calendar loading...
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-[#26362F]/10 text-xs text-[#5F6F68] mt-4 flex items-center justify-between">
            <span>Sowing Date: {field.sowingDate}</span>
            <span>Harvest: ~140 days</span>
          </div>
        </Card>
      </div>

      {/* Past Plans History Section */}
      <div>
        <h3 className="font-extrabold text-xl text-[#26362F] mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-[#6B9E7A]" />
          <span>{t('dashboard.past_plans_title')}</span>
        </h3>

        {pastPlans.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {pastPlans.map((pastP) => (
              <Card key={pastP.week} className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-extrabold text-base text-[#26362F]">
                      Week {pastP.week} Advisory
                    </span>
                    <span className="text-xs text-[#5F6F68]">{pastP.as_of_date || pastP.asOfDate}</span>
                  </div>

                  {pastP.water && (
                    <div className="text-xs text-[#26362F] my-1 flex items-center gap-1.5">
                      <Droplets className="w-3.5 h-3.5 text-[#6B9E7A]" />
                      <span>{pastP.water.advice}</span>
                    </div>
                  )}

                  {pastP.leaves && (
                    <div className="text-xs text-[#5F6F68] mt-1 line-clamp-2">
                      {typeof pastP.leaves.symptoms === 'string'
                        ? pastP.leaves.symptoms
                        : pastP.leaves.symptoms?.join(', ')}
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-[#26362F]/10 mt-3 flex items-center justify-between text-xs">
                  <span className="text-[#1E3A28] font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#6B9E7A]" />
                    Verified
                  </span>
                  <span className="text-[#375941] font-bold">Recorded</span>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="text-center py-8 text-xs text-[#5F6F68]">
            {t('dashboard.no_past_plans')}
          </Card>
        )}
      </div>
    </div>
  );
};
