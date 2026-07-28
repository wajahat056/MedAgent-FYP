# ============================================================
# REFERENCE RANGES DICTIONARY
# ============================================================
# This file stores what "normal" looks like for common blood tests.
# The Analysis Agent uses this to decide if a lab value is
# NORMAL, HIGH, or LOW.
#
# I hardcoded the ranges here instead of calling an external
# medical API because:
#   1. It's faster (no internet call needed for every check)
#   2. It's deterministic (same input = same output every time)
#   3. The system works fully offline
# ============================================================


# This is a dictionary. Each KEY is a test name (in lowercase).
# Each VALUE is another dictionary containing the min value,
# max value, and the unit for that test.
REFERENCE_RANGES = {

    # -------- Complete Blood Count (CBC) tests --------
    # Different labs write "haemoglobin" in different ways
    # (haemoglobin, hemoglobin, hgb) so I include all of them
    # pointing to the same range - this way I catch every variant
    "haemoglobin":        {"min": 12.0, "max": 17.5, "unit": "g/dL"},
    "hemoglobin":         {"min": 12.0, "max": 17.5, "unit": "g/dL"},
    "hgb":                {"min": 12.0, "max": 17.5, "unit": "g/dL"},

    # White Blood Cell count - immune system indicator
    "wbc":                {"min": 4.0,  "max": 11.0,  "unit": "10^9/L"},
    "white blood cells":  {"min": 4.0,  "max": 11.0,  "unit": "10^9/L"},
    "total leucocyte count": {"min": 4.0, "max": 11.0, "unit": "10^9/L"},

    # Red Blood Cell count - oxygen carrying capacity
    "rbc":                {"min": 3.8,  "max": 5.8,   "unit": "10^12/L"},
    "red blood cells":    {"min": 3.8,  "max": 5.8,   "unit": "10^12/L"},

    # Platelets - blood clotting cells
    "platelets":          {"min": 150,  "max": 400,   "unit": "10^9/L"},
    "platelet count":     {"min": 150,  "max": 400,   "unit": "10^9/L"},
    "plt":                {"min": 150,  "max": 400,   "unit": "10^9/L"},

    # Haematocrit - percentage of blood that is red cells
    "haematocrit":        {"min": 36.0, "max": 52.0,  "unit": "%"},
    "hematocrit":         {"min": 36.0, "max": 52.0,  "unit": "%"},
    "hct":                {"min": 36.0, "max": 52.0,  "unit": "%"},

    # Additional CBC values
    "mcv":                {"min": 80,   "max": 100,   "unit": "fL"},
    "mch":                {"min": 27,   "max": 33,    "unit": "pg"},
    "mchc":               {"min": 32,   "max": 36,    "unit": "g/dL"},

    # -------- Liver Function Test (LFT) --------
    # ALT (also called SGPT) - liver damage marker
    "alt":                {"min": 7,    "max": 56,    "unit": "U/L"},
    "sgpt":               {"min": 7,    "max": 56,    "unit": "U/L"},
    "alanine aminotransferase": {"min": 7, "max": 56, "unit": "U/L"},

    # AST (also called SGOT) - another liver damage marker
    "ast":                {"min": 10,   "max": 40,    "unit": "U/L"},
    "sgot":               {"min": 10,   "max": 40,    "unit": "U/L"},
    "aspartate aminotransferase": {"min": 10, "max": 40, "unit": "U/L"},

    # Other liver markers
    "alp":                {"min": 44,   "max": 147,   "unit": "U/L"},
    "alkaline phosphatase": {"min": 44, "max": 147,   "unit": "U/L"},
    "bilirubin":          {"min": 0.2,  "max": 1.2,   "unit": "mg/dL"},
    "total bilirubin":    {"min": 0.2,  "max": 1.2,   "unit": "mg/dL"},
    "albumin":            {"min": 3.5,  "max": 5.0,   "unit": "g/dL"},

    # -------- Renal Function Test (RFT) - kidney function --------
    "creatinine":         {"min": 0.6,  "max": 1.2,   "unit": "mg/dL"},
    "serum creatinine":   {"min": 0.6,  "max": 1.2,   "unit": "mg/dL"},
    "urea":               {"min": 15,   "max": 45,    "unit": "mg/dL"},
    "blood urea":         {"min": 15,   "max": 45,    "unit": "mg/dL"},
    "bun":                {"min": 7,    "max": 20,    "unit": "mg/dL"},
    "sodium":             {"min": 136,  "max": 145,   "unit": "mmol/L"},
    "potassium":          {"min": 3.5,  "max": 5.0,   "unit": "mmol/L"},
    "chloride":           {"min": 98,   "max": 107,   "unit": "mmol/L"},

    # -------- Blood Sugar --------
    "glucose":            {"min": 70,   "max": 100,   "unit": "mg/dL"},
    "fasting glucose":    {"min": 70,   "max": 100,   "unit": "mg/dL"},
    "fasting blood sugar": {"min": 70,  "max": 100,   "unit": "mg/dL"},
    "random blood sugar": {"min": 70,   "max": 140,   "unit": "mg/dL"},
    "hba1c":              {"min": 4.0,  "max": 5.6,   "unit": "%"},

    # -------- Thyroid Tests --------
    "tsh":                {"min": 0.4,  "max": 4.0,   "unit": "mIU/L"},
    "t3":                 {"min": 80,   "max": 200,   "unit": "ng/dL"},
    "t4":                 {"min": 5.0,  "max": 12.0,  "unit": "ug/dL"},

    # -------- Lipid Profile --------
    "cholesterol":        {"min": 0,    "max": 200,   "unit": "mg/dL"},
    "total cholesterol":  {"min": 0,    "max": 200,   "unit": "mg/dL"},
    "hdl":                {"min": 40,   "max": 999,   "unit": "mg/dL"},
    "ldl":                {"min": 0,    "max": 100,   "unit": "mg/dL"},
    "triglycerides":      {"min": 0,    "max": 150,   "unit": "mg/dL"},
}


