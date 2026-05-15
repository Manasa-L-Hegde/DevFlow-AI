"""
Database Connection & Management Module
Handles SQLite database operations for DevFlow AI
"""

import sqlite3
import pandas as pd
from sqlalchemy import create_engine, inspect
from typing import List, Dict, Any
import os

# Database file path - creates devflow.db in project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "devflow.db")


def get_connection():
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    return sqlite3.connect(DATABASE_PATH)


def create_engine_connection():
    """
    Create SQLAlchemy engine for database operations.
    
    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine object
    """
    return create_engine(f"sqlite:///{DATABASE_PATH}")


def get_database_schema() -> Dict[str, List[str]]:
    """
    Retrieve all table names and their column names from database.
    
    Returns:
        Dict[str, List[str]]: {table_name: [column1, column2, ...]}
    """
    engine = create_engine_connection()
    inspector = inspect(engine)
    
    schema = {}
    for table_name in inspector.get_table_names():
        # Get all columns for this table
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        schema[table_name] = columns
    
    return schema


def execute_query(query: str) -> pd.DataFrame:
    """
    Execute a SQL SELECT query and return results as DataFrame.
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        pd.DataFrame: Query results
        
    Raises:
        Exception: If query fails
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        raise Exception(f"Query failed: {str(e)}")


def get_table_preview(table_name: str, rows: int = 5) -> pd.DataFrame:
    """
    Get a preview of a specific table.
    
    Args:
        table_name (str): Name of the table
        rows (int): Number of rows to preview
        
    Returns:
        pd.DataFrame: Preview of table data
    """
    query = f"SELECT * FROM {table_name} LIMIT {rows}"
    return execute_query(query)


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        table_name (str): Name to check
        
    Returns:
        bool: True if table exists
    """
    engine = create_engine_connection()
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def get_table_stats(table_name: str) -> Dict[str, Any]:
    """
    Get basic statistics about a table.
    
    Args:
        table_name (str): Name of the table
        
    Returns:
        Dict: {row_count, column_count, column_names}
    """
    query = f"SELECT COUNT(*) as row_count FROM {table_name}"
    result = execute_query(query)
    
    engine = create_engine_connection()
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    return {
        "row_count": int(result['row_count'][0]),
        "column_count": len(columns),
        "column_names": columns
    }
