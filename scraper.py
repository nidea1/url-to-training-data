"""Web scraping functionality for BDO guides."""

import re
import logging
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class WebScraper:
    """Handles web content scraping from different sources."""
    
    def __init__(self, timeout: int = 180):
        """
        Initialize the web scraper.
        
        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
    
    def scrape_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetch title and main content from a URL.
        
        Uses different strategies based on the URL domain:
        - blackdesertfoundry.com: Uses urltomarkdown API
        - Others: Uses Jina AI Reader API
        
        Args:
            url: The URL to scrape.
            
        Returns:
            Dictionary with 'title', 'url', and 'content' keys, or None on failure.
        """
        logger.info(f"Fetching data from: {url}")
        
        try:
            if "blackdesertfoundry.com" in url:
                return self._scrape_with_urltomarkdown(url)
            elif any(domain in url for domain in ["garmoth.com", "playblackdesert.com"]):
            # elif "garmoth.com" in url:
                return self._scrape_with_tomarkdown(url)
            else:
                return self._scrape_with_jina(url)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _scrape_with_urltomarkdown(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape using urltomarkdown API (for blackdesertfoundry.com)."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Return-Format": "markdown"
        }
        
        response = requests.get(
            f"https://urltomarkdown.herokuapp.com/?url={url}&title=false&links=true&clean=false",
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        logger.info("Content fetched successfully with urltomarkdown")
        
        return {
            "title": "",
            "url": url,
            "content": response.text
        }
    
    def _scrape_with_jina(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape using Jina AI Reader API."""
        response = requests.get(
            f"https://r.jina.ai/{url}",
            headers={},
            timeout=self.timeout
        )
        response.raise_for_status()
        
        logger.info("Content fetched successfully with Jina AI")
        logger.debug(f"Response preview: {response.text[:1000]}")
        
        full_response = response.json()
        data = full_response.get("data", full_response)
        
        return data

    def _scrape_with_tomarkdown(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape using tomarkdown API (for garmoth.com)."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        data = {
            "url": url,
            "advancedOptions": {
                "targetSelectors": [],
                "waitForSelectors": [],
                "excludeSelectors": [],
                "removeImages": False,
                "bypassCache": False,
                "useV2": False,
                "timeout": 10,
                "preExecuteJs": ""
            },
            "options": {
                "headingStyle": "atx",
                "hr": "***",
                "bulletListMarker": "*",
                "codeBlockStyle": "fenced",
                "fence": "```",
                "emDelimiter": "_",
                "strongDelimiter": "**",
                "linkStyle": "inlined",
                "linkReferenceStyle": "full"
            }
        }
        
        response = requests.post(
            f"https://www.tomarkdown.org/api/url-to-markdown",
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        logger.info("Content fetched successfully with tomarkdown")
        
        return {
            "title": "",
            "url": url,
            "content": response.json().get("markdown", "")
        }

def extract_date_from_content(content: str, url: str) -> str:
    """
    Extract publication/update date from content based on URL domain.
    
    Args:
        content: The markdown content to search.
        url: The source URL (determines extraction pattern).
        
    Returns:
        Extracted date string, or empty string if not found.
    """
    if "playblackdesert.com" in url:
        # Pattern: "Last Edited on : <Date> Share"
        pattern = re.compile(r'Last Edited on\s*:\s*(.*?)\s+Share', re.IGNORECASE)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
    
    elif "blackdesertfoundry.com" in url:
        # Pattern: "**Last Updated:** <Date>"
        pattern = re.compile(
            r'\*\*Last Updated:\*\*\s*(.*?)(?:\s*\||\s*$)',
            re.IGNORECASE | re.MULTILINE
        )
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
    
    elif "garmoth.com" in url:
        # Pattern: "Updated: <Date>"
        pattern = re.compile(r'Updated:\s*(.*?)(?:\s*\||\s*$)', re.IGNORECASE | re.MULTILINE)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
    
    return ""


def extract_links_from_markdown(filename: str) -> list:
    """
    Extract standard markdown hyperlinks from a file.
    
    Skips image links (![alt](url)) and plain URLs.
    
    Args:
        filename: Path to the markdown file.
        
    Returns:
        List of unique URLs found in the markdown.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"Markdown file not found: {filename}")
        return []
    except Exception as e:
        logger.error(f"Error reading markdown file: {e}")
        return []
    
    # Regex: [text](url) but not ![alt](url)
    link_pattern = re.compile(
        r'(?<!!)\[[^\]]*\]\((https?://[^\s)]+)(?:\s+"[^"]*")?\)',
        flags=re.MULTILINE
    )
    
    links = [m.group(1) for m in link_pattern.finditer(content)]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for url in links:
        if url not in seen:
            seen.add(url)
            unique_links.append(url)
    
    return unique_links
