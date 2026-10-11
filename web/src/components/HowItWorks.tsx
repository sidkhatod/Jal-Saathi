import React from 'react';
import { Language } from './Navbar';

interface HowItWorksProps {
  lang: Language;
}

export const HowItWorks: React.FC<HowItWorksProps> = ({ lang }) => {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Title */}
      <div className="border-b border-slate-800/80 pb-4">
        <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
          {lang === 'en' ? 'System Architecture & Engineering Design' : 'प्रणाली की संरचना और तकनीकी डिजाइन'}
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          {lang === 'en'
            ? 'Transparent breakdown of physics simulation, computer vision, data ingestion, and hackathon presentation boundaries.'
            : 'भौतिकी सिमुलेशन, कंप्यूटर विज़न और डेटा एकीकरण का स्पष्ट व पारदर्शी विवरण।'}
        </p>
      </div>

      {/* 3 Pillars Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 rounded-2xl border-t-4 border-t-cyan-400 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xl">
            💧
          </div>
          <h3 className="text-lg font-bold text-white">
            {lang === 'en' ? '1. Physics & RL Irrigation' : '1. भौतिकी व आरएल सिंचाई'}
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            {lang === 'en'
              ? 'Implements daily FAO-56 root-zone depletion balance with dynamic Kc curve interpolation, effective rainfall (80%), and soil water holding capacities. Reinforcement Learning (PPO) learns to anticipate water demand and skip applications before forecast rain.'
              : 'दैनिक FAO-56 जल संतुलन मॉडल और जड़-क्षेत्र नमी का हिसाब। PPO मॉडल बारिश के पूर्वानुमान को ध्यान में रखकर अनावश्यक सिंचाई टालता है।'}
          </p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border-t-4 border-t-amber-400 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-xl">
            🍃
          </div>
          <h3 className="text-lg font-bold text-white">
            {lang === 'en' ? '2. Foliage Audit & Protection' : '2. फसल सुरक्षा व पत्ती विश्लेषण'}
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            {lang === 'en'
              ? 'Computer vision diagnostics coupled with strict safety invariants. If image quality is poor ("retake"), protect advice is suppressed. Reviewed advisory rules gate foliar application behind weather windows (rain/high wind).'
              : 'कंप्यूटर विज़न द्वारा पत्ती की जांच। यदि फोटो धुंधली हो तो गलत सलाह देने के बजाय पुनः फोटो लेने की सलाह दी जाती है। छिड़काव मौसम अनुकूल होने पर ही संभव।'}
          </p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border-t-4 border-t-emerald-400 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xl">
            🌱
          </div>
          <h3 className="text-lg font-bold text-white">
            {lang === 'en' ? '3. Soil Health Card Ingestion' : '3. मृदा स्वास्थ्य कार्ड एकीकरण'}
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            {lang === 'en'
              ? 'Queries local Soil Health Card Parquet datasets across village, block, and district levels. Because chemical dosing is sensitive, the system returns dominant nutrient ratings (N/P/K) and always defers specific doses to local KVK scientists.'
              : 'हरियाणा मृदा स्वास्थ्य कार्ड के ब्लॉक/जिला स्तरीय आंकड़ों का उपयोग। रासायनिक खाद की मनमानी खुराक देने के बजाय KVK वैज्ञानिकों से पुष्टि अनिवार्य है।'}
          </p>
        </div>
      </div>

      {/* Transparency Table: Built vs Simulated */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center space-x-2">
          <span className="text-xl">⚖️</span>
          <h2 className="text-lg font-extrabold text-white">
            {lang === 'en' ? 'Transparency Matrix: What is Built vs. What is Simulated' : 'पारदर्शिता तालिका: क्या निर्मित है और क्या सिमुलेटेड है'}
          </h2>
        </div>
        <p className="text-xs text-slate-400">
          {lang === 'en'
            ? 'In strict compliance with local compute constraints (no GPU/heavy model fine-tuning on laptop), all core logic, physics, schemas, APIs, and tests are implemented in code, while heavy neural nets and live telecom channels are mocked for local demonstration.'
            : 'कंप्यूटर नियमों के अनुसार भारी न्यूरल ट्रेनिंग लोकल लैपटॉप पर वर्जित है। सभी समीकरण, डेटा पाइपलाइन, लैम्ब्डा इंजन और टेस्ट वास्तविक हैं।'}
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Component</th>
                <th className="py-3 px-4">Status in Repository</th>
                <th className="py-3 px-4">Implementation Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              <tr>
                <td className="py-3 px-4 font-bold text-white">FAO-56 Soil Physics</td>
                <td className="py-3 px-4 text-emerald-400 font-semibold">✅ Fully Implemented</td>
                <td className="py-3 px-4 text-slate-300">
                  Daily root-zone depletion balance in <code className="text-emerald-300 font-mono">rl/envs/wheat.py</code> and <code className="text-emerald-300 font-mono">backend/decide/engine.py</code>.
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-white">Decision Engine Lambda</td>
                <td className="py-3 px-4 text-emerald-400 font-semibold">✅ Fully Implemented</td>
                <td className="py-3 px-4 text-slate-300">
                  AWS Lambda handler <code className="text-emerald-300 font-mono">backend/decide/handler.py</code> with 18 automated unit tests passing 100%.
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-white">Soil Health Card Portal API</td>
                <td className="py-3 px-4 text-emerald-400 font-semibold">✅ Fully Implemented</td>
                <td className="py-3 px-4 text-slate-300">
                  Parquet data ingestion with DuckDB hierarchical fallback (village → block → district) in <code className="text-emerald-300 font-mono">data/soil_api.py</code>.
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-white">RL Policy Model Weights</td>
                <td className="py-3 px-4 text-amber-400 font-semibold">🔶 Simulated / Mocked</td>
                <td className="py-3 px-4 text-slate-400">
                  Gymnasium environment and ONNX exporter ready in <code className="text-slate-300 font-mono">rl/train.py</code>. Full PPO training script runs on Kaggle; local demo uses exact policy rule fallback and golden fixture.
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-white">Computer Vision (Leaf Disease)</td>
                <td className="py-3 px-4 text-amber-400 font-semibold">🔶 Simulated / Mocked</td>
                <td className="py-3 px-4 text-slate-400">
                  Dataset audit & leakage verification completed in <code className="text-slate-300 font-mono">cv/audit.py</code>. Live inference mocked via JSON contracts to adhere to local compute rule.
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-white">WhatsApp Webhook & Twilio</td>
                <td className="py-3 px-4 text-emerald-400 font-semibold">✅ Fully Implemented (Mocked AWS)</td>
                <td className="py-3 px-4 text-slate-300">
                  HMAC phone hashing, DynamoDB storage, and Twilio validation tested with Moto in <code className="text-emerald-300 font-mono">backend/tests/test_webhook.py</code>.
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-white">Web Presentation UI</td>
                <td className="py-3 px-4 text-emerald-400 font-semibold">✅ Fully Implemented</td>
                <td className="py-3 px-4 text-slate-300">
                  Vite + React + TypeScript + Tailwind SPA delivering Season Replay scrubbing and bilingual advisory cards.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Agronomic Citations & Data Sources */}
      <div className="glass-panel p-6 rounded-2xl space-y-3 text-xs text-slate-400">
        <h3 className="text-sm font-bold text-slate-200">📚 Primary Sourced Data & Scientific Citations</h3>
        <ul className="list-disc list-inside space-y-1.5 leading-relaxed text-slate-300">
          <li>
            <strong>Crop Coefficients & Evapotranspiration:</strong> FAO Irrigation and Drainage Paper No. 56 (Allen et al., 1998), Tables 11, 12, 19, and 22.
          </li>
          <li>
            <strong>Soil Water Characteristics:</strong> FAO-56 Table 19 median hydraulic capacities for Loam (AWC = 130 mm/m) and Clay (AWC = 140 mm/m).
          </li>
          <li>
            <strong>Soil Nutrient Data:</strong> Soil Health Card Portal (Government of India / Haryana Department of Agriculture), Cycle II district and block records.
          </li>
          <li>
            <strong>Agronomic Advisories:</strong> CCS Haryana Agricultural University (HAU) Hisar Wheat Package of Practices; ICAR-Central Soil Salinity Research Institute (CSSRI) Karnal.
          </li>
        </ul>
      </div>
    </div>
  );
};
