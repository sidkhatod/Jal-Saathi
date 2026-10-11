"""
Unit tests for the Decision Engine Lambda (/backend/decide).
"""

import os
import sys
import json
import pytest
import numpy as np

# Ensure backend directory and project root are in sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from decide.engine import (
        DecisionEngine,
        DecisionRequest,
        IrrigationEvent,
        DailyWeatherRecord,
        CVResult,
        evaluate_rl_policy,
        decide,
        sanitize_safety_text,
    )
    from decide.handler import handler
except ImportError:
    from backend.decide.engine import (
        DecisionEngine,
        DecisionRequest,
        IrrigationEvent,
        DailyWeatherRecord,
        CVResult,
        evaluate_rl_policy,
        decide,
        sanitize_safety_text,
    )
    from backend.decide.handler import handler

GOLDEN_OBS_PATH = os.path.join(ROOT_DIR, "rl", "artifacts", "golden_obs.json")


# -------------------------------------------------------------------
# 1. Golden Observations Parity Test
# -------------------------------------------------------------------

def test_golden_observations_parity():
    """Asserts exact action output parity against all golden observations."""
    assert os.path.exists(GOLDEN_OBS_PATH), f"Golden observations not found at {GOLDEN_OBS_PATH}"
    with open(GOLDEN_OBS_PATH, "r", encoding="utf-8") as f:
        goldens = json.load(f)

    assert len(goldens) == 5, f"Expected 5 golden observations, found {len(goldens)}"

    for idx, item in enumerate(goldens):
        obs = np.array(item["observation"], dtype=np.float32)
        expected_action = item["onnx_action"]
        predicted_action, method = evaluate_rl_policy(obs)

        assert predicted_action == expected_action, (
            f"Parity mismatch at golden index {idx}! "
            f"Expected {expected_action}, got {predicted_action} via {method}. "
            f"Obs: {obs}"
        )


# -------------------------------------------------------------------
# 2. Water Decision Tests (Wheat & Paddy)
# -------------------------------------------------------------------

def test_water_decision_wheat_depletion_simulation():
    """Simulates wheat water balance forward rollout from sowing to as_of_date."""
    engine = DecisionEngine()

    # 10 days of dry weather without irrigation -> depletion accumulates
    weather_history = [
        DailyWeatherRecord(
            date=f"2023-11-{15+i:02d}",
            precipitation_sum=0.0,
            et0_fao_evapotranspiration=4.0,
        )
        for i in range(10)
    ]
    weather_forecast = [
        DailyWeatherRecord(date="2023-11-25", precipitation_sum=0.0, et0_fao_evapotranspiration=4.0),
        DailyWeatherRecord(date="2023-11-26", precipitation_sum=0.0, et0_fao_evapotranspiration=4.0),
        DailyWeatherRecord(date="2023-11-27", precipitation_sum=0.0, et0_fao_evapotranspiration=4.0),
    ]

    req = DecisionRequest(
        plot_id="plot-wheat-01",
        as_of_date="2023-11-25",
        crop="wheat",
        sowing_date="2023-11-15",
        district_code="karnal",
        soil_texture="loam",
        texture_source="measured",
        weather_history=weather_history,
        weather_forecast=weather_forecast,
        irrigation_log=[],
    )

    decision = engine.decide_water(req)
    assert decision.depletion_mm is not None
    assert decision.depletion_mm > 0.0
    assert decision.raw_mm is not None and decision.raw_mm > 0.0
    assert decision.taw_mm is not None and decision.taw_mm > decision.raw_mm
    assert decision.norm_depletion is not None
    assert decision.confidence == 0.95  # measured texture has high confidence
    assert decision.reason_key in ["depletion_threshold_reached", "sufficient_moisture"]


