# Placeholder for crawler logic 
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
import warnings
import chardet
from collections import deque
from .config import CRAWL_DELAY, IS_CHECK, MAX_THREADS, TARGET_SITES
from .db import get_session, insert_or_update_case
from .breadcrumb import extract_breadcrumb
from .utils import normalize_url

# Suppress BeautifulSoup warnings
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

logger = logging.getLogger(__name__)

# Thread-safe visited sets for each domain
visited_sets = {}
visited_locks = {}

# Thread-local storage for per-thread requests.Session
thread_local = threading.local()

def initialize_domain_tracking():
    """Initialize thread-safe tracking for each domain"""
    for site in TARGET_SITES:
        domain = site['domain']
        visited_sets[domain] = set()
        visited_locks[domain] = threading.Lock()

def is_valid_url(url, domain):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc.endswith(domain):
        return False
    if url.startswith("mailto:") or url.startswith("javascript:"):
        return False
    return True

def detect_encoding(content):
    """Detect the encoding of content using chardet"""
    try:
        result = chardet.detect(content)
        return result['encoding'] if result['encoding'] else 'utf-8'
    except:
        return 'utf-8'

def decode_content(content, encoding=None):
    """Safely decode content with fallback encodings"""
    if not content:
        return ""
    
    # Try the provided encoding first
    if encoding:
        try:
            return content.decode(encoding, errors='replace')
        except (UnicodeDecodeError, LookupError):
            pass
    
    # Try to detect encoding
    detected_encoding = detect_encoding(content)
    try:
        return content.decode(detected_encoding, errors='replace')
    except (UnicodeDecodeError, LookupError):
        pass
    
    # Fallback to common encodings with error handling
    for fallback_encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']:
        try:
            return content.decode(fallback_encoding, errors='replace')
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Last resort: decode with replacement characters and ignore errors
    try:
        return content.decode('utf-8', errors='ignore')
    except:
        # If all else fails, return a safe string representation
        try:
            return str(content, errors='replace')
        except:
            return "[Content could not be decoded]"

def create_soup(html, content_type=None):
    """Create BeautifulSoup object with appropriate parser based on content type"""
    if not html or len(html.strip()) == 0:
        return None
    
    # Check if content looks like XML/XHTML
    html_lower = html.lower().strip()
    if content_type and 'xml' in content_type.lower():
        try:
            return BeautifulSoup(html, "xml")
        except:
            pass
    
    # Check for XML-like content
    if html_lower.startswith('<?xml') or html_lower.startswith('<rss') or html_lower.startswith('<feed'):
        try:
            return BeautifulSoup(html, "xml")
        except:
            pass
    
    # Default to HTML parser
    try:
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.warning(f"Failed to parse HTML: {e}")
        return None

def extract_links(html, base_url, content_type=None, exclude_extensions=None):
    soup = create_soup(html, content_type)
    if not soup:
        return set()
    
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        normalized = normalize_url(href, exclude_extensions)
        if normalized:
            links.add(normalized)
    return links

def extract_title(soup):
    """Extract title from soup object with fallbacks"""
    if not soup:
        return None
    
    # Try title tag first
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        return title_tag.string.strip()
    
    # Try h1 tag
    h1_tag = soup.find('h1')
    if h1_tag and h1_tag.string:
        return h1_tag.string.strip()
    
    # Try meta title
    meta_title = soup.find('meta', attrs={'name': 'title'})
    if meta_title and meta_title.get('content'):
        return meta_title['content'].strip()
    
    return None

def get_thread_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

