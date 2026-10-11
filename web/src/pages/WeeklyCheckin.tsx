import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from '../i18n';
import { backend, Field, PlanData } from '../lib/backend';
import { analyzePhotoQuality, QualityCheckResult } from '../lib/cv-quality';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Chip } from '../components/ui/Chip';
import { Stepper } from '../components/ui/Stepper';
import { Input } from '../components/ui/Input';
import { useToast } from '../components/ui/Toast';
import {
  Camera,
  CheckCircle2,
  Droplets,
  Sprout,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Info,
  Loader2,
  PhoneCall,
  Check,
  X,
} from 'lucide-react';

interface PhotoSlot {
  id: string;
  type: 'leaf' | 'soil' | 'flower';
  tip: string;
  file?: File;
  previewUrl?: string;
  result?: QualityCheckResult;
}

export const WeeklyCheckin: React.FC = () => {
  const { fieldId } = useParams<{ fieldId: string }>();
  const { t } = useTranslation();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState(0);
  const [field, setField] = useState<Field | null>(null);
  const [plan, setPlan] = useState<PlanData | null>(null);

  // Step 1: Photos state (4 leaf, 2 soil, 2 flower/ear)
  const [photoSlots, setPhotoSlots] = useState<PhotoSlot[]>([
    { id: 'leaf_1', type: 'leaf', tip: 'Leaf blade (upper side in natural light)' },
    { id: 'leaf_2', type: 'leaf', tip: 'Leaf blade (lower canopy or underside)' },
    { id: 'leaf_3', type: 'leaf', tip: 'Leaf tip & margins' },
    { id: 'leaf_4', type: 'leaf', tip: 'Whole plant cluster' },
    { id: 'soil_1', type: 'soil', tip: 'Topsoil crumb & surface moisture' },
    { id: 'soil_2', type: 'soil', tip: 'Soil near root crown' },
    { id: 'flower_1', type: 'flower', tip: 'Tiller node or emergence' },
    { id: 'flower_2', type: 'flower', tip: 'Ear head or panicle (if present)' },
  ]);

  // Step 2: Farm observation state
  const [irrigated, setIrrigated] = useState<'no' | 'yes'>('no');
  const [irrigationDetails, setIrrigationDetails] = useState('');
  const [rainfallNoticed, setRainfallNoticed] = useState<boolean>(false);
  const [notes, setNotes] = useState('');

  // Step 3: Plan loading & user action state
  const [isPreparingPlan, setIsPreparingPlan] = useState(false);
  const [selectedAction, setSelectedAction] = useState<'done' | 'not_yet' | 'kvk' | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let mounted = true;
    backend.farms
      .getFields()
      .then((fields) => {
        const target = fields.find((f) => f.id === fieldId) || fields[0] || null;
        if (mounted && target) {
          setField(target);
          backend.plans.getPlan(target.id, target.currentWeek).then((p) => {
            if (mounted) setPlan(p);
          });
        }
      })
      .catch(() => {});

    return () => {
      mounted = false;
    };
  }, [fieldId]);

  // Handle Photo Upload & Client-Side Quality Check
  const handlePhotoUpload = async (slotId: string, file: File) => {
    const previewUrl = URL.createObjectURL(file);
    const result = await analyzePhotoQuality(file);

    setPhotoSlots((prev) =>
      prev.map((slot) =>
        slot.id === slotId
          ? {
              ...slot,
              file,
              previewUrl,
              result,
            }
          : slot
      )
    );
  };

  const handleLoadDemoPhotos = async () => {
    const urls = [
      { id: 'leaf_1', url: './test_assets/blurry_dark.jpg' },
      { id: 'leaf_2', url: './test_assets/good_photo_1.jpg' },
      { id: 'leaf_3', url: './test_assets/good_photo_2.jpg' },
      { id: 'leaf_4', url: './test_assets/good_photo_3.jpg' },
    ];

    const updated = [...photoSlots];
    for (const item of urls) {
      try {
        const res = await fetch(item.url);
        const blob = await res.blob();
        const result = await analyzePhotoQuality(blob);
        const idx = updated.findIndex((s) => s.id === item.id);
        if (idx !== -1) {
          updated[idx] = {
            ...updated[idx],
            previewUrl: item.url,
            result,
          };
        }
      } catch {
        // ignore
      }
    }
    setPhotoSlots(updated);
  };

  const goodPhotosCount = photoSlots.filter((s) => s.result && s.result.isGood).length;
  const canProceedFromPhotos = goodPhotosCount >= 3;

  // Transition from Step 1 to Step 2
  const handleGoToObservations = () => {
    if (!canProceedFromPhotos) return;
    setCurrentStep(1);
  };

  // Transition from Step 2 to Step 3 (neutral short preparing state)
  const handleGoToPlan = () => {
    setIsPreparingPlan(true);
    setCurrentStep(2);
    setTimeout(() => {
      setIsPreparingPlan(false);
    }, 600); // Under 1 second neutral state
  };

  // Final Action Submission
  const handleCompleteCheckin = async () => {
    if (!field) return;
    setIsSaving(true);

    try {
      await backend.checkins.submitCheckin({
        id: `checkin-${Date.now()}`,
        fieldId: field.id,
        week: field.currentWeek,
        date: new Date().toISOString(),
        irrigated,
        irrigationDetails: irrigated === 'yes' ? irrigationDetails : undefined,
        rainfallNoticed,
        notes: notes.trim() || undefined,
        goodPhotoCount: goodPhotosCount,
      });

      showToast(t('checkin.plan_saved_toast'), 'success');
      navigate('/');
    } catch {
      setIsSaving(false);
    }
  };

  const stepsList = [
    { id: 0, label: t('checkin.step_photos') },
    { id: 1, label: t('checkin.step_field') },
    { id: 2, label: t('checkin.step_plan') },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto py-4 sm:py-6 flex flex-col gap-6">
      {/* Header & Stepper */}
      <div className="flex flex-col gap-4 text-center">
        <div>
          <span className="text-xs font-bold text-[#6B9E7A] tracking-wider uppercase">
            {t('app.name')}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#26362F] mt-1">
            {t('checkin.title')}
          </h1>
          <p className="text-sm text-[#5F6F68] mt-1">
            {t('checkin.subtitle', {
              week: field?.currentWeek || 6,
              name: field?.name || 'Field',
            })}
          </p>
        </div>

        <Stepper steps={stepsList} currentStepIndex={currentStep} className="max-w-xl mx-auto" />
      </div>

      <Card elevated className="w-full">
        {/* ================= STEP 0: PHOTOS ================= */}
        {currentStep === 0 && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#26362F]/10 pb-4">
              <div>
                <h2 className="text-xl font-bold text-[#26362F]">
                  Upload Field Photos
                </h2>
                <p className="text-xs sm:text-sm text-[#5F6F68] mt-1">
                  {t('checkin.photo_instruction')}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleLoadDemoPhotos}
                  className="text-xs font-semibold text-[#375941] underline underline-offset-4 hover:text-[#1E3A28] cursor-pointer"
                >
                  Load sample field photos
                </button>
                <Chip
                  label={t('checkin.good_photos_count', { count: goodPhotosCount })}
                  variant={canProceedFromPhotos ? 'leaf' : 'alert'}
                  size="md"
                />
              </div>
            </div>

            {/* Photo Slots Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {photoSlots.map((slot) => {
                const hasPhoto = Boolean(slot.previewUrl);
                const result = slot.result;

                return (
                  <div
                    key={slot.id}
                    className="relative flex flex-col rounded-2xl border border-[#26362F]/12 bg-[#FAF6EF] overflow-hidden p-3 min-h-[190px] justify-between text-left"
                  >
                    {hasPhoto ? (
                      <div className="relative w-full h-28 rounded-xl overflow-hidden bg-black/5">
                        <img
                          src={slot.previewUrl}
                          alt={slot.tip}
                          className="w-full h-full object-cover"
                        />
                        {result && result.isGood && (
                          <div className="absolute top-2 right-2 bg-[#6B9E7A] text-white p-1 rounded-full shadow-xs">
                            <Check className="w-3.5 h-3.5" />
                          </div>
                        )}
                      </div>
                    ) : (
                      <label
                        htmlFor={`file-input-${slot.id}`}
                        className="w-full h-28 rounded-xl border-2 border-dashed border-[#26362F]/20 flex flex-col items-center justify-center gap-2 cursor-pointer hover:bg-white/60 transition-colors"
                      >
                        <Camera className="w-6 h-6 text-[#5F6F68]" />
                        <span className="text-[11px] font-semibold text-[#5F6F68] text-center px-2">
                          Add Photo
                        </span>
                        <input
                          id={`file-input-${slot.id}`}
                          type="file"
                          accept="image/*"
                          capture="environment"
                          className="hidden"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handlePhotoUpload(slot.id, file);
                          }}
                        />
                      </label>
                    )}

                    <div className="mt-2 flex flex-col gap-1">
                      <span className="text-[11px] text-[#5F6F68] line-clamp-1 font-medium">
                        {slot.tip}
                      </span>

                      {/* Real Quality Feedback Chip */}
                      {result && !result.isGood && result.chipLabel && (
                        <span className="inline-flex text-[10px] font-semibold text-[#C86047] bg-[#FCE8E2] px-2 py-0.5 rounded-full w-fit">
                          {result.chipLabel}
                        </span>
                      )}

                      {hasPhoto && (
                        <label className="text-[11px] text-[#375941] underline cursor-pointer font-bold mt-1">
                          Retake
                          <input
                            type="file"
                            accept="image/*"
                            capture="environment"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handlePhotoUpload(slot.id, file);
                            }}
                          />
                        </label>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Photo Quality Notice */}
            {!canProceedFromPhotos && (
              <div className="p-3.5 rounded-2xl bg-[#FAF0D7] border border-[#EBCB8B]/40 text-xs text-[#473612] flex items-center gap-2">
                <Info className="w-4 h-4 text-[#8C6D23] shrink-0" />
                <span>{t('checkin.need_more_photos')}</span>
              </div>
            )}

            <div className="flex justify-end pt-4 border-t border-[#26362F]/10">
              <Button
                variant="primary"
                disabled={!canProceedFromPhotos}
                onClick={handleGoToObservations}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                {t('common.next')}
              </Button>
            </div>
          </div>
        )}

        {/* ================= STEP 1: FIELD STATUS ================= */}
        {currentStep === 1 && (
          <div className="flex flex-col gap-6">
            <div className="border-b border-[#26362F]/10 pb-4">
              <h2 className="text-xl font-bold text-[#26362F]">
                This week on your farm
              </h2>
              <p className="text-xs sm:text-sm text-[#5F6F68] mt-1">
                Record any water applied, natural rain, or unusual crop observations.
              </p>
            </div>

            {/* Irrigated question */}
            <div className="flex flex-col gap-3">
              <label className="text-sm font-bold text-[#26362F]">
                {t('checkin.irrigated_question')}
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setIrrigated('no')}
                  className={`px-6 py-2.5 rounded-full font-semibold text-sm border transition-all cursor-pointer min-h-[48px] ${
                    irrigated === 'no'
                      ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28]'
                      : 'bg-white/80 border-[#26362F]/12 text-[#5F6F68]'
                  }`}
                >
                  {t('checkin.irrigate_no')}
                </button>
                <button
                  type="button"
                  onClick={() => setIrrigated('yes')}
                  className={`px-6 py-2.5 rounded-full font-semibold text-sm border transition-all cursor-pointer min-h-[48px] ${
                    irrigated === 'yes'
                      ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28]'
                      : 'bg-white/80 border-[#26362F]/12 text-[#5F6F68]'
                  }`}
                >
                  {t('checkin.irrigate_yes')}
                </button>
              </div>

              {irrigated === 'yes' && (
                <div className="mt-2 max-w-sm">
                  <Input
                    label={t('checkin.irrigation_amount_label')}
                    value={irrigationDetails}
                    onChange={(e) => setIrrigationDetails(e.target.value)}
                    placeholder={t('checkin.irrigation_amount_hint')}
                  />
                </div>
              )}
            </div>

            {/* Rain question */}
            <div className="flex flex-col gap-3 pt-2">
              <label className="text-sm font-bold text-[#26362F]">
                {t('checkin.rain_question')}
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setRainfallNoticed(false)}
                  className={`px-6 py-2.5 rounded-full font-semibold text-sm border transition-all cursor-pointer min-h-[48px] ${
                    !rainfallNoticed
                      ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28]'
                      : 'bg-white/80 border-[#26362F]/12 text-[#5F6F68]'
                  }`}
                >
                  {t('checkin.rain_no')}
                </button>
                <button
                  type="button"
                  onClick={() => setRainfallNoticed(true)}
                  className={`px-6 py-2.5 rounded-full font-semibold text-sm border transition-all cursor-pointer min-h-[48px] ${
                    rainfallNoticed
                      ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28]'
                      : 'bg-white/80 border-[#26362F]/12 text-[#5F6F68]'
                  }`}
                >
                  {t('checkin.rain_yes')}
                </button>
              </div>
            </div>

            {/* Free text notes */}
            <div className="pt-2">
              <Input
                label={t('checkin.notes_label')}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={t('checkin.notes_hint')}
              />
            </div>

            <div className="flex items-center justify-between pt-6 border-t border-[#26362F]/10">
              <Button
                variant="ghost"
                onClick={() => setCurrentStep(0)}
                leftIcon={<ArrowLeft className="w-4 h-4" />}
              >
                {t('common.back')}
              </Button>
              <Button
                variant="primary"
                onClick={handleGoToPlan}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                {t('common.next')}
              </Button>
            </div>
          </div>
        )}

        {/* ================= STEP 2: YOUR PLAN ================= */}
        {currentStep === 2 && (
          <div className="flex flex-col gap-6">
            {isPreparingPlan ? (
              <div className="py-16 flex flex-col items-center justify-center gap-3 text-center">
                <Loader2 className="w-8 h-8 animate-spin text-[#6B9E7A]" />
                <p className="text-sm font-semibold text-[#26362F]">
                  {t('checkin.preparing_plan')}
                </p>
              </div>
            ) : (
              <>
                <div className="border-b border-[#26362F]/10 pb-4">
                  <h2 className="text-xl font-bold text-[#26362F]">
                    Your Weekly Plan
                  </h2>
                  <p className="text-xs sm:text-sm text-[#5F6F68] mt-1">
                    Grounded recommendations calibrated from root-zone depletion and reviewed agronomic advisories.
                  </p>
                </div>

                {/* 3 Grounded Cards: Water, Leaves, Feed */}
                <div className="grid grid-cols-1 gap-5">
                  {/* CARD 1: WATER */}
                  {plan?.water && (
                    <Card className="p-6 border border-[#26362F]/10 bg-white/90">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-10 h-10 rounded-xl bg-[#8CC2DD]/30 text-[#13384A] flex items-center justify-center">
                            <Droplets className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-extrabold text-base text-[#26362F]">
                              {t('checkin.card_water_title')}
                            </h3>
                            <span className="text-xs font-semibold text-[#5F6F68] capitalize">
                              Action: {plan.water.action}
                              {plan.water.amount_mm ? ` (${plan.water.amount_mm} mm)` : ''}
                            </span>
                          </div>
                        </div>

                        {/* Confidence chip ONLY if present in data */}
                        {typeof plan.water.confidence === 'number' && (
                          <Chip
                            label={`${Math.round(plan.water.confidence * 100)}% confidence`}
                            variant="water"
                            size="sm"
                          />
                        )}
                      </div>

                      <p className="text-sm text-[#26362F] leading-relaxed">
                        {plan.water.advice}
                      </p>
                    </Card>
                  )}

                  {/* CARD 2: LEAVES */}
                  {plan?.leaves && (
                    <Card className="p-6 border border-[#26362F]/10 bg-white/90">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-10 h-10 rounded-xl bg-[#BFE0C8]/40 text-[#1E3A28] flex items-center justify-center">
                            <Sprout className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-extrabold text-base text-[#26362F]">
                              {plan.leaves.title || t('checkin.card_leaves_title')}
                            </h3>
                            <span className="text-xs text-[#5F6F68]">
                              Source: {plan.leaves.source}
                            </span>
                          </div>
                        </div>

                        <Chip
                          label={t('checkin.photos_saved_notice')}
                          variant="leaf"
                          size="sm"
                        />
                      </div>

                      <div className="text-sm text-[#26362F] leading-relaxed flex flex-col gap-2">
                        <p>
                          <strong>Symptoms to look for: </strong>
                          {typeof plan.leaves.symptoms === 'string'
                            ? plan.leaves.symptoms
                            : plan.leaves.symptoms?.join(', ')}
                        </p>
                        {plan.leaves.cultural_advice && (
                          <p className="text-xs text-[#5F6F68]">
                            <strong>Management: </strong>
                            {plan.leaves.cultural_advice}
                          </p>
                        )}
                      </div>

                      {/* Safety Fallback */}
                      <div className="mt-3 pt-3 border-t border-[#26362F]/10 text-xs font-semibold text-[#5F6F68] flex items-center gap-1.5">
                        <Info className="w-3.5 h-3.5 text-[#6B9E7A]" />
                        <span>{plan.leaves.kvk_note || 'confirm with your KVK'}</span>
                      </div>
                    </Card>
                  )}

                  {/* CARD 3: FEED */}
                  {plan?.feed && (
                    <Card className="p-6 border border-[#26362F]/10 bg-white/90">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-10 h-10 rounded-xl bg-[#FAF0D7] text-[#473612] flex items-center justify-center">
                            <Sparkles className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-extrabold text-base text-[#26362F]">
                              {t('checkin.card_feed_title')}
                            </h3>
                            <span className="text-xs text-[#5F6F68]">
                              Soil Health Record context ({plan.feed.soil_context?.district})
                            </span>
                          </div>
                        </div>
                      </div>

                      <p className="text-sm text-[#26362F] leading-relaxed mb-3">
                        {plan.feed.advice}
                      </p>

                      {plan.feed.soil_context?.dominant_ratings && (
                        <div className="grid grid-cols-3 gap-2 p-3 rounded-2xl bg-[#FAF6EF] text-xs">
                          {Object.entries(plan.feed.soil_context.dominant_ratings).map(
                            ([nutrient, rating]) => (
                              <div key={nutrient}>
                                <span className="text-[#5F6F68] block">{nutrient}</span>
                                <strong className="text-[#26362F]">{rating}</strong>
                              </div>
                            )
                          )}
                        </div>
                      )}

                      <div className="mt-3 pt-3 border-t border-[#26362F]/10 text-xs font-semibold text-[#5F6F68] flex items-center gap-1.5">
                        <Info className="w-3.5 h-3.5 text-[#6B9E7A]" />
                        <span>{plan.feed.kvk_note || 'confirm dose with your KVK'}</span>
                      </div>
                    </Card>
                  )}
                </div>

                {/* Farmer Response Actions */}
                <div className="pt-4 border-t border-[#26362F]/10 flex flex-col gap-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="text-sm font-bold text-[#26362F]">
                      Record Action for this Week:
                    </span>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setSelectedAction('done')}
                        className={`px-4 py-2 min-h-[44px] rounded-full text-xs font-bold border transition-all cursor-pointer flex items-center gap-1.5 ${
                          selectedAction === 'done'
                            ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28]'
                            : 'bg-white/80 border-[#26362F]/15 text-[#5F6F68]'
                        }`}
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>{t('checkin.action_done')}</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedAction('not_yet')}
                        className={`px-4 py-2 min-h-[44px] rounded-full text-xs font-bold border transition-all cursor-pointer flex items-center gap-1.5 ${
                          selectedAction === 'not_yet'
                            ? 'bg-[#FCE8E2] border-[#EBA896] text-[#5C1D13]'
                            : 'bg-white/80 border-[#26362F]/15 text-[#5F6F68]'
                        }`}
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>{t('checkin.action_not_yet')}</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedAction('kvk')}
                        className={`px-4 py-2 min-h-[44px] rounded-full text-xs font-bold border transition-all cursor-pointer flex items-center gap-1.5 ${
                          selectedAction === 'kvk'
                            ? 'bg-[#D8EDF8] border-[#8CC2DD] text-[#13384A]'
                            : 'bg-white/80 border-[#26362F]/15 text-[#5F6F68]'
                        }`}
                      >
                        <PhoneCall className="w-3.5 h-3.5" />
                        <span>{t('checkin.action_talk_kvk')}</span>
                      </button>
                    </div>
                  </div>

                  {selectedAction === 'kvk' && (
                    <div className="p-4 rounded-2xl bg-[#D8EDF8] border border-[#8CC2DD]/40 text-xs text-[#13384A]">
                      {t('checkin.kvk_referral_text')}
                    </div>
                  )}

                  <div className="flex justify-end pt-3">
                    <Button
                      variant="primary"
                      size="lg"
                      isLoading={isSaving}
                      onClick={handleCompleteCheckin}
                      rightIcon={<CheckCircle2 className="w-4 h-4" />}
                    >
                      Save Weekly Record
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
