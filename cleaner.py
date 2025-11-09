"""Content cleaning strategies for different BDO guide sources."""

import re
import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)


def clean_playblackdesert(content: str) -> str:
    """
    Clean content from playblackdesert.com wiki pages.
    
    Removes header boilerplate (Request Edit, Last Edited, Social sharing buttons)
    and footer disclaimers.
    
    Args:
        content: Raw markdown content from playblackdesert.com
        
    Returns:
        Cleaned markdown content with title preserved.
    """
    # Remove header boilerplate: ### <Title> Request Edit ... Copy URL Facebook X
    start_pattern = re.compile(
        r"^###\s+(?P<title>.+?)\s+Request Edit\s*\r?\n+"
        r"\s*Last Edited on\s*:\s*.+?Share\s*\r?\n+"
        r"\s*Copy URL Facebook X\s*\r?\n*",
        re.MULTILINE
    )
    
    match = start_pattern.search(content)
    if not match:
        return content.strip()
    
    title = match.group("title")
    body = content[match.end():]
    
    # Remove footer disclaimer and common bottom blocks: "Request Edit", social links,
    # copy/share blocks, and policy/terms link blocks. Playblackdesert often places these
    # as a cluster of short lines; match a block starting at a known marker (Request Edit,
    # Close Request to Update, Send Request to Update, or repeated social/link lines)
    footer_patterns = [
        # explicit site footer disclaimer present on many pages
        r'(?ims)^_*The content of the game guide may differ from the actual game content.*$',
        r'(?ims)^###\s*Request Edit\b.*$',
        r'(?ims)^Close Request to Update\b.*$',
        r'(?ims)^Send Request to Update\b.*$',
        # social/share/copy url cluster (matches lines containing Share, Copy URL, Facebook, X, Instagram, etc.)
        r'(?ims)(?:^\s*(?:Share|Copy URL|Facebook|Instagram|Twitch|Twitter|Youtube|Discord|TikTok).*$\n?){2,}',
        # long policy/links footer starting with '[' (many consecutive link items)
        r'(?ims)(?:^\[.*?\]\(https?:.*?\).*$\n?){3,}',
        # PEGI image/footer marker
        r'(?ims)^\[!\[Image.*?PEGI.*?\]\(.*?\)\].*$'
    ]

    # Remove all matched footer-like blocks wherever they appear
    for fp in footer_patterns:
        body = re.sub(fp, '', body)

    # Defensive: if any footer marker still exists, cut everything from the earliest marker onward
    cut_idx = None
    for fp in footer_patterns:
        m = re.search(fp, body)
        if m:
            if cut_idx is None or m.start() < cut_idx:
                cut_idx = m.start()
    if cut_idx is not None:
        body = body[:cut_idx]

    # Normalize excessive blank lines produced by removals
    body = re.sub(r'\n{3,}', '\n\n', body)
    
    body = body.strip()
    return f"### {title}\n\n{body}"


def clean_bdofoundry(content: str) -> str:
    """
    Clean content from blackdesertfoundry.com pages.
    
    Removes site navigation, headers, breadcrumbs, quick links,
    author information, and footer disclaimers.
    
    Args:
        content: Raw markdown content from blackdesertfoundry.com
        
    Returns:
        Cleaned markdown content with extracted title as H1.
    """
    if not content:
        return ""
    
    # Extract title (try "Title:" format first, then fallback)
    title_match = re.search(
        r'^Title:\s*(.+?)\s*-\s*BDFoundry\s*$',
        content,
        re.MULTILINE
    )
    if not title_match:
        title_match = re.search(
            r'^(.+?)\s*-\s*BDFoundry\s*$',
            content,
            re.MULTILINE
        )
    
    title = title_match.group(1).strip() if title_match else "Unknown"
    
    cleaned = content
    
    # Find "Introduction" section and start from there
    intro_patterns = [
        r'(?im)^Introduction\s*[\r\n]+[-=]{3,}',
        r'(?im)^##\s+Introduction\s*$',
        r'(?im)^###\s+Introduction\s*$',
        r'(?im)^####\s+Introduction\s*$',
    ]
    
    intro_idx = -1
    for pattern in intro_patterns:
        match = re.search(pattern, cleaned)
        if match:
            intro_idx = match.start()
            break
    
    if intro_idx != -1:
        cleaned = cleaned[intro_idx:]
    else:
        # Clean header elements if Introduction not found
        cleaned = re.sub(r'(?im)^Title:.*?-\s*BDFoundry\s*$', '', cleaned, count=1)
        cleaned = re.sub(r'(?im)^Description:.*$', '', cleaned, count=1)
        cleaned = re.sub(r'(?im)^Skip to content\s*$', '', cleaned, count=1)
    
    # Remove "Last Updated" and breadcrumb sections
    header_cleanup = re.compile(
        r'(?ims)^(?:\*\*Last Updated:\*\*.*?(?=^#|^##|^###|^####|^Introduction|\Z)'
        r'|You are here:.*?(?=^#|^##|^###|^####|^Introduction|\Z))'
    )
    cleaned = header_cleanup.sub('', cleaned)
    
    # Remove footer disclaimers
    end_marker = "The content of the game guide may differ from the actual game content"
    end_idx = cleaned.find(end_marker)
    if end_idx != -1:
        cleaned = cleaned[:end_idx]
    
    # Remove "Quick Links" or navigation sections
    quick_links_pattern = re.compile(
        r'(?ims)^\s*(?:####\s*Quick\s+Links|\*\*Navigation\*\*\s*Hide)\s*$'
        r'(.+?)(?=^\s*(?:##|###|####|\[By|Introduction|\Z))'
    )
    cleaned = quick_links_pattern.sub('', cleaned)
    
    # Remove author sections and "Check these out" footers
    end_patterns = [
        r'(?im)^\s*\[By\s+[^\]]+\]\(.*?\).*$',
        r'(?im)^\s*###\s+Check\s+these\s+out\s+before\s+you\s+go!\s*$'
    ]
    
    cut_points = []
    for pattern in end_patterns:
        match = re.search(pattern, cleaned)
        if match:
            cut_points.append(match.start())
    
    if cut_points:
        cleaned = cleaned[:min(cut_points)]
    
    # Final cleanup
    cleaned = re.sub(r'(?im)^\s*\[By\s+[^\]]+\]\(.*?\).*$\n?', '', cleaned)
    cleaned = cleaned.strip() + "\n"
    
    return f"# {title}\n\n{cleaned}"