def crawl_page(url, domain, parent_id=None, depth=0, max_depth=5, exclude_extensions=None):
    """DFS implementation - original recursive crawler"""
    normalized_url = normalize_url(url, exclude_extensions)
    if not normalized_url or not is_valid_url(normalized_url, domain):
        return
    
    # Thread-safe check for visited URLs
    with visited_locks[domain]:
        if normalized_url in visited_sets[domain]:
            return
        visited_sets[domain].add(normalized_url)
    
    logger.info(f"Crawling [{domain}] (DFS depth {depth}): {normalized_url}")
    try:
        session = get_thread_session()
        resp = session.get(normalized_url, timeout=10)
        status_code = resp.status_code
        
        if resp.status_code != 200:
            html = ""
            content_type = resp.headers.get('content-type', '')
        else:
            # Handle encoding properly
            content_type = resp.headers.get('content-type', '')
            
            # Try to get encoding from content-type header
            encoding = None
            if 'charset=' in content_type.lower():
                try:
                    encoding = content_type.split('charset=')[-1].split(';')[0].strip()
                except:
                    pass
            
            # Decode content with proper encoding handling
            html = decode_content(resp.content, encoding)
            
    except Exception as e:
        logger.error(f"Error fetching {normalized_url}: {e}")
        return
    
    # Create soup with appropriate parser
    soup = create_soup(html, content_type)
    if not soup:
        logger.warning(f"Could not parse content from {normalized_url}")
        return
    
    # Extract title with fallbacks
    title = extract_title(soup)
    if not title:
        title = normalized_url
    
    path_url = extract_breadcrumb(soup, normalized_url)
    session = get_session()
    try:
        case_id = insert_or_update_case(session, normalized_url, parent_id, path_url, title, status_code, IS_CHECK)
    except Exception as e:
        logger.error(f"DB error for {normalized_url}: {e}")
        session.rollback()
        return
    finally:
        session.close()
    
    if depth >= max_depth:
        return
    
    links = extract_links(html, normalized_url, content_type, exclude_extensions)
    time.sleep(CRAWL_DELAY)
    
    # Only crawl links that belong to the same domain
    for link in links:
        if is_valid_url(link, domain):
            crawl_page(link, domain, parent_id=case_id, depth=depth+1, max_depth=max_depth, exclude_extensions=exclude_extensions)

def crawl_page_bfs(start_url, domain, max_depth=5, exclude_extensions=None):
    """BFS implementation - iterative crawler using queue"""
    queue = deque([(start_url, None, 0)])  # (url, parent_id, depth)
    visited = set()
    
    while queue:
        url, parent_id, depth = queue.popleft()
        
        normalized_url = normalize_url(url, exclude_extensions)
        if not normalized_url or not is_valid_url(normalized_url, domain):
            continue
            
        # Check if already visited
        if normalized_url in visited:
            continue
        visited.add(normalized_url)
        
        logger.info(f"Crawling [{domain}] (BFS depth {depth}): {normalized_url}")
        
        try:
            session = get_thread_session()
            resp = session.get(normalized_url, timeout=10)
            status_code = resp.status_code
            
            if resp.status_code != 200:
                html = ""
                content_type = resp.headers.get('content-type', '')
            else:
                content_type = resp.headers.get('content-type', '')
                encoding = None
                if 'charset=' in content_type.lower():
                    try:
                        encoding = content_type.split('charset=')[-1].split(';')[0].strip()
                    except:
                        pass
                html = decode_content(resp.content, encoding)
                
        except Exception as e:
            logger.error(f"Error fetching {normalized_url}: {e}")
            continue
        
        # Create soup with appropriate parser
        soup = create_soup(html, content_type)
        if not soup:
            logger.warning(f"Could not parse content from {normalized_url}")
            continue
        
        # Extract title with fallbacks
        title = extract_title(soup)
        if not title:
            title = normalized_url
        
        path_url = extract_breadcrumb(soup, normalized_url)
        db_session = get_session()
        try:
            case_id = insert_or_update_case(db_session, normalized_url, parent_id, path_url, title, status_code, IS_CHECK)
        except Exception as e:
            logger.error(f"DB error for {normalized_url}: {e}")
            db_session.rollback()
            continue
        finally:
            db_session.close()
        
        # If we haven't reached max depth, extract links and add to queue
        if depth < max_depth:
            links = extract_links(html, normalized_url, content_type, exclude_extensions)
            time.sleep(CRAWL_DELAY)
            
            # Add valid links to queue for next depth level
            for link in links:
                if is_valid_url(link, domain):
                    queue.append((link, case_id, depth + 1))

