import anthropic
import os
from dotenv import load_dotenv

from agents.rag_agent import retrieve_context_for_all_abnormals

load_dotenv()


LENGTH_MODES = {
    "quick": {
        "label": "Quick Overview (30 seconds)",
        "max_tokens": 300,
        "instructions": """Write a VERY BRIEF explanation (60-80 words maximum):
1. One sentence overall summary (is everything fine or are there concerns?).
2. List each ABNORMAL value in a single short line: "TestName is HIGH/LOW - what this may mean in one plain-English phrase."
3. End with one sentence reminding them to discuss with a doctor.

Be extremely concise. No introductions. No extra paragraphs. Just the essentials."""
    },
    "standard": {
        "label": "Standard Explanation (2 minutes)",
        "max_tokens": 700,
        "instructions": """Write a clear, friendly, plain-English explanation (150-250 words):
1. Start with a brief 2-3 sentence overall summary.
2. For each ABNORMAL value: explain simply what the test measures and what a high/low result may generally indicate.
3. End with a clear reminder that these results must be discussed with a doctor, and this is educational only.

Use simple everyday language. Do not diagnose. Do not recommend treatments."""
    },
    "detailed": {
        "label": "Detailed Explanation (5 minutes)",
        "max_tokens": 1500,
        "instructions": """Write a thorough, friendly, plain-English explanation (400-600 words):
1. Start with a 3-4 sentence overall summary of how the results look.
2. For each ABNORMAL value: explain what the test measures, what a high/low result may generally indicate, whether it appears mildly or significantly out of range, and what factors could contribute (using the TRUSTED MEDICAL CONTEXT above).
3. For NORMAL values that are relevant to any abnormal values, briefly acknowledge them and what they show.
4. Include a paragraph on general next steps (types of questions to ask a doctor, lifestyle factors to consider).
5. End with a strong reminder that these results must be discussed with a doctor, and this explanation is educational only - not medical advice.

Use simple everyday language throughout. Explain any technical terms. Do not diagnose. Do not recommend specific treatments."""
    }
}


def generate_plain_english_explanation(abnormal_results, all_results, mode="standard"):
    if mode not in LENGTH_MODES:
        mode = "standard"

    mode_config = LENGTH_MODES[mode]

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print(f"  Retrieving medical context from knowledge base... (mode: {mode})")
    context_map = retrieve_context_for_all_abnormals(abnormal_results)

    context_text = ""
    if context_map:
        context_text = "TRUSTED MEDICAL CONTEXT (from MedlinePlus):\n"
        for test, context in context_map.items():
            context_text += f"\n[About {test}]:\n{context}\n"
        print(f"  Retrieved context for {len(context_map)} test(s)")
    else:
        print("  No context retrieved (no abnormals or KB empty)")

    abnormal_text = ""
    if abnormal_results:
        abnormal_text = "ABNORMAL VALUES:\n"
        for r in abnormal_results:
            abnormal_text += (f"- {r['test']}: {r['value']} {r['unit']} "
                              f"({r['status']}) | Normal range: {r['reference_range']}\n")
    else:
        abnormal_text = "No abnormal values were found.\n"

    normal_text = "NORMAL VALUES:\n"
    for r in all_results:
        if r["status"] == "NORMAL":
            normal_text += f"- {r['test']}: {r['value']} {r['unit']}\n"

    prompt = f"""You are a medical report explainer helping a patient with no medical background understand their blood test results.

Here are their results:

{abnormal_text}
{normal_text}

{context_text}

{mode_config["instructions"]}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=mode_config["max_tokens"],
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
