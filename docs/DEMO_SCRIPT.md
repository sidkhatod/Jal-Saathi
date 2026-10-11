# Jal-Saathi (जल-साथी) — 3-Minute Hackathon Demo Script

**Event:** AWS Bharat Build Hackathon 2026  
**Focus:** Frontend UI Walkthrough, Physics-informed RL Water Savings, and Responsible Agronomic AI  
**Total Target Duration:** 3:00 (180 seconds)

---

## Shot List & Narration Table

| Time | Visual / Screen Action | Spoken Narration (English) | Technical & Safety Cue |
|---|---|---|---|
| **0:00 – 0:30** | **Intro & Problem:**<br>Screen opens on the Jal-Saathi web app at the **Season Replay** tab. Camera pans over the clean emerald UI, the **"Simulated on historical weather (held-out season). Not field-validated."** disclaimer badge, and the "Haryana Pilot (Karnal)" pill. | *"In the fertile plains of Haryana, groundwater tables are dropping by over a meter every year. Over 80% of irrigation comes from tubewell pumping. Smallholder farmers either flood their fields on a rigid calendar every 20 days or guess when to water, wasting millions of liters of diesel and precious water. Meet **Jal-Saathi (जल-साथी)**: an AI-guided irrigation, crop protection, and soil health advisory system built specifically for smallholders."* | Emphasize real Haryana groundwater context and the permanent safety simulation disclaimer. |
| **0:30 – 1:20** | **Season Replay (46.7% Water Savings):**<br>Click **Play Replay** at 2x speed. Scrub slider across Day 0 to 119. Point to the dynamic root-zone moisture bar tracking FAO-56 depletion between Field Capacity and RAW (37.5 mm). Pause on **Day 72** right before the 36 mm rainfall event. Toggle between **⭐ RL Policy (PPO)** and **Fixed (20-Day)**. | *"Here on our interactive Season Replay dashboard, we simulate a 120-day winter wheat season in Karnal using historical FAO-56 dual balance weather. Watch the root-zone moisture meter. Traditional farmers irrigate blindly on a fixed 20-day cycle. On Day 72, fixed and threshold rules waste 40 mm right before a major 36 mm winter rainstorm. Our PPO Reinforcement Learning policy anticipates upcoming rainfall and skips the wasteful watering. Over the full 120 days, PPO applies just **160 mm** across 4 irrigations with **zero stress days**, saving **46.7% water** compared to the 300 mm flooded by traditional schedules."* | Show live cumulative water counter saving 140 mm. |
| **1:20 – 2:05** | **This Week Advisory Card:**<br>Click the **"This Week"** navigation tab. Click the **"🌐 हिन्दी में देखें"** button to show instant Hindi localization. Hover over the 3 cards: **Water (सिंचाई)**, **Leaves (फसल सुरक्षा)**, and **Feed (मृदा पोषण)**. | *"Farmers receive their weekly action card directly on WhatsApp or our web portal. First, **Water**: an exact 40 mm irrigation recommendation based on their plot's depletion balance. Second, **Leaves**: our foliage audit detects Yellow Rust symptoms, providing non-chemical airflow and spacing advice with an explicit weather spray window alert. Third, **Feed**: we query the Government of India Soil Health Card portal for block-level N-P-K ratings and always confirm dosage with local Krishi Vigyan Kendra (KVK) scientists. Notice our 91% verified model confidence score."* | Highlight the 3-pillar design and bilingual English/Hindi toggle. |
| **2:05 – 2:40** | **Architecture & Safety Disclosures:**<br>Click the **"How it Works"** tab. Scroll through the 3-pillar breakdown and the **Transparency Matrix** table. | *"Agronomic safety is our top priority. Jal-Saathi enforces strict invariants: we never output proprietary chemical brand names or unreviewed doses. If leaf photo quality is poor ('retake'), protect advice is automatically suppressed. In full transparency, all FAO-56 soil physics, Decision Engine Lambda handlers, and data APIs are fully implemented with 18 automated unit tests passing 100%. Deep learning and RL training were conducted offline on CPU/Kaggle to respect local compute boundaries, feeding verified fixtures into our production-ready AWS Serverless pipeline."* | Point to the Transparency Matrix table and citations (FAO-56, HAU Hisar, CSSRI). |
| **2:40 – 3:00** | **Conclusion & Call to Action:**<br>Return to the main dashboard. Final camera view on the Jal-Saathi header. | *"Built on AWS Serverless architecture, Jal-Saathi proves that responsible, physics-informed AI can conserve Haryana's groundwater while keeping smallholder farmers informed, safe, and productive. Thank you."* | End cleanly on the brand logo. |

---

## Production & Recording Tips

1. **Screen Resolution:** Record at 1080p (1920x1080) in full screen mode (F11 in browser).
2. **Scrubbing Demo:** Spend at least 15 seconds scrubbing back and forth between Day 60 and Day 80 in Season Replay to show the rain event (Day 73-74) and how PPO stays out of stress without wasting water.
3. **Language Toggle:** Toggle Hindi on and off during the "This Week" view to prove real smallholder accessibility for rural Haryana.
