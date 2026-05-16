"""
Charts & Visualization Module
Renders interactive Plotly charts for query results with cyberpunk theming
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


TIME_LIKE_KEYWORDS = ("date", "month", "week", "year", "quarter", "time", "day")

# Cyberpunk neon color palette
CYBERPUNK_COLORS = [
    '#00FFFF',  # Cyan
    '#FF00FF',  # Magenta
    '#9D00FF',  # Purple
    '#00FF41',  # Neon Green
    '#FF006E',  # Hot Pink
    '#00D9FF',  # Electric Blue
    '#FFD700',  # Gold
    '#FF1493',  # Deep Pink
]

def apply_cyberpunk_theme(fig: go.Figure) -> go.Figure:
    """
    Apply cyberpunk styling to any Plotly figure.
    
    Args:
        fig: Plotly figure object
        
    Returns:
        Styled figure with cyberpunk theme
    """
    fig.update_layout(
        # Dark transparent background
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(10,10,20,0.3)',
        
        # Neon color scheme
        colorway=CYBERPUNK_COLORS,
        
        # Font styling
        font=dict(
            family='monospace',
            size=12,
            color='#00FFFF'
        ),
        
        # Title styling
        title=dict(
            font=dict(size=16, color='#00FFFF', family='monospace'),
            x=0.5,
            xanchor='center'
        ),
        
        # Grid and axes
        xaxis=dict(
            gridcolor='rgba(0, 255, 255, 0.1)',
            linecolor='rgba(0, 255, 255, 0.3)',
            zerolinecolor='rgba(0, 255, 255, 0.2)',
            tickfont=dict(color='#00FFFF')
        ),
        yaxis=dict(
            gridcolor='rgba(0, 255, 255, 0.1)',
            linecolor='rgba(0, 255, 255, 0.3)',
            zerolinecolor='rgba(0, 255, 255, 0.2)',
            tickfont=dict(color='#00FFFF')
        ),
        
        # Hover styling
        hoverlabel=dict(
            bgcolor='rgba(10,10,20,0.9)',
            font_size=12,
            font_family='monospace',
            font_color='#00FFFF',
            bordercolor='#00FFFF'
        ),
        
        # Responsive layout
        autosize=True,
        margin=dict(l=60, r=40, t=60, b=60),
        
        # Legend styling
        legend=dict(
            bgcolor='rgba(10,10,20,0.7)',
            bordercolor='#00FFFF',
            borderwidth=1,
            font=dict(color='#00FFFF')
        )
    )
    
    # Add glow effect to traces
    for trace in fig.data:
        if hasattr(trace, 'marker'):
            trace.marker.line = dict(width=0)
        if hasattr(trace, 'line'):
            trace.line.width = 3
    
    return fig


def detect_chart_type(df: pd.DataFrame) -> str:
    """
    Intelligently detect best chart type based on DataFrame structure.
    Enhanced with more sophisticated logic for better visualizations.
    
    Args:
        df (pd.DataFrame): Query result
        
    Returns:
        str: Recommended chart type (table, bar, horizontal_bar, line, area, scatter, pie)
    """
    
    # Empty or too large? Show table
    if df is None or len(df) == 0:
        return "table"
    
    if len(df) > 10000:
        return "table"
    
    # Get column count and types
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    string_columns = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    num_cols = len(numeric_columns)
    str_cols = len(string_columns)
    total_rows = len(df)
    column_names = [str(column).lower() for column in df.columns]
    
    # Check for time-like columns
    has_time_like_column = any(
        any(keyword in column_name for keyword in TIME_LIKE_KEYWORDS) for column_name in column_names
    )
    
    # Check label length for horizontal bar decision
    avg_label_length = 0
    if str_cols > 0:
        first_str_col = string_columns[0]
        avg_label_length = df[first_str_col].astype(str).str.len().mean()
    
    # Enhanced decision logic:
    
    # 1. Time series data → line or area chart
    if has_time_like_column and num_cols >= 1 and total_rows > 2:
        return "area" if total_rows <= 50 else "line"
    
    # 2. Two numeric columns → scatter plot
    if num_cols == 2 and str_cols == 0 and total_rows <= 500:
        return "scatter"
    
    # 3. Small categorical breakdown → pie chart
    if num_cols == 1 and str_cols == 1 and total_rows <= 8:
        return "pie"
    
    # 4. Long labels → horizontal bar
    if num_cols >= 1 and str_cols >= 1 and avg_label_length > 15 and total_rows <= 20:
        return "horizontal_bar"
    
    # 5. Categorical comparison → bar chart
    if num_cols >= 1 and str_cols >= 1 and total_rows <= 30:
        return "bar"
    
    # 6. Multiple numeric columns with few rows → line chart
    if num_cols >= 2 and total_rows <= 100:
        return "line"
    
    # 7. Text-only data → frequency bar
    if num_cols == 0 and str_cols > 0 and total_rows > 1:
        return "bar"
    
    # Default to table for complex or large datasets
    return "table"


def create_bar_chart(df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None, horizontal: bool = False):
    """
    Create interactive bar chart with cyberpunk styling.
    
    Args:
        df (pd.DataFrame): Data
        x (str): Column for X-axis (auto-detect if None)
        y (str): Column for Y-axis (auto-detect if None)
        horizontal (bool): Create horizontal bar chart
        
    Returns:
        plotly.graph_objects.Figure: Chart object
    """
    
    # Auto-detect columns if not provided
    str_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

    if not num_cols:
        return create_frequency_bar_chart(df)

    if x is None or y is None:
        x = x or (str_cols[0] if str_cols else df.columns[0])
        y = y or (num_cols[0] if num_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    # Create bar chart
    if horizontal:
        fig = px.bar(
            df,
            x=y,
            y=x,
            orientation='h',
            title=f"{y} by {x}",
            labels={x: x.replace('_', ' ').title(), y: y.replace('_', ' ').title()},
        )
    else:
        fig = px.bar(
            df,
            x=x,
            y=y,
            title=f"{y} by {x}",
            labels={x: x.replace('_', ' ').title(), y: y.replace('_', ' ').title()},
        )
    
    # Apply cyberpunk theme
    fig = apply_cyberpunk_theme(fig)
    fig.update_layout(hovermode='x unified', height=600)
    
    return fig


def create_frequency_bar_chart(df: pd.DataFrame):
    """
    Create a frequency chart from the first categorical column with cyberpunk styling.
    """
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()

    if not categorical_cols:
        return None

    label_col = categorical_cols[0]
    counts = df[label_col].astype(str).value_counts(dropna=False).reset_index()
    counts.columns = [label_col, 'Count']

    fig = px.bar(
        counts,
        x=label_col,
        y='Count',
        title=f'Distribution of {label_col}',
        labels={label_col: label_col.replace('_', ' ').title(), 'Count': 'Count'},
    )

    fig = apply_cyberpunk_theme(fig)
    fig.update_layout(hovermode='x unified', height=600)
    return fig


def create_line_chart(df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None):
    """
    Create interactive line chart with cyberpunk styling.
    """
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not num_cols:
        return None
    
    x = x or df.columns[0]
    y = y or num_cols[0]

    chart_df = df.copy()
    chart_df[x] = chart_df[x].astype(str)
    chart_df = chart_df.sort_values(by=x)
    
    fig = px.line(
        chart_df,
        x=x,
        y=y,
        title=f"Trend: {y} over {x}",
        markers=True,
    )
    
    fig = apply_cyberpunk_theme(fig)
    fig.update_layout(hovermode='x unified', height=600)
    
    # Enhanced glow effect for line charts
    fig.update_traces(line=dict(width=4), marker=dict(size=10))
    
    return fig


def create_area_chart(df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None):
    """
    Create interactive area chart with cyberpunk styling.
    """
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not num_cols:
        return None
    
    x = x or df.columns[0]
    y = y or num_cols[0]

    chart_df = df.copy()
    chart_df[x] = chart_df[x].astype(str)
    chart_df = chart_df.sort_values(by=x)
    
    fig = px.area(
        chart_df,
        x=x,
        y=y,
        title=f"Trend: {y} over {x}",
    )
    
    fig = apply_cyberpunk_theme(fig)
    fig.update_layout(hovermode='x unified', height=600)
    
    # Add fill opacity for area effect
    fig.update_traces(fillcolor='rgba(0, 255, 255, 0.2)')
    
    return fig


def create_scatter_chart(df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None):
    """
    Create interactive scatter plot with cyberpunk styling.
    """
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if len(num_cols) < 2:
        return None
    
    x = x or num_cols[0]
    y = y or num_cols[1]
    
    fig = px.scatter(
        df,
        x=x,
        y=y,
        title=f"{y} vs {x}",
        labels={x: x.replace('_', ' ').title(), y: y.replace('_', ' ').title()},
    )
    
    fig = apply_cyberpunk_theme(fig)
    fig.update_layout(height=600)
    
    # Enhanced markers with glow
    fig.update_traces(marker=dict(size=12, line=dict(width=2, color='#00FFFF')))
    
    return fig


def create_pie_chart(df: pd.DataFrame, values: Optional[str] = None, names: Optional[str] = None):
    """
    Create interactive pie chart with cyberpunk styling.
    """
    str_cols = df.select_dtypes(include=['object']).columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    names = names or (str_cols[0] if str_cols else df.columns[0])
    values = values or (num_cols[0] if num_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    fig = px.pie(
        df,
        values=values,
        names=names,
        title=f"Distribution of {values}",
        color_discrete_sequence=CYBERPUNK_COLORS
    )
    
    fig = apply_cyberpunk_theme(fig)
    fig.update_layout(height=600)
    
    # Enhanced pie styling
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#000000', width=2)),
        textfont=dict(size=14)
    )
    
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
    Render appropriate chart based on data and type with intelligent fallback.
    
    Args:
        df (pd.DataFrame): Query result
        chart_type (str): Type of chart to create
        
    Returns:
        plotly.graph_objects.Figure or None
    """
    
    if df is None or len(df) == 0:
        return None
    
    # Auto-detect if not provided
    chart_type = chart_type or detect_chart_type(df)
    
    # Route to appropriate chart creator with fallback
    try:
        if chart_type == "bar":
            chart = create_bar_chart(df, horizontal=False)
            return chart if chart is not None else create_frequency_bar_chart(df)
        
        elif chart_type == "horizontal_bar":
            chart = create_bar_chart(df, horizontal=True)
            return chart if chart is not None else create_frequency_bar_chart(df)
        
        elif chart_type == "line":
            chart = create_line_chart(df)
            return chart if chart is not None else create_frequency_bar_chart(df)
        
        elif chart_type == "area":
            chart = create_area_chart(df)
            return chart if chart is not None else create_line_chart(df)
        
        elif chart_type == "scatter":
            chart = create_scatter_chart(df)
            return chart if chart is not None else create_bar_chart(df)
        
        elif chart_type == "pie":
            chart = create_pie_chart(df)
            return chart if chart is not None else create_frequency_bar_chart(df)
        
        else:
            # Default fallback
            return create_frequency_bar_chart(df)
    
    except Exception:
        # Graceful fallback on any error
        return create_frequency_bar_chart(df)


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
