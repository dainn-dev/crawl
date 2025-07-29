# Placeholder for utility functions 

from urllib.parse import urlparse, urlunparse, urljoin

NON_HTML_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz']

def normalize_url(url):
    """
    Normalize a URL by removing fragments and skipping non-HTML file types.
    Returns None if the URL should be skipped.
    """
    parsed = urlparse(url)
    # Remove fragment
    parsed = parsed._replace(fragment='')
    # Optionally, sort or remove query params here if needed
    # Remove trailing slash for consistency
    path = parsed.path.rstrip('/')
    # Skip non-HTML file types
    for ext in NON_HTML_EXTENSIONS:
        if path.lower().endswith(ext):
            return None
    # Rebuild the URL without fragment
    normalized = urlunparse(parsed._replace(path=path))
    return normalized

def should_skip_url(url):
    """
    Returns True if the URL should be skipped (e.g., non-HTML file types).
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in NON_HTML_EXTENSIONS:
        if path.endswith(ext):
            return True
    return False 