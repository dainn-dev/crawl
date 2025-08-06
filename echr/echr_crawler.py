import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import threading
from collections import deque

# Import from the main crawler modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.db import get_session, insert_or_update_case
from crawler.breadcrumb import extract_breadcrumb
from crawler.utils import normalize_url
from crawler.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class ECHRCrawler:
    def __init__(self, headless=True, scroll_pause_time=2, max_scroll_attempts=10):
        """
        Initialize the ECHR crawler
        
        Args:
            headless (bool): Run browser in headless mode
            scroll_pause_time (int): Time to wait between scrolls
            max_scroll_attempts (int): Maximum number of scroll attempts
        """
        self.headless = headless
        self.scroll_pause_time = scroll_pause_time
        self.max_scroll_attempts = max_scroll_attempts
        self.driver = None
        self.visited_urls = set()
        self.url_lock = threading.Lock()
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better performance and stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome WebDriver setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            raise
    
    def scroll_to_load_content(self, max_scrolls=None):
        """
        Scroll down to load more content dynamically
        
        Args:
            max_scrolls (int): Maximum number of scroll attempts
        """
        if max_scrolls is None:
            max_scrolls = self.max_scroll_attempts
            
        logger.info("Starting scroll to load content...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        
        while scroll_attempts < max_scrolls:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait to load page
            time.sleep(self.scroll_pause_time)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # Try scrolling a bit more to see if content loads
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 100);")
                time.sleep(self.scroll_pause_time)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    logger.info(f"No more content to load after {scroll_attempts + 1} scroll attempts")
                    break
            
            last_height = new_height
            scroll_attempts += 1
            logger.info(f"Scroll attempt {scroll_attempts}: New content loaded")
        
        logger.info(f"Scroll completed. Total scroll attempts: {scroll_attempts}")
    
    def extract_links_from_page(self):
        """
        Extract all links from the current page
        
        Returns:
            set: Set of extracted URLs
        """
        links = set()
        
        try:
            # Find all anchor tags
            anchor_elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            base_url = self.driver.current_url
            
            for anchor in anchor_elements:
                try:
                    href = anchor.get_attribute("href")
                    if href:
                        # Normalize the URL
                        full_url = urljoin(base_url, href)
                        normalized_url = normalize_url(full_url)
                        
                        if normalized_url and self.is_valid_echr_url(normalized_url):
                            links.add(normalized_url)
                except Exception as e:
                    logger.debug(f"Error extracting link from anchor: {e}")
                    continue
            
            logger.info(f"Extracted {len(links)} valid links from current page")
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links from page: {e}")
            return set()
    
    def is_valid_echr_url(self, url):
        """
        Check if URL is valid for ECHR crawling
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if valid ECHR URL
        """
        if not url:
            return False
            
        parsed = urlparse(url)
        
        # Check if it's an ECHR domain
        if not parsed.netloc.endswith('hudoc.echr.coe.int'):
            return False
            
        # Exclude certain file types
        excluded_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                             '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif']
        
        for ext in excluded_extensions:
            if url.lower().endswith(ext):
                return False
        
        # Exclude certain URL patterns
        exclude_patterns = ['mailto:', 'javascript:', 'tel:', '#' ]
        for pattern in exclude_patterns:
            if url.lower().startswith(pattern):
                return False
        
        return True
    
    def extract_page_info(self):
        """
        Extract title and other information from the current page
        
        Returns:
            dict: Page information including title and status
        """
        try:
            # Get page title
            title = self.driver.title
            if not title:
                title = self.driver.current_url
            
            # Get current URL
            current_url = self.driver.current_url
            
            # Get status code (approximate)
            status_code = 200  # Default to 200 if page loaded successfully
            
            return {
                'url': current_url,
                'title': title,
                'status_code': status_code
            }
            
        except Exception as e:
            logger.error(f"Error extracting page info: {e}")
            return {
                'url': self.driver.current_url if self.driver else '',
                'title': '',
                'status_code': 500
            }
    
    def save_to_database(self, url, parent_id=None, path_url=None, title=None, status_code=200):
        """
        Save page information to database
        
        Args:
            url (str): URL to save
            parent_id: Parent case ID
            path_url (str): Breadcrumb path
            title (str): Page title
            status_code (int): HTTP status code
            
        Returns:
            str: Case ID if successful, None otherwise
        """
        try:
            session = get_session()
            case_id = insert_or_update_case(session, url, parent_id, path_url, title, status_code, True)
            session.close()
            return case_id
        except Exception as e:
            logger.error(f"Database error for {url}: {e}")
            return None
    
    def crawl_page(self, url, parent_id=None):
        """
        Crawl a single page and extract all links
        
        Args:
            url (str): URL to crawl
            parent_id: Parent case ID
            
        Returns:
            set: Set of discovered URLs
        """
        try:
            logger.info(f"Crawling page: {url}")
            
            # Navigate to the page
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load more content
            self.scroll_to_load_content()
            
            # Extract page information
            page_info = self.extract_page_info()
            
            # Extract breadcrumb
            try:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                path_url = extract_breadcrumb(soup, url)
            except Exception as e:
                logger.warning(f"Error extracting breadcrumb: {e}")
                path_url = None
            
            # Save to database
            case_id = self.save_to_database(
                url=page_info['url'],
                parent_id=parent_id,
                path_url=path_url,
                title=page_info['title'],
                status_code=page_info['status_code']
            )
            
            # Extract links
            discovered_links = self.extract_links_from_page()
            
            logger.info(f"Page crawled successfully. Discovered {len(discovered_links)} links")
            
            return discovered_links, case_id
            
        except TimeoutException:
            logger.error(f"Timeout while loading page: {url}")
            return set(), None
        except WebDriverException as e:
            logger.error(f"WebDriver error for {url}: {e}")
            return set(), None
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            return set(), None
    
    def crawl_site_bfs(self, start_url, max_depth=3, max_urls_per_depth=50):
        """
        Crawl the ECHR site using Breadth-First Search
        
        Args:
            start_url (str): Starting URL
            max_depth (int): Maximum crawl depth
            max_urls_per_depth (int): Maximum URLs to process per depth level
        """
        queue = deque([(start_url, None, 0)])  # (url, parent_id, depth)
        depth_urls = {}  # Track URLs per depth level
        
        logger.info(f"Starting BFS crawl from {start_url} with max depth {max_depth}")
        
        while queue:
            url, parent_id, depth = queue.popleft()
            
            # Check if we've already visited this URL
            with self.url_lock:
                if url in self.visited_urls:
                    continue
                self.visited_urls.add(url)
            
            # Check depth limits
            if depth >= max_depth:
                logger.info(f"Reached max depth {max_depth}, skipping {url}")
                continue
            
            # Check URLs per depth limit
            if depth not in depth_urls:
                depth_urls[depth] = 0
            
            if depth_urls[depth] >= max_urls_per_depth:
                logger.info(f"Reached max URLs per depth {depth}, skipping remaining URLs at this depth")
                continue
            
            depth_urls[depth] += 1
            
            logger.info(f"Processing URL at depth {depth}: {url}")
            
            # Crawl the page
            discovered_links, case_id = self.crawl_page(url, parent_id)
            
            # Add discovered links to queue for next depth
            for link in discovered_links:
                with self.url_lock:
                    if link not in self.visited_urls:
                        queue.append((link, case_id, depth + 1))
            
            # Small delay between requests
            time.sleep(1)
        
        logger.info(f"BFS crawl completed. Total URLs processed: {len(self.visited_urls)}")
    
    def crawl_site_dfs(self, start_url, max_depth=3, max_urls=100):
        """
        Crawl the ECHR site using Depth-First Search
        
        Args:
            start_url (str): Starting URL
            max_depth (int): Maximum crawl depth
            max_urls (int): Maximum total URLs to process
        """
        def dfs_crawl(url, parent_id, depth):
            # Check limits
            if depth >= max_depth or len(self.visited_urls) >= max_urls:
                return
            
            # Check if already visited
            with self.url_lock:
                if url in self.visited_urls:
                    return
                self.visited_urls.add(url)
            
            logger.info(f"DFS crawling depth {depth}: {url}")
            
            # Crawl the page
            discovered_links, case_id = self.crawl_page(url, parent_id)
            
            # Recursively crawl discovered links
            for link in discovered_links:
                if len(self.visited_urls) < max_urls:
                    dfs_crawl(link, case_id, depth + 1)
        
        logger.info(f"Starting DFS crawl from {start_url} with max depth {max_depth}")
        dfs_crawl(start_url, None, 0)
        logger.info(f"DFS crawl completed. Total URLs processed: {len(self.visited_urls)}")
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Main function to run the ECHR crawler"""
    target_url = "https://hudoc.echr.coe.int/#{%22tabview%22:[%22document%22]}"
    
    crawler = ECHRCrawler(headless=False, scroll_pause_time=2, max_scroll_attempts=5)
    
    try:
        # Setup WebDriver
        crawler.setup_driver()
        
        # Start crawling
        logger.info("Starting ECHR crawler...")
        
        # You can choose between BFS or DFS approach
        # crawler.crawl_site_bfs(target_url, max_depth=2, max_urls_per_depth=20)
        crawler.crawl_site_dfs(target_url, max_depth=2, max_urls=50)
        
    except Exception as e:
        logger.error(f"Error in main crawler execution: {e}")
    finally:
        crawler.close()

if __name__ == "__main__":
    main()
