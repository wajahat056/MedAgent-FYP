# ============================================================
# ANALYSIS AGENT
# ============================================================
# This is the SECOND agent in the MedAgent pipeline.
# It takes the extracted lab values from the Extraction Agent
# and decides whether each one is NORMAL, HIGH, LOW, or UNKNOWN.
#
# KEY DESIGN DECISION:
# This agent is DETERMINISTIC and RULE-BASED.
# I deliberately did NOT use the LLM here. The reason is safety:
# if I asked Claude "is 72 U/L abnormal for ALT?", it might
# hallucinate or say "possibly" when the answer should be
# definite. A simple rule-based comparison against known
# reference ranges guarantees the abnormality flag is always
# 100% correct. The LLM only comes in later, in the Report
# Writer Agent, and only for language generation - never for
# medical decisions.
#
# This separation of deterministic logic from LLM generation is
# a well-known principle in safety-sensitive AI systems and is
# also used in Sai et al. (2025).
# ============================================================


# -------- IMPORTS: helping Python find our other files --------

# sys is Python's system module - I use it to modify how Python
# searches for imports.
import sys

# os lets me work with file paths in a way that works on
# any operating system (Mac, Linux, Windows).
import os

# The next line is a workaround for Python's import system.
# This file lives in the 'agents/' folder, but I need to
# import from the 'data/' folder which is one level up.
# Python doesn't automatically know that, so I have to tell
# it: "look at the folder that's the parent of this file's
# parent folder" - which is the project root.
#
# Breaking it down:
#   __file__                                  = this file's location
#   os.path.abspath(__file__)                 = full path to this file
#   os.path.dirname(...)                      = its containing folder (agents/)
#   os.path.dirname(os.path.dirname(...))     = the folder above (project root)
#   sys.path.append(...)                      = add that to Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now that Python knows where to look, I can import the
# flag_abnormal function I wrote in reference_ranges.py.
# This is the function that does the actual NORMAL/HIGH/LOW
# comparison - all the medical rules live in that file.
from data.reference_ranges import flag_abnormal


# ============================================================
# FUNCTION 1: analyse_results
# ============================================================
# The main function of this agent. Takes the raw list of test
# values from the Extraction Agent and adds a "status" to each
# one, telling us whether it's NORMAL, HIGH, LOW, or UNKNOWN.
# ============================================================

def analyse_results(lab_values):
    """
    Flags each extracted lab value as NORMAL, HIGH, LOW, or UNKNOWN.
    """

    # Empty list to collect our analysed results.
    # We keep the original data but add a "status" field.
    analysed = []

    # Loop through every test the Extraction Agent found.
    for item in lab_values:

        # STEP 1: Safely get the test name and value from the item.
        # I use .get() instead of item["test"] because .get()
        # returns a default vaalue (empty string here) if the key
        # is missing, whereas item["test"] would crash the program.
        # This is defensive programming - assume the input might
        # not be perfectly formatted.
        test = item.get("test", "")
        value = item.get("value", "")

        # STEP 2: Call the rule-based checker from reference_ranges.py.
        # This returns two things:
        #   status: a string like "NORMAL", "HIGH", "LOW", or "UNKNOWN"
        #   ref:    the reference range dict for that test (or None
        #           if the test wasn't found in our dictionary)
        # Python lets me "unpack" a returned tuple into two
        # variables using this comma syntax.
        status, ref = flag_abnormal(test, value)

        # STEP 3: Build the analysed result dictionary.
        # We keep everything from the original item AND add
        # the new "status" field.
        analysed.append({
            "test": test,
            "value": value,

            # For the unit, use whatever the Extraction Agent
            # provided. If that's empty, fall back to the unit
            # from our reference range dictionary. This is what
            # the "or" operator does here - it picks the first
            # truthy value.
            "unit": item.get("unit") or (ref["unit"] if ref else ""),

            # Same trick for the reference range - use the one
            # the extraction found in the report, or build one
            # from our dictionary if we know the test.
            "reference_range": item.get("reference_range") or
                               (f"{ref['min']}-{ref['max']}" if ref else ""),

            # The new field we're adding - the status.
            "status": status,
        })

    # Return the list with statuses added to each item.
    return analysed


# ============================================================
# FUNCTION 2: get_abnormal_results
# ============================================================
# A helper function that filters the analysed list to just
# the abnormal ones. Used later by the Report Writer Agent
# so it can focus its explanation on what actually matters.
# ============================================================

def get_abnormal_results(analysed_results):
    """Return only HIGH or LOW results."""

    # This is a "list comprehension" - a compact way to say
    # "give me a new list containing every item r from
    # analysed_results where the status is HIGH or LOW".
    # Equivalent to a for-loop with an if-check, but shorter.
    return [r for r in analysed_results if r["status"] in ("HIGH", "LOW")]


# ============================================================
# FUNCTION 3: format_analysis_summary
# ============================================================
# Prints a clean, formatted summary of the analysis to the
# terminal - grouped into ABNORMAL, NORMAL, and UNRECOGNISED.
# Also returns the abnormal results for the next step.
# ============================================================

def format_analysis_summary(analysed_results):
    """Print a clean summary and return abnormal results."""

    # Print a divider line for visual clarity.
    # "\n" adds a blank line before. "=" * 60 makes a line
    # of 60 equal signs - a nice separator in terminal output.
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)

    # STEP 1: Split the results into three separate lists
    # based on their status. Same list-comprehension trick
    # as in Function 2.
    abnormal = [r for r in analysed_results if r["status"] in ("HIGH", "LOW")]
    normal   = [r for r in analysed_results if r["status"] == "NORMAL"]
    unknown  = [r for r in analysed_results if r["status"] == "UNKNOWN"]

    # STEP 2: Print the abnormal values first (most important).
    # The 'if abnormal:' check means "only print this section
    # if the list actually contains something". An empty list
    # is falsy in Python.
    if abnormal:
        # len() gives the count. f-strings ({variable}) let me
        # insert values into the printed text.
        print(f"\n[!] ABNORMAL VALUES ({len(abnormal)}):")
        for r in abnormal:
            # Print each abnormal test with its value, unit,
            # status, and normal range.
            print(f"    {r['test']}: {r['value']} {r['unit']} "
                  f"[{r['status']}]  (normal: {r['reference_range']})")

    # STEP 3: Print the normal values (less critical but useful).
    if normal:
        print(f"\n[OK] NORMAL VALUES ({len(normal)}):")
        for r in normal:
            print(f"    {r['test']}: {r['value']} {r['unit']}")

    # STEP 4: Print anything the Analysis Agent didn't recognise.
    # This is useful for debugging - if a test appears here,
    # it means we need to add it to reference_ranges.py.
    if unknown:
        print(f"\n[?] UNRECOGNISED ({len(unknown)}):")
        for r in unknown:
            print(f"    {r['test']}: {r['value']}")

    # Closing divider.
    print("=" * 60)

    # Return the abnormal list for the next agent to use.
    return abnormal