def crawl_page_hybrid(start_url, domain, max_depth=5, bfs_depth=2, exclude_extensions=None):
    """
    Hybrid crawler that uses BFS for initial levels and DFS for deeper exploration.
    This approach discovers more URLs quickly with BFS, then explores them thoroughly with DFS.
    """
    queue = deque([(start_url, None, 0)])  # (url, parent_id, depth)
    visited = set()
    
    # Phase 1: BFS for initial levels (faster discovery)
    while queue:
        url, parent_id, depth = queue.popleft()
        
        normalized_url = normalize_url(url, exclude_extensions)
        if not normalized_url or not is_valid_url(normalized_url, domain):
            continue
            
        if normalized_url in visited:
            continue
        visited.add(normalized_url)
        
        logger.info(f"Crawling [{domain}] (Hybrid BFS depth {depth}): {normalized_url}")
        
        try:
            session = get_thread_session()
            resp = session.get(normalized_url, timeout=10)
            status_code = resp.status_code
            
            if resp.status_code != 200:
                html = ""
                content_type = resp.headers.get('content-type', '')
            else:
                content_type = resp.headers.get('content-type', '')
                encoding = None
                if 'charset=' in content_type.lower():
                    try:
                        encoding = content_type.split('charset=')[-1].split(';')[0].strip()
                    except:
                        pass
                html = decode_content(resp.content, encoding)
                
        except Exception as e:
            logger.error(f"Error fetching {normalized_url}: {e}")
            continue
        
        soup = create_soup(html, content_type)
        if not soup:
            logger.warning(f"Could not parse content from {normalized_url}")
            continue
        
        title = extract_title(soup)
        if not title:
            title = normalized_url
        
        path_url = extract_breadcrumb(soup, normalized_url)
        db_session = get_session()
        try:
            case_id = insert_or_update_case(db_session, normalized_url, parent_id, path_url, title, status_code, IS_CHECK)
        except Exception as e:
            logger.error(f"DB error for {normalized_url}: {e}")
            db_session.rollback()
            continue
        finally:
            db_session.close()
        
        # Extract links for next level
        if depth < max_depth:
            links = extract_links(html, normalized_url, content_type, exclude_extensions)
            time.sleep(CRAWL_DELAY)
            
            # If we're still in BFS phase, add to queue
            if depth < bfs_depth:
                for link in links:
                    if is_valid_url(link, domain):
                        queue.append((link, case_id, depth + 1))
            # If we've reached DFS phase, start DFS exploration
            elif depth < max_depth:
                for link in links:
                    if is_valid_url(link, domain):
                        crawl_page_dfs_from_hybrid(link, domain, case_id, depth + 1, max_depth, visited, exclude_extensions)

def crawl_page_dfs_from_hybrid(url, domain, parent_id, depth, max_depth, visited, exclude_extensions=None):
    """DFS helper for hybrid crawler"""
    normalized_url = normalize_url(url, exclude_extensions)
    if not normalized_url or not is_valid_url(normalized_url, domain):
        return
    
    if normalized_url in visited:
        return
    visited.add(normalized_url)
    
    logger.info(f"Crawling [{domain}] (Hybrid DFS depth {depth}): {normalized_url}")
    
    try:
        session = get_thread_session()
        resp = session.get(normalized_url, timeout=10)
        status_code = resp.status_code
        
        if resp.status_code != 200:
            html = ""
            content_type = resp.headers.get('content-type', '')
        else:
            content_type = resp.headers.get('content-type', '')
            encoding = None
            if 'charset=' in content_type.lower():
                try:
                    encoding = content_type.split('charset=')[-1].split(';')[0].strip()
                except:
                    pass
            html = decode_content(resp.content, encoding)
            
    except Exception as e:
        logger.error(f"Error fetching {normalized_url}: {e}")
        return
    
    soup = create_soup(html, content_type)
    if not soup:
        logger.warning(f"Could not parse content from {normalized_url}")
        return
    
    title = extract_title(soup)
    if not title:
        title = normalized_url
    
    path_url = extract_breadcrumb(soup, normalized_url)
    db_session = get_session()
    try:
        case_id = insert_or_update_case(db_session, normalized_url, parent_id, path_url, title, status_code, IS_CHECK)
    except Exception as e:
        logger.error(f"DB error for {normalized_url}: {e}")
        db_session.rollback()
        return
    finally:
        db_session.close()
    
    if depth >= max_depth:
        return
    
    links = extract_links(html, normalized_url, content_type, exclude_extensions)
    time.sleep(CRAWL_DELAY)
    
    for link in links:
        if is_valid_url(link, domain):
            crawl_page_dfs_from_hybrid(link, domain, case_id, depth + 1, max_depth, visited, exclude_extensions)

