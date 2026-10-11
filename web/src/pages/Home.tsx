import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../i18n';
import { useAuth } from '../lib/auth-context';
import { backend, Field } from '../lib/backend';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Skeleton } from '../components/ui/Skeleton';
import { Sprout, Droplets, Calendar, Plus, MapPin, Sparkles } from 'lucide-react';

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [fields, setFields] = useState<Field[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    backend.farms
      .getFields()
      .then((data) => {
        if (mounted) {
          setFields(data);
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

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto w-full">
      {/* Top Banner / Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#26362F]">
            {t('home.greeting')}, {user?.name || ''}
          </h1>
          <p className="text-sm sm:text-base text-[#5F6F68] mt-1">
            {user?.id === 'demo_farmer'
              ? t('home.demo_field_notice')
              : 'Keep track of your crop growth, soil health, and weekly irrigation.'}
          </p>
        </div>

        <Button
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => navigate('/onboarding')}
        >
          {t('home.start_new_crop')}
        </Button>
      </div>

      {/* Field Cards Section */}
      <div>
        <h2 className="text-xl font-bold text-[#26362F] mb-4">
          {t('home.overview_title')}
        </h2>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Skeleton className="h-64 rounded-3xl" />
            <Skeleton className="h-64 rounded-3xl" />
          </div>
        ) : fields.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {fields.map((field) => (
              <Card
                key={field.id}
                elevated
                interactive
                onClick={() => navigate(`/dashboard/${field.id}`)}
                className="flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-xl font-bold text-[#26362F]">{field.name}</h3>
                        {field.isDemo && (
                          <Chip label={t('app.demo_badge')} variant="leaf" size="sm" />
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-[#5F6F68] mt-1">
                        <MapPin className="w-3.5 h-3.5" />
                        <span>{field.district}, Haryana</span>
                        <span>•</span>
                        <span>{field.area} {field.areaUnit}</span>
                      </div>
                    </div>

                    <div className="w-12 h-12 rounded-2xl bg-[#E1EFE4] text-[#1E3A28] flex items-center justify-center shrink-0">
                      <Sprout className="w-6 h-6 stroke-[2.2]" />
                    </div>
                  </div>

                  {/* Crop & Stage Info */}
                  <div className="p-4 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-2.5 my-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-[#5F6F68]">{t('home.stage')}</span>
                      <span className="font-bold text-[#26362F]">{field.stage}</span>
                    </div>

                    <div className="w-full bg-[#26362F]/10 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-[#6B9E7A] h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(100, Math.round((field.currentWeek / field.totalWeeks) * 100))}%`,
                        }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-xs text-[#5F6F68]">
                      <span>Week {field.currentWeek} of {field.totalWeeks}</span>
                      <span>Day {field.currentWeek * 7} of {field.totalWeeks * 7}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-[#26362F]/10 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-[#1E3A28]">
                    <Droplets className="w-4 h-4 text-[#6B9E7A]" />
                    <span>{t('home.status_optimal')}</span>
                  </div>

                  <span className="text-xs font-bold text-[#375941] underline underline-offset-2">
                    {t('home.view_season')} →
                  </span>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          /* Empty state for newly signed up user */
          <Card className="text-center py-12 flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-[#BFE0C8]/40 flex items-center justify-center text-[#2F533B] mb-4">
              <Sparkles className="w-7 h-7" />
            </div>
            <h3 className="text-xl font-bold text-[#26362F] mb-2">No fields added yet</h3>
            <p className="text-sm text-[#5F6F68] max-w-sm mb-6 leading-relaxed">
              Start by registering your wheat or paddy crop to receive calibrated irrigation and soil guidance.
            </p>
            <Button
              variant="primary"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => navigate('/onboarding')}
            >
              {t('home.start_new_crop')}
            </Button>
          </Card>
        )}
      </div>

      {/* Advisory Context Card */}
      <div className="p-6 rounded-3xl bg-white/70 border border-[#26362F]/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#EBCB8B]/40 text-[#473612] flex items-center justify-center shrink-0">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-[#26362F]">Weekly Field Check-ins</h4>
            <p className="text-xs text-[#5F6F68] mt-0.5">
              Check-ins update weekly to assess weather windows, plant condition, and irrigation timing.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
