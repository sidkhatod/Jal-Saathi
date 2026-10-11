# Jal-Saathi System Contracts & Schemas

This document defines the schemas and data contracts across modules in Jal-Saathi (RL policies, weather processing, CV audit, web visualizer, and backend services).

---

## 1. Season Replay Schema (`season_replay.json`)

The season replay file records daily rollout states, irrigation actions, and atmospheric water demand for a single held-out season (crop year). It powers the offline evaluation reports and web replay dashboard.

### Wheat Schema (`wheat_season_replay.json`)
List of daily trajectory records:

```json
[
  {
    "day": 0,
    "depletion_mm": 0.0,
    "action_mm": 0.0,
    "water_applied": 0.0,
    "etc": 2.15
  },
  {
    "day": 1,
    "depletion_mm": 2.15,
    "action_mm": 0.0,
    "water_applied": 0.0,
    "etc": 2.30
  }
]
```

| Field | Type | Description |
|---|---|---|
| `day` | `int` | Day of season ($0 \dots \text{total days}-1$). |
| `depletion_mm` | `float` | Daily root-zone depletion $D_r$ in mm ($0.0 \dots \text{TAW}$). |
| `action_mm` | `float` | Scheduled irrigation action in mm ($0.0, 20.0, 40.0, 60.0$). |
| `water_applied` | `float` | Actual water depth applied to the soil in mm. |
| `etc` | `float` | Daily crop evapotranspiration $ET_c = K_c \times ET_0$ in mm. |

---

### Paddy Schema (`paddy_season_replay.json`)
List of daily trajectory records:

```json
[
  {
    "day": 0,
    "ponded_mm": 10.0,
    "action_mm": 0.0,
    "water_applied": 0.0,
    "etc": 3.42
  },
  {
    "day": 1,
    "ponded_mm": 3.58,
    "action_mm": 20.0,
    "water_applied": 20.0,
    "etc": 3.50
  }
]
```

| Field | Type | Description |
|---|---|---|
| `day` | `int` | Day of season ($0 \dots \text{total days}-1$). |
| `ponded_mm` | `float` | Ponded water depth above soil surface in mm (negative = below surface). |
| `action_mm` | `float` | Scheduled irrigation action in mm ($0.0, 20.0, 40.0, 60.0$). |
| `water_applied` | `float` | Actual water depth applied to field in mm. |
| `etc` | `float` | Daily crop evapotranspiration in mm. |

---

## 2. Golden Observations Schema (`golden_obs.json`)

Saved in `rl/artifacts/golden_obs.json`. Used for ONNX parity testing and downstream backend inference verification (Task B3).

```json
[
  {
    "observation": [0.0, 0.0, 0.0, 3.2, 0.0, 3.1, 0.0, 3.0, 0.0],
    "onnx_action": 0
  }
]
```

| Field | Type | Description |
|---|---|---|
| `observation` | `List[float]` | Vector of normalized observation features (9 floats). |
| `onnx_action` | `int` | Discrete action predicted by the exported ONNX model ($0, 1, 2, 3$). |

---

## 3. Decision Engine Lambda Contract (`/backend/decide`)

The Decision Engine processes plot state, soil characteristics, recent weather history, short-term weather forecasts, and CV photo diagnostics to produce integrated agronomic advice across three core pillars: **Water**, **Protect**, and **Nourish**.

### 3.1 Input Event Schema (`DecisionRequest`)

```json
{
  "plot_id": "plot-101",
  "farmer_id": "farmer-202",
  "crop": "wheat",
  "sowing_date": "2023-11-15",
  "as_of_date": "2023-12-05",
  "district_code": "0602",
  "block_code": "0045",
  "village_code": "0123",
  "soil_texture": "loam",
  "texture_source": "farmer",
  "irrigation_log": [
    {
      "date": "2023-11-25",
      "amount_mm": 40.0
    }
  ],
  "weather_history": [
    {
      "date": "2023-11-15",
      "precipitation_sum": 0.0,
      "et0_fao_evapotranspiration": 3.2,
      "temperature_2m_max": 26.5,
      "temperature_2m_min": 12.0
    }
  ],
  "weather_forecast": [
    {
      "date": "2023-12-05",
      "precipitation_sum": 0.0,
      "et0_fao_evapotranspiration": 3.5,
      "wind_speed_10m_max": 4.2
    },
    {
      "date": "2023-12-06",
      "precipitation_sum": 0.0,
      "et0_fao_evapotranspiration": 3.6,
      "wind_speed_10m_max": 3.8
    },
    {
      "date": "2023-12-07",
      "precipitation_sum": 0.0,
      "et0_fao_evapotranspiration": 3.4,
      "wind_speed_10m_max": 5.0
    }
  ],
  "cv_result": {
    "disease_predicted": "wheat_rust",
    "status": "confident",
    "confidence": 0.92
  }
}
```

### 3.2 Output Decision Schema (`DecisionResponse`)

```json
{
  "plot_id": "plot-101",
  "as_of_date": "2023-12-05",
  "water": {
    "action": "irrigate",
    "amount_mm": 40.0,
    "method": "rl_ppo",
    "depletion_mm": 38.5,
    "advice": "Apply 40 mm irrigation based on root-zone depletion balance.",
    "reason_key": "depletion_threshold_reached",
    "confidence": 0.95
  },
  "protect": {
    "status": "advice",
    "advice": "Yellow rust symptoms detected. Inspect lower foliage and follow IPM sanitation.",
    "weather_window": "check the weather window on the label",
    "reason_key": "reviewed_advisory_active",
    "confidence": 0.92
  },
  "nourish": {
    "status": "confirm_with_kvk",
    "advice": "confirm dose with KVK",
    "soil_context": {
      "level_used": "block",
      "year_used": 2021,
      "dominant_ratings": {
        "N": "low",
        "P": "medium",
        "K": "high"
      }
    },
    "reason_key": "soil_health_rating_available",
    "confidence": 0.85
  },
  "overall_confidence": 0.85
}
```

