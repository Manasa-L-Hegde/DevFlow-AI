"""
Main Streamlit application for NLytics.

This app gives NLytics a product-style UI: a hero banner, analytics tab,
generated SQL view, insights panel, and schema explorer.
"""

import traceback

import pandas as pd
import streamlit as st

from ai import generate_sql_from_question, validate_api_key
from charts import detect_chart_type, render_chart
from db import execute_query, get_database_schema, get_table_stats, table_exists
from schema import get_schema_ascii_tree, get_schema_description, get_schema_diagram_mermaid


st.set_page_config(
    page_title="NLytics - AI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "last_query_result" not in st.session_state:
    st.session_state.last_query_result = None


def apply_styles() -> None:
    """Inject a premium dark visual style so the app feels like a product."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syncopate:wght@400;700&display=swap');

        /* Global App Styling - Deep Cyber Violet Base */
        .stApp {
            background: linear-gradient(135deg, #05010d 0%, #0d0614 30%, #12091f 70%, #070314 100%);
            color: #e2e8f0;
            font-family: 'Space Grotesk', sans-serif;
            background-attachment: fixed;
        }

        /* Base Typography */
        html, body, [class*="css"] {
            font-family: "Space Grotesk", sans-serif;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: "Syncopate", sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background: rgba(8, 3, 15, 0.6) !important;
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border-right: 1px solid rgba(209, 0, 255, 0.15);
        }

        /* Hero Section */
        .nl-hero {
            padding: 3.5rem 3rem;
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 24px;
            background: linear-gradient(145deg, rgba(13, 6, 20, 0.7), rgba(5, 1, 13, 0.9));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), inset 0 0 20px rgba(209, 0, 255, 0.05);
            margin-bottom: 2.5rem;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .nl-hero:hover {
            transform: translateY(-5px) scale(1.01);
            box-shadow: 0 20px 60px rgba(0, 240, 255, 0.15), 0 0 40px rgba(209, 0, 255, 0.1);
            border-color: rgba(0, 240, 255, 0.5);
        }

        .nl-hero::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(209,0,255,0.08) 0%, rgba(0,0,0,0) 60%);
            z-index: 0;
            pointer-events: none;
            animation: pulseBg 8s infinite alternate;
        }
        
        @keyframes pulseBg {
            0% { transform: scale(1); opacity: 0.5; }
            100% { transform: scale(1.2); opacity: 1; }
        }

        .nl-kicker {
            color: #00f0ff;
            text-transform: uppercase;
            letter-spacing: 0.3em;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
            text-shadow: 0 0 12px rgba(0, 240, 255, 0.6);
        }

        .nl-title {
            font-family: 'Syncopate', sans-serif;
            font-size: 4rem;
            font-weight: 700;
            line-height: 1.1;
            margin: 0;
            background: linear-gradient(135deg, #ffffff 0%, #00f0ff 50%, #d100ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
            z-index: 1;
            filter: drop-shadow(0 0 10px rgba(209,0,255,0.2));
        }

        .nl-subtitle {
            color: #a19fb0;
            font-size: 1.2rem;
            margin-top: 1.2rem;
            max-width: 52rem;
            line-height: 1.7;
            position: relative;
            z-index: 1;
            font-weight: 400;
        }

        /* Generic Cards */
        .nl-card {
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            background: rgba(13, 6, 20, 0.5);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 1.8rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .nl-card::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00f0ff, transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .nl-card:hover {
            background: rgba(20, 9, 30, 0.7);
            transform: translateY(-4px);
            border-color: rgba(209, 0, 255, 0.3);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(209, 0, 255, 0.15);
        }
        
        .nl-card:hover::after {
            opacity: 1;
        }

        .nl-card-strong {
            border: 1px solid rgba(0, 240, 255, 0.2);
            background: linear-gradient(180deg, rgba(20, 9, 30, 0.8), rgba(13, 6, 20, 0.6));
            box-shadow: 0 10px 30px rgba(0, 240, 255, 0.05);
        }

        .nl-section-title {
            font-family: 'Syncopate', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
            color: #ffffff;
            letter-spacing: 0.05em;
        }

        .nl-section-copy {
            color: #a19fb0;
            font-size: 1rem;
            margin-bottom: 1.2rem;
            line-height: 1.6;
        }

        /* Pills/Tags */
        .nl-pill {
            display: inline-block;
            border: 1px solid rgba(209, 0, 255, 0.4);
            background: rgba(209, 0, 255, 0.1);
            color: #eabfff;
            border-radius: 4px;
            padding: 0.4rem 1rem;
            margin: 0.3rem 0.4rem 0 0;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            transition: all 0.2s ease;
        }
        
        .nl-pill:hover {
            background: rgba(209, 0, 255, 0.3);
            border-color: #d100ff;
            box-shadow: 0 0 15px rgba(209, 0, 255, 0.4);
            color: #ffffff;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            background: rgba(13, 6, 20, 0.5);
            backdrop-filter: blur(10px);
            padding: 0.5rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stTabs [data-baseweb="tab"] {
            height: 3.2rem;
            border-radius: 8px;
            color: #a19fb0;
            padding-left: 2rem;
            padding-right: 2rem;
            font-weight: 600;
            font-family: 'Syncopate', sans-serif;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(0, 240, 255, 0.05);
            color: #00f0ff;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, rgba(0, 240, 255, 0.15), rgba(209, 0, 255, 0.15)) !important;
            color: #ffffff !important;
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-bottom: 2px solid #00f0ff !important;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
        }

        /* Metric Widgets */
        div[data-testid="stMetric"] {
            background: rgba(13, 6, 20, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 1.2rem 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border-left: 3px solid #d100ff;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px) scale(1.02);
            border-color: rgba(209, 0, 255, 0.5);
            border-left: 4px solid #00f0ff;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 240, 255, 0.2);
        }

        div[data-testid="stMetricLabel"] {
            font-weight: 600;
            color: #a19fb0;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        div[data-testid="stMetricValue"] {
            font-family: 'Syncopate', sans-serif;
            font-weight: 700;
            color: #ffffff;
            font-size: 2.2rem;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
        }

        /* Input Fields */
        .stTextInput > div > div > input {
            background: rgba(8, 3, 15, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 1.2rem !important;
            font-size: 1.1rem !important;
            transition: all 0.3s ease !important;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.5) !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #00f0ff !important;
            box-shadow: 0 0 0 1px #00f0ff, 0 0 15px rgba(0, 240, 255, 0.3), inset 0 2px 5px rgba(0,0,0,0.5) !important;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 8px !important;
            font-family: 'Syncopate', sans-serif !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            padding: 0.6rem 1.2rem !important;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            border: 1px solid rgba(0, 240, 255, 0.3) !important;
            background: linear-gradient(90deg, rgba(0, 240, 255, 0.1), rgba(209, 0, 255, 0.1)) !important;
            color: #ffffff !important;
            position: relative;
            overflow: hidden;
        }

        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0; left: -100%; width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }

        .stButton > button:hover {
            transform: translateY(-3px) scale(1.05) !important;
            box-shadow: 0 10px 25px rgba(0, 240, 255, 0.4), 0 0 15px rgba(209, 0, 255, 0.4) !important;
            border-color: #00f0ff !important;
            color: #00f0ff !important;
            background: linear-gradient(90deg, rgba(0, 240, 255, 0.2), rgba(209, 0, 255, 0.2)) !important;
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }

        /* Primary button override */
        .stButton > button:active, .stButton > button:focus {
            border-color: #d100ff !important;
            color: #d100ff !important;
            box-shadow: 0 0 20px rgba(209, 0, 255, 0.5) !important;
        }

        /* Code blocks */
        .stCodeBlock {
            border-radius: 12px !important;
            overflow: hidden !important;
            border: 1px solid rgba(0, 240, 255, 0.15) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
            background: #05010d !important;
        }
        
        /* Dataframes */
        [data-testid="stDataFrame"] {
            border-radius: 12px !important;
            overflow: hidden !important;
            border: 1px solid rgba(209, 0, 255, 0.15) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="nl-hero">
            <div class="nl-kicker">AI-powered analytics copilot</div>
            <h1 class="nl-title">NLytics</h1>
            <div class="nl-subtitle">
                Ask business questions in plain English, convert them into SQL, execute live against the database,
                and turn the result into charts, schema context, and decision-ready insights.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_schema_cards(schema: dict) -> str:
    """Build a compact schema viewer from the live database schema."""
    if not schema:
        return "<div class='nl-card'>No tables found yet. Load the dataset first.</div>"

    cards = ["<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:0.9rem;'>"]
    for table_name, columns in schema.items():
        column_lines = "\n".join([f"├─ {column}" for column in columns[:-1]])
        if columns:
            column_lines += ("\n└─ " + columns[-1]) if len(columns) > 1 else columns[-1]
        cards.append(
            f"""
            <div class='nl-card'>
                <div class='nl-section-title'>{table_name}</div>
                <div class='nl-section-copy'>{len(columns)} columns</div>
                <div style='white-space:pre-wrap;font-family:Consolas, "SFMono-Regular", monospace;color:#dce8fb;font-size:0.84rem;line-height:1.35;'>{column_lines}</div>
            </div>
            """
        )
    cards.append("</div>")
    return "".join(cards)


def generate_local_insight(df: pd.DataFrame) -> str:
    """Generate a fast business insight without another model call."""
    if df is None or df.empty:
        return "Run a query to generate an insight summary."

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    text_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()

    if numeric_cols and text_cols:
        value_col = numeric_cols[0]
        label_col = text_cols[0]
        top_row = df.sort_values(value_col, ascending=False).iloc[0]
        top_label = top_row[label_col]
        top_value = top_row[value_col]
        total_value = df[value_col].sum()
        share = (top_value / total_value * 100) if total_value else 0
        return (
            f"**Key Insight:** **`{top_label}`** is the strongest contributor in this result set with **{top_value:,.2f}**, "
            f"representing about **{share:.1f}%** of the total `{value_col}`."
        )

    if numeric_cols:
        value_col = numeric_cols[0]
        return (
            f"**Statistical Summary:** The average `{value_col}` is **{df[value_col].mean():,.2f}**, with a range from "
            f"**{df[value_col].min():,.2f}** to **{df[value_col].max():,.2f}**."
        )

    return "This result is primarily categorical. Use the schema and filters to drill deeper into patterns."


def render_sidebar() -> None:
    st.sidebar.title("📊 NLytics")
    st.sidebar.markdown(
        """
        **AI-Powered Business Analytics**

        Convert natural language to SQL instantly.
        Get insights in seconds.
        """
    )

    st.sidebar.markdown("### Product Status")

    db_ready = table_exists("train")
    api_ready = validate_api_key()

    st.sidebar.metric("Database", "Ready" if db_ready else "Missing")
    st.sidebar.metric("Groq", "Ready" if api_ready else "Missing")

    if db_ready:
        stats = get_table_stats("train")
        st.sidebar.markdown(
            f"""
            <div class='nl-card nl-card-strong'>
                <div class='nl-section-title'>Dataset snapshot</div>
                <div class='nl-section-copy'>{stats['row_count']:,} rows • {stats['column_count']} columns</div>
                <span class='nl-pill'>Live SQL</span>
                <span class='nl-pill'>Plotly charts</span>
                <span class='nl-pill'>Schema aware</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("### Recent Queries")
    if not st.session_state.query_history:
        st.sidebar.caption("No queries yet. Ask a question in Analytics.")
    else:
        for idx, query_record in enumerate(st.session_state.query_history[:5], 1):
            with st.sidebar.expander(f"{idx}. {query_record['question'][:32]}", expanded=False):
                st.write(query_record["question"])
                st.code(query_record["sql"], language="sql")


def check_prerequisites() -> list[str]:
    """Return any setup issues that should be shown before the app runs."""
    issues = []

    if not table_exists("train"):
        issues.append("Database not loaded. Run: python load_data.py")

    if not validate_api_key():
        issues.append("Groq API key not configured. Add GROQ_API_KEY to .env")

    return issues


def main() -> None:
    """Main application flow."""
    apply_styles()
    render_sidebar()
    render_hero()

    issues = check_prerequisites()
    if issues:
        st.error("Setup required")
        for issue in issues:
            st.write(issue)
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(["Analytics", "Generated SQL", "Insights", "Schema"])

    with tab1:
        st.markdown(
            """
            <div class='nl-card nl-card-strong'>
                <div class='nl-section-title'>Ask your data</div>
                <div class='nl-section-copy'>Use a plain-English question, get SQL instantly, and keep the workflow transparent.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_question = st.text_input(
            "Ask a question about your data:",
            placeholder="Example: What are the top 10 products by sales?",
            key="user_question",
        )

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            run_query = st.button("🚀 Generate & Execute", key="run_query_btn")
        with col2:
            show_schema_btn = st.button("📋 View Schema")
        with col3:
            clear_history_btn = st.button("🗑️ Clear History")

        if clear_history_btn:
            st.session_state.query_history = []
            st.success("History cleared!")

        if show_schema_btn:
            with st.expander("Database Schema", expanded=True):
                schema = get_database_schema()
                st.markdown(build_schema_cards(schema), unsafe_allow_html=True)

        if run_query and user_question:
            st.write("---")
            with st.spinner("Generating SQL..."):
                try:
                    sql_query, explanation = generate_sql_from_question(user_question)

                    if not sql_query:
                        st.error(explanation)
                        st.stop()

                    st.subheader("Generated SQL")
                    st.code(sql_query, language="sql")

                    st.subheader("Explanation")
                    st.info(explanation)

                    result_df = execute_query(sql_query)
                    st.session_state.last_query_result = {
                        "question": user_question,
                        "sql": sql_query,
                        "result": result_df,
                        "rows": len(result_df),
                    }
                    st.session_state.query_history.insert(0, st.session_state.last_query_result)

                    st.success(f"Query executed successfully. Found {len(result_df)} rows.")

                    st.subheader("Results")
                    st.dataframe(result_df, use_container_width=True)

                    st.subheader("Insight")
                    st.success(generate_local_insight(result_df))

                    st.subheader("Visualization")
                    chart_type = detect_chart_type(result_df)
                    chart = render_chart(result_df, chart_type)
                    if chart is not None and chart_type != "table":
                        st.plotly_chart(chart, use_container_width=True)

                    st.download_button(
                        label="📥 Download as CSV",
                        data=result_df.to_csv(index=False),
                        file_name="query_result.csv",
                        mime="text/csv",
                    )

                except Exception as exc:
                    st.error(f"Error executing query: {exc}")
                    st.write(traceback.format_exc())
        elif run_query:
            st.warning("Please enter a question first.")

    with tab2:
        st.markdown(
            """
            <div class='nl-card nl-card-strong'>
                <div class='nl-section-title'>Generated SQL</div>
                <div class='nl-section-copy'>The SQL stays visible so the workflow remains transparent and easy to explain.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.last_query_result:
            record = st.session_state.last_query_result
            col1, col2 = st.columns([2, 1])
            with col1:
                st.code(record["sql"], language="sql")
            with col2:
                st.metric("Rows Returned", f"{record['rows']:,}")
                st.metric("Query History", f"{len(st.session_state.query_history):,}")
        else:
            st.info("Run a query in Analytics to see the generated SQL here.")

    with tab3:
        st.markdown(
            """
            <div class='nl-card nl-card-strong'>
                <div class='nl-section-title'>Insights</div>
                <div class='nl-section-copy'>This panel translates raw query output into a short business readout.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.last_query_result:
            result_df = st.session_state.last_query_result["result"]
            st.markdown(
                f"""
                <div class='nl-card'>
                    <div class='nl-section-title'>Business summary</div>
                    <div class='nl-section-copy'>{generate_local_insight(result_df)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("---")
            st.subheader("Query History")
            if not st.session_state.query_history:
                st.info("No queries executed yet.")
            else:
                for i, query_record in enumerate(st.session_state.query_history, 1):
                    with st.expander(f"Query #{i} - {query_record['question'][:50]}...", expanded=False):
                        st.write("**Question:**", query_record["question"])
                        st.write("**SQL:**")
                        st.code(query_record["sql"], language="sql")
                        st.write(f"**Result:** {query_record['rows']} rows")
        else:
            st.info("Run a query first to populate the insights panel.")

    with tab4:
        st.markdown(
            """
            <div class='nl-card nl-card-strong'>
                <div class='nl-section-title'>Schema</div>
                <div class='nl-section-copy'>Visual schema context helps users trust the generated SQL.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        schema = get_database_schema()
        if not schema:
            st.warning("No tables found in database.")
            st.info("Run: python load_data.py to load data.")
        else:
            st.subheader("Schema Diagram")
            st.caption("Mermaid diagram markup for the live database schema.")
            st.code(get_schema_diagram_mermaid(), language="text")

            st.subheader("Readable Tree")
            st.code(get_schema_ascii_tree(), language="text")

            st.subheader("Schema Cards")
            st.markdown(build_schema_cards(schema), unsafe_allow_html=True)

            st.write("---")
            with st.expander("Schema description", expanded=False):
                st.text(get_schema_description())


if __name__ == "__main__":
    main()