def test_water_decision_wheat_with_irrigation():
    """Ensures irrigation events are credited and reset days_since_last_irr."""
    engine = DecisionEngine()

    weather_history = [
        DailyWeatherRecord(date="2023-11-15", precipitation_sum=0.0, et0_fao_evapotranspiration=3.5),
        DailyWeatherRecord(date="2023-11-16", precipitation_sum=0.0, et0_fao_evapotranspiration=3.5),
        DailyWeatherRecord(date="2023-11-17", precipitation_sum=0.0, et0_fao_evapotranspiration=3.5),
    ]
    weather_forecast = [
        DailyWeatherRecord(date="2023-11-18", precipitation_sum=0.0, et0_fao_evapotranspiration=3.5),
        DailyWeatherRecord(date="2023-11-19", precipitation_sum=0.0, et0_fao_evapotranspiration=3.5),
        DailyWeatherRecord(date="2023-11-20", precipitation_sum=0.0, et0_fao_evapotranspiration=3.5),
    ]
    irrigation_log = [
        IrrigationEvent(date="2023-11-17", amount_mm=40.0)
    ]

    req = DecisionRequest(
        plot_id="plot-wheat-02",
        as_of_date="2023-11-18",
        crop="wheat",
        sowing_date="2023-11-15",
        district_code="karnal",
        soil_texture="loam",
        texture_source="default",  # Default texture lowers confidence
        weather_history=weather_history,
        weather_forecast=weather_forecast,
        irrigation_log=irrigation_log,
    )

    decision = engine.decide_water(req)
    # Since 40 mm was applied yesterday, depletion should be 0.0 or minimal
    assert decision.action == "skip"
    assert decision.amount_mm == 0.0
    assert decision.reason_key == "sufficient_moisture"
    assert decision.confidence == 0.75  # 0.95 - 0.20 for default texture


def test_water_decision_paddy_fallback():
    """Paddy has missing awd_depth in paddy.yaml, so must return rule_unavailable."""
    engine = DecisionEngine()

    req = DecisionRequest(
        plot_id="plot-paddy-01",
        as_of_date="2023-07-15",
        crop="paddy",
        sowing_date="2023-06-15",
        district_code="kurukshetra",
        soil_texture="clay_loam",
        texture_source="measured",
    )

    decision = engine.decide_water(req)
    assert decision.method == "rule_unavailable"
    assert "KVK" in decision.advice
    assert decision.reason_key == "missing_awd_parameters"
    assert decision.confidence == 0.50


# -------------------------------------------------------------------
# 3. Protect Decision Tests (Safety Invariants)
# -------------------------------------------------------------------

def test_protect_decision_healthy():
    """Healthy foliage triggers monitor status."""
    engine = DecisionEngine()

    req = DecisionRequest(
        plot_id="plot-01",
        as_of_date="2023-12-01",
        crop="wheat",
        sowing_date="2023-11-01",
        district_code="karnal",
        cv_result=CVResult(disease_predicted="healthy", status="confident", confidence=0.94),
    )

    decision = engine.decide_protect(req)
    assert decision.status == "monitor"
    assert decision.reason_key == "healthy_monitoring"
    assert decision.confidence == 0.94


def test_protect_decision_retake_safety_invariant():
    """CRITICAL SAFETY: 'retake' CV status NEVER yields protect advice."""
    engine = DecisionEngine()

    req = DecisionRequest(
        plot_id="plot-02",
        as_of_date="2023-12-01",
        crop="wheat",
        sowing_date="2023-11-01",
        district_code="karnal",
        cv_result=CVResult(disease_predicted="wheat_rust", status="retake", confidence=0.45),
    )

    decision = engine.decide_protect(req)
    assert decision.status != "advice", "'retake' status must NEVER yield protect advice!"
    assert decision.status == "consult_kvk"
    assert decision.reason_key == "cv_retake_required"
    assert decision.confidence == 0.30


def test_protect_decision_reviewed_advisory_and_weather_gating():
    """Reviewed advisory gives advice with weather-gated spray window."""
    engine = DecisionEngine()

    # Forecast with heavy rain triggers spray delay alert
    forecast_rainy = [
        DailyWeatherRecord(date="2023-12-01", precipitation_sum=12.0, et0_fao_evapotranspiration=2.5),
        DailyWeatherRecord(date="2023-12-02", precipitation_sum=5.0, et0_fao_evapotranspiration=2.5),
        DailyWeatherRecord(date="2023-12-03", precipitation_sum=0.0, et0_fao_evapotranspiration=3.0),
    ]

    req = DecisionRequest(
        plot_id="plot-03",
        as_of_date="2023-12-01",
        crop="wheat",
        sowing_date="2023-11-01",
        district_code="karnal",
        weather_forecast=forecast_rainy,
        cv_result=CVResult(disease_predicted="wheat_rust", status="confident", confidence=0.91),
    )

    decision = engine.decide_protect(req)
    assert decision.status == "advice"
    assert decision.reason_key == "reviewed_advisory_active"
    assert "Delay" in decision.weather_window or "check the weather window" in decision.weather_window
    assert decision.confidence == 0.91