def crawl_page_hybrid_parallel(start_url, domain, max_depth=5, bfs_depth=2, exclude_extensions=None, max_workers=10):
    """
    Enhanced hybrid crawler with parallel URL processing within each site.
    Uses BFS for initial levels, then DFS with parallel processing for deeper exploration.
    """
    queue = deque([(start_url, None, 0)])  # (url, parent_id, depth)
    visited = set()
    visited_lock = threading.Lock()  # Thread-safe visited set
    
    def crawl_single_url(url_data):
        """Crawl a single URL - used for parallel processing"""
        url, parent_id, depth = url_data
        normalized_url = normalize_url(url, exclude_extensions)
        
        if not normalized_url or not is_valid_url(normalized_url, domain):
            return []
        
        # Thread-safe visited check
        with visited_lock:
            if normalized_url in visited:
                return []
            visited.add(normalized_url)
        
        logger.info(f"Crawling [{domain}] (Parallel Hybrid depth {depth}): {normalized_url}")
        
        try:
            session = get_thread_session()
            resp = session.get(normalized_url, timeout=10)
            status_code = resp.status_code
            
            if resp.status_code != 200:
                html = ""
                content_type = resp.headers.get('content-type', '')
            else:
                content_type = resp.headers.get('content-type', '')
                encoding = None
                if 'charset=' in content_type.lower():
                    try:
                        encoding = content_type.split('charset=')[-1].split(';')[0].strip()
                    except:
                        pass
                html = decode_content(resp.content, encoding)
                
        except Exception as e:
            logger.error(f"Error fetching {normalized_url}: {e}")
            return []
        
        soup = create_soup(html, content_type)
        if not soup:
            logger.warning(f"Could not parse content from {normalized_url}")
            return []
        
        title = extract_title(soup)
        if not title:
            title = normalized_url
        
        path_url = extract_breadcrumb(soup, normalized_url)
        db_session = get_session()
        try:
            case_id = insert_or_update_case(db_session, normalized_url, parent_id, path_url, title, status_code, IS_CHECK)
        except Exception as e:
            logger.error(f"DB error for {normalized_url}: {e}")
            db_session.rollback()
            return []
        finally:
            db_session.close()
        
        # Extract links for next level
        if depth < max_depth:
            links = extract_links(html, normalized_url, content_type, exclude_extensions)
            time.sleep(CRAWL_DELAY)
            
            # Return discovered links for next level processing
            return [(link, case_id, depth + 1) for link in links if is_valid_url(link, domain)]
        
        return []
    
    # Phase 1: BFS for initial levels (faster discovery)
    while queue:
        current_batch = []
        # Collect a batch of URLs to process in parallel
        while queue and len(current_batch) < max_workers:
            current_batch.append(queue.popleft())
        
        if not current_batch:
            break
        
        # Process batch in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(crawl_single_url, url_data) for url_data in current_batch]
            
            # Collect results and add new URLs to queue
            for future in as_completed(futures):
                try:
                    new_urls = future.result()
                    for url_data in new_urls:
                        url, parent_id, depth = url_data
                        # If we're still in BFS phase, add to queue
                        if depth <= bfs_depth:
                            queue.append(url_data)
                        # If we've reached DFS phase, process immediately in parallel
                        elif depth < max_depth:
                            # Process DFS URLs in parallel
                            with ThreadPoolExecutor(max_workers=max_workers) as dfs_executor:
                                dfs_futures = [dfs_executor.submit(crawl_single_url, url_data)]
                                for dfs_future in as_completed(dfs_futures):
                                    try:
                                        dfs_future.result()
                                    except Exception as e:
                                        logger.error(f"DFS processing error: {e}")
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")

