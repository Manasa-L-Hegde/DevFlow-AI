"""
Repository Explainer Module
Analyzes GitHub repositories and provides AI-powered insights
"""

import os
import re
import json
from typing import Dict, Optional, Tuple
import requests
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)


def get_openai_client():
    """Create an OpenAI-compatible client configured for Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key or OpenAI is None:
        return None
    
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Parse GitHub URL to extract owner and repo name.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo) or None if invalid
    """
    # Remove .git suffix if present
    url = url.rstrip('/').replace('.git', '')
    
    # Match various GitHub URL formats
    patterns = [
        r'github\.com[:/]([^/]+)/([^/]+)',
        r'github\.com/([^/]+)/([^/]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    
    return None


def fetch_repo_info(owner: str, repo: str) -> Optional[Dict]:
    """
    Fetch repository information from GitHub API.
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Dictionary with repo info or None if failed
    """
    try:
        # Fetch basic repo info
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Add GitHub token if available (for higher rate limits)
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        response = requests.get(repo_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        repo_data = response.json()
        
        # Fetch README
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        readme_response = requests.get(readme_url, headers=headers, timeout=10)
        readme_content = ""
        
        if readme_response.status_code == 200:
            readme_data = readme_response.json()
            # Decode base64 content
            import base64
            readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8", errors="ignore")
            # Limit README length
            readme_content = readme_content[:3000]
        
        # Fetch languages
        languages_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        languages_response = requests.get(languages_url, headers=headers, timeout=10)
        languages = {}
        
        if languages_response.status_code == 200:
            languages = languages_response.json()
        
        # Fetch directory structure (root level)
        contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        contents_response = requests.get(contents_url, headers=headers, timeout=10)
        file_structure = []
        
        if contents_response.status_code == 200:
            contents = contents_response.json()
            file_structure = [item["name"] for item in contents if isinstance(item, dict)]
        
        return {
            "name": repo_data.get("name", ""),
            "description": repo_data.get("description", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "language": repo_data.get("language", ""),
            "topics": repo_data.get("topics", []),
            "readme": readme_content,
            "languages": languages,
            "file_structure": file_structure,
            "created_at": repo_data.get("created_at", ""),
            "updated_at": repo_data.get("updated_at", ""),
            "open_issues": repo_data.get("open_issues_count", 0),
            "url": repo_data.get("html_url", ""),
        }
        
    except Exception as e:
        print(f"Error fetching repo info: {e}")
        return None


def analyze_repository(repo_info: Dict) -> Optional[Dict]:
    """
    Use AI to analyze repository and generate insights.
    
    Args:
        repo_info: Repository information dictionary
        
    Returns:
        Dictionary with analysis results or None if failed
    """
    client = get_openai_client()
    
    if client is None:
        return None
    
    # Prepare context for AI
    languages_str = ", ".join([f"{lang} ({bytes})" for lang, bytes in repo_info["languages"].items()])
    files_str = ", ".join(repo_info["file_structure"][:20])  # Limit to first 20 files
    
    system_prompt = """You are an expert software architect and code analyst for DevFlow AI.

Your task is to analyze GitHub repositories and provide comprehensive, actionable insights for developers.

Provide analysis in the following structured format (return valid JSON):
{
    "summary": "A concise 2-3 sentence overview of what this project does and its purpose",
    "architecture": "Detailed explanation of the project architecture, design patterns, and code organization",
    "tech_stack": ["List of technologies, frameworks, and tools detected"],
    "improvements": ["List of 3-5 specific, actionable improvement suggestions"],
    "productivity_insights": ["List of 3-5 insights about developer productivity, code quality, or workflow optimization"]
}

Be specific, professional, and focus on actionable insights that help developers understand and improve the codebase."""

    user_message = f"""Analyze this GitHub repository:

**Repository:** {repo_info['name']}
**Description:** {repo_info['description']}
**Primary Language:** {repo_info['language']}
**Stars:** {repo_info['stars']} | **Forks:** {repo_info['forks']}
**Topics:** {', '.join(repo_info['topics'])}

**Languages Used:**
{languages_str}

**Root Files/Directories:**
{files_str}

**README Content (first 3000 chars):**
{repo_info['readme'][:3000]}

Provide a comprehensive analysis following the JSON format specified."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        ai_response = response.choices[0].message.content or ""
        
        try:
            analysis = json.loads(ai_response)
            return analysis
        except json.JSONDecodeError:
            return None
            
    except Exception as e:
        print(f"Error analyzing repository: {e}")
        return None


def explain_repository(github_url: str) -> Tuple[bool, str, Optional[Dict], Optional[Dict]]:
    """
    Main function to explain a GitHub repository.
    
    Args:
        github_url: GitHub repository URL
        
    Returns:
        Tuple of (success, message, repo_info, analysis)
    """
    # Parse URL
    parsed = parse_github_url(github_url)
    if not parsed:
        return False, "Invalid GitHub URL. Please provide a valid repository URL.", None, None
    
    owner, repo = parsed
    
    # Fetch repo info
    repo_info = fetch_repo_info(owner, repo)
    if not repo_info:
        return False, f"Could not fetch repository information. Please check if the repository exists and is public.", None, None
    
    # Analyze with AI
    analysis = analyze_repository(repo_info)
    if not analysis:
        return False, "Could not generate AI analysis. Please check your Groq API key configuration.", repo_info, None
    
    return True, "Analysis completed successfully!", repo_info, analysis

# Made with Bob
