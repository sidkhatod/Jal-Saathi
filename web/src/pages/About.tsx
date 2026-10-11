import React, { useEffect } from 'react';
import { useTranslation } from '../i18n';
import { Card } from '../components/ui/Card';
import { Chip } from '../components/ui/Chip';
import {
  Sprout,
  Activity,
  Database,
  Compass,
  FileCheck,
  ShieldAlert,
} from 'lucide-react';

export const About: React.FC = () => {
  const { t } = useTranslation();

  useEffect(() => {
    document.title = 'Jal-Saathi - About this Demo';
  }, []);

  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto w-full py-4 sm:py-8">
      {/* Page Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E1EFE4] text-[#1E3A28] border border-[#6B9E7A]/25 text-xs font-bold mb-3">
          <Sprout className="w-4 h-4" />
          <span>{t('app.name')}</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#26362F] tracking-tight">
          About this Demo
        </h1>
        <p className="text-base text-[#5F6F68] mt-2 leading-relaxed">
          Jal-Saathi is an agronomic water-stewardship advisory built for smallholder farmers in Northern India.
          Here is a transparent breakdown of what runs live, what uses stored research data, and what is planned next.
        </p>
      </div>

      {/* Section 1: What Runs Live */}
      <Card elevated className="flex flex-col gap-4">
        <div className="flex items-center gap-2.5 border-b border-[#26362F]/10 pb-3">
          <div className="w-9 h-9 rounded-xl bg-[#6B9E7A]/20 text-[#1E3A28] flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#26362F]">What Runs Live in Your Browser</h2>
            <p className="text-xs text-[#5F6F68]">Client-side execution and device interactions</p>
          </div>
        </div>

        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs sm:text-sm text-[#26362F]">
          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <strong className="text-[#1E3A28]">Geolocation & District Proximity</strong>
            <span className="text-[#5F6F68] text-xs">
              Queries device coordinates via navigator.geolocation and computes Haversine distance to pilot districts (Karnal and Kurukshetra).
            </span>
          </li>

          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <strong className="text-[#1E3A28]">Client-side Photo Quality Check</strong>
            <span className="text-[#5F6F68] text-xs">
              Runs in-browser HTML5 canvas image processing (Laplacian variance blur score and mean luminance check) to ensure clear field documentation.
            </span>
          </li>

          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <strong className="text-[#1E3A28]">WebCrypto PBKDF2 Password Security</strong>
            <span className="text-[#5F6F68] text-xs">
              Derives cryptographic keys using 100,000 iterations of PBKDF2 SHA-256 with a 16-byte random salt. Zero plaintext passwords ever touch storage.
            </span>
          </li>

          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <strong className="text-[#1E3A28]">Phenological Stage Alignment</strong>
            <span className="text-[#5F6F68] text-xs">
              Calculates cumulative growth stage boundaries (CRI, Tillering, Flowering, Ripening) dynamically from the farmer's entered sowing date.
            </span>
          </li>
        </ul>
      </Card>

      {/* Section 2: What Uses Stored Data */}
      <Card elevated className="flex flex-col gap-4">
        <div className="flex items-center gap-2.5 border-b border-[#26362F]/10 pb-3">
          <div className="w-9 h-9 rounded-xl bg-[#8CC2DD]/30 text-[#13384A] flex items-center justify-center">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#26362F]">What Uses Stored Sample Data</h2>
            <p className="text-xs text-[#5F6F68]">Verified research files and regional government records</p>
          </div>
        </div>

        <ul className="flex flex-col gap-3 text-xs sm:text-sm text-[#26362F]">
          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <strong className="text-[#26362F]">Soil Health Card Survey Exports</strong>
              <Chip label="Real Parquet Export" variant="leaf" size="sm" />
            </div>
            <span className="text-[#5F6F68] text-xs leading-relaxed">
              Extracted from official Soil Health Card database records for Haryana (Karnal and Kurukshetra). Shows dominant block and district ratings for 12 nutrients without any guessed values.
            </span>
          </li>

          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <strong className="text-[#26362F]">Weather & Climate History</strong>
              <Chip label="Open-Meteo Parquet" variant="water" size="sm" />
            </div>
            <span className="text-[#5F6F68] text-xs leading-relaxed">
              Historical weather observations (2010–2023) sourced from Open-Meteo reanalysis archive for Karnal (29.68°N, 76.99°E) and Kurukshetra (29.96°N, 76.82°E).
            </span>
          </li>

          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <strong className="text-[#26362F]">FAO-56 Crop Evapotranspiration Parameters</strong>
              <Chip label="FAO-56 Tables" variant="sand" size="sm" />
            </div>
            <span className="text-[#5F6F68] text-xs leading-relaxed">
              Single crop coefficients (Kc ini, mid, end), maximum effective root zone depths, and depletion fractions (p) sourced directly from FAO Irrigation and Drainage Paper 56.
            </span>
          </li>

          <li className="p-3.5 rounded-2xl bg-[#FAF6EF] border border-[#26362F]/8 flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <strong className="text-[#26362F]">Reviewed Agronomic Extension Bulletins</strong>
              <Chip label="ICAR-IIWBR / HAU" variant="leaf" size="sm" />
            </div>
            <span className="text-[#5F6F68] text-xs leading-relaxed">
              Wheat and paddy scouting guides and cultural controls are verified from extension advisories published by ICAR-IIWBR Karnal and CCSHAU Hisar.
            </span>
          </li>
        </ul>
      </Card>

      {/* Section 3: Safety Guardrails */}
      <Card elevated className="flex flex-col gap-4 border-[#EBA896]/30">
        <div className="flex items-center gap-2.5 border-b border-[#26362F]/10 pb-3">
          <div className="w-9 h-9 rounded-xl bg-[#FCE8E2] text-[#5C1D13] flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-[#C86047]" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#26362F]">Agronomic Safety Guardrails</h2>
            <p className="text-xs text-[#5F6F68]">Strict safety protocols enforced throughout the interface</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 rounded-2xl bg-white border border-[#26362F]/10 flex flex-col gap-1">
            <strong className="text-[#26362F]">No Unverified Brand Names</strong>
            <p className="text-[#5F6F68]">
              We never promote specific commercial agrochemical brands or formulations.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-[#26362F]/10 flex flex-col gap-1">
            <strong className="text-[#26362F]">No Autonomous Doses</strong>
            <p className="text-[#5F6F68]">
              Application quantities are never generated algorithmically. Always deferred to official CIB&RC labels and KVK experts.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-[#26362F]/10 flex flex-col gap-1">
            <strong className="text-[#26362F]">Mandatory Fallbacks</strong>
            <p className="text-[#5F6F68]">
              Every protection and nourishment card reminds farmers to check label weather windows and consult their block KVK officer.
            </p>
          </div>
        </div>
      </Card>

      {/* Section 4: Data Sources & Licenses */}
      <Card elevated className="flex flex-col gap-4">
        <div className="flex items-center gap-2.5 border-b border-[#26362F]/10 pb-3">
          <div className="w-9 h-9 rounded-xl bg-[#EBCB8B]/30 text-[#473612] flex items-center justify-center">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#26362F]">Data Sources & Licensing</h2>
            <p className="text-xs text-[#5F6F68]">Citations and transparent license disclosures</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#26362F]/10 text-[#5F6F68]">
                <th className="py-2.5 pr-4 font-semibold">Dataset / Source</th>
                <th className="py-2.5 pr-4 font-semibold">Provider</th>
                <th className="py-2.5 font-semibold">License / Attribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#26362F]/8 text-[#26362F]">
              <tr>
                <td className="py-3 pr-4 font-medium">Soil Health Card Surveys</td>
                <td className="py-3 pr-4 text-[#5F6F68]">Dept of Agriculture, Govt of India</td>
                <td className="py-3">Open Government Data (OGD) License India</td>
              </tr>
              <tr>
                <td className="py-3 pr-4 font-medium">Historical Weather Archive</td>
                <td className="py-3 pr-4 text-[#5F6F68]">Open-Meteo Historical API</td>
                <td className="py-3">CC-BY 4.0 (Non-commercial open reanalysis)</td>
              </tr>
              <tr>
                <td className="py-3 pr-4 font-medium">Crop Coefficients (FAO-56)</td>
                <td className="py-3 pr-4 text-[#5F6F68]">UN FAO Irrigation & Drainage</td>
                <td className="py-3">FAO Copyright (Academic fair use cited)</td>
              </tr>
              <tr>
                <td className="py-3 pr-4 font-medium">Extension Advisories</td>
                <td className="py-3 pr-4 text-[#5F6F68]">ICAR-IIWBR & CCSHAU</td>
                <td className="py-3">Public agricultural extension notices</td>
              </tr>
              <tr>
                <td className="py-3 pr-4 font-medium">Wheat Rust Image Datasets</td>
                <td className="py-3 pr-4 text-[#5F6F68]">Kaggle Community Datasets</td>
                <td className="py-3 text-[#5F6F68]">
                  Unknown / Unspecified community license (Audit completed in cv/audit.py)
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      {/* Section 5: Roadmap */}
      <Card elevated className="flex flex-col gap-4">
        <div className="flex items-center gap-2.5 border-b border-[#26362F]/10 pb-3">
          <div className="w-9 h-9 rounded-xl bg-[#BFE0C8]/40 text-[#1E3A28] flex items-center justify-center">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#26362F]">Project Roadmap</h2>
            <p className="text-xs text-[#5F6F68]">Upcoming engineering sprints</p>
          </div>
        </div>

        <ul className="flex flex-col gap-3 text-xs sm:text-sm text-[#26362F]">
          <li className="flex items-start gap-3">
            <span className="w-2 h-2 rounded-full bg-[#6B9E7A] mt-2 shrink-0" />
            <div>
              <strong>AWS Cloud Infrastructure (AuthStack & S3 Presigned Uploads)</strong>
              <p className="text-xs text-[#5F6F68]">
                Cognito User Pool with auto-confirm trigger for hackathon evaluation and Lambda Function URL generating presigned PUT URLs for direct S3 photo storage.
              </p>
            </div>
          </li>

          <li className="flex items-start gap-3">
            <span className="w-2 h-2 rounded-full bg-[#8CC2DD] mt-2 shrink-0" />
            <div>
              <strong>Kaggle/AWS Model Training Pipeline</strong>
              <p className="text-xs text-[#5F6F68]">
                Executing rl/kaggle_rl.ipynb on cloud CPU/GPU to export verified ppo_wheat.onnx and full evaluation tables for seasonal irrigation comparisons.
              </p>
            </div>
          </li>

          <li className="flex items-start gap-3">
            <span className="w-2 h-2 rounded-full bg-[#EBCB8B] mt-2 shrink-0" />
            <div>
              <strong>Soil Moisture Probe IoT Telemetry</strong>
              <p className="text-xs text-[#5F6F68]">
                Direct telemetry integration from LoRaWAN capacitance soil moisture probes placed at 15 cm and 30 cm root-zone depths.
              </p>
            </div>
          </li>
        </ul>
      </Card>
    </div>
  );
};
