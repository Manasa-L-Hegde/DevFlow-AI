"""
Main Streamlit application for DevFlow AI.

This app provides a developer-focused UI: a hero banner, analytics tab,
generated SQL view, insights panel, schema explorer, and an Error Explainer.
"""

import os
import random
import re
import traceback

import pandas as pd
import streamlit as st

from ai import generate_sql_from_question, validate_api_key
from error_explainer import explain_error_text
from repo_explainer import explain_repository
from charts import detect_chart_type, render_chart
from db import execute_query, get_database_schema, get_table_stats, table_exists
from load_data import load_excel_to_sqlite
from schema import get_schema_ascii_tree, get_schema_description, get_schema_diagram_mermaid


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_XLSX_PATH = os.path.join(BASE_DIR, "train.xlsx")


st.set_page_config(
    page_title="DevFlow AI - AI-powered developer productivity assistant",
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

        /* ===== GLOBAL STYLES ===== */
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
            margin-top: 0;
        }

        /* Consistent Spacing Variables */
        :root {
            --spacing-xs: 0.5rem;
            --spacing-sm: 1rem;
            --spacing-md: 1.5rem;
            --spacing-lg: 2rem;
            --spacing-xl: 2.5rem;
            --spacing-2xl: 3rem;
            --spacing-3xl: 4rem;
            --border-radius-sm: 8px;
            --border-radius-md: 12px;
            --border-radius-lg: 16px;
            --border-radius-xl: 24px;
        }

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {
            background: rgba(8, 3, 15, 0.6) !important;
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border-right: 1px solid rgba(209, 0, 255, 0.15);
            padding: var(--spacing-md) !important;
        }

        /* ===== HERO SECTION ===== */
        .nl-hero {
            padding: var(--spacing-2xl) var(--spacing-lg);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: var(--border-radius-xl);
            background: linear-gradient(145deg, rgba(13, 6, 20, 0.7), rgba(5, 1, 13, 0.9));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), inset 0 0 20px rgba(209, 0, 255, 0.05);
            margin-bottom: var(--spacing-xl);
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
            margin-bottom: var(--spacing-sm);
            position: relative;
            z-index: 1;
            text-shadow: 0 0 12px rgba(0, 240, 255, 0.6);
        }

        .nl-title {
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(2rem, 5vw, 4rem);
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
            font-size: clamp(1rem, 2vw, 1.2rem);
            margin-top: var(--spacing-md);
            max-width: 52rem;
            line-height: 1.7;
            position: relative;
            z-index: 1;
            font-weight: 400;
        }

        /* ===== CARDS ===== */
        /* Generic Cards */
        .nl-card {
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--border-radius-lg);
            background: rgba(13, 6, 20, 0.5);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: var(--spacing-lg);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            margin-bottom: var(--spacing-md);
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
            font-size: clamp(1rem, 2vw, 1.1rem);
            font-weight: 700;
            margin-bottom: var(--spacing-sm);
            color: #ffffff;
            letter-spacing: 0.05em;
        }

        .nl-section-copy {
            color: #a19fb0;
            font-size: clamp(0.9rem, 1.5vw, 1rem);
            margin-bottom: var(--spacing-md);
            line-height: 1.6;
        }

        /* ===== PILLS/TAGS ===== */
        .nl-pill {
            display: inline-block;
            border: 1px solid rgba(209, 0, 255, 0.4);
            background: rgba(209, 0, 255, 0.1);
            color: #eabfff;
            border-radius: var(--border-radius-sm);
            padding: var(--spacing-xs) var(--spacing-sm);
            margin: var(--spacing-xs) var(--spacing-xs) 0 0;
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

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {
            gap: var(--spacing-sm);
            background: rgba(13, 6, 20, 0.5);
            backdrop-filter: blur(10px);
            padding: var(--spacing-xs);
            border-radius: var(--border-radius-md);
            border: 1px solid rgba(255, 255, 255, 0.05);
            flex-wrap: wrap;
        }

        .stTabs [data-baseweb="tab"] {
            height: 3.2rem;
            border-radius: var(--border-radius-sm);
            color: #a19fb0;
            padding-left: clamp(1rem, 3vw, 2rem);
            padding-right: clamp(1rem, 3vw, 2rem);
            font-weight: 600;
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(0.75rem, 1.5vw, 0.9rem);
            transition: all 0.3s ease;
            white-space: nowrap;
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

        /* ===== METRICS ===== */
        div[data-testid="stMetric"] {
            background: rgba(13, 6, 20, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--border-radius-lg);
            padding: var(--spacing-md) var(--spacing-lg);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border-left: 3px solid #d100ff;
            margin-bottom: var(--spacing-sm);
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
            font-size: clamp(1.5rem, 3vw, 2.2rem);
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
        }

        /* ===== INPUT FIELDS ===== */
        .stTextInput > div > div > input {
            background: rgba(8, 3, 15, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border-radius: var(--border-radius-sm) !important;
            padding: var(--spacing-md) !important;
            font-size: clamp(1rem, 2vw, 1.1rem) !important;
            transition: all 0.3s ease !important;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.5) !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #00f0ff !important;
            box-shadow: 0 0 0 1px #00f0ff, 0 0 15px rgba(0, 240, 255, 0.3), inset 0 2px 5px rgba(0,0,0,0.5) !important;
        }

        /* ===== BUTTONS ===== */
        .stButton > button {
            border-radius: var(--border-radius-sm) !important;
            font-family: 'Syncopate', sans-serif !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            padding: var(--spacing-sm) var(--spacing-md) !important;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            border: 1px solid rgba(0, 240, 255, 0.3) !important;
            background: linear-gradient(90deg, rgba(0, 240, 255, 0.1), rgba(209, 0, 255, 0.1)) !important;
            color: #ffffff !important;
            position: relative;
            overflow: hidden;
            min-height: 2.5rem;
            font-size: clamp(0.75rem, 1.5vw, 0.9rem) !important;
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

        /* ===== CODE BLOCKS & DATAFRAMES ===== */
        .stCodeBlock {
            border-radius: var(--border-radius-md) !important;
            overflow: hidden !important;
            border: 1px solid rgba(0, 240, 255, 0.15) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
            background: #05010d !important;
            margin-bottom: var(--spacing-md) !important;
        }
        
        [data-testid="stDataFrame"] {
            border-radius: var(--border-radius-md) !important;
            overflow: hidden !important;
            border: 1px solid rgba(209, 0, 255, 0.15) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
            margin-bottom: var(--spacing-md) !important;
        }

        /* ===== QUICK ACTIONS ===== */
        .qa-container {
            margin: var(--spacing-xl) 0;
        }

        .qa-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: var(--spacing-md);
            margin-top: var(--spacing-md);
        }

        .qa-card {
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-radius: var(--border-radius-lg);
            background: linear-gradient(145deg, rgba(13, 6, 20, 0.7), rgba(5, 1, 13, 0.9));
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: var(--spacing-lg);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .qa-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, #00f0ff, #d100ff);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .qa-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(0, 240, 255, 0.4);
            box-shadow: 0 20px 50px rgba(0, 240, 255, 0.2), 0 0 30px rgba(209, 0, 255, 0.15);
        }

        .qa-card:hover::before {
            opacity: 1;
        }

        .qa-icon {
            font-size: clamp(2rem, 4vw, 2.5rem);
            margin-bottom: var(--spacing-sm);
            display: block;
            filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.3));
        }

        .qa-title {
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(0.95rem, 2vw, 1.1rem);
            font-weight: 700;
            color: #ffffff;
            margin-bottom: var(--spacing-sm);
            letter-spacing: 0.05em;
        }

        .qa-description {
            color: #a19fb0;
            font-size: clamp(0.85rem, 1.5vw, 0.95rem);
            line-height: 1.6;
            margin-bottom: var(--spacing-md);
            flex-grow: 1;
        }

        .qa-button {
            display: inline-block;
            padding: var(--spacing-sm) var(--spacing-md);
            background: linear-gradient(90deg, rgba(0, 240, 255, 0.1), rgba(209, 0, 255, 0.1));
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: var(--border-radius-sm);
            color: #00f0ff;
            font-size: clamp(0.75rem, 1.5vw, 0.85rem);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.3s ease;
            cursor: pointer;
            text-align: center;
        }

        .qa-button:hover {
            background: linear-gradient(90deg, rgba(0, 240, 255, 0.2), rgba(209, 0, 255, 0.2));
            border-color: #00f0ff;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
            color: #ffffff;
        }

        /* ===== AI WORKFLOW SUMMARY ===== */
        .workflow-summary {
            border: 1px solid rgba(0, 240, 255, 0.25);
            border-radius: var(--border-radius-lg);
            background: linear-gradient(145deg, rgba(0, 240, 255, 0.03), rgba(209, 0, 255, 0.03));
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: var(--spacing-lg);
            margin: var(--spacing-lg) 0;
            box-shadow: 0 10px 30px rgba(0, 240, 255, 0.1), inset 0 0 20px rgba(0, 240, 255, 0.02);
            position: relative;
            overflow: hidden;
        }

        .workflow-summary::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, transparent, #00f0ff, #d100ff, transparent);
            animation: shimmer 3s infinite;
        }

        @keyframes shimmer {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }

        .workflow-summary-title {
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(1rem, 2vw, 1.2rem);
            font-weight: 700;
            color: #00f0ff;
            margin-bottom: var(--spacing-md);
            letter-spacing: 0.05em;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
        }

        .workflow-summary-title::before {
            content: '🤖';
            font-size: 1.5rem;
            filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.5));
        }

        .workflow-section {
            margin-bottom: var(--spacing-md);
        }

        .workflow-section:last-child {
            margin-bottom: 0;
        }

        .workflow-section-header {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(0.9rem, 1.5vw, 1rem);
            font-weight: 600;
            color: #d100ff;
            margin-bottom: var(--spacing-xs);
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
        }

        .workflow-section-content {
            color: #e2e8f0;
            font-size: clamp(0.85rem, 1.5vw, 0.95rem);
            line-height: 1.7;
            padding-left: var(--spacing-lg);
        }

        .workflow-section-content ul {
            margin: 0;
            padding-left: var(--spacing-md);
            list-style: none;
        }

        .workflow-section-content li {
            position: relative;
            padding-left: var(--spacing-md);
            margin-bottom: var(--spacing-xs);
        }

        .workflow-section-content li::before {
            content: '▸';
            position: absolute;
            left: 0;
            color: #00f0ff;
            font-weight: bold;
        }

        .workflow-badge {
            display: inline-block;
            background: rgba(0, 240, 255, 0.1);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: var(--border-radius-sm);
            padding: var(--spacing-xs) var(--spacing-sm);
            font-size: 0.75rem;
            font-weight: 600;
            color: #00f0ff;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: var(--spacing-sm);
        }

        /* ===== AI PRODUCTIVITY SCORE ===== */
        .productivity-score-card {
            border: 2px solid rgba(0, 240, 255, 0.3);
            border-radius: var(--border-radius-xl);
            background: linear-gradient(145deg, rgba(13, 6, 20, 0.9), rgba(5, 1, 13, 0.95));
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: var(--spacing-2xl);
            margin: var(--spacing-xl) 0;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(0, 240, 255, 0.15);
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.8s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .productivity-score-card::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #00f0ff, #d100ff, #00f0ff);
            border-radius: var(--border-radius-xl);
            z-index: -1;
            opacity: 0.5;
            animation: rotateBorder 4s linear infinite;
        }

        @keyframes rotateBorder {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .score-header {
            text-align: center;
            margin-bottom: var(--spacing-xl);
        }

        .score-title {
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(1.2rem, 3vw, 1.5rem);
            font-weight: 700;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: var(--spacing-sm);
            text-shadow: 0 0 20px rgba(0, 240, 255, 0.5);
        }

        .score-subtitle {
            color: #a19fb0;
            font-size: clamp(0.9rem, 1.5vw, 1rem);
        }

        .score-display {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: var(--spacing-xl) auto;
            position: relative;
        }

        .score-circle {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            background: radial-gradient(circle, rgba(13, 6, 20, 0.8), rgba(5, 1, 13, 0.9));
            border: 3px solid;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .score-circle.excellent {
            border-color: #00ff88;
            box-shadow: 0 0 40px rgba(0, 255, 136, 0.6), inset 0 0 30px rgba(0, 255, 136, 0.1);
        }

        .score-circle.good {
            border-color: #00f0ff;
            box-shadow: 0 0 40px rgba(0, 240, 255, 0.6), inset 0 0 30px rgba(0, 240, 255, 0.1);
        }

        .score-circle.moderate {
            border-color: #ffcc00;
            box-shadow: 0 0 40px rgba(255, 204, 0, 0.6), inset 0 0 30px rgba(255, 204, 0, 0.1);
        }

        .score-circle.needs-improvement {
            border-color: #ff3366;
            box-shadow: 0 0 40px rgba(255, 51, 102, 0.6), inset 0 0 30px rgba(255, 51, 102, 0.1);
        }

        .score-number {
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(3rem, 8vw, 4.5rem);
            font-weight: 700;
            line-height: 1;
            margin: 0;
        }

        .score-circle.excellent .score-number {
            color: #00ff88;
            text-shadow: 0 0 30px rgba(0, 255, 136, 0.8);
        }

        .score-circle.good .score-number {
            color: #00f0ff;
            text-shadow: 0 0 30px rgba(0, 240, 255, 0.8);
        }

        .score-circle.moderate .score-number {
            color: #ffcc00;
            text-shadow: 0 0 30px rgba(255, 204, 0, 0.8);
        }

        .score-circle.needs-improvement .score-number {
            color: #ff3366;
            text-shadow: 0 0 30px rgba(255, 51, 102, 0.8);
        }

        .score-label {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(0.9rem, 2vw, 1.1rem);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-top: var(--spacing-xs);
        }

        .score-circle.excellent .score-label {
            color: #00ff88;
        }

        .score-circle.good .score-label {
            color: #00f0ff;
        }

        .score-circle.moderate .score-label {
            color: #ffcc00;
        }

        .score-circle.needs-improvement .score-label {
            color: #ff3366;
        }

        .score-dimensions {
            margin-top: var(--spacing-2xl);
            display: grid;
            gap: var(--spacing-md);
        }

        .dimension-item {
            background: rgba(13, 6, 20, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--border-radius-md);
            padding: var(--spacing-md);
            transition: all 0.3s ease;
        }

        .dimension-item:hover {
            background: rgba(20, 9, 30, 0.7);
            border-color: rgba(0, 240, 255, 0.3);
            transform: translateX(5px);
        }

        .dimension-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-xs);
        }

        .dimension-name {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(0.9rem, 1.5vw, 1rem);
            font-weight: 600;
            color: #ffffff;
        }

        .dimension-score {
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(0.85rem, 1.5vw, 0.95rem);
            font-weight: 700;
            padding: 0.2rem 0.6rem;
            border-radius: var(--border-radius-sm);
            background: rgba(0, 240, 255, 0.1);
            border: 1px solid rgba(0, 240, 255, 0.3);
        }

        .dimension-score.excellent { color: #00ff88; border-color: #00ff88; background: rgba(0, 255, 136, 0.1); }
        .dimension-score.good { color: #00f0ff; border-color: #00f0ff; background: rgba(0, 240, 255, 0.1); }
        .dimension-score.moderate { color: #ffcc00; border-color: #ffcc00; background: rgba(255, 204, 0, 0.1); }
        .dimension-score.needs-improvement { color: #ff3366; border-color: #ff3366; background: rgba(255, 51, 102, 0.1); }

        .dimension-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }

        .dimension-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease-out;
            position: relative;
            overflow: hidden;
        }

        .dimension-bar-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            animation: shimmerBar 2s infinite;
        }

        @keyframes shimmerBar {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        .dimension-bar-fill.excellent {
            background: linear-gradient(90deg, #00ff88, #00cc6a);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }

        .dimension-bar-fill.good {
            background: linear-gradient(90deg, #00f0ff, #00b8cc);
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }

        .dimension-bar-fill.moderate {
            background: linear-gradient(90deg, #ffcc00, #cc9900);
            box-shadow: 0 0 10px rgba(255, 204, 0, 0.5);
        }

        .dimension-bar-fill.needs-improvement {
            background: linear-gradient(90deg, #ff3366, #cc0033);
            box-shadow: 0 0 10px rgba(255, 51, 102, 0.5);
        }

        .score-suggestions {
            margin-top: var(--spacing-xl);
            padding: var(--spacing-lg);
            background: rgba(0, 240, 255, 0.03);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: var(--border-radius-md);
        }

        .suggestions-title {
            font-family: 'Syncopate', sans-serif;
            font-size: clamp(0.95rem, 2vw, 1.1rem);
            font-weight: 700;
            color: #00f0ff;
            margin-bottom: var(--spacing-sm);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .suggestions-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .suggestions-list li {
            color: #e2e8f0;
            font-size: clamp(0.85rem, 1.5vw, 0.95rem);
            line-height: 1.7;
            padding-left: var(--spacing-lg);
            margin-bottom: var(--spacing-xs);
            position: relative;
        }

        .suggestions-list li::before {
            content: '💡';
            position: absolute;
            left: 0;
            filter: drop-shadow(0 0 5px rgba(255, 204, 0, 0.5));
        }

        .score-badge-compact {
            display: inline-flex;
            align-items: center;
            gap: var(--spacing-xs);
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--border-radius-sm);
            font-family: 'Syncopate', sans-serif;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .score-badge-compact.excellent {
            background: rgba(0, 255, 136, 0.1);
            border-color: #00ff88;
            color: #00ff88;
        }

        .score-badge-compact.good {
            background: rgba(0, 240, 255, 0.1);
            border-color: #00f0ff;
            color: #00f0ff;
        }

        .score-badge-compact.moderate {
            background: rgba(255, 204, 0, 0.1);
            border-color: #ffcc00;
            color: #ffcc00;
        }

        .score-badge-compact.needs-improvement {
            background: rgba(255, 51, 102, 0.1);
            border-color: #ff3366;
            color: #ff3366;
        }

        .score-badge-compact:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px currentColor;
        }

        /* ===== RESPONSIVE DESIGN ===== */
        /* Tablet and below */
        @media (max-width: 768px) {
            .nl-hero {
                padding: var(--spacing-lg) var(--spacing-md);
                margin-bottom: var(--spacing-lg);
            }

            .nl-title {
                font-size: 2.5rem;
            }

            .nl-subtitle {
                font-size: 1rem;
            }

            .qa-grid {
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: var(--spacing-sm);
            }

            .qa-card {
                padding: var(--spacing-md);
            }

            .stTabs [data-baseweb="tab"] {
                padding-left: var(--spacing-sm);
                padding-right: var(--spacing-sm);
                font-size: 0.75rem;
            }

            div[data-testid="stMetric"] {
                padding: var(--spacing-sm) var(--spacing-md);
            }

            .nl-card {
                padding: var(--spacing-md);
            }

            section[data-testid="stSidebar"] {
                padding: var(--spacing-sm) !important;
            }
        }

        /* Mobile */
        @media (max-width: 480px) {
            .nl-hero {
                padding: var(--spacing-md) var(--spacing-sm);
                border-radius: var(--border-radius-md);
            }

            .nl-title {
                font-size: 2rem;
            }

            .nl-kicker {
                font-size: 0.7rem;
                letter-spacing: 0.2em;
            }

            .nl-subtitle {
                font-size: 0.9rem;
                margin-top: var(--spacing-sm);
            }

            .qa-grid {
                grid-template-columns: 1fr;
                gap: var(--spacing-sm);
            }

            .qa-card {
                padding: var(--spacing-sm);
            }

            .qa-icon {
                font-size: 1.8rem;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: var(--spacing-xs);
                padding: var(--spacing-xs);
            }

            .stTabs [data-baseweb="tab"] {
                height: 2.5rem;
                padding-left: var(--spacing-xs);
                padding-right: var(--spacing-xs);
                font-size: 0.7rem;
            }

            .stButton > button {
                padding: var(--spacing-xs) var(--spacing-sm) !important;
                font-size: 0.75rem !important;
                min-height: 2rem;
            }

            div[data-testid="stMetric"] {
                padding: var(--spacing-xs) var(--spacing-sm);
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.5rem;
            }

            .nl-card {
                padding: var(--spacing-sm);
                border-radius: var(--border-radius-md);
            }

            .nl-section-title {
                font-size: 0.95rem;
            }

            .nl-section-copy {
                font-size: 0.85rem;
            }
        }

        /* Large screens - optimize spacing */
        @media (min-width: 1400px) {
            .qa-grid {
                gap: var(--spacing-lg);
            }

            .nl-hero {
                padding: var(--spacing-3xl) var(--spacing-2xl);
            }
        }

        /* Ensure proper column spacing in Streamlit */
        .row-widget.stHorizontal {
            gap: var(--spacing-md) !important;
        }

        /* Fix button container width issues */
        .stButton {
            width: 100%;
        }

        /* Improve expander spacing */
        .streamlit-expanderHeader {
            border-radius: var(--border-radius-sm) !important;
            padding: var(--spacing-sm) var(--spacing-md) !important;
        }

        /* Better alert/info box spacing */
        .stAlert {
            margin-bottom: var(--spacing-md) !important;
            border-radius: var(--border-radius-md) !important;
            padding: var(--spacing-md) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="nl-hero">
            <div class="nl-kicker">AI-powered developer productivity assistant</div>
            <h1 class="nl-title">DevFlow AI</h1>
            <div class="nl-subtitle">
                Paste stack traces, SQL errors, or Python tracebacks and get plain-English explanations,
                targeted debugging steps, and suggested fixes — alongside SQL generation and visualization.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quick_actions() -> None:
    """Render Quick Actions section with sample prompts for common tasks."""
    st.markdown(
        """
        <div class="qa-container">
            <div class="nl-card nl-card-strong">
                <div class="nl-section-title">Quick Actions</div>
                <div class="nl-section-copy">Jump-start your workflow with these common developer tasks</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Sample prompt pools for dynamic rotation
    python_errors = [
        "AttributeError: 'NoneType' object has no attribute 'split'",
        "KeyError: 'user_id' not found in dictionary",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "IndexError: list index out of range",
        "ModuleNotFoundError: No module named 'requests'",
        "ValueError: invalid literal for int() with base 10: 'abc'",
        "FileNotFoundError: [Errno 2] No such file or directory: 'data.csv'"
    ]
    
    sql_queries = [
        "What are the top 10 products by sales?",
        "Show monthly revenue trends for the last year",
        "Which customers have the highest lifetime value?",
        "Compare sales performance across different regions",
        "What is the average order value by product category?",
        "Find products with declining sales in the last quarter",
        "Show customer retention rate by month"
    ]
    
    readme_prompts = [
        "Generate a README for a Python data analysis project",
        "Create documentation for a Streamlit dashboard application",
        "Write a README for a machine learning model training pipeline",
        "Generate README for a developer productivity tool",
        "Create documentation for a REST API backend service",
        "Write a README for a data visualization library"
    ]
    
    repo_examples = [
        "Explain the architecture of streamlit/streamlit repository",
        "Analyze the structure of pandas-dev/pandas codebase",
        "Describe the organization of microsoft/vscode repository",
        "Explain the architecture of langchain-ai/langchain project",
        "Analyze the structure of this DevFlow AI application",
        "Describe the organization of fastapi/fastapi repository"
    ]
    
    # Define quick action cards with dynamic prompts
    actions = [
        {
            "icon": "🐍",
            "title": "Explain Python Error",
            "description": "Paste a Python traceback and get instant debugging guidance",
            "prompt": random.choice(python_errors),
            "tab": 4  # Error Explainer tab
        },
        {
            "icon": "💾",
            "title": "Generate SQL Query",
            "description": "Ask a question in plain English and get executable SQL",
            "prompt": random.choice(sql_queries),
            "tab": 0  # Analytics tab
        },
        {
            "icon": "📝",
            "title": "Generate README",
            "description": "Create professional documentation for your project",
            "prompt": random.choice(readme_prompts),
            "tab": 4  # Error Explainer tab (can be used for general AI tasks)
        },
        {
            "icon": "🔍",
            "title": "Explain Repository",
            "description": "Get insights about codebase structure and architecture",
            "prompt": random.choice(repo_examples),
            "tab": 4  # Error Explainer tab
        }
    ]
    
    # Create grid layout
    cols = st.columns(4)
    
    for idx, action in enumerate(actions):
        with cols[idx]:
            st.markdown(
                f"""
                <div class="qa-card">
                    <span class="qa-icon">{action['icon']}</span>
                    <div class="qa-title">{action['title']}</div>
                    <div class="qa-description">{action['description']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Add button to use sample prompt
            if st.button(f"Try Sample", key=f"qa_btn_{idx}", use_container_width=True):
                if action['tab'] == 0:
                    st.session_state['user_question'] = action['prompt']
                    st.info(f"Sample prompt loaded: '{action['prompt']}' - Go to Analytics tab to execute!")
                elif action['tab'] == 4:
                    st.session_state['error_trace'] = action['prompt']
                    st.info(f"Sample prompt loaded: '{action['prompt']}' - Go to Error Explainer tab to analyze!")


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


def render_workflow_summary(
    context_type: str,
    insights: list[str],
    actions: list[str],
    next_steps: list[str],
    badge_text: str = "AI Copilot"
) -> None:
    """
    Render an AI Workflow Summary component with key insights, actions, and next steps.
    
    Args:
        context_type: Type of analysis (e.g., "Error Analysis", "Repository Analysis", "SQL Query")
        insights: List of key insights (2-3 items)
        actions: List of suggested actions (2-3 items)
        next_steps: List of next steps or productivity recommendations (2-3 items)
        badge_text: Text for the badge (default: "AI Copilot")
    """
    insights_html = "".join([f"<li>{insight}</li>" for insight in insights])
    actions_html = "".join([f"<li>{action}</li>" for action in actions])
    next_steps_html = "".join([f"<li>{step}</li>" for step in next_steps])
    
    summary_html = f"""
    <div class="workflow-summary">
        <div class="workflow-summary-title">AI Workflow Summary</div>
        
        <div class="workflow-section">
            <div class="workflow-section-header">🎯 Key Insights</div>
            <div class="workflow-section-content">
                <ul>{insights_html}</ul>
            </div>
        </div>
        
        <div class="workflow-section">
            <div class="workflow-section-header">🚀 Suggested Actions</div>
            <div class="workflow-section-content">
                <ul>{actions_html}</ul>
            </div>
        </div>
        
        <div class="workflow-section">
            <div class="workflow-section-header">💡 Next Steps</div>
            <div class="workflow-section-content">
                <ul>{next_steps_html}</ul>
            </div>
        </div>
        
        <span class="workflow-badge">{badge_text}</span>
    </div>
    """
    
    st.markdown(summary_html, unsafe_allow_html=True)


def extract_error_workflow_insights(explanation: str) -> tuple[list[str], list[str], list[str]]:
    """Extract workflow insights from error explanation text."""
    insights = []
    actions = []
    next_steps = []
    
    # Parse the explanation to extract structured information
    lines = explanation.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect sections
        if 'summary' in line.lower() or 'what' in line.lower():
            current_section = 'insights'
        elif 'cause' in line.lower() or 'why' in line.lower():
            current_section = 'insights'
        elif 'debug' in line.lower() or 'step' in line.lower() or 'fix' in line.lower():
            current_section = 'actions'
        elif 'suggest' in line.lower() or 'recommend' in line.lower():
            current_section = 'next_steps'
        
        # Extract bullet points or numbered items
        if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
            clean_line = line.lstrip('-•*123456789. ').strip()
            if len(clean_line) > 10:  # Ignore very short lines
                if current_section == 'insights' and len(insights) < 3:
                    insights.append(clean_line)
                elif current_section == 'actions' and len(actions) < 3:
                    actions.append(clean_line)
                elif current_section == 'next_steps' and len(next_steps) < 3:
                    next_steps.append(clean_line)
    
    # Provide defaults if extraction failed
    if not insights:
        insights = [
            "Error has been analyzed by AI",
            "Root cause identified in the explanation above",
            "Debugging guidance provided"
        ]
    
    if not actions:
        actions = [
            "Review the error explanation carefully",
            "Check the suggested fixes section",
            "Test the proposed solutions incrementally"
        ]
    
    if not next_steps:
        next_steps = [
            "Implement the suggested fixes",
            "Add error handling to prevent recurrence",
            "Document the solution for future reference"
        ]
    
    return insights[:3], actions[:3], next_steps[:3]


def extract_repo_workflow_insights(analysis: dict) -> tuple[list[str], list[str], list[str]]:
    """Extract workflow insights from repository analysis."""
    insights = []
    actions = []
    next_steps = []
    
    # Extract insights from summary and architecture
    if analysis.get('summary'):
        summary_text = analysis['summary'][:100] + "..." if len(analysis['summary']) > 100 else analysis['summary']
        insights.append(f"Project purpose: {summary_text}")
    
    if analysis.get('tech_stack'):
        tech_count = len(analysis['tech_stack'])
        tech_list = ', '.join(analysis['tech_stack'][:3])
        insights.append(f"Uses {tech_count} technologies including {tech_list}")
    
    if analysis.get('architecture'):
        insights.append("Architecture patterns and design identified")
    
    # Extract actions from improvements
    if analysis.get('improvements'):
        for improvement in analysis['improvements'][:3]:
            short_improvement = improvement[:150] + "..." if len(improvement) > 150 else improvement
            actions.append(short_improvement)
    
    # Extract next steps from productivity insights
    if analysis.get('productivity_insights'):
        for insight in analysis['productivity_insights'][:3]:
            short_insight = insight[:150] + "..." if len(insight) > 150 else insight
            next_steps.append(short_insight)
    
    # Provide defaults if needed
    if not insights:
        insights = ["Repository structure analyzed", "Codebase patterns identified", "Tech stack detected"]
    
    if not actions:
        actions = ["Review the architecture explanation", "Consider the improvement suggestions", "Evaluate tech stack choices"]
    
    if not next_steps:
        next_steps = ["Implement suggested improvements", "Optimize code organization", "Enhance documentation"]
    
    return insights[:3], actions[:3], next_steps[:3]


def extract_sql_workflow_insights(question: str, result_df, insight: str) -> tuple[list[str], list[str], list[str]]:
    """Extract workflow insights from SQL query results."""
    insights = []
    actions = []
    next_steps = []
    
    # Generate insights based on query results
    row_count = len(result_df)
    col_count = len(result_df.columns)
    
    insights.append(f"Query returned {row_count:,} rows with {col_count} columns")
    
    # Truncate insight if too long
    short_insight = insight[:100] + "..." if len(insight) > 100 else insight
    insights.append(f"Analysis: {short_insight}")
    
    if row_count > 0:
        insights.append("Data successfully retrieved and visualized")
    else:
        insights.append("Query executed but returned no results")
    
    # Suggest actions based on results
    if row_count > 100:
        actions.append("Consider adding filters to narrow down results")
        actions.append("Export data for deeper analysis in external tools")
    else:
        actions.append("Results are manageable - review the visualization")
        actions.append("Refine query if more data is needed")
    
    actions.append("Download CSV for offline analysis if needed")
    
    # Next steps for productivity
    next_steps.append("Save this query for future reference")
    next_steps.append("Create a dashboard with multiple related queries")
    next_steps.append("Share insights with your team")
    
    return insights[:3], actions[:3], next_steps[:3]


def calculate_productivity_score(repo_info: dict, analysis: dict) -> dict:
    """
    Calculate AI Productivity Score based on repository data and analysis.
    Returns a dict with overall score, dimension scores, and suggestions.
    
    Score Dimensions (weighted):
    - Documentation Quality (20%): README, comments, docstrings
    - Architecture Clarity (25%): Structure, organization, modularity
    - Debugging Readiness (20%): Error handling, logging, tests
    - Workflow Efficiency (20%): CI/CD, automation, dependencies
    - AI Readiness (15%): Code clarity, naming, API docs
    """
    
    dimensions = {}
    
    # 1. Documentation Quality (20%)
    doc_score = 0
    readme_length = len(repo_info.get('readme', ''))
    if readme_length > 2000:
        doc_score += 40
    elif readme_length > 1000:
        doc_score += 30
    elif readme_length > 500:
        doc_score += 20
    else:
        doc_score += 10
    
    # Check for description
    if repo_info.get('description'):
        doc_score += 20
    
    # Check for topics/tags
    if len(repo_info.get('topics', [])) >= 3:
        doc_score += 20
    elif len(repo_info.get('topics', [])) >= 1:
        doc_score += 10
    
    # Check file structure for docs
    files = repo_info.get('file_structure', [])
    if any('LICENSE' in f.upper() for f in files):
        doc_score += 10
    if any('CONTRIBUTING' in f.upper() for f in files):
        doc_score += 10
    
    dimensions['Documentation Quality'] = min(100, doc_score)
    
    # 2. Architecture Clarity (25%)
    arch_score = 0
    
    # Check for organized structure
    common_dirs = ['src', 'lib', 'app', 'tests', 'docs', 'config', 'utils']
    dir_count = sum(1 for d in common_dirs if any(d in f.lower() for f in files))
    arch_score += min(40, dir_count * 8)
    
    # Check for config files
    config_files = ['package.json', 'requirements.txt', 'setup.py', 'pyproject.toml', 'Cargo.toml', 'go.mod']
    if any(cf in files for cf in config_files):
        arch_score += 20
    
    # Check language diversity (but not too many)
    lang_count = len(repo_info.get('languages', {}))
    if 2 <= lang_count <= 5:
        arch_score += 20
    elif lang_count == 1:
        arch_score += 15
    else:
        arch_score += 10
    
    # Bonus for analysis mentioning good architecture
    if analysis and 'architecture' in analysis.get('architecture', '').lower():
        arch_score += 20
    
    dimensions['Architecture Clarity'] = min(100, arch_score)
    
    # 3. Debugging Readiness (20%)
    debug_score = 0
    
    # Check for test files
    test_indicators = ['test', 'spec', '__tests__', 'tests']
    if any(ti in ' '.join(files).lower() for ti in test_indicators):
        debug_score += 30
    
    # Check for CI/CD
    ci_files = ['.github', '.gitlab-ci', 'Jenkinsfile', '.travis.yml', 'circle.yml']
    if any(ci in ' '.join(files).lower() for ci in ci_files):
        debug_score += 25
    
    # Check for logging/error handling mentions
    if analysis:
        improvements = ' '.join(analysis.get('improvements', []))
        if 'error' in improvements.lower() or 'logging' in improvements.lower():
            debug_score += 15
        else:
            debug_score += 25  # Assume good if not mentioned as improvement
    
    # Stars indicate community trust
    stars = repo_info.get('stars', 0)
    if stars > 1000:
        debug_score += 20
    elif stars > 100:
        debug_score += 15
    elif stars > 10:
        debug_score += 10
    
    dimensions['Debugging Readiness'] = min(100, debug_score)
    
    # 4. Workflow Efficiency (20%)
    workflow_score = 0
    
    # CI/CD presence
    if any(ci in ' '.join(files).lower() for ci in ci_files):
        workflow_score += 30
    
    # Dependency management
    dep_files = ['package.json', 'requirements.txt', 'Gemfile', 'Cargo.toml', 'go.mod', 'pom.xml']
    if any(df in files for df in dep_files):
        workflow_score += 25
    
    # Docker/containerization
    if any('docker' in f.lower() for f in files):
        workflow_score += 20
    
    # Scripts/automation
    script_dirs = ['scripts', 'bin', '.github/workflows']
    if any(sd in ' '.join(files).lower() for sd in script_dirs):
        workflow_score += 15
    
    # Recent activity
    if repo_info.get('open_issues', 0) < 50:
        workflow_score += 10
    
    dimensions['Workflow Efficiency'] = min(100, workflow_score)
    
    # 5. AI Readiness (15%)
    ai_score = 0
    
    # Good README helps AI understand
    if readme_length > 1500:
        ai_score += 30
    elif readme_length > 800:
        ai_score += 20
    else:
        ai_score += 10
    
    # Clear tech stack
    if len(repo_info.get('languages', {})) <= 5:
        ai_score += 20
    
    # Topics help categorization
    if len(repo_info.get('topics', [])) >= 3:
        ai_score += 20
    elif len(repo_info.get('topics', [])) >= 1:
        ai_score += 10
    
    # Analysis quality indicates code clarity
    if analysis and len(analysis.get('tech_stack', [])) >= 3:
        ai_score += 15
    
    # Description clarity
    if repo_info.get('description') and len(repo_info.get('description', '')) > 50:
        ai_score += 15
    
    dimensions['AI Readiness'] = min(100, ai_score)
    
    # Calculate weighted overall score
    weights = {
        'Documentation Quality': 0.20,
        'Architecture Clarity': 0.25,
        'Debugging Readiness': 0.20,
        'Workflow Efficiency': 0.20,
        'AI Readiness': 0.15
    }
    
    overall_score = sum(dimensions[dim] * weights[dim] for dim in dimensions)
    overall_score = int(overall_score)
    
    # Generate suggestions for lower-scoring dimensions
    suggestions = []
    for dim, score in dimensions.items():
        if score < 70:
            if dim == 'Documentation Quality':
                suggestions.append("Enhance README with setup instructions, usage examples, and API documentation")
            elif dim == 'Architecture Clarity':
                suggestions.append("Organize code into clear modules/packages with separation of concerns")
            elif dim == 'Debugging Readiness':
                suggestions.append("Add comprehensive test coverage and implement CI/CD pipelines")
            elif dim == 'Workflow Efficiency':
                suggestions.append("Set up automated workflows, dependency management, and containerization")
            elif dim == 'AI Readiness':
                suggestions.append("Improve code documentation and add descriptive comments for AI analysis")
    
    # Limit to top 3 suggestions
    suggestions = suggestions[:3]
    
    # If score is high, add positive reinforcement
    if overall_score >= 80 and not suggestions:
        suggestions = [
            "Excellent work! Consider sharing your best practices with the community",
            "Maintain this quality by keeping documentation up-to-date",
            "Your codebase is well-structured for AI-assisted development"
        ]
    
    return {
        'overall_score': overall_score,
        'dimensions': dimensions,
        'suggestions': suggestions
    }


def get_score_category(score: int) -> tuple[str, str]:
    """Return category label and CSS class for a score."""
    if score >= 90:
        return "Excellent", "excellent"
    elif score >= 70:
        return "Good", "good"
    elif score >= 50:
        return "Moderate", "moderate"
    else:
        return "Needs Improvement", "needs-improvement"


def render_productivity_score_card(score_data: dict) -> None:
    """Render the AI Productivity Score card with full details."""
    overall_score = score_data['overall_score']
    dimensions = score_data['dimensions']
    suggestions = score_data['suggestions']
    
    category_label, category_class = get_score_category(overall_score)
    
    # Build dimension items HTML
    dimension_items_html = ""
    for dim_name, dim_score in dimensions.items():
        dim_category_label, dim_category_class = get_score_category(dim_score)
        dimension_items_html += f"""
        <div class="dimension-item">
            <div class="dimension-header">
                <span class="dimension-name">{dim_name}</span>
                <span class="dimension-score {dim_category_class}">{dim_score}/100</span>
            </div>
            <div class="dimension-bar">
                <div class="dimension-bar-fill {dim_category_class}" style="width: {dim_score}%;"></div>
            </div>
        </div>
        """
    
    # Build suggestions HTML
    suggestions_html = ""
    if suggestions:
        suggestions_items = "".join([f"<li>{sug}</li>" for sug in suggestions])
        suggestions_html = f"""
        <div class="score-suggestions">
            <div class="suggestions-title">💡 Recommendations</div>
            <ul class="suggestions-list">
                {suggestions_items}
            </ul>
        </div>
        """
    
    # Render the complete card
    card_html = f"""
    <div class="productivity-score-card">
        <div class="score-header">
            <div class="score-title">🤖 AI Productivity Score</div>
            <div class="score-subtitle">Comprehensive analysis of repository quality and developer readiness</div>
        </div>
        
        <div class="score-display">
            <div class="score-circle {category_class}">
                <div class="score-number">{overall_score}</div>
                <div class="score-label">{category_label}</div>
            </div>
        </div>
        
        <div class="score-dimensions">
            {dimension_items_html}
        </div>
        
        {suggestions_html}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_score_badge_compact(score: int) -> str:
    """Return HTML for a compact score badge."""
    category_label, category_class = get_score_category(score)
    return f'<span class="score-badge-compact {category_class}">⚡ Score: {score}/100</span>'


def render_sidebar() -> None:
    st.sidebar.title("⚙️ DevFlow AI")
    st.sidebar.markdown(
        """
        **AI-powered developer workflow assistant**

        Explain errors, generate SQL, and accelerate debugging.
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


def ensure_dataset_loaded() -> bool:
    """Load train.xlsx into SQLite if the train table has not been created yet."""
    if table_exists("train"):
        return True

    if not os.path.exists(TRAIN_XLSX_PATH):
        return False

    return load_excel_to_sqlite(TRAIN_XLSX_PATH, "train")


def adjust_trend_sql_for_dataset(question: str, sql_query: str) -> str:
    """Replace current-date trend filters with dataset-relative windows when needed."""
    question_text = question.lower()
    sql_text = sql_query.lower()

    if not any(keyword in question_text for keyword in ["trend", "monthly", "month", "last year", "last 12 months"]):
        return sql_query

    if "now" not in sql_text and "date('now'" not in sql_text and "datetime('now'" not in sql_text:
        return sql_query

    replacements = [
        (r"(?i)date\(\s*'now'\s*,\s*'-1 year'\s*\)", "DATE((SELECT MAX(`Order_Date`) FROM `train`), '-1 year')"),
        (r"(?i)date\(\s*'now'\s*,\s*'-12 months'\s*\)", "DATE((SELECT MAX(`Order_Date`) FROM `train`), '-12 months')"),
        (r"(?i)datetime\(\s*'now'\s*,\s*'-1 year'\s*\)", "DATETIME((SELECT MAX(`Order_Date`) FROM `train`), '-1 year')"),
        (r"(?i)datetime\(\s*'now'\s*,\s*'-12 months'\s*\)", "DATETIME((SELECT MAX(`Order_Date`) FROM `train`), '-12 months')"),
    ]

    adjusted_sql = sql_query
    for pattern, replacement in replacements:
        adjusted_sql = re.sub(pattern, replacement, adjusted_sql)

    return adjusted_sql


def check_prerequisites() -> tuple[list[str], list[str]]:
    """
    Return (blocking_issues, warnings).

    blocking_issues  – problems that prevent the app from running at all
                       (e.g. database not loaded).
    warnings         – non-fatal config gaps that degrade functionality
                       (e.g. missing API key on a hosted deployment).
    """
    blocking: list[str] = []
    warnings: list[str] = []

    if not table_exists("train"):
        blocking.append(
            "Database not loaded. The app could not initialize from train.xlsx. "
            "Run: **python load_data.py** locally or ship the dataset file with the deployment."
        )

    if not validate_api_key():
        warnings.append(
            "**Groq API key not configured.** "
            "The AI query feature is disabled.\n\n"
            "**To fix locally:** add `GROQ_API_KEY=<your-key>` to your `.env` file.\n\n"
            "**To fix on deployment (Streamlit Cloud / Render / Railway):** "
            "add `GROQ_API_KEY` as a platform secret / environment variable — "
            "never commit your `.env` to the repository. "
            "Get a free key at [console.groq.com/keys](https://console.groq.com/keys)."
        )

    return blocking, warnings


def main() -> None:
    """Main application flow."""
    dataset_bootstrapped = False
    if not table_exists("train"):
        dataset_bootstrapped = ensure_dataset_loaded()

    apply_styles()
    render_sidebar()
    render_hero()
    render_quick_actions()

    if dataset_bootstrapped:
        st.success("Initialized the database from train.xlsx for this deployment.")

    blocking, warnings = check_prerequisites()

    # Hard stop — nothing works without the database.
    if blocking:
        st.error("\u26a0\ufe0f Setup required before DevFlow AI can run:")
        for issue in blocking:
            st.markdown(f"- {issue}")
        st.stop()

    # Soft warning — app works but AI queries are disabled.
    api_ready = not warnings
    if warnings:
        for msg in warnings:
            st.info(msg, icon="\U0001f511")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Analytics", "Generated SQL", "Insights", "Schema", "Error Explainer", "Repository Explainer"])

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
            run_query = st.button(
                "🚀 Generate & Execute",
                key="run_query_btn",
                disabled=not api_ready,
                help="Configure GROQ_API_KEY to enable AI queries." if not api_ready else None,
            )
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

                    adjusted_sql_query = adjust_trend_sql_for_dataset(user_question, sql_query)
                    if adjusted_sql_query != sql_query:
                        sql_query = adjusted_sql_query
                        explanation = (
                            f"{explanation} "
                            "The date window was adjusted to the dataset's own timeline so the trend shows real rows."
                        )

                    st.subheader("Generated SQL")
                    st.code(sql_query, language="sql")

                    st.subheader("Answer")
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
                    insight_text = generate_local_insight(result_df)
                    st.success(insight_text)
                    
                    # Add AI Workflow Summary for SQL Analytics
                    st.write("---")
                    insights, actions, next_steps = extract_sql_workflow_insights(
                        user_question, result_df, insight_text
                    )
                    render_workflow_summary(
                        "SQL Query Analysis",
                        insights,
                        actions,
                        next_steps,
                        "SQL Copilot"
                    )

                    st.subheader("Visualization")
                    chart_type = detect_chart_type(result_df)
                    chart = render_chart(result_df, chart_type)
                    if chart is not None:
                        st.plotly_chart(chart, use_container_width=True)
                    else:
                        st.info("No chartable visualization could be generated for this result.")

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

        with tab5:
            st.markdown(
                """
                <div class='nl-card nl-card-strong'>
                    <div class='nl-section-title'>Error Explainer</div>
                    <div class='nl-section-copy'>Paste a stack trace, SQL error, or traceback and get a plain-English explanation and debugging steps.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            trace_text = st.text_area(
                "Paste stack trace or error message:",
                height=200,
                placeholder="Example: Traceback (most recent call last): ...",
                key="error_trace",
            )

            col1, col2 = st.columns([1, 3])
            with col1:
                explain_btn = st.button("🛠️ Explain Error", key="explain_error_btn")
            with col2:
                st.caption("DevFlow AI will summarize the error and suggest targeted debugging steps.")

            if explain_btn:
                if not trace_text:
                    st.warning("Please paste an error or traceback first.")
                else:
                    with st.spinner("Analyzing error with AI..."):
                        explanation = explain_error_text(trace_text)
                        st.subheader("Explanation")
                        st.info(explanation)
                        
                        # Add AI Workflow Summary for Error Explainer
                        st.write("---")
                        insights, actions, next_steps = extract_error_workflow_insights(explanation)
                        render_workflow_summary(
                            "Error Analysis",
                            insights,
                            actions,
                            next_steps,
                            "Debug Copilot"
                        )


    with tab6:
        st.markdown(
            """
            <div class='nl-card nl-card-strong'>
                <div class='nl-section-title'>Repository Explainer</div>
                <div class='nl-section-copy'>Analyze any GitHub repository to understand its architecture, tech stack, and get AI-powered improvement suggestions.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        repo_url = st.text_input(
            "Enter GitHub Repository URL:",
            placeholder="https://github.com/username/repository",
            key="repo_url_input",
            help="Enter a public GitHub repository URL to analyze"
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            analyze_btn = st.button("🔍 Analyze Repository", key="analyze_repo_btn", disabled=not api_ready)
        with col2:
            if not api_ready:
                st.caption("⚠️ Configure GROQ_API_KEY to enable repository analysis")
            else:
                st.caption("DevFlow AI will analyze the repository structure and provide comprehensive insights")

        if analyze_btn:
            if not repo_url:
                st.warning("Please enter a GitHub repository URL first.")
            else:
                with st.spinner("Fetching repository information..."):
                    success, message, repo_info, analysis = explain_repository(repo_url)
                    
                    if not success:
                        st.error(f"❌ {message}")
                    else:
                        st.success(f"✅ {message}")
                        
                        # Display repository metadata
                        if repo_info:
                            st.write("---")
                            st.subheader("📊 Repository Overview")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("⭐ Stars", f"{repo_info['stars']:,}")
                            with col2:
                                st.metric("🔱 Forks", f"{repo_info['forks']:,}")
                            with col3:
                                st.metric("🐛 Open Issues", f"{repo_info['open_issues']:,}")
                            with col4:
                                st.metric("💻 Primary Language", repo_info['language'] or "N/A")
                            
                            if repo_info['description']:
                                st.markdown(
                                    f"""
                                    <div class='nl-card'>
                                        <div class='nl-section-title'>Description</div>
                                        <div class='nl-section-copy'>{repo_info['description']}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            
                            if repo_info['topics']:
                                st.markdown("**Topics:**")
                                topics_html = "".join([f"<span class='nl-pill'>{topic}</span>" for topic in repo_info['topics']])
                                st.markdown(topics_html, unsafe_allow_html=True)
                        
                        # Display AI analysis
                        if analysis:
                            st.write("---")
                            st.subheader("🤖 AI-Powered Analysis")
                            
                            # Project Summary
                            st.markdown(
                                f"""
                                <div class='nl-card nl-card-strong'>
                                    <div class='nl-section-title'>📝 Project Summary</div>
                                    <div class='nl-section-copy'>{analysis.get('summary', 'No summary available')}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            
                            # Architecture Explanation
                            st.markdown(
                                f"""
                                <div class='nl-card'>
                                    <div class='nl-section-title'>🏗️ Architecture Explanation</div>
                                    <div class='nl-section-copy'>{analysis.get('architecture', 'No architecture details available')}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            
                            # Tech Stack
                            if analysis.get('tech_stack'):
                                st.markdown("### 💻 Detected Tech Stack")
                                tech_cols = st.columns(3)
                                for idx, tech in enumerate(analysis['tech_stack']):
                                    with tech_cols[idx % 3]:
                                        st.markdown(f"<span class='nl-pill'>{tech}</span>", unsafe_allow_html=True)
                            
                            # Improvements
                            if analysis.get('improvements'):
                                st.markdown("### 🚀 Possible Improvements")
                                for idx, improvement in enumerate(analysis['improvements'], 1):
                                    st.markdown(
                                        f"""
                                        <div class='nl-card'>
                                            <div class='nl-section-copy'><strong>{idx}.</strong> {improvement}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                            
                            # Productivity Insights
                            if analysis.get('productivity_insights'):
                                st.markdown("### ⚡ Developer Productivity Insights")
                                for idx, insight in enumerate(analysis['productivity_insights'], 1):
                                    st.markdown(
                                        f"""
                                        <div class='nl-card'>
                                            <div class='nl-section-copy'><strong>{idx}.</strong> {insight}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                            
                            # Add AI Productivity Score
                            st.write("---")
                            with st.spinner("Calculating AI Productivity Score..."):
                                score_data = calculate_productivity_score(repo_info, analysis)
                                render_productivity_score_card(score_data)
                            
                            # Add AI Workflow Summary for Repository Explainer
                            st.write("---")
                            insights, actions, next_steps = extract_repo_workflow_insights(analysis)
                            render_workflow_summary(
                                "Repository Analysis",
                                insights,
                                actions,
                                next_steps,
                                "Repo Copilot"
                            )


if __name__ == "__main__":
    main()
