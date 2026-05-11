"""
AI/LLM Module
Handles Groq API integration for natural language to SQL conversion
"""

from dotenv import load_dotenv
import os
from schema import get_schema_for_prompt
from typing import Tuple
import json

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# Load environment variables from .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)


def get_openai_client():
    """
    Create an OpenAI-compatible client configured for Groq.

    Returns:
        OpenAI | None: Configured client or None if the SDK/key is missing.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or OpenAI is None:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


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
    system_prompt = f"""You are an expert SQL data analyst and AI assistant for NLytics.

Your task is to convert natural language business questions into precise SQLite SQL queries and provide clear, professional explanations.

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
        # Call Groq API with the modern SDK.
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        ai_response = response.choices[0].message.content or ""

        try:
            parsed = json.loads(ai_response)
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
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
    return bool(os.getenv("GROQ_API_KEY")) and OpenAI is not None


if __name__ == "__main__":
    # Test the AI module
    print("Testing NLytics AI Module...")
    
    if not validate_api_key():
        print("❌ Error: GROQ_API_KEY not set in .env file")
        print("Get your key from: https://console.groq.com/keys")
    else:
        print("✅ API key is configured")
        
        # Test with a sample question
        question = "How many records are in the dataset?"
        print(f"\nTest Question: {question}")
        
        sql, explanation = generate_sql_from_question(question)
        print(f"\nGenerated SQL:\n{sql}")
        print(f"\nExplanation:\n{explanation}")
