# ============================================================
# MAIN.PY - THE PIPELINE ORCHESTRATOR
# ============================================================
# This is the ENTRY POINT of the MedAgent system.
# It is what runs when I type: python main.py test.pdf
#
# Its job is to connect all four agents together and run them
# in the right order:
#
#   Extraction Agent -> Analysis Agent -> Report Writer Agent
#
# main.py does NOT do any actual work itself - it just
# ORCHESTRATES. Each real task is handled by a dedicated agent
# file in the agents/ folder. This separation of concerns is
# what makes the system maintainable: if I want to improve
# extraction, I only touch extraction_agent.py.
# ============================================================


# -------- IMPORTS --------

# 'sys' gives me access to command-line arguments.
# When someone runs "python main.py test.pdf", the word "test.pdf"
# is stored in sys.argv - I need sys to read that.
import sys

# Import the two functions I need from the Extraction Agent.
# This is where the "from FOLDER.FILE import FUNCTION" syntax
# comes in - it says "go into agents/extraction_agent.py and
# grab these specific functions".
from agents.extraction_agent import extract_text_from_pdf, parse_lab_values

# Import functions from the Analysis Agent.
from agents.analysis_agent import analyse_results, format_analysis_summary

# Import the function from the Report Writer Agent.
from agents.report_writer_agent import generate_plain_english_explanation


# ============================================================
# FUNCTION: run_pipeline
# ============================================================
# The heart of main.py. Takes a PDF file path and runs the
# whole four-agent pipeline on it end-to-end.
# ============================================================

def run_pipeline(pdf_path):

    # STEP 0: Print a header so the user knows the system started.
    # "=" * 60 makes a horizontal line of 60 equals signs -
    # a clean visual divider in the terminal.
    # \n at the start adds a blank line for readability.
    print("\n" + "=" * 60)
    print("MEDAGENT - AI Medical Report Analyser")
    print("=" * 60)

    # f"..." is an f-string - lets me insert the pdf_path
    # variable directly into the printed message.
    print(f"Processing: {pdf_path}\n")

    # STEP 1: EXTRACTION AGENT
    # Call the Extraction Agent to read the PDF and get raw text.
    # This is the first agent in the pipeline.
    print("Step 1: Extracting text from report...")
    text = extract_text_from_pdf(pdf_path)

    # Show the user how much text was found - useful for
    # debugging if something goes wrong (e.g. "Extracted 0
    # characters" means the PDF couldn't be read).
    # len(text) counts the number of characters in the string.
    print(f"  Extracted {len(text)} characters")

    # STEP 2: Still part of extraction - parse the raw text
    # to find actual lab test values.
    print("\nStep 2: Parsing lab values...")
    lab_values = parse_lab_values(text)
    print(f"  Found {len(lab_values)} test results")

    # DEFENSIVE CHECK: If no test values were found, we have a
    # problem. Instead of crashing later, we handle it gracefully.
    # This is called a "guard clause" - an early exit that
    # protects the rest of the code.
    if not lab_values:
        print("  No lab values found - check the PDF format.")

        # Show the first 500 characters of raw text so I can
        # debug what went wrong. text[:500] takes the first
        # 500 characters using Python's slice syntax.
        print("\n--- Raw extracted text (first 500 chars) ---")
        print(text[:500])

        # 'return' exits the function early. The rest of the
        # pipeline doesn't run because there's nothing to analyse.
        return

    # STEP 3: ANALYSIS AGENT
    # Pass the extracted values to the Analysis Agent, which
    # flags each one as NORMAL, HIGH, LOW, or UNKNOWN using
    # the deterministic rule-based checker.
    print("\nStep 3: Analysing against reference ranges...")
    analysed = analyse_results(lab_values)

    # format_analysis_summary prints the results to the terminal
    # AND returns just the abnormal ones. So 'abnormal' now
    # contains only the HIGH and LOW values - which is what the
    # Report Writer Agent will focus on.
    abnormal = format_analysis_summary(analysed)

    # STEP 4: REPORT WRITER AGENT
    # Send the abnormal results (plus the full context) to the
    # Claude API to generate a plain-English explanation.
    # THIS is the only step that touches the LLM - all previous
    # steps are 100% deterministic.
    print("\nStep 4: Generating plain-English explanation via Claude API...")
    explanation = generate_plain_english_explanation(abnormal, analysed)

    # STEP 5: Print the final output - the plain-English
    # explanation that the whole pipeline was built to produce.
    print("\n" + "=" * 60)
    print("PLAIN-ENGLISH EXPLANATION")
    print("=" * 60)
    print(explanation)
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================
# This special block runs when the file is executed directly
# (e.g. "python main.py test.pdf") but NOT when it's imported
# by another file. It's a Python convention that lets a file
# be usable both as a script and as a library.
# ============================================================

if __name__ == "__main__":

    # sys.argv is a list of command-line arguments.
    # sys.argv[0] is always the script name ("main.py").
    # sys.argv[1] would be the first argument after the script name.
    #
    # If the user only typed "python main.py" without a PDF path,
    # len(sys.argv) will be 1 (just the script name).
    # We need at least 2 items (script + PDF path).
    if len(sys.argv) < 2:
        # Show the user how to run the script correctly.
        print("Usage: python main.py <path_to_pdf>")
        print("Example: python main.py data/sample_reports/test.pdf")
    else:
        # The user provided a PDF path - grab it from sys.argv[1]
        # and run the pipeline on it.
        run_pipeline(sys.argv[1])