# ============================================================
# REPORT WRITER AGENT (with RAG)
# ============================================================
# This is the fourth agent in the MedAgent pipeline. It uses
# the Claude API to turn analysed lab results into a plain-
# English explanation, grounded in retrieved MedlinePlus
# content via the RAG Agent.
#
# The LLM still only handles LANGUAGE GENERATION - it never
# makes medical decisions. Those were already made by the
# deterministic Analysis Agent. RAG just gives the LLM better
# raw material to write clearer, more accurate explanations.
# ============================================================

import anthropic
import os
from dotenv import load_dotenv

# Import the RAG agent - this is the new dependency
from agents.rag_agent import retrieve_context_for_all_abnormals

load_dotenv()


def generate_plain_english_explanation(abnormal_results, all_results):
    """
    Uses the Claude API to generate a plain-English explanation.
    Now grounded in retrieved MedlinePlus content via RAG.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Retrieve trusted context via RAG
    print("  Retrieving medical context from knowledge base...")
    context_map = retrieve_context_for_all_abnormals(abnormal_results)

    # Build the trusted-context section of the prompt
    context_text = ""
    if context_map:
        context_text = "TRUSTED MEDICAL CONTEXT (from MedlinePlus):\n"
        for test, context in context_map.items():
            context_text += f"\n[About {test}]:\n{context}\n"
        print(f"  Retrieved context for {len(context_map)} test(s)")
    else:
        print("  No context retrieved (no abnormals or KB empty)")

    # Build the abnormal values summary
    abnormal_text = ""
    if abnormal_results:
        abnormal_text = "ABNORMAL VALUES:\n"
        for r in abnormal_results:
            abnormal_text += (f"- {r['test']}: {r['value']} {r['unit']} "
                              f"({r['status']}) | Normal range: {r['reference_range']}\n")
    else:
        abnormal_text = "No abnormal values were found.\n"

    # Build the normal values summary
    normal_text = "NORMAL VALUES:\n"
    for r in all_results:
        if r["status"] == "NORMAL":
            normal_text += f"- {r['test']}: {r['value']} {r['unit']}\n"

    # Build the prompt with retrieved context
    prompt = f"""You are a medical report explainer helping a patient with no medical background understand their blood test results.

Here are their results:

{abnormal_text}
{normal_text}

{context_text}

Write a clear, friendly, plain-English explanation:
1. Start with a brief 2-3 sentence overall summary of how the results look.
2. For each ABNORMAL value: explain simply what the test measures, what a high/low result may generally indicate, and whether it appears mildly or significantly out of range. Base your explanation on the TRUSTED MEDICAL CONTEXT above where available.
3. End with a clear reminder that these results must be discussed with a doctor, and this explanation is educational only — not medical advice.

Use simple everyday language. Do not diagnose. Do not recommend treatments. Write in plain paragraphs."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text