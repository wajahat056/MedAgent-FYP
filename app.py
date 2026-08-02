# ============================================================
# MEDAGENT WEB INTERFACE (STREAMLIT)
# ============================================================
# Web interface for MedAgent with:
#   - Three explanation length modes (Quick/Standard/Detailed)
#   - English/Urdu language support
#   - Flesch-Kincaid readability comparison
#   - Sample report quick-select for easy demoing
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
st.markdown(
    "#### AI-Powered Plain-English Explanations of Medical Lab Reports"
)
st.markdown(
    "Upload a medical lab report PDF and receive a clear explanation "
    "of the results — available in **English or Urdu**, and grounded "
    "in trusted medical sources."
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
        "- 🌐 **Bilingual output** (English / Urdu)\n"
    )
    st.markdown("---")
    st.markdown("**Ethics Protocol:** 2594 ST HSET 2026")
    st.markdown("**Researcher:** Wajahat Maroof")
    st.markdown("**Supervisor:** Prapa Rattadilok")
    st.markdown("**Module:** 6WCM0029-0509")


# ------------------------------------------------------------
# SAMPLE REPORT QUICK-SELECT
# ------------------------------------------------------------
st.markdown("### 📤 Choose a Lab Report")

tab1, tab2 = st.tabs(["📁 Upload Your Own", "📋 Try a Sample Report"])

uploaded_file = None
sample_choice = None

with tab1:
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a Complete Blood Count (CBC), Liver Function Test (LFT), "
             "or Renal Function Test (RFT) report.",
    )

with tab2:
    st.markdown("No PDF handy? Try one of these sample reports:")
    sample_options = {
        "🩸 Sample CBC (Blood Count)": "data/sample_reports/sample_cbc.pdf",
        "🧪 Sample LFT (Liver Function)": "data/sample_reports/sample_lft.pdf",
        "🫘 Sample RFT (Kidney Function)": "data/sample_reports/sample_rft.pdf",
    }
    sample_choice = st.radio(
        "Select a sample:",
        options=["None"] + list(sample_options.keys()),
        index=0,
    )

# Determine which file path to actually use
active_pdf_path = None
active_filename = None

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        active_pdf_path = tmp_file.name
        active_filename = uploaded_file.name

elif sample_choice and sample_choice != "None":
    sample_path = sample_options[sample_choice]
    if os.path.exists(sample_path):
        active_pdf_path = sample_path
        active_filename = sample_choice
    else:
        st.error(f"⚠️ Sample file not found at {sample_path}")


