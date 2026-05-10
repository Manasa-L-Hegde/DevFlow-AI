"""
Database Schema Module
Formats database schema for AI prompts
Helps the AI generate correct SQL queries
"""

from db import get_database_schema, get_table_stats
from typing import Dict, Any
import json


def humanize_column_name(column_name: str) -> str:
    """
    Turn a sanitized column name into a short business-friendly label.

    Example: Order_Date -> order date
    """
    return column_name.replace("_", " ").strip().lower()


def get_schema_description() -> str:
    """
    Generate human-readable schema description for AI prompts.
    
    Returns:
        str: Formatted schema information
    """
    schema = get_database_schema()
    
    if not schema:
        return "No tables found in database. Run load_data.py first."
    
    description = "DATABASE SCHEMA:\n\n"
    
    for table_name, columns in schema.items():
        stats = get_table_stats(table_name)
        description += f"Table: {table_name}\n"
        description += f"  Rows: {stats['row_count']}\n"
        description += "  Columns:\n"

        for column in columns:
            description += f"    - {column}: {humanize_column_name(column)}\n"

        description += "\n"
    
    return description


def get_schema_for_prompt() -> str:
    """
    Get schema formatted specifically for LLM SQL generation prompts.
    
    Returns:
        str: Schema in a format optimized for AI prompts
    """
    schema = get_database_schema()
    
    if not schema:
        return ""
    
    prompt = "You have access to the following database:\n\n"
    
    for table_name, columns in schema.items():
        # Format: Table `name` with exact backticked columns.
        columns_str = ", ".join(f"`{column}`" for column in columns)
        prompt += f"- Table `{table_name}` with columns: {columns_str}\n"
    
    prompt += (
        "\nIMPORTANT:\n"
        "- Use exact column names only\n"
        "- Wrap every table and column name in backticks\n"
        "- Never invent columns\n"
        "- Generate valid SQLite SQL queries based on user questions.\n"
    )
    
    return prompt


def get_schema_diagram_mermaid() -> str:
    """
    Generate a Mermaid flowchart representation of the database schema.

    Returns:
        str: Mermaid diagram markup for the schema.
    """
    schema = get_database_schema()

    if not schema:
        return "flowchart TB\n    empty[No tables found]"

    lines = ["flowchart TB"]

    for table_name, columns in schema.items():
        table_id = table_name.replace(" ", "_")
        lines.append(f"    subgraph {table_id}[\"{table_name}\"]")
        lines.append(f"        {table_id}_table[\"Table: {table_name}\"]")

        for column in columns:
            column_id = f"{table_id}_{column}".replace(" ", "_")
            lines.append(f"        {column_id}[\"{column}\"]")
            lines.append(f"        {table_id}_table --> {column_id}")

        lines.append("    end")

    return "\n".join(lines)


def get_schema_ascii_tree() -> str:
    """
    Generate a readable ASCII tree of the schema as a fallback display.

    Returns:
        str: Tree-style text diagram.
    """
    schema = get_database_schema()

    if not schema:
        return "No tables found in database."

    output = []
    for table_name, columns in schema.items():
        output.append(table_name)
        for index, column in enumerate(columns):
            branch = "└─" if index == len(columns) - 1 else "├─"
            output.append(f"  {branch} {column}")
        output.append("")

    return "\n".join(output).strip()


def get_column_sample_values(table_name: str, column_name: str, limit: int = 5) -> list:
    """
    Get sample values from a specific column (helps AI understand data).
    
    Args:
        table_name (str): Table name
        column_name (str): Column name
        limit (int): Number of samples
        
    Returns:
        list: Sample values
    """
    from db import execute_query
    
    query = f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT {limit}"
    
    try:
        df = execute_query(query)
        return df[column_name].tolist()
    except:
        return []


def print_schema():
    """
    Print schema to console (for debugging).
    Run this to see what tables/columns are available.
    """
    print("=" * 60)
    print("DATABASE SCHEMA")
    print("=" * 60)
    
    schema = get_database_schema()
    
    if not schema:
        print("❌ No tables found. Run: python load_data.py")
        return
    
    for table_name, columns in schema.items():
        print(f"\n✅ Table: {table_name}")
        print(f"   Columns: {len(columns)}")
        
        for col in columns:
            samples = get_column_sample_values(table_name, col, limit=3)
            samples_str = str(samples)[1:-1]  # Remove brackets
            print(f"   - {col}: {samples_str}")


if __name__ == "__main__":
    # Run this to inspect database
    # Usage: python schema.py
    print_schema()
