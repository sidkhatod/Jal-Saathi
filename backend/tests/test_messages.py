"""
Tests for backend/messages.py advisory templates and formatting.
"""

import pytest
from backend.messages import format_advisory_message, ADVISORY_TEMPLATES

def test_format_advisory_message_en():
    advisory = {
        "plot_id": "plot-karnal-01",
        "as_of_date": "2023-12-05",
        "water": {
            "action": "irrigate",
            "amount_mm": 40.0,
            "advice": "Apply 40 mm irrigation based on root-zone depletion balance.",
        },
        "protect": {
            "status": "advice",
            "advice": "Symptoms of Wheat Rust detected. Follow IPM sanitation.",
            "weather_window": "check label",
        },
        "nourish": {
            "status": "confirm_with_kvk",
            "advice": "confirm dose with KVK",
            "soil_context": {
                "level_used": "block",
                "dominant_ratings": {"N": "Low", "P": "Medium", "K": "High"}
            }
        },
        "overall_confidence": 0.91
    }

    msg = format_advisory_message(advisory, lang="en")
    lines = msg.strip().split("\n")
    assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}: {msg}"
    assert "Jal-Saathi Weekly Advisory" in lines[0]
    assert "WATER:" in lines[1] and "40 mm" in lines[1]
    assert "LEAVES:" in lines[2]
    assert "FEED:" in lines[3] and "confirm dose with KVK" in lines[3]
    assert "Confidence: 91%" in lines[4]

def test_format_advisory_message_hi():
    advisory = {
        "plot_id": "plot-karnal-01",
        "as_of_date": "2023-12-05",
        "water": {
            "action": "irrigate",
            "amount_mm": 40.0,
            "advice": "जड़-क्षेत्र नमी संतुलन के आधार पर 40 मिमी सिंचाई करें।",
        },
        "protect": {
            "status": "advice",
            "advice": "गेहूं के पीले रतुआ के लक्षण दिखे हैं।",
            "weather_window": "दवा लेबल पर जांचें",
        },
        "nourish": {
            "status": "confirm_with_kvk",
            "advice": "कृषि विज्ञान केंद्र (KVK) से पुष्टि करें",
            "soil_context": None
        },
        "overall_confidence": 0.88
    }

    msg = format_advisory_message(advisory, lang="hi")
    lines = msg.strip().split("\n")
    assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}: {msg}"
    assert "जल-साथी साप्ताहिक सलाह" in lines[0]
    assert "सिंचाई (WATER):" in lines[1] and "40 मिमी" in lines[1]
    assert "फसल सुरक्षा (LEAVES):" in lines[2]
    assert "पोषण (FEED):" in lines[3]
    assert "विश्वसनीयता: 88%" in lines[4]
