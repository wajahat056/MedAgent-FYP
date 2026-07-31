# ============================================================
# MEDAGENT WEB INTERFACE (STREAMLIT)
# ============================================================
# This is a web-based interface for MedAgent, replacing the
# terminal-only demo. It lets a user upload a PDF lab report
# and see the full pipeline output in a clean, visual layout.
#
# Includes readability scoring (Flesch-Kincaid) to objectively
# measure how much simpler the AI explanation is compared to
# the original report.
#
# Runs with: streamlit run app.py
# ============================================================

import streamlit as st
import os
import tempfile
import textstat

from agents.extraction_agent import extract_text_from_pdf, parse_lab_values
from agents.analysis_agent import analyse_results
from agents.report_writer_agent import generate_plain_english_explanation


# ------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(
    page_title="MedAgent — AI Lab Report Analyser",
    page_icon="🩺",
    layout="wide",
)


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("🩺 MedAgent")
st.markdown("### AI-Powered Plain-English Explanations of Medical Lab Reports")
st.markdown(
    "Upload a medical lab report PDF and receive a clear, plain-English "
    "explanation of the results — grounded in trusted medical sources."
)

st.divider()


# ------------------------------------------------------------
# SIDEBAR — Project Info
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### About MedAgent")
    st.markdown(
        "MedAgent is a multi-agent AI system that combines:\n"
        "- 📄 **PDF text extraction** (PyMuPDF + Tesseract OCR)\n"
        "- 🔬 **Rule-based abnormality detection** (deterministic, safe)\n"
        "- 🧠 **RAG retrieval** (ChromaDB + MedlinePlus)\n"
        "- ✍️ **Plain-English generation** (Claude API)\n"
    )
    st.markdown("---")
    st.markdown("**Ethics Protocol:** 2594 ST HSET 2026")
    st.markdown("**Researcher:** Wajahat Maroof")
    st.markdown("**Supervisor:** Prapa Rattadilok")
    st.markdown("**Module:** 6WCM0029-0509")


# ------------------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------------------
st.markdown("### 📤 Upload Your Lab Report")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Upload a Complete Blood Count (CBC), Liver Function Test (LFT), "
         "or Renal Function Test (RFT) report.",
)


# ------------------------------------------------------------
# PROCESS THE UPLOADED FILE
# ------------------------------------------------------------
if uploaded_file is not None:

    # Save the uploaded file to a temporary location so agents can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_pdf_path = tmp_file.name

    st.success(f"✅ File uploaded: **{uploaded_file.name}**")

    # Analyse button
    if st.button("🔍 Analyse Report", type="primary"):

        # -----------------
        # STEP 1: Extraction
        # -----------------
        with st.spinner("Step 1: Extracting text from PDF..."):
            text = extract_text_from_pdf(tmp_pdf_path)
            lab_values = parse_lab_values(text)

        if not lab_values:
            st.error(
                "❌ No lab values found in the PDF. "
                "Try a different report format."
            )
            st.stop()

        st.success(
            f"✅ Extracted **{len(lab_values)} lab values** from the report."
        )

        # -----------------
        # STEP 2: Analysis
        # -----------------
        with st.spinner(
            "Step 2: Analysing values against clinical reference ranges..."
        ):
            analysed = analyse_results(lab_values)

        # Split by status for a cleaner display
        abnormal = [r for r in analysed if r["status"] in ("HIGH", "LOW")]
        normal = [r for r in analysed if r["status"] == "NORMAL"]
        unknown = [r for r in analysed if r["status"] == "UNKNOWN"]

        # Show results in two side-by-side columns
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ⚠️ Abnormal Values")
            if abnormal:
                for r in abnormal:
                    status_colour = "🔴" if r["status"] == "HIGH" else "🔵"
                    st.markdown(
                        f"{status_colour} **{r['test'].title()}**: "
                        f"{r['value']} {r['unit']}  \n"
                        f"↳ Status: **{r['status']}** "
                        f"(Normal range: {r['reference_range']})"
                    )
            else:
                st.info("No abnormal values detected.")

        with col2:
            st.markdown("#### ✅ Normal Values")
            if normal:
                for r in normal:
                    st.markdown(
                        f"🟢 **{r['test'].title()}**: "
                        f"{r['value']} {r['unit']}"
                    )
            else:
                st.info("No values within the normal range.")

        # Show unknowns collapsed (only useful for debugging)
        if unknown:
            with st.expander(
                "❓ Unrecognised tests (not in reference database)"
            ):
                for r in unknown:
                    st.markdown(f"• {r['test']}: {r['value']}")

        st.divider()

        # -----------------
        # STEP 3: RAG + Report Writer
        # -----------------
        with st.spinner(
            "Step 3: Retrieving trusted medical context and generating "
            "explanation..."
        ):
            explanation = generate_plain_english_explanation(abnormal, analysed)

        # Display the AI-generated explanation
        st.markdown("### 📝 Plain-English Explanation")
        st.markdown(explanation)

        st.divider()

        # -----------------
        # STEP 4: READABILITY COMPARISON
        # -----------------
        # This section objectively measures how much simpler the AI's
        # explanation is compared to the original report, using standard
        # readability metrics (Flesch-Kincaid and Flesch Reading Ease).
        # -----------------
        st.markdown("### 📊 Readability Comparison")
        st.markdown(
            "**Objective measurement** of how much simpler the AI explanation "
            "is compared to the original report, using standard academic "
            "readability metrics."
        )

        # Calculate readability scores for both texts
        original_grade = textstat.flesch_kincaid_grade(text)
        explanation_grade = textstat.flesch_kincaid_grade(explanation)

        original_ease = textstat.flesch_reading_ease(text)
        explanation_ease = textstat.flesch_reading_ease(explanation)

        # Show side-by-side comparison in three columns
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric(
                label="📄 Original Report",
                value=f"Grade {original_grade:.1f}",
                help="Flesch-Kincaid Grade Level — the US school grade "
                     "needed to understand this text."
            )
            st.caption(f"Reading Ease: {original_ease:.1f}/100")

        with col_b:
            st.metric(
                label="✨ AI Explanation",
                value=f"Grade {explanation_grade:.1f}",
                delta=f"{explanation_grade - original_grade:.1f} grades",
                delta_color="inverse",
                help="Negative delta = the AI explanation is EASIER to read."
            )
            st.caption(f"Reading Ease: {explanation_ease:.1f}/100")

        with col_c:
            improvement = original_grade - explanation_grade
            if improvement > 0:
                st.success(
                    f"**{improvement:.1f} grade levels easier**\n\n"
                    f"The AI explanation is measurably simpler to read."
                )
            elif improvement < 0:
                st.warning(
                    f"AI explanation is {abs(improvement):.1f} grades harder. "
                    f"Consider revising the prompt."
                )
            else:
                st.info("Similar reading difficulty.")

        st.caption(
            "📚 **Flesch-Kincaid Grade Level** is a standard readability "
            "metric used in academic and educational research. Lower = easier "
            "to read. Grade 7-8 = general public; Grade 12+ = college level. "
            "**Flesch Reading Ease** ranges 0-100; higher = easier."
        )

        st.divider()

        # -----------------
        # DISCLAIMER
        # -----------------
        st.warning(
            "⚠️ **Important:** This explanation is for educational purposes "
            "only and is **not medical advice**. Please discuss all lab "
            "results with a qualified healthcare professional."
        )

    # Clean up the temp file
    os.unlink(tmp_pdf_path)

else:
    # Placeholder shown before file upload
    st.info(
        "👆 Upload a PDF lab report above to see the analysis. "
        "The system supports CBC, LFT, and RFT reports."
    )