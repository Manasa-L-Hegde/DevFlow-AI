# DevFlow AI — AI-powered developer productivity assistant

DevFlow AI helps developers accelerate debugging, SQL workflows, and data exploration by combining simple Streamlit UI with AI-powered explanations and SQL generation. It is a lightweight, hackathon-friendly app built to demo AI-assisted developer workflows.

New repo: https://github.com/Manasa-L-Hegde/DevFlow-AI.git

## Problem Statement

Developers spend too much time deciphering stack traces, fixing SQL errors, and writing ad-hoc queries. DevFlow AI shortens that loop by explaining errors in plain English, suggesting debugging steps, and generating SQL from natural language — all in a simple, shareable demo app.

## Key Features

- Error Explainer: Paste a stack trace or SQL error and get a clear explanation plus prioritized debugging steps.
- Natural Language → SQL: Convert English questions into SQLite queries using Groq/OpenAI-compatible APIs.
- Live Query Execution: Run generated SQL against a local SQLite dataset.
- Visualizations: Auto-detect chart types and render Plotly charts for results.
- Schema Explorer: View schema as ascii tree and mermaid diagram to understand table relationships.
- Query History & CSV export: Keep and export query results for collaboration.

## Tech Stack

- Frontend: Streamlit
- LLM: Groq (OpenAI-compatible SDK)
- Database: SQLite
- Visualization: Plotly
- Data: pandas, numpy

## IBM Bob

This project was adapted to demonstrate an IBM Bob integration-style workflow. The UI and modular design make it easy to plug into chat-based assistants like IBM Bob for additional orchestration and context-aware interactions.

## Getting Started (Local Demo)

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Add your Groq API key to `.env`

```text
GROQ_API_KEY=gsk_your_key_here
```

3. Load the sample data (if `train.xlsx` is present)

```bash
python load_data.py
```

4. Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 to try the demo.

## Error Explainer Usage

1. Open the `Error Explainer` tab.
2. Paste a stack trace, SQL error, or Python traceback.
3. Click `Explain Error` to receive a summary, possible causes, concrete debug steps, and suggested fixes.

## Deployment

- The app is lightweight and suitable for Streamlit Cloud, Render, or Railway. Ensure `GROQ_API_KEY` is added as a platform secret.
- Do not commit `.env` to source control.

## Future Improvements

- Add code-aware fixes (patch suggestions) with diffs.
- Add multi-file trace navigation and source linking.
- Support more LLM providers and local models.
- Add user authentication for team demos.

## Screenshots

- Placeholder: screenshot_hero.png — hero and analytics tabs
- Placeholder: screenshot_error_explainer.png — error explainer results

## Suggested Commit Message

"chore: rebrand NLytics -> DevFlow AI; add Error Explainer, update README"

---

If you'd like, I can also prepare a lightweight demo script that exercises the Error Explainer and SQL generation for the README screenshots.
**Happy analyzing! 📊✨**
