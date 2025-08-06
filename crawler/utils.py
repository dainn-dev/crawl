# Placeholder for utility functions 

from urllib.parse import urlparse, urlunparse, urljoin

# Default extensions to exclude (fallback)
DEFAULT_EXCLUDE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz']

def normalize_url(url, exclude_extensions=None):
    """
    Normalize a URL by removing fragments and skipping non-HTML file types.
    Returns None if the URL should be skipped.
    
    Args:
        url: The URL to normalize
        exclude_extensions: List of file extensions to exclude (optional)
    """
    if exclude_extensions is None:
        exclude_extensions = DEFAULT_EXCLUDE_EXTENSIONS
        
    parsed = urlparse(url)
    # Remove fragment
    parsed = parsed._replace(fragment='')
    # Optionally, sort or remove query params here if needed
    # Remove trailing slash for consistency
    path = parsed.path.rstrip('/')
    # Skip non-HTML file types
    for ext in exclude_extensions:
        if path.lower().endswith(ext):
            return None
    # Rebuild the URL without fragment
    normalized = urlunparse(parsed._replace(path=path))
    return normalized

def should_skip_url(url, exclude_extensions=None):
    """
    Returns True if the URL should be skipped (e.g., non-HTML file types).
    
    Args:
        url: The URL to check
        exclude_extensions: List of file extensions to exclude (optional)
    """
    if exclude_extensions is None:
        exclude_extensions = DEFAULT_EXCLUDE_EXTENSIONS
        
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in exclude_extensions:
        if path.endswith(ext):
            return True
    return False 