def clean_garmoth(content: str) -> str:
    """
    Clean content from garmoth.com.
    
    Removes navigation headers and footers.
    
    Args:
        content: Raw markdown content from garmoth.com
        
    Returns:
        Cleaned content (currently returns as-is).
    """
    if not content:
        return ""
    
    # Title Pattern: <Title> | Guide | Garmoth.com - BDO Companion
    title_match = re.search(
        r'^(?P<title>.+?)\s*\|\s*Guide\s*\|\s*Garmoth\.com\s*-\s*BDO\s*Companion\s*$',
        content,
        re.MULTILINE
    )
    title = title_match.group("title").strip() if title_match else "Unknown"
    cleaned = content.strip()
    
    # Find Introduction section
    # Introduction Pattern: 1.  Introduction
    intro_patterns = [
        r'(?im)^1\.\s+Introduction\s*$',
        r'(?im)^##\s+Introduction\s*$',
        r'(?im)^###\s+Introduction\s*$',
        r'(?im)^####\s+Introduction\s*$',
    ]
    intro_idx = -1
    for pattern in intro_patterns:
        match = re.search(pattern, cleaned)
        if match:
            intro_idx = match.start()
            break
    if intro_idx != -1:
        cleaned = cleaned[intro_idx:]
    else:
        # Clean header elements if Introduction not found
        # Pattern: <Image> By <Author>
        match = re.search(r'(?im)^!\[.*?\]\(.*?\)\s*By\s+.*$', cleaned)
        if match:
            cleaned = cleaned[match.end():]
        
    # --- Footer cut: from 'Let us know!' line to the end ---
    footer_match = re.search(r'(?im)^.*?[*_]*\s*Let\s+us\s+know!\s*[*_]*.*$', cleaned)
    if footer_match:
        cleaned = cleaned[:footer_match.start()]
    cleaned = cleaned.strip() + "\n"
    return f"# {title}\n\n{cleaned}"


# Cleaning strategy registry
CLEANING_STRATEGIES: Dict[str, Callable[[str], str]] = {
    "garmoth.com": clean_garmoth,
    "playblackdesert.com": clean_playblackdesert,
    "blackdesertfoundry.com": clean_bdofoundry,
}


def clean_text(content: str, url: str) -> str:
    """
    Clean text content based on the source URL domain.
    
    Applies domain-specific cleaning strategies to remove navigation,
    headers, footers, and other boilerplate content.
    
    Args:
        content: Raw markdown content to clean.
        url: Source URL (determines which cleaning strategy to use).
        
    Returns:
        Cleaned markdown content.
    """
    if not content:
        return ""
    
    logger.info("Cleaning content...")
    
    # Find matching cleaning strategy
    for domain, cleaner_func in CLEANING_STRATEGIES.items():
        if domain in url:
            logger.info(f"Applying '{cleaner_func.__name__}' strategy")
            return cleaner_func(content)
    
    # Default cleaning if no specific strategy found
    logger.info("Applying default cleaning strategy")
    content = re.sub(r'\[.*?\]\(.*?\)', '', content)  # Remove all links
    content = re.sub(r'\n+', '\n', content).strip()  # Normalize whitespace
    return content
