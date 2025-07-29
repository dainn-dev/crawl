from bs4 import BeautifulSoup
from urllib.parse import urlparse

def extract_breadcrumb(soup: BeautifulSoup, url: str) -> str:
    # Look for common breadcrumb containers
    breadcrumb_selectors = [
        '[class*="breadcrumb"]',
        'nav.breadcrumb',
        'ul.breadcrumb',
        'div.breadcrumb',
        'nav[aria-label="breadcrumb"]',
    ]
    for selector in breadcrumb_selectors:
        el = soup.select_one(selector)
        if el:
            # Join text from <a> and <span> in breadcrumb
            parts = [a.get_text(strip=True) for a in el.find_all(['a', 'span']) if a.get_text(strip=True)]
            if parts:
                return ' > '.join(parts)
    # Fallback: infer from URL path
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]
    if not path_parts:
        return 'Home'
    return 'Home > ' + ' > '.join(part.capitalize() for part in path_parts) 