# ------------------------------------------------------------
# PROCESS THE SELECTED FILE
# ------------------------------------------------------------
if active_pdf_path is not None:

    st.success(f"✅ Ready to analyse: **{active_filename}**")

    st.divider()

    # -----------------
    # SETTINGS ROW: Mode + Language side by side
    # -----------------
    st.markdown("### ⚙️ Explanation Settings")

    settings_col1, settings_col2 = st.columns(2)

    with settings_col1:
        st.markdown("**🎯 Explanation Length**")
        mode_options = {
            "⚡ Quick (30 sec)": "quick",
            "📋 Standard (2 min)": "standard",
            "📚 Detailed (5 min)": "detailed",
        }
        selected_mode_label = st.radio(
            "Length:",
            options=list(mode_options.keys()),
            index=1,
            label_visibility="collapsed",
        )
        selected_mode = mode_options[selected_mode_label]

    with settings_col2:
        st.markdown("**🌐 Language**")
        language_options = {
            "🇬🇧 English": "english",
            "🇵🇰 اردو (Urdu)": "urdu",
        }
        selected_language_label = st.radio(
            "Language:",
            options=list(language_options.keys()),
            index=0,
            label_visibility="collapsed",
        )
        selected_language = language_options[selected_language_label]

    st.divider()

    # Analyse button
    if st.button("🔍 Analyse Report", type="primary", use_container_width=True):

        # -----------------
        # STEP 1: Extraction
        # -----------------
        with st.spinner("Step 1/3 — Extracting text from PDF..."):
            text = extract_text_from_pdf(active_pdf_path)
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
        with st.spinner("Step 2/3 — Analysing against clinical reference ranges..."):
            analysed = analyse_results(lab_values)

        abnormal = [r for r in analysed if r["status"] in ("HIGH", "LOW")]
        normal = [r for r in analysed if r["status"] == "NORMAL"]
        unknown = [r for r in analysed if r["status"] == "UNKNOWN"]

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
        mode_display = selected_mode_label.split(" (")[0]
        lang_display = selected_language_label

        with st.spinner(
            f"Step 3/3 — Generating {mode_display.lower()} explanation "
            f"in {lang_display}..."
        ):
            explanation = generate_plain_english_explanation(
                abnormal,
                analysed,
                mode=selected_mode,
                language=selected_language,
            )

        st.markdown(
            f"### 📝 Explanation — {mode_display} · {lang_display}"
        )

        # Right-align text box for Urdu (RTL script)
        if selected_language == "urdu":
            st.markdown(
                f'<div dir="rtl" style="text-align: right; '
                f'font-size: 1.05rem; line-height: 2;">{explanation}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(explanation)

        st.divider()

        # -----------------
        # STEP 4: READABILITY COMPARISON
        # -----------------
        # Note: readability metrics (Flesch-Kincaid) are English-only
        # measures, so we only show this for English output.
        # -----------------
        if selected_language == "english":
            st.markdown("### 📊 Readability Comparison")
            st.markdown(
                "**Objective measurement** of how much simpler the AI "
                "explanation is compared to the original report."
            )

            original_grade = textstat.flesch_kincaid_grade(text)
            explanation_grade = textstat.flesch_kincaid_grade(explanation)
            original_ease = textstat.flesch_reading_ease(text)
            explanation_ease = textstat.flesch_reading_ease(explanation)

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.metric(
                    label="📄 Original Report",
                    value=f"Grade {original_grade:.1f}",
                    help="Flesch-Kincaid Grade Level."
                )
                st.caption(f"Reading Ease: {original_ease:.1f}/100")

            with col_b:
                st.metric(
                    label="✨ AI Explanation",
                    value=f"Grade {explanation_grade:.1f}",
                    delta=f"{explanation_grade - original_grade:.1f} grades",
                    delta_color="inverse",
                )
                st.caption(f"Reading Ease: {explanation_ease:.1f}/100")

            with col_c:
                improvement = original_grade - explanation_grade
                if improvement > 0:
                    st.success(
                        f"**{improvement:.1f} grade levels easier**"
                    )
                elif improvement < 0:
                    st.warning(
                        f"{abs(improvement):.1f} grades harder"
                    )
                else:
                    st.info("Similar difficulty")

            st.caption(
                "📚 Flesch-Kincaid measures reading difficulty. "
                "Lower grade = easier to read."
            )
        else:
            st.info(
                "📊 Readability metrics (Flesch-Kincaid) are calibrated "
                "for English text only and are not shown for Urdu output."
            )

        st.divider()

        # -----------------
        # DISCLAIMER
        # -----------------
        if selected_language == "urdu":
            st.warning(
                "⚠️ **اہم نوٹ:** یہ وضاحت صرف تعلیمی مقاصد کے لیے ہے اور "
                "طبی مشورہ نہیں ہے۔ براہ کرم اپنے تمام لیب رزلٹس کسی "
                "مستند ڈاکٹر سے ضرور شیئر کریں۔"
            )
        else:
            st.warning(
                "⚠️ **Important:** This explanation is for educational "
                "purposes only and is **not medical advice**. Please "
                "discuss all lab results with a qualified healthcare "
                "professional."
            )

    # Clean up temp file if it was an upload
    if uploaded_file is not None and os.path.exists(active_pdf_path):
        os.unlink(active_pdf_path)

else:
    st.info(
        "👆 Upload a PDF lab report, or try a sample report above, "
        "to see the analysis."
    )