"""
AI/LLM Module
Handles Groq API integration for natural language to SQL conversion
"""

from dotenv import load_dotenv
import os
from schema import get_schema_for_prompt
from typing import Tuple, List, Optional
import json

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# Load environment variables from .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH, override=True)


def get_groq_api_key() -> Optional[str]:
    """Retrieve Groq API key from environment or Streamlit secrets."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            pass
    return api_key


def get_configured_model() -> str:
    """Retrieve preferred model name from environment or secrets."""
    model = os.getenv("GROQ_MODEL")
    if not model:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_MODEL" in st.secrets:
                model = st.secrets["GROQ_MODEL"]
        except Exception:
            pass
    # If configured model is decommissioned, override to active Groq model
    if model in ("llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-70b"):
        model = "openai/gpt-oss-120b"
    return model or "openai/gpt-oss-120b"


def get_candidate_models() -> List[str]:
    """Return ordered list of models to try in case of 404 model_not_found."""
    configured = get_configured_model()
    candidates = [
        configured,
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "llama-3.1-8b-instant",
    ]
    seen = set()
    ordered = []
    for m in candidates:
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered


def get_openai_client() -> Optional[OpenAI]:
    """Create an OpenAI-compatible client configured for Groq.

    Returns:
        OpenAI | None: Configured client or None if the SDK/key is missing.
    """
    api_key = get_groq_api_key()

    if not api_key or OpenAI is None:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def create_chat_completion(client: OpenAI, **kwargs):
    """Execute chat completion with automatic fallback if the requested model is unavailable (404)."""
    models_to_try = kwargs.pop("models", None)
    if not models_to_try:
        requested = kwargs.get("model", get_configured_model())
        models_to_try = [requested]
        for c in get_candidate_models():
            if c not in models_to_try:
                models_to_try.append(c)

    last_error = None
    for model_name in models_to_try:
        try:
            call_args = dict(kwargs)
            call_args["model"] = model_name
            return client.chat.completions.create(**call_args)
        except Exception as exc:
            err_str = str(exc).lower()
            if "response_format" in err_str and "response_format" in call_args:
                # Retry this model without response_format if not supported
                call_args_no_rf = dict(call_args)
                call_args_no_rf.pop("response_format", None)
                try:
                    return client.chat.completions.create(**call_args_no_rf)
                except Exception as inner_exc:
                    err_str = str(inner_exc).lower()
                    exc = inner_exc
            if any(k in err_str for k in ("not found", "does not exist", "access", "404", "decommissioned", "deprecated")):
                last_error = exc
                continue
            raise exc

    if last_error:
        raise last_error


def generate_sql_from_question(question: str) -> Tuple[str, str]:
    """
    Convert user's natural language question to SQL query using Groq.
    
    Args:
        question (str): User's question in plain English
        
    Returns:
        Tuple[str, str]: (sql_query, explanation)
        
    Example:
        sql, explanation = generate_sql_from_question("What are the top 5 products?")
    """
    
    # Get the database schema formatted for AI
    schema_info = get_schema_for_prompt()
    
    # Build the prompt for Groq
    system_prompt = f"""You are an expert SQL data analyst and developer assistant for DevFlow AI.

Your task is to convert natural language developer and data questions into precise SQLite SQL queries and provide clear, professional explanations that are useful for debugging and developer workflows.

{schema_info}

IMPORTANT RULES:
1. Generate ONLY valid SQLite SQL
2. Always use LIMIT to prevent huge results (default LIMIT 100)
3. Use COUNT(*) for counts, SUM() for totals, AVG() for averages
4. Column and table names are CASE SENSITIVE - use exact names from schema
5. Always wrap table and column names in backticks
6. Prefer chart-friendly aggregates and rankings when the question asks for comparisons, trends, summaries, or top/bottom lists
7. For relative time questions such as "last year" or "last 12 months", prefer the dataset's own date range using the maximum date in the table instead of the current system date
8. Return results in a format that can be visualized whenever possible
9. Never hallucinate columns or tables - ONLY use what's in schema
10. Use proper JOIN syntax if multiple tables needed
11. For filtering, use WHERE clauses
12. For sorting, use ORDER BY
13. Return JSON with two keys: "sql" and "explanation"
"""
    
    user_message = f"""
Question: {question}

Generate a SQLite SQL query to answer this question.

Use ONLY the exact schema names shown above and wrap them in backticks.
If a requested field does not exist, choose the closest valid column from the schema instead of inventing one.

Return EXACTLY in this format (valid JSON):
{{
    "sql": "SELECT ... FROM ...",
    "explanation": "Provide a thorough, business-friendly final answer that directly addresses the user's question, explains exactly what this query calculates, how it works, and what the user should expect from the results. Be highly professional, clear, and make the response feel complete and decision-ready."
}}
"""
    
    client = get_openai_client()

    if client is None:
        return "", "Groq API key is not configured or the OpenAI SDK is unavailable"

    try:
        # Call Groq API with fallback support
        response = create_chat_completion(
            client,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        ai_response = response.choices[0].message.content or ""

        try:
            clean_json = ai_response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```", 1)[1].split("```", 1)[0].strip()
            parsed = json.loads(clean_json)
            sql = parsed.get("sql", "").strip()
            explanation = parsed.get("explanation", "No explanation available")
            return sql, explanation
        except json.JSONDecodeError:
            return "", f"AI Response (not valid JSON): {ai_response}"

    except Exception as e:
        return "", f"Groq API Error: {str(e)}"


def explain_query(query: str) -> str:
    """
    Ask AI to explain what a SQL query does.
    Useful for educational purposes.
    
    Args:
        query (str): SQL query to explain
        
    Returns:
        str: Explanation of the query
    """
    
    client = get_openai_client()

    if client is None:
        return "Groq API key is not configured or the OpenAI SDK is unavailable"

    try:
        response = create_chat_completion(
            client,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SQL expert. Explain what SQL queries do in simple terms.",
                },
                {
                    "role": "user",
                    "content": f"Explain this SQL query:\n\n{query}",
                },
            ],
            temperature=0.5,
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        return f"Error explaining query: {str(e)}"


def validate_api_key() -> bool:
    """
    Check if Groq API key is configured.
    
    Returns:
        bool: True if API key exists
    """
    return bool(get_groq_api_key()) and OpenAI is not None


if __name__ == "__main__":
    # Test the AI module
    print("Testing DevFlow AI module...")

    if not validate_api_key():
        print("❌ Error: GROQ_API_KEY not set in .env file or environment")
        print("Get your key from: https://console.groq.com/keys")
    else:
        print(f"✅ API key is configured. Model: {get_configured_model()}")

        # Test with a sample question
        question = "How many records are in the dataset?"
        print(f"\nTest Question: {question}")

        sql, explanation = generate_sql_from_question(question)
        print(f"\nGenerated SQL:\n{sql}")
        print(f"\nExplanation:\n{explanation}")