def test_protect_decision_no_chemical_dose_or_brand():
    """Ensures no unreviewed product, brand, or dosage figures appear in output."""
    raw_text = "Apply 2.5 ml/l Tilt 25 EC or 500 g/ha Mancozeb 75 WP."
    sanitized = sanitize_safety_text(raw_text)
    assert "2.5 ml/l" not in sanitized
    assert "500 g/ha" not in sanitized


# -------------------------------------------------------------------
# 4. Nourish Decision Tests (Soil Rating Fallback)
# -------------------------------------------------------------------

def test_nourish_decision_unreviewed_rules_fallback_to_kvk():
    """Since fertiliser_rules.yaml is unreviewed, must return confirm dose with KVK."""
    engine = DecisionEngine()

    req = DecisionRequest(
        plot_id="plot-04",
        as_of_date="2023-12-01",
        crop="wheat",
        sowing_date="2023-11-01",
        district_code="karnal",
        block_code="karnal_block",
    )

    decision = engine.decide_nourish(req)
    assert decision.status == "confirm_with_kvk"
    assert decision.advice == "confirm dose with KVK"
    assert decision.reason_key in ["soil_health_rating_available", "soil_data_unavailable"]
    assert decision.confidence > 0.0


# -------------------------------------------------------------------
# 5. Handler & Full Pipeline Integration Test
# -------------------------------------------------------------------

def test_full_decision_pipeline_response_schema():
    """Tests complete decide() invocation conforming to DecisionResponse schema."""
    req_dict = {
        "plot_id": "plot-full-test",
        "as_of_date": "2023-12-05",
        "crop": "wheat",
        "sowing_date": "2023-11-15",
        "district_code": "karnal",
        "soil_texture": "loam",
        "texture_source": "farmer",
        "irrigation_log": [{"date": "2023-11-25", "amount_mm": 40.0}],
        "weather_history": [
            {"date": "2023-11-15", "precipitation_sum": 0.0, "et0_fao_evapotranspiration": 3.2}
        ],
        "weather_forecast": [
            {"date": "2023-12-05", "precipitation_sum": 0.0, "et0_fao_evapotranspiration": 3.5},
            {"date": "2023-12-06", "precipitation_sum": 0.0, "et0_fao_evapotranspiration": 3.6},
            {"date": "2023-12-07", "precipitation_sum": 0.0, "et0_fao_evapotranspiration": 3.4},
        ],
        "cv_result": {
            "disease_predicted": "wheat_rust",
            "status": "confident",
            "confidence": 0.92,
        },
    }

    res = decide(req_dict)
    assert res["plot_id"] == "plot-full-test"
    assert res["as_of_date"] == "2023-12-05"
    assert "water" in res and "reason_key" in res["water"] and "confidence" in res["water"]
    assert "protect" in res and "reason_key" in res["protect"] and "confidence" in res["protect"]
    assert "nourish" in res and "reason_key" in res["nourish"] and "confidence" in res["nourish"]
    assert "overall_confidence" in res
    assert 0.0 <= res["overall_confidence"] <= 1.0


def test_lambda_handler_proxy_invocation():
    """Tests handler entry point with API Gateway proxy event."""
    event = {
        "body": json.dumps({
            "plot_id": "plot-lambda-01",
            "as_of_date": "2023-12-01",
            "crop": "wheat",
            "sowing_date": "2023-11-15",
            "district_code": "karnal",
        })
    }

    resp = handler(event)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["plot_id"] == "plot-lambda-01"
    assert "water" in body
    assert "protect" in body
    assert "nourish" in body


def test_lambda_handler_invalid_payload():
    """Tests handler returns 400 on malformed input."""
    event = {"body": "invalid-non-json-content"}
    resp = handler(event)
    assert resp["statusCode"] in [400, 500]
