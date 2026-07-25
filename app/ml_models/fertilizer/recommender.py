FERTILIZERS = {
    "Urea": {
        "description":     "High nitrogen fertilizer. Best for leafy growth and green color.",
        "npk":             {"N": 46, "P": 0, "K": 0},
        "how_to_apply":    "Broadcast or band application. Apply in split doses. Avoid waterlogged fields.",
        "qty_per_acre":    "50–65 kg/acre",
    },
    "DAP": {
        "description":     "Diammonium Phosphate. Rich in phosphorus. Ideal for root development.",
        "npk":             {"N": 18, "P": 46, "K": 0},
        "how_to_apply":    "Basal application before sowing. Mix well with soil.",
        "qty_per_acre":    "50 kg/acre",
    },
    "MOP": {
        "description":     "Muriate of Potash. Boosts potassium. Improves crop quality and disease resistance.",
        "npk":             {"N": 0, "P": 0, "K": 60},
        "how_to_apply":    "Apply before planting or at 30 days after sowing.",
        "qty_per_acre":    "33–40 kg/acre",
    },
    "NPK 20-20-20": {
        "description":     "Balanced fertilizer. Suitable for general crop nutrition.",
        "npk":             {"N": 20, "P": 20, "K": 20},
        "how_to_apply":    "Use as foliar spray or soil application. Good for all stages.",
        "qty_per_acre":    "50 kg/acre",
    },
    "NPK 10-26-26": {
        "description":     "High P and K fertilizer. Ideal for fruiting and root crops.",
        "npk":             {"N": 10, "P": 26, "K": 26},
        "how_to_apply":    "Basal application. Mix well into soil before planting.",
        "qty_per_acre":    "50 kg/acre",
    },
    "Ammonium Sulphate": {
        "description":     "Provides nitrogen and sulphur. Good for alkaline soils.",
        "npk":             {"N": 21, "P": 0, "K": 0},
        "how_to_apply":    "Apply in split doses. Good for paddy and wheat.",
        "qty_per_acre":    "80–100 kg/acre",
    },
    "SSP": {
        "description":     "Single Super Phosphate. Contains phosphorus, calcium, and sulphur.",
        "npk":             {"N": 0, "P": 16, "K": 0},
        "how_to_apply":    "Basal application. Mix with soil before sowing.",
        "qty_per_acre":    "100–125 kg/acre",
    },
    "Compost / Organic Manure": {
        "description":     "Improves soil structure and microbial activity. Best for long-term soil health.",
        "npk":             {"N": 1, "P": 0.5, "K": 1},
        "how_to_apply":    "Apply 2–4 weeks before planting. Mix well into topsoil.",
        "qty_per_acre":    "2–4 tonnes/acre",
    },
}


CROP_FERTILIZER_MAP = {
    "rice":        "Urea",
    "wheat":       "Urea",
    "maize":       "NPK 20-20-20",
    "sugarcane":   "NPK 10-26-26",
    "cotton":      "DAP",
    "groundnut":   "SSP",
    "soybean":     "DAP",
    "potato":      "NPK 10-26-26",
    "tomato":      "NPK 20-20-20",
    "onion":       "MOP",
    "garlic":      "Urea",
    "banana":      "NPK 20-20-20",
    "mango":       "NPK 10-26-26",
    "chilli":      "NPK 20-20-20",
    "turmeric":    "Compost / Organic Manure",
    "ginger":      "Compost / Organic Manure",
    "default":     "NPK 20-20-20",
}


def detect_deficiency(n: float, p: float, k: float) -> dict:
    """
    Detects which nutrient is most deficient
    and returns the suggested fertilizer.
    """
    thresholds = {"N": 40, "P": 20, "K": 30}   # ideal minimum values

    deficiencies = {
        "N": max(0, thresholds["N"] - n),
        "P": max(0, thresholds["P"] - p),
        "K": max(0, thresholds["K"] - k),
    }

    # If all nutrients are sufficient
    if all(v == 0 for v in deficiencies.values()):
        return {
            "most_deficient": None,
            "suggestion":     "Compost / Organic Manure",
            "note":           "Soil nutrients are adequate. Use organic manure to maintain health.",
        }

    # Find the most deficient nutrient
    most_deficient = max(deficiencies, key=deficiencies.get)

    fertilizer_map = {
        "N": "Urea",
        "P": "DAP",
        "K": "MOP",
    }

    return {
        "most_deficient": most_deficient,
        "suggestion":     fertilizer_map[most_deficient],
        "note":           f"Soil is low in {most_deficient}. "
                          f"Deficiency: {deficiencies[most_deficient]:.1f} units below ideal.",
    }


def recommend_fertilizer(
    crop_name:  str,
    nitrogen:   float,
    phosphorus: float,
    potassium:  float,
    soil_type:  str,
) -> dict:
    """
    Returns a fertilizer recommendation based on:
    - What the crop needs (crop_fertilizer_map)
    - What the soil is missing (npk deficiency check)
    - Final decision = whichever is more critical
    """
    crop_key   = crop_name.lower().strip()
    deficiency = detect_deficiency(nitrogen, phosphorus, potassium)

    # Priority: fix deficiency first, then crop-specific
    if deficiency["most_deficient"]:
        fertilizer_name = deficiency["suggestion"]
        note            = deficiency["note"]
    else:
        fertilizer_name = CROP_FERTILIZER_MAP.get(crop_key, CROP_FERTILIZER_MAP["default"])
        note            = f"Soil is healthy. Applying crop-specific fertilizer for {crop_name}."

    fertilizer = FERTILIZERS.get(fertilizer_name, FERTILIZERS["NPK 20-20-20"])

    # Soil-type specific tip
    soil_tips = {
        "Sandy":   "Sandy soil drains fast. Apply fertilizer in small frequent doses.",
        "Loamy":   "Loamy soil retains nutrients well. Standard application works.",
        "Black":   "Black soil is naturally fertile. Reduce nitrogen dose by 20%.",
        "Red":     "Red soil is low in N and P. DAP + Urea combination recommended.",
        "Clayey":  "Clayey soil retains water. Avoid over-application. Use split doses.",
    }
    soil_note = soil_tips.get(soil_type, "Follow standard agronomic practices.")

    return {
        "crop_name":         crop_name,
        "soil_type":         soil_type,
        "fertilizer_name":   fertilizer_name,
        "description":       fertilizer["description"],
        "how_to_apply":      fertilizer["how_to_apply"] + f" {soil_note}",
        "quantity_per_acre": fertilizer["qty_per_acre"],
        "npk_suggestion":    fertilizer["npk"],
        "note":              note,
    }
