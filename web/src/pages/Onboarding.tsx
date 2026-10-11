import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../i18n';
import { backend } from '../lib/backend';
import { Stepper } from '../components/ui/Stepper';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Chip } from '../components/ui/Chip';
import {
  MapPin,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Wheat as WheatIcon,
  Sprout,
  ShieldAlert,
} from 'lucide-react';

interface DistrictConfig {
  name: string;
  state: string;
  latitude: number;
  longitude: number;
  is_pilot: boolean;
  soil_file: string;
}

interface CropStage {
  stage_id: string;
  name_en: string;
  name_hi: string;
  days: number;
  description_en: string;
  description_hi: string;
}

interface CropConfig {
  name: string;
  display_name_en: string;
  display_name_hi: string;
  season: string;
  stages: CropStage[];
  total_days: number;
}

interface SoilNutrientInfo {
  dominant_level: string;
  level_used: string;
  year_used: string;
  n_samples: number;
}

interface SoilRecord {
  district: string;
  district_code: string;
  nutrients: Record<string, SoilNutrientInfo>;
}

function calculateDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

export const Onboarding: React.FC = () => {
  const { t, language } = useTranslation();
  const navigate = useNavigate();

  // Current Step (0 to 4)
  const [currentStep, setCurrentStep] = useState(0);

  // Form State
  const [district, setDistrict] = useState<string>('Karnal');
  const [districtDistance, setDistrictDistance] = useState<number | null>(null);
  const [locationStatus, setLocationStatus] = useState<
    'idle' | 'detecting' | 'granted' | 'denied' | 'timeout' | 'far'
  >('idle');

  const [crop, setCrop] = useState<'wheat' | 'paddy'>('wheat');
  const [variety, setVariety] = useState<string>('');

  const [fieldName, setFieldName] = useState<string>('Main Plot');
  const [area, setArea] = useState<number>(2.0);
  const [areaUnit, setAreaUnit] = useState<'acre' | 'hectare' | 'bigha'>('acre');
  const [irrigationSource, setIrrigationSource] = useState<'borewell' | 'canal' | 'rainfed'>(
    'borewell'
  );
  const [irrigationMethod, setIrrigationMethod] = useState<'flood' | 'furrow' | 'drip'>('flood');

  const [sowingDate, setSowingDate] = useState<string>(
    () => new Date().toISOString().split('T')[0]
  );

  // Loaded real dataset records
  const [districtsData, setDistrictsData] = useState<Record<string, DistrictConfig>>({});
  const [cropsData, setCropsData] = useState<Record<string, CropConfig>>({});
  const [soilData, setSoilData] = useState<SoilRecord | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load static data from exported JSON
  useEffect(() => {
    fetch('./data/districts.json')
      .then((r) => r.json())
      .then((d) => setDistrictsData(d))
      .catch(() => {});

    fetch('./data/crops.json')
      .then((r) => r.json())
      .then((c) => setCropsData(c))
      .catch(() => {});
  }, []);

  // Load real soil record whenever district changes
  useEffect(() => {
    if (district) {
      fetch(`./data/soil_${district}.json`)
        .then((r) => r.json())
        .then((s) => setSoilData(s))
        .catch(() => setSoilData(null));
    }
  }, [district]);

  // Stepper Items
  const stepsList = [
    { id: 0, label: t('onboarding.steps.location') },
    { id: 1, label: t('onboarding.steps.crop') },
    { id: 2, label: t('onboarding.steps.field') },
    { id: 3, label: t('onboarding.steps.sowing') },
    { id: 4, label: t('onboarding.steps.review') },
  ];

  // Geolocation Handler
  const handleAllowLocation = () => {
    setLocationStatus('detecting');
    if (!navigator.geolocation) {
      setLocationStatus('denied');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const userLat = pos.coords.latitude;
        const userLon = pos.coords.longitude;

        // Compare against pilot districts (Karnal: 29.68, 76.99; Kurukshetra: 29.96, 76.82)
        const dKarnal = calculateDistanceKm(userLat, userLon, 29.68, 76.99);
        const dKurukshetra = calculateDistanceKm(userLat, userLon, 29.96, 76.82);

        const nearest = dKarnal <= dKurukshetra ? 'Karnal' : 'Kurukshetra';
        const minDistance = Math.min(dKarnal, dKurukshetra);

        setDistrict(nearest);
        setDistrictDistance(minDistance);

        if (minDistance > 150) {
          setLocationStatus('far');
        } else {
          setLocationStatus('granted');
        }
      },
      (err) => {
        if (err.code === 1) {
          setLocationStatus('denied');
        } else {
          setLocationStatus('timeout');
        }
      },
      { timeout: 8000 }
    );
  };

  // Compute Stage Dates from Real Calendar Lengths
  const calculateStagesWithDates = () => {
    const cropConfig = cropsData[crop];
    if (!cropConfig || !cropConfig.stages) return [];

    let currentDate = new Date(sowingDate || new Date());
    return cropConfig.stages.map((stg) => {
      const startDate = new Date(currentDate);
      const days = stg.days || 0;
      currentDate = new Date(currentDate.getTime() + days * 24 * 60 * 60 * 1000);
      const endDate = new Date(currentDate);

      return {
        ...stg,
        startDate: startDate.toLocaleDateString(language === 'hi' ? 'hi-IN' : 'en-US', {
          month: 'short',
          day: 'numeric',
        }),
        endDate: endDate.toLocaleDateString(language === 'hi' ? 'hi-IN' : 'en-US', {
          month: 'short',
          day: 'numeric',
        }),
      };
    });
  };

  // Save Field Action
  const handleCreateField = async () => {
    setIsSubmitting(true);
    try {
      const cropConfig = cropsData[crop];
      const totalWeeks = cropConfig ? Math.ceil(cropConfig.total_days / 7) : 18;
      const initialStage = crop === 'wheat' ? 'Crown Root Initiation' : 'Transplanting';

      await backend.farms.createField({
        name: fieldName.trim() || (crop === 'wheat' ? 'Wheat Field' : 'Paddy Field'),
        crop,
        district,
        currentWeek: 1,
        totalWeeks,
        stage: initialStage,
        area: Number(area) || 1.0,
        areaUnit,
        irrigationSource,
        irrigationMethod,
        sowingDate,
        isDemo: false,
      });

      navigate('/');
    } catch {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto py-4 sm:py-8 flex flex-col gap-6">
      {/* Top Header & Progress Stepper */}
      <div className="flex flex-col gap-6 text-center">
        <div>
          <span className="text-xs font-bold text-[#6B9E7A] tracking-wider uppercase">
            {t('app.name')}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#26362F] mt-1">
            {t('onboarding.title')}
          </h1>
        </div>

        <Stepper steps={stepsList} currentStepIndex={currentStep} className="max-w-2xl mx-auto" />
      </div>

      {/* Main Step Container */}
      <Card elevated className="w-full mt-2">
        {/* ================= STEP 0: LOCATION ================= */}
        {currentStep === 0 && (
          <div className="flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-bold text-[#26362F] flex items-center gap-2">
                <MapPin className="w-5 h-5 text-[#6B9E7A]" />
                <span>{t('onboarding.steps.location')}</span>
              </h2>
              <p className="text-sm text-[#5F6F68] mt-1.5 leading-relaxed">
                {t('onboarding.location_why')}
              </p>
            </div>

            {/* Actions for Location */}
            <div className="flex flex-wrap gap-3">
              <Button
                variant="primary"
                onClick={handleAllowLocation}
                isLoading={locationStatus === 'detecting'}
                leftIcon={<MapPin className="w-4 h-4" />}
              >
                {t('onboarding.allow_location_btn')}
              </Button>
              <Button
                variant="outline"
                onClick={() => setLocationStatus('idle')}
              >
                {t('onboarding.enter_manually_btn')}
              </Button>
            </div>

            {/* Geolocation feedback messages */}
            {locationStatus === 'denied' && (
              <div className="p-4 rounded-2xl bg-[#FCE8E2] border border-[#EBA896]/40 text-xs text-[#5C1D13] flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 text-[#C86047]" />
                <span>{t('onboarding.location_denied')}</span>
              </div>
            )}

            {locationStatus === 'timeout' && (
              <div className="p-4 rounded-2xl bg-[#FAF0D7] border border-[#EBCB8B]/50 text-xs text-[#473612] flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 text-[#8C6D23]" />
                <span>{t('onboarding.location_timeout')}</span>
              </div>
            )}

            {locationStatus === 'far' && (
              <div className="p-4 rounded-2xl bg-[#D8EDF8] border border-[#8CC2DD]/40 text-xs text-[#13384A] flex items-start gap-2.5">
                <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-[#2C6E8A]" />
                <span>{t('onboarding.location_far_away', { dist: districtDistance || 150 })}</span>
              </div>
            )}

            {/* District Selection & Friendly Confirmation Card */}
            <div className="p-5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/10 flex flex-col gap-4">
              <label className="text-sm font-bold text-[#26362F]">
                {t('onboarding.select_district')}
              </label>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.keys(districtsData).length > 0
                  ? Object.values(districtsData).map((d) => (
                      <button
                        key={d.name}
                        type="button"
                        onClick={() => {
                          setDistrict(d.name);
                          if (locationStatus !== 'granted') setLocationStatus('idle');
                        }}
                        className={`p-4 rounded-2xl text-left border transition-all duration-200 cursor-pointer min-h-[54px] flex items-center justify-between ${
                          district === d.name
                            ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28] font-bold shadow-xs'
                            : 'bg-white/80 border-[#26362F]/10 text-[#26362F] hover:bg-white'
                        }`}
                      >
                        <div>
                          <p className="text-base">{d.name}</p>
                          <p className="text-xs text-[#5F6F68]">{d.state} (Pilot District)</p>
                        </div>
                        {district === d.name && (
                          <CheckCircle2 className="w-5 h-5 text-[#6B9E7A]" />
                        )}
                      </button>
                    ))
                  : ['Karnal', 'Kurukshetra'].map((dName) => (
                      <button
                        key={dName}
                        type="button"
                        onClick={() => setDistrict(dName)}
                        className={`p-4 rounded-2xl text-left border transition-all cursor-pointer ${
                          district === dName
                            ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28] font-bold'
                            : 'bg-white/80 border-[#26362F]/10'
                        }`}
                      >
                        <p className="text-base">{dName}</p>
                        <p className="text-xs text-[#5F6F68]">Haryana</p>
                      </button>
                    ))}
              </div>

              {district && (
                <div className="pt-2 flex items-center gap-2 text-xs text-[#1E3A28] font-medium">
                  <CheckCircle2 className="w-4 h-4 text-[#6B9E7A]" />
                  <span>
                    {t('onboarding.pilot_district_selected')} <strong>{district}, Haryana</strong>
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================= STEP 1: CROP ================= */}
        {currentStep === 1 && (
          <div className="flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-bold text-[#26362F]">
                {t('onboarding.crop_select_title')}
              </h2>
              <p className="text-sm text-[#5F6F68] mt-1.5 leading-relaxed">
                {t('onboarding.crop_select_sub')}
              </p>
            </div>

            {/* Crop Selection Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Wheat Card */}
              <button
                type="button"
                onClick={() => setCrop('wheat')}
                className={`p-6 rounded-3xl text-left border transition-all duration-200 cursor-pointer flex flex-col justify-between min-h-[160px] ${
                  crop === 'wheat'
                    ? 'bg-[#FAF0D7] border-[#EBCB8B] shadow-sm ring-2 ring-[#EBCB8B]/50'
                    : 'bg-white/70 border-[#26362F]/10 hover:bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="w-12 h-12 rounded-2xl bg-[#EBCB8B]/30 text-[#473612] flex items-center justify-center">
                    <WheatIcon className="w-6 h-6 stroke-[2]" />
                  </div>
                  {crop === 'wheat' && (
                    <Chip label="Selected" variant="sand" size="sm" />
                  )}
                </div>

                <div className="mt-4">
                  <h3 className="text-xl font-extrabold text-[#26362F]">
                    {t('onboarding.wheat_title')}
                  </h3>
                  <p className="text-xs text-[#5F6F68] mt-0.5">
                    {t('onboarding.wheat_sub')}
                  </p>
                </div>
              </button>

              {/* Paddy Card */}
              <button
                type="button"
                onClick={() => setCrop('paddy')}
                className={`p-6 rounded-3xl text-left border transition-all duration-200 cursor-pointer flex flex-col justify-between min-h-[160px] ${
                  crop === 'paddy'
                    ? 'bg-[#E1EFE4] border-[#6B9E7A] shadow-sm ring-2 ring-[#6B9E7A]/40'
                    : 'bg-white/70 border-[#26362F]/10 hover:bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="w-12 h-12 rounded-2xl bg-[#6B9E7A]/20 text-[#1E3A28] flex items-center justify-center">
                    <Sprout className="w-6 h-6 stroke-[2.2]" />
                  </div>
                  {crop === 'paddy' && (
                    <Chip label="Selected" variant="leaf" size="sm" />
                  )}
                </div>

                <div className="mt-4">
                  <h3 className="text-xl font-extrabold text-[#26362F]">
                    {t('onboarding.paddy_title')}
                  </h3>
                  <p className="text-xs text-[#5F6F68] mt-0.5">
                    {t('onboarding.paddy_sub')}
                  </p>
                </div>
              </button>
            </div>

            {/* Variety text input */}
            <div className="pt-2">
              <Input
                label={t('onboarding.variety_label')}
                value={variety}
                onChange={(e) => setVariety(e.target.value)}
                placeholder={t('onboarding.variety_hint')}
              />
            </div>
          </div>
        )}

        {/* ================= STEP 2: FIELD ================= */}
        {currentStep === 2 && (
          <div className="flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-bold text-[#26362F]">
                {t('onboarding.field_title')}
              </h2>
              <p className="text-sm text-[#5F6F68] mt-1.5 leading-relaxed">
                Provide field size and water delivery method to calculate depth requirements.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label={t('onboarding.field_name_label')}
                value={fieldName}
                onChange={(e) => setFieldName(e.target.value)}
                placeholder={t('onboarding.field_name_hint')}
                required
              />

              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <Input
                    label={t('onboarding.area_label')}
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={area}
                    onChange={(e) => setArea(parseFloat(e.target.value) || 1)}
                    required
                  />
                </div>
                <div className="w-32">
                  <label className="text-sm font-semibold text-[#26362F] block mb-1.5">
                    {t('onboarding.unit_label')}
                  </label>
                  <select
                    value={areaUnit}
                    onChange={(e) => setAreaUnit(e.target.value as any)}
                    className="w-full min-h-[48px] px-3 py-2.5 rounded-2xl bg-white/90 text-[#26362F] border border-[#26362F]/12 text-sm font-medium focus-visible:outline-[#6B9E7A]"
                  >
                    <option value="acre">Acre</option>
                    <option value="hectare">Hectare</option>
                    <option value="bigha">Bigha</option>
                  </select>
                </div>
              </div>
            </div>

            {areaUnit === 'bigha' && (
              <p className="text-xs text-[#5F6F68] italic -mt-2">
                {t('onboarding.bigha_note')}
              </p>
            )}

            {/* Irrigation Source */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-bold text-[#26362F]">
                {t('onboarding.irrigation_source_label')}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {[
                  { id: 'borewell', label: t('onboarding.source_borewell') },
                  { id: 'canal', label: t('onboarding.source_canal') },
                  { id: 'rainfed', label: t('onboarding.source_rainfed') },
                ].map((src) => (
                  <button
                    key={src.id}
                    type="button"
                    onClick={() => setIrrigationSource(src.id as any)}
                    className={`p-3.5 min-h-[48px] rounded-2xl border text-sm font-semibold transition-all cursor-pointer ${
                      irrigationSource === src.id
                        ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28]'
                        : 'bg-white/80 border-[#26362F]/10 text-[#5F6F68] hover:bg-white'
                    }`}
                  >
                    {src.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Irrigation Method */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-bold text-[#26362F]">
                {t('onboarding.irrigation_method_label')}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {[
                  { id: 'flood', label: t('onboarding.method_flood') },
                  { id: 'furrow', label: t('onboarding.method_furrow') },
                  { id: 'drip', label: t('onboarding.method_drip') },
                ].map((mth) => (
                  <button
                    key={mth.id}
                    type="button"
                    onClick={() => setIrrigationMethod(mth.id as any)}
                    className={`p-3.5 min-h-[48px] rounded-2xl border text-sm font-semibold transition-all cursor-pointer ${
                      irrigationMethod === mth.id
                        ? 'bg-[#E1EFE4] border-[#6B9E7A] text-[#1E3A28]'
                        : 'bg-white/80 border-[#26362F]/10 text-[#5F6F68] hover:bg-white'
                    }`}
                  >
                    {mth.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= STEP 3: SOWING & SOIL CARD ================= */}
        {currentStep === 3 && (
          <div className="flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-bold text-[#26362F]">
                {crop === 'paddy'
                  ? t('onboarding.transplanting_date_label')
                  : t('onboarding.sowing_date_label')}
              </h2>
              <p className="text-sm text-[#5F6F68] mt-1.5 leading-relaxed">
                Dates are used to align crop growth stages with historical and live weather.
              </p>
            </div>

            <div className="max-w-xs">
              <Input
                type="date"
                label={
                  crop === 'paddy'
                    ? t('onboarding.transplanting_date_label')
                    : t('onboarding.sowing_date_label')
                }
                value={sowingDate}
                onChange={(e) => setSowingDate(e.target.value)}
                required
              />
            </div>

            {/* Real Soil Card for District */}
            <div className="p-6 rounded-3xl bg-white/90 border border-[#26362F]/12 shadow-xs flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#26362F]/10 pb-3">
                <div>
                  <h3 className="font-extrabold text-base text-[#26362F]">
                    {t('onboarding.soil_card_title', { district })}
                  </h3>
                  <p className="text-xs text-[#5F6F68] mt-0.5">
                    {soilData && soilData.nutrients['Nitrogen']
                      ? t('onboarding.soil_source_caption', {
                          level: soilData.nutrients['Nitrogen'].level_used,
                          year: soilData.nutrients['Nitrogen'].year_used,
                        })
                      : 'Soil Health Card survey records.'}
                  </p>
                </div>
                <Chip label={`${district} District Record`} variant="leaf" size="sm" />
              </div>

              {/* Grid of Key Nutrients */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1">
                {[
                  { key: 'Nitrogen', label: 'Nitrogen (N)' },
                  { key: 'Phosphorus', label: 'Phosphorus (P)' },
                  { key: 'Potassium', label: 'Potassium (K)' },
                  { key: 'Soil Ph', label: 'pH Value' },
                  { key: 'Electrical Conductivity', label: 'Salinity (EC)' },
                  { key: 'Organic Carbon', label: 'Organic Carbon (OC)' },
                ].map(({ key, label }) => {
                  const nut = soilData?.nutrients[key];
                  const hasData = nut && nut.dominant_level;

                  return (
                    <div
                      key={key}
                      className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col justify-between min-h-[75px]"
                    >
                      <span className="text-xs text-[#5F6F68] font-medium">{label}</span>
                      {hasData ? (
                        <div className="flex items-center justify-between mt-1.5">
                          <span className="text-sm font-extrabold text-[#26362F]">
                            {nut.dominant_level}
                          </span>
                          <span className="text-[10px] text-[#5F6F68]/80">
                            {nut.level_used}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-[#5F6F68] italic mt-1.5">
                          {t('onboarding.nutrient_not_available')}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ================= STEP 4: REVIEW & CONFIRM ================= */}
        {currentStep === 4 && (
          <div className="flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-bold text-[#26362F]">
                {t('onboarding.confirm_title')}
              </h2>
              <p className="text-sm text-[#5F6F68] mt-1.5 leading-relaxed">
                {t('onboarding.confirm_sub')}
              </p>
            </div>

            {/* Field Parameters Summary */}
            <div className="p-5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/10 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-[#5F6F68] block">Field</span>
                <span className="font-bold text-[#26362F] text-sm">{fieldName}</span>
              </div>
              <div>
                <span className="text-[#5F6F68] block">Crop & Variety</span>
                <span className="font-bold text-[#26362F] text-sm capitalize">
                  {crop} {variety ? `(${variety})` : ''}
                </span>
              </div>
              <div>
                <span className="text-[#5F6F68] block">Location</span>
                <span className="font-bold text-[#26362F] text-sm">{district}, Haryana</span>
              </div>
              <div>
                <span className="text-[#5F6F68] block">Area & Source</span>
                <span className="font-bold text-[#26362F] text-sm">
                  {area} {areaUnit} • {irrigationSource}
                </span>
              </div>
            </div>

            {/* Projected Growth Stage Timeline */}
            <div>
              <h3 className="font-bold text-base text-[#26362F] mb-3 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-[#6B9E7A]" />
                <span>{t('onboarding.stage_timeline_title')}</span>
              </h3>

              <div className="flex flex-col gap-2.5">
                {calculateStagesWithDates().map((stg, idx) => (
                  <div
                    key={stg.stage_id}
                    className={`p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                      idx === 0
                        ? 'bg-[#E1EFE4] border-[#6B9E7A]/40 text-[#1E3A28]'
                        : 'bg-white/80 border-[#26362F]/8 text-[#26362F]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                          idx === 0
                            ? 'bg-[#6B9E7A] text-white'
                            : 'bg-[#26362F]/10 text-[#5F6F68]'
                        }`}
                      >
                        {idx + 1}
                      </div>
                      <div>
                        <h4 className="font-extrabold text-sm">
                          {language === 'hi' ? stg.name_hi : stg.name_en}
                        </h4>
                        <p className="text-xs text-[#5F6F68] mt-0.5">
                          {language === 'hi' ? stg.description_hi : stg.description_en}
                        </p>
                      </div>
                    </div>

                    <div className="text-right sm:shrink-0 text-xs">
                      <span className="font-semibold block">
                        {stg.startDate} – {stg.endDate}
                      </span>
                      <span className="text-[#5F6F68]">
                        {stg.days ? `${stg.days} days` : t('onboarding.kvk_fallback_line')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* First Irrigation Guidance */}
            <div className="p-4 rounded-2xl bg-[#D8EDF8] border border-[#8CC2DD]/40 text-xs text-[#13384A] flex items-start gap-3">
              <Layers className="w-5 h-5 text-[#2C6E8A] shrink-0 mt-0.5" />
              <div>
                <strong className="block text-sm mb-0.5">
                  {t('onboarding.first_irrigation_guidance')}
                </strong>
                <p>
                  {crop === 'wheat'
                    ? t('onboarding.first_irrigation_wheat')
                    : t('onboarding.first_irrigation_paddy')}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Stepper Bottom Navigation (Back & Next) */}
        <div className="flex items-center justify-between pt-8 border-t border-[#26362F]/10 mt-6">
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              if (currentStep > 0) setCurrentStep(currentStep - 1);
              else navigate('/');
            }}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            {t('common.back')}
          </Button>

          {currentStep < 4 ? (
            <Button
              type="button"
              variant="primary"
              onClick={() => setCurrentStep(currentStep + 1)}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              {t('common.next')}
            </Button>
          ) : (
            <Button
              type="button"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              onClick={handleCreateField}
              rightIcon={<CheckCircle2 className="w-4 h-4" />}
            >
              {isSubmitting
                ? t('onboarding.creating_field')
                : t('onboarding.create_field_btn')}
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};
