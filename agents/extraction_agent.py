# ============================================================
# EXTRACTION AGENT
# ============================================================
# This is the FIRST agent in the MedAgent pipeline.
# Its job is to take an uploaded PDF report and turn it into
# structured lab data (test names + values + reference ranges).
#
# It works in two stages:
#   Stage 1: read the raw text out of the PDF file
#   Stage 2: parse that raw text to find lab test results
# ============================================================


# -------- IMPORTS: bringing in the tools I need --------

# fitz is the internal name for PyMuPDF  it opens PDF files
# and reads their contents. Chosen because it's fast and handles
# complex layouts better than alternatives like PyPDF2.
import fitz

# pytesseract is a Python wrapper for Tesseract, the standard
# open-source OCR engine. OCR = Optical Character Recognition,
# which means "reading text from images pixel by pixel".
import pytesseract

# PIL (Pillow) is the standard Python image library.
# I need this to convert PDF pages into images before OCR.
from PIL import Image

# io lets me handle raw byte data in memory instead of
# writing temporary files to disk (faster and cleaner).
import io

# re is Python's regular expressions library, used for
# pattern-matching numbers inside text.
import re


# ============================================================
# FUNCTION 1: extract_text_from_pdf
# ============================================================
# Takes a path to a PDF file and returns all the text as one
# big string. Uses direct extraction first, OCR as fallback.
# ============================================================

def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a PDF file.
    Tries direct text extraction first; falls back to OCR for scanned pages.
    """

    # STEP 1: Open the PDF file. 'doc' is now an object
    # representing the whole document with all its pages.
    doc = fitz.open(pdf_path)

    # STEP 2: Create an empty string to build up all the text.
    # I'll add each page's text to this as I go.
    full_text = ""

    # STEP 3: Loop through every page in the PDF.
    # len(doc) gives the total page count.
    # range() creates the numbers 0, 1, 2... for the loop.
    for page_num in range(len(doc)):

        # Get the actual page object for this page number
        page = doc[page_num]

        # STEP 4: Try direct text extraction first.
        # get_text() pulls text directly if the PDF has real,
        # selectable text (as opposed to being a scanned image).
        # This is FAST and 100% ACCURATE when it works.
        text = page.get_text()

        # STEP 5: Check if direct extraction failed.
        # If the page had very little text (< 50 characters),
        # it's probably a scanned image with no digital text.
        # In that case, fall back to OCR.
        if len(text.strip()) < 50:
            # Tell the user we're using OCR (helps with debugging)
            print(f"  Page {page_num + 1}: low text detected, using OCR...")

            # Convert the PDF page into a high-resolution image.
            # dpi=300 means 300 dots per inch - higher DPI gives
            # better OCR accuracy but takes longer to process.
            pix = page.get_pixmap(dpi=300)

            # Convert the image data into a format PIL can read.
            # BytesIO lets me treat the image bytes as a "file"
            # in memory (no need to save to disk).
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            # Run Tesseract OCR on the image - this converts
            # the pixels of text into actual character data.
            text = pytesseract.image_to_string(img)

        # STEP 6: Add this page's text to our running total,
        # with a newline before it to keep pages separated.
        full_text += f"\n{text}"

    # STEP 7: Close the PDF - releases memory. Important for
    # long-running programs. Always close what you open.
    doc.close()

    # STEP 8: Return all the extracted text as one string.
    return full_text


# ============================================================
# FUNCTION 2: parse_lab_values
# ============================================================
# Takes the raw text from Function 1 and finds the lab test
# results inside it. Returns a list of dictionaries, one per
# test found.
# ============================================================

def parse_lab_values(text):
    """
    Parse extracted text to find lab test results.
    Returns list of dicts: {test, value, unit, reference_range}
    """

    # An empty list to collect all the tests we find.
    # Each item will be a dict like {"test": "haemoglobin", "value": "11.2", ...}
    results = []

    # A 'set' is like a list but with no duplicates. I use it to
    # track which tests I've already found, so I don't accidentally
    # extract the same test twice if it appears multiple times.
    seen_tests = set()

    # STEP 1: Define the list of test names we know how to
    # recognise. This is the "vocabulary" of the extractor.
    # I only look for these specific words to avoid picking up
    # random numbers from unrelated parts of the report
    # (like patient ID, phone number, dates, etc.)
    known_tests = [
        "haemoglobin", "hemoglobin", "hgb", "wbc", "white blood cells",
        "total leucocyte count", "rbc", "red blood cells", "platelets",
        "platelet count", "plt", "haematocrit", "hematocrit", "hct",
        "mcv", "mch", "mchc", "alt", "sgpt", "ast", "sgot", "alp",
        "alkaline phosphatase", "bilirubin", "total bilirubin", "albumin",
        "creatinine", "serum creatinine", "urea", "blood urea", "bun",
        "sodium", "potassium", "chloride", "glucose", "fasting glucose",
        "fasting blood sugar", "random blood sugar", "hba1c", "tsh",
        "t3", "t4", "cholesterol", "total cholesterol", "hdl", "ldl",
        "triglycerides",
    ]

    # STEP 2: Split the big text blob into individual lines.
    # Lab reports are usually formatted one test per line, so
    # processing line by line makes sense.
    lines = text.split("\n")

    # STEP 3: Go through each line of the report.
    for line in lines:

        # Make the line lowercase (so "ALT" matches "alt") and
        # remove any leading/trailing spaces.
        line_lower = line.lower().strip()

        # If the line is empty after cleaning, skip it and move
        # to the next line. 'continue' means "skip the rest of
        # this loop iteration and go to the next one".
        if not line_lower:
            continue

        # STEP 4: For each line, check if any of our known
        # test names appear in it.
        for test in known_tests:

            # Two conditions must be true:
            # 1. The test name is somewhere in this line
            # 2. We haven't already extracted this test earlier
            if test in line_lower and test not in seen_tests:

                # STEP 5: Split the line at the test name and keep
                # only the part AFTER the test name. The number
                # 1 as the second argument means "only split
                # once", so we get exactly two pieces.
                # Example: "haemoglobin 11.2 12.0-17.5"
                #          split at "haemoglobin" gives:
                #          ["", " 11.2 12.0-17.5"]
                # We take [1] which is " 11.2 12.0-17.5"
                after_test = line_lower.split(test, 1)[1]

                # STEP 6: Extract all numbers from that text.
                # The regex r'\d+\.?\d*' means:
                #   \d+   = one or more digits
                #   \.?   = an optional dot (for decimals)
                #   \d*   = zero or more digits after the dot
                # This matches things like "11.2", "150", "0.9"
                # findall returns a list of every match.
                numbers = re.findall(r'\d+\.?\d*', after_test)

                # STEP 7: If we found at least one number...
                if numbers:
                    # Remember we've seen this test so we don't
                    # extract it again from another line.
                    seen_tests.add(test)

                    # Add the result to our list as a dictionary.
                    # numbers[0] is the actual test value.
                    # If there are 3+ numbers, numbers[1] and
                    # numbers[2] are the min-max reference range.
                    results.append({
                        "test": test,
                        "value": numbers[0],
                        "unit": "",
                        "reference_range": f"{numbers[1]}-{numbers[2]}" if len(numbers) >= 3 else ""
                    })

                # 'break' exits the inner loop - we found a
                # match for this line, no need to check the
                # other test names against the same line.
                break

    # STEP 8: Return the full list of extracted tests.
    return results