# ============================================================
# FLAG_ABNORMAL FUNCTION
# ============================================================
# This is the main function of the file. It takes a test name
# (like "haemoglobin") and a value (like 11.2), then tells us
# whether that value is NORMAL, HIGH, LOW, or UNKNOWN.
# ============================================================

def flag_abnormal(test_name, value):
    """Check if a lab value is NORMAL, LOW, or HIGH against reference ranges."""

    # 'try' means: attempt this code, but if anything goes wrong,
    # jump to the 'except' block instead of crashing the program
    try:
        # STEP 1: Clean up the test name so we can look it up.
        # .lower() converts to lowercase (so "ALT" matches "alt")
        # .strip() removes any accidental spaces at the start/end
        key = test_name.lower().strip()

        # STEP 2: Convert the value to a proper number (float).
        # str(value) makes sure it's a string first (in case a
        # number was passed). .replace(",", "") removes commas
        # (some reports write "1,200" instead of "1200")
        # float(...) converts the cleaned string to a decimal number
        val = float(str(value).replace(",", ""))

        # STEP 3: Look up the test in our reference dictionary.
        # If the test name exists as a key in the dictionary...
        if key in REFERENCE_RANGES:
            # ...get the min/max/unit info for that test
            ref = REFERENCE_RANGES[key]

            # STEP 4: Compare the value against the normal range.

            # If the value is BELOW the minimum = LOW
            if val < ref["min"]:
                return "LOW", ref

            # If the value is ABOVE the maximum = HIGH
            elif val > ref["max"]:
                return "HIGH", ref

            # If the value is between min and max = NORMAL
            else:
                return "NORMAL", ref

        # If the test name is NOT in our dictionary (e.g. an
        # obscure test we don't have data for), return UNKNOWN
        return "UNKNOWN", None

    # If anything went wrong above (e.g. the value wasn't a number),
    # return UNKNOWN safely instead of crashing
    except (ValueError, TypeError):
        return "UNKNOWN", None