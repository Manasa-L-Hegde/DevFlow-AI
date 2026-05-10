"""
Charts & Visualization Module
Renders interactive Plotly charts for query results
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def detect_chart_type(df: pd.DataFrame) -> str:
    """
    Auto-detect best chart type based on DataFrame structure.
    
    Args:
        df (pd.DataFrame): Query result
        
    Returns:
        str: Recommended chart type (table, bar, line, scatter, pie)
    """
    
    # Too many rows? Just show table
    if len(df) > 10000:
        return "table"
    
    # Get column count and types
    num_cols = len(df.select_dtypes(include=['number']).columns)
    str_cols = len(df.select_dtypes(include=['object']).columns)
    total_rows = len(df)
    
    # Decision logic:
    # - Few rows with numbers → bar chart (good for comparisons)
    # - Time series → line chart
    # - Few categories with one number → pie chart
    # - Scatter plot data → scatter
    # - Default → table
    
    if num_cols == 0 and str_cols > 0:
        # Only text/categories - show table
        return "table"
    
    elif num_cols == 1 and str_cols == 1 and total_rows <= 20:
        # One category, one number, few rows → bar chart
        return "bar"
    
    elif num_cols >= 2 and total_rows <= 100:
        # Multiple numeric columns → line or scatter
        return "line"
    
    elif num_cols == 1 and str_cols == 1 and total_rows <= 10:
        # Perfect for pie chart
        return "pie"
    
    else:
        # Default to table
        return "table"


def create_bar_chart(df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None):
    """
    Create interactive bar chart.
    
    Args:
        df (pd.DataFrame): Data
        x (str): Column for X-axis (auto-detect if None)
        y (str): Column for Y-axis (auto-detect if None)
        
    Returns:
        plotly.graph_objects.Figure: Chart object
    """
    
    # Auto-detect columns if not provided
    if x is None or y is None:
        str_cols = df.select_dtypes(include=['object']).columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        x = x or (str_cols[0] if str_cols else df.columns[0])
        y = y or (num_cols[0] if num_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=f"{y} by {x}",
        labels={x: x.replace('_', ' ').title(), y: y.replace('_', ' ').title()},
        template="plotly_white"
    )
    
    fig.update_layout(hovermode='x unified', height=500)
    return fig


def create_line_chart(df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None):
    """
    Create interactive line chart.
    
    Args:
        df (pd.DataFrame): Data
        x (str): Column for X-axis (auto-detect if None)
        y (str): Column for Y-axis (auto-detect if None)
        
    Returns:
        plotly.graph_objects.Figure: Chart object
    """
    
    # Auto-detect columns
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not num_cols:
        return None
    
    x = x or df.columns[0]
    y = y or num_cols[0]
    
    fig = px.line(
        df,
        x=x,
        y=y,
        title=f"Trend: {y} over {x}",
        markers=True,
        template="plotly_white"
    )
    
    fig.update_layout(hovermode='x unified', height=500)
    return fig


def create_pie_chart(df: pd.DataFrame, values: Optional[str] = None, names: Optional[str] = None):
    """
    Create interactive pie chart.
    
    Args:
        df (pd.DataFrame): Data
        values (str): Column for values (auto-detect if None)
        names (str): Column for names/categories (auto-detect if None)
        
    Returns:
        plotly.graph_objects.Figure: Chart object
    """
    
    # Auto-detect columns
    str_cols = df.select_dtypes(include=['object']).columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    names = names or (str_cols[0] if str_cols else df.columns[0])
    values = values or (num_cols[0] if num_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    fig = px.pie(
        df,
        values=values,
        names=names,
        title=f"Distribution of {values}"
    )
    
    fig.update_layout(height=500)
    return fig


def create_table_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format DataFrame for display in Streamlit.
    
    Args:
        df (pd.DataFrame): Data to display
        
    Returns:
        pd.DataFrame: Formatted DataFrame
    """
    
    # Limit columns for readability
    if len(df.columns) > 15:
        df = df.iloc[:, :15]
    
    # Limit rows for readability
    if len(df) > 1000:
        df = df.head(1000)
    
    return df


def render_chart(df: pd.DataFrame, chart_type: Optional[str] = None):
    """
    Render appropriate chart based on data and type.
    
    Args:
        df (pd.DataFrame): Query result
        chart_type (str): Type of chart to create
        
    Returns:
        plotly.graph_objects.Figure or pd.DataFrame
    """
    
    if df is None or len(df) == 0:
        return None
    
    # Auto-detect if not provided
    chart_type = chart_type or detect_chart_type(df)
    
    if chart_type == "bar":
        return create_bar_chart(df)
    elif chart_type == "line":
        return create_line_chart(df)
    elif chart_type == "pie":
        return create_pie_chart(df)
    else:
        # Table view
        return create_table_display(df)


if __name__ == "__main__":
    # Test chart module
    import pandas as pd
    
    # Create sample data
    test_df = pd.DataFrame({
        'Product': ['A', 'B', 'C', 'D'],
        'Sales': [100, 150, 120, 200]
    })
    
    print("Testing chart detection...")
    chart_type = detect_chart_type(test_df)
    print(f"Detected chart type: {chart_type}")
    
    # Note: Can't display charts in console, but you can see the object created
    chart = render_chart(test_df)
    print(f"Chart object created successfully: {type(chart)}")