def crawl_site_parallel(site_config, max_depth=5, use_bfs=False, use_hybrid=False, use_parallel_hybrid=False):
    """Crawl a single site with parallel processing of discovered URLs"""
    domain = site_config['domain']
    start_url = site_config['start_url']
    site_name = site_config['name']
    exclude_extensions = site_config.get('exclude_extensions', [])
    
    if use_parallel_hybrid:
        logger.info(f"Starting Parallel Hybrid crawl for {site_name} ({domain})")
        crawl_page_hybrid_parallel(start_url, domain, max_depth, exclude_extensions=exclude_extensions, max_workers=10)
    elif use_hybrid:
        logger.info(f"Starting Hybrid crawl for {site_name} ({domain})")
        crawl_page_hybrid(start_url, domain, max_depth, exclude_extensions=exclude_extensions)
    elif use_bfs:
        logger.info(f"Starting BFS crawl for {site_name} ({domain})")
        crawl_page_bfs(start_url, domain, max_depth, exclude_extensions=exclude_extensions)
    else:
        logger.info(f"Starting DFS crawl for {site_name} ({domain})")
        crawl_page(start_url, domain, None, 0, max_depth, exclude_extensions=exclude_extensions)

def crawl_site(site_config, max_depth=5, use_bfs=False):
    """Crawl a single site using either DFS or BFS"""
    domain = site_config['domain']
    start_url = site_config['start_url']
    site_name = site_config['name']
    exclude_extensions = site_config.get('exclude_extensions', [])
    
    logger.info(f"Starting {'BFS' if use_bfs else 'DFS'} crawl for {site_name} ({domain})")
    try:
        if use_bfs:
            crawl_page_bfs(start_url, domain, max_depth, exclude_extensions=exclude_extensions)
        else:
            crawl_page(start_url, domain, None, 0, max_depth, exclude_extensions=exclude_extensions)
        logger.info(f"Completed {'BFS' if use_bfs else 'DFS'} crawl for {site_name}")
    except Exception as e:
        logger.error(f"Error crawling {site_name}: {e}")

def start_crawl(max_depth=5, sites=None, use_bfs=False):
    """Start crawling all sites using multiple threads with DFS or BFS"""
    initialize_domain_tracking()
    
    if sites is None:
        sites = TARGET_SITES
    logger.info(f"Starting multi-site {'BFS' if use_bfs else 'DFS'} crawl with {MAX_THREADS} threads")
    logger.info(f"Target sites: {[site['name'] for site in sites]}")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit each site to be crawled in its own thread
        futures = [
            executor.submit(crawl_site, site, max_depth, use_bfs) 
            for site in sites
        ]
        
        # Wait for all sites to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Thread execution error: {e}")
    
    logger.info(f"Multi-site {'BFS' if use_bfs else 'DFS'} crawl completed")

def start_crawl_hybrid(max_depth=5, sites=None):
    """Start crawling using hybrid approach (BFS + DFS)"""
    initialize_domain_tracking()
    
    if sites is None:
        sites = TARGET_SITES
    logger.info(f"Starting multi-site Hybrid crawl with {MAX_THREADS} threads")
    logger.info(f"Target sites: {[site['name'] for site in sites]}")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit each site to be crawled in its own thread
        futures = [
            executor.submit(crawl_site_parallel, site, max_depth, use_bfs=False, use_hybrid=True) 
            for site in sites
        ]
        
        # Wait for all sites to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Thread execution error: {e}")
    
    logger.info(f"Multi-site Hybrid crawl completed")

def start_crawl_hybrid_parallel(max_depth=5, sites=None):
    """Start crawling using enhanced parallel hybrid approach (BFS + DFS with URL-level parallelism)"""
    initialize_domain_tracking()
    
    if sites is None:
        sites = TARGET_SITES
    logger.info(f"Starting multi-site Parallel Hybrid crawl with {MAX_THREADS} threads")
    logger.info(f"Target sites: {[site['name'] for site in sites]}")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit each site to be crawled in its own thread with parallel URL processing
        futures = [
            executor.submit(crawl_site_parallel, site, max_depth, use_bfs=False, use_hybrid=False, use_parallel_hybrid=True) 
            for site in sites
        ]
        
        # Wait for all sites to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Thread execution error: {e}")
    
    logger.info(f"Multi-site Parallel Hybrid crawl completed")

# Convenience functions for specific traversal methods
def start_crawl_dfs(max_depth=5, sites=None):
    """Start crawling using Depth-First Search"""
    return start_crawl(max_depth, sites, use_bfs=False)

def start_crawl_bfs(max_depth=5, sites=None):
    """Start crawling using Breadth-First Search"""
    return start_crawl(max_depth, sites, use_bfs=True)