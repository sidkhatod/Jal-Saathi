MESSAGES = {
    "en": {
        "welcome": "Welcome to Jal-Saathi! Let's get started.\n1. English\n2. Hindi\nReply with a number.",
        "location": "Please send your location pin.",
        "crop": "What crop are you growing?\n1. Paddy\n2. Wheat",
        "area": "What is the area of your farm? (e.g., '2 acres' or '1.5 hectares')",
        "sowing_date": "When did you sow the crop? (e.g., YYYY-MM-DD or 'last week')",
        "irrigation": "What is your main irrigation source and method? (e.g., Tube well, drip)",
        "consent": "Do you consent to Jal-Saathi storing your farm data and messaging you weekly? (Yes/No)",
        "done": "Onboarding complete! You can now send photos of your crop.",
        "photo_received": "Photo received! You have sent {count} photos this week.",
        "invalid": "Invalid input, please try again.",
        "reset": "Progress reset. Send 'hi' to start again.",
        "location_found": "Location identified in district: {district}.",
        "location_fallback": "Location reverse geocoding failed. Using nearest pilot district: {district}.",
        "error": "An error occurred, please try again."
    },
    "hi": {
        "welcome": "जल-साथी में आपका स्वागत है! चलिए शुरू करते हैं।\n1. अंग्रेज़ी\n2. हिंदी\nनंबर लिखकर भेजें।",
        "location": "कृपया अपना लोकेशन पिन भेजें।",
        "crop": "आप कौन सी फसल उगा रहे हैं?\n1. धान\n2. गेहूं",
        "area": "आपके खेत का क्षेत्रफल क्या है? (जैसे, '2 एकड़' या '1.5 हेक्टेयर')",
        "sowing_date": "आपने फसल कब बोई? (जैसे, YYYY-MM-DD या 'पिछले हफ्ते')",
        "irrigation": "आपकी मुख्य सिंचाई का स्रोत और विधि क्या है? (जैसे, ट्यूबवेल, ड्रिप)",
        "consent": "क्या आप सहमत हैं कि जल-साथी आपके खेत का डेटा सहेजे और आपको साप्ताहिक संदेश भेजे? (हाँ/नहीं)",
        "done": "शुरुआती प्रक्रिया पूरी हुई! अब आप अपनी फसल की तस्वीरें भेज सकते हैं।",
        "photo_received": "तस्वीर मिल गई! आपने इस हफ्ते {count} तस्वीरें भेजी हैं।",
        "invalid": "अमान्य इनपुट, कृपया फिर से प्रयास करें।",
        "reset": "प्रगति रीसेट हो गई। फिर से शुरू करने के लिए 'hi' भेजें।",
        "location_found": "जिले में स्थान की पहचान की गई: {district}।",
        "location_fallback": "स्थान की पहचान विफल रही। सबसे निकटतम पायलट जिले का उपयोग: {district}।",
        "error": "एक त्रुटि हुई, कृपया पुनः प्रयास करें।"
    }
}


# -------------------------------------------------------------------
# Standard 5-Line Advisory Templates (WATER / LEAVES / FEED)
# -------------------------------------------------------------------

ADVISORY_TEMPLATES = {
    "en": (
        "🌾 *Jal-Saathi Weekly Advisory ({as_of_date})*\n"
        "💧 WATER: {water_advice} ({water_amount} mm)\n"
        "🍃 LEAVES: {protect_advice} (Window: {weather_window})\n"
        "🌱 FEED: {nourish_advice} (Soil Context: {soil_context})\n"
        "ℹ️ Confidence: {confidence}% | Powered by Jal-Saathi"
    ),
    "hi": (
        "🌾 *जल-साथी साप्ताहिक सलाह ({as_of_date})*\n"
        "💧 सिंचाई (WATER): {water_advice} ({water_amount} मिमी)\n"
        "🍃 फसल सुरक्षा (LEAVES): {protect_advice} (समय: {weather_window})\n"
        "🌱 पोषण (FEED): {nourish_advice} (मिट्टी स्थिति: {soil_context})\n"
        "ℹ️ विश्वसनीयता: {confidence}% | जल-साथी द्वारा संचालित"
    )
}


def format_advisory_message(advisory: dict, lang: str = "en") -> str:
    """
    Formats a DecisionResponse dictionary into a standard 5-line WhatsApp advisory message.
    """
    template = ADVISORY_TEMPLATES.get(lang, ADVISORY_TEMPLATES["en"])

    water = advisory.get("water", {})
    protect = advisory.get("protect", {})
    nourish = advisory.get("nourish", {})
    soil_ctx = nourish.get("soil_context")

    if soil_ctx and isinstance(soil_ctx, dict):
        dominant = soil_ctx.get("dominant_ratings", {})
        dom_str = ", ".join(f"{k}:{v}" for k, v in dominant.items()) if dominant else "Available"
        soil_summary = f"{soil_ctx.get('level_used', 'district')} ({dom_str})"
    else:
        soil_summary = "KVK consultation recommended"

    water_advice = water.get("advice", "Follow routine watering.")
    water_amount = int(water.get("amount_mm", 0.0))
    protect_advice = protect.get("advice", "Crop foliage healthy.")
    weather_window = protect.get("weather_window", "check label")
    nourish_advice = nourish.get("advice", "confirm dose with KVK")
    confidence_pct = int(round(advisory.get("overall_confidence", 0.85) * 100))

    return template.format(
        as_of_date=advisory.get("as_of_date", "Today"),
        water_advice=water_advice,
        water_amount=water_amount,
        protect_advice=protect_advice,
        weather_window=weather_window,
        nourish_advice=nourish_advice,
        soil_context=soil_summary,
        confidence=confidence_pct,
    )

