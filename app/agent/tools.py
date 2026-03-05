"""Tools for the Agent."""

import trafilatura
import requests
from typing import Optional
from langchain_core.tools import tool


@tool
def fetch_url_content(url: str) -> str:
    """
    Fetch and extract main content from a URL.

    This tool extracts the article text from any webpage,
    including news articles, blog posts, technical documents, etc.

    Args:
        url: The URL to fetch content from

    Returns:
        Extracted text content, or error message if failed
    """
    if not url:
        return "Error: URL cannot be empty"

    # Validate URL
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    try:
        # Use trafilatura for smart content extraction
        downloaded = trafilatura.fetch_url(url)

        if downloaded is None:
            # Fallback to requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            downloaded = response.text

        # Extract content
        result = trafilatura.extract(
            downloaded, include_links=True, include_images=True, output_format="json"
        )

        if result:
            import json

            data = json.loads(result)
            text = data.get("text", "")

            if text and len(text) > 100:
                # Return with title
                title = data.get("title", "Untitled")
                return f"## {title}\n\n{text}"
            else:
                return "Error: Could not extract meaningful content from this URL"
        else:
            return "Error: Could not extract content from this webpage"

    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try a different URL."
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to fetch URL - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def summarize_text(text: str, max_length: int = 500) -> str:
    """
    Summarize the given text into a concise summary.

    Args:
        text: The text to summarize
        max_length: Maximum length of summary in characters

    Returns:
        A concise summary
    """
    if not text:
        return "Error: No text provided"

    if len(text) <= max_length:
        return text

    # Extract key sentences (simple extraction-based summarization)
    sentences = text.replace("\n", " ").split(". ")
    if len(sentences) <= 3:
        return text[:max_length] + "..."

    # Take first and last few sentences
    summary = ". ".join(sentences[:3]) + "..."
    return summary


# List of tools available to the agent
AVAILABLE_TOOLS = [fetch_url_content, summarize_text]
