"""
Error Explainer module for DevFlow AI.
Accepts raw stack traces, SQL errors, or tracebacks and returns a plain-English
explanation plus step-by-step debugging suggestions. Reuses the Groq/OpenAI
client configured in `ai.py`.
"""
from typing import Optional
from ai import get_openai_client


def explain_error_text(trace_text: str) -> str:
    """Return an AI-generated explanation and debugging steps for the provided error text.

    Args:
        trace_text: Raw stack trace, SQL error, or exception text pasted by the user.

    Returns:
        A developer-friendly explanation and suggested next steps.
    """
    client = get_openai_client()
    if client is None:
        return "Groq API key is not configured or the OpenAI SDK is unavailable"

    system_prompt = (
        "You are DevFlow AI, an expert developer assistant.\n"
        "Given a raw stack trace, SQL error, or Python traceback, produce:\n"
        "1) A concise, plain-English summary of what the error means.\n"
        "2) Likely root causes (short bullets).\n"
        "3) Concrete, prioritized debugging steps a developer can take immediately.\n"
        "4) If relevant, suggest code-level changes or SQL fixes.\n"
        "Be specific, cite filenames/lines if visible in the trace, and avoid vague statements.\n"
    )

    user_prompt = f"Error text:\n\n{trace_text}\n\nRespond with sections labeled: Summary, Possible Causes, Debug Steps, Suggested Fixes."

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        return response.choices[0].message.content or ""

    except Exception as exc:
        return f"Error calling Groq API: {exc}"


if __name__ == "__main__":
    sample = "Traceback (most recent call last):\n  File \"app.py\", line 120, in <module>\n    result = execute_query(sql)\nsqlite3.OperationalError: no such column: total_revenue"
    print(explain_error_text(sample))
