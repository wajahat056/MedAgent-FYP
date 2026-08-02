import sys
from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, END

from agents.extraction_agent import extract_text_from_pdf, parse_lab_values
from agents.analysis_agent import analyse_results, format_analysis_summary
from agents.report_writer_agent import generate_plain_english_explanation


class MedAgentState(TypedDict):
    pdf_path: str
    raw_text: str
    lab_values: List[Dict]
    analysed_results: List[Dict]
    abnormal_results: List[Dict]
    explanation: Optional[str]
    mode: str


def extraction_node(state: MedAgentState) -> MedAgentState:
    print("\n[NODE] Extraction Agent")
    print("-" * 60)

    pdf_path = state["pdf_path"]
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"  Extracted {len(raw_text)} characters")

    lab_values = parse_lab_values(raw_text)
    print(f"  Found {len(lab_values)} lab values")

    state["raw_text"] = raw_text
    state["lab_values"] = lab_values

    return state


def analysis_node(state: MedAgentState) -> MedAgentState:
    print("\n[NODE] Analysis Agent")
    print("-" * 60)

    analysed = analyse_results(state["lab_values"])
    abnormal = format_analysis_summary(analysed)

    state["analysed_results"] = analysed
    state["abnormal_results"] = abnormal

    return state


def report_writer_node(state: MedAgentState) -> MedAgentState:
    print("\n[NODE] Report Writer Agent (with RAG)")
    print("-" * 60)

    explanation = generate_plain_english_explanation(
        state["abnormal_results"],
        state["analysed_results"],
        mode=state.get("mode", "standard")
    )

    state["explanation"] = explanation

    return state


def no_abnormal_node(state: MedAgentState) -> MedAgentState:
    print("\n[NODE] No Abnormals - Skipping Report Writer")
    print("-" * 60)
    print("  All values within normal reference ranges.")
    print("  Saved one Claude API call.")

    state["explanation"] = (
        "All extracted values are within normal reference ranges. "
        "This is educational information only - please still discuss "
        "your results with a qualified healthcare professional."
    )

    return state


def route_after_analysis(state: MedAgentState) -> str:
    if state["abnormal_results"]:
        print(f"\n[ROUTER] {len(state['abnormal_results'])} abnormal value(s) found -> Report Writer")
        return "report_writer"
    else:
        print("\n[ROUTER] No abnormal values -> skip Report Writer")
        return "no_abnormal"


def build_graph():
    graph = StateGraph(MedAgentState)

    graph.add_node("extract", extraction_node)
    graph.add_node("analyse", analysis_node)
    graph.add_node("report_writer", report_writer_node)
    graph.add_node("no_abnormal", no_abnormal_node)

    graph.set_entry_point("extract")

    graph.add_edge("extract", "analyse")

    graph.add_conditional_edges(
        "analyse",
        route_after_analysis,
        {
            "report_writer": "report_writer",
            "no_abnormal": "no_abnormal",
        }
    )

    graph.add_edge("report_writer", END)
    graph.add_edge("no_abnormal", END)

    return graph.compile()


def run_pipeline(pdf_path: str, mode: str = "standard"):
    print("\n" + "=" * 60)
    print("MEDAGENT - LANGGRAPH ORCHESTRATION")
    print("=" * 60)
    print(f"Processing: {pdf_path}")
    print(f"Explanation mode: {mode}")

    graph = build_graph()

    initial_state: MedAgentState = {
        "pdf_path": pdf_path,
        "raw_text": "",
        "lab_values": [],
        "analysed_results": [],
        "abnormal_results": [],
        "explanation": None,
        "mode": mode,
    }

    final_state = graph.invoke(initial_state)

    print("\n" + "=" * 60)
    print("PLAIN-ENGLISH EXPLANATION")
    print("=" * 60)
    print(final_state["explanation"])
    print("=" * 60)

    return final_state


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main_langgraph.py <path_to_pdf> [mode]")
        print("Modes: quick, standard, detailed (default: standard)")
        print("Example: python main_langgraph.py data/sample_reports/sample_cbc.pdf standard")
    else:
        pdf_path = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) >= 3 else "standard"
        run_pipeline(pdf_path, mode)
