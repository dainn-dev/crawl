from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import sys
import os
import argparse

# Add the parent directory to the path to import crawler modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.db import create_tables, get_session, insert_or_update_case, get_case_by_url
from crawler.config import IS_CHECK

def setup_webdriver(headless=True):
    """
    Set up Chrome WebDriver with proper options and error handling for Linux
    
    Args:
        headless (bool): If True, runs browser in headless mode (no visible window)
    """
    try:
        # Configure Chrome options optimized for Linux
        chrome_options = Options()
        
        # Essential Linux options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_argument("--disable-javascript")  # Uncomment if JS not needed
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Memory and performance optimizations
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Window settings
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Enable headless mode if requested
        if headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            print("Running in headless mode (no browser window will be visible)")
        else:
            print("Running with visible browser window")
        
        # Try to set up the service with ChromeDriverManager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Additional setup for Linux
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("ChromeDriver set up successfully with ChromeDriverManager")
            return driver
        except Exception as e:
            print(f"ChromeDriverManager failed: {e}")
            
            # Fallback: try to use system Chrome driver
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("Using system ChromeDriver")
                return driver
            except Exception as e2:
                print(f"System ChromeDriver also failed: {e2}")
                
                # Final fallback: try with minimal options
                try:
                    minimal_options = Options()
                    minimal_options.add_argument("--no-sandbox")
                    minimal_options.add_argument("--disable-dev-shm-usage")
                    if headless:
                        minimal_options.add_argument("--headless=new")
                    
                    driver = webdriver.Chrome(options=minimal_options)
                    print("Using minimal ChromeDriver setup")
                    return driver
                except Exception as e3:
                    print(f"Minimal setup also failed: {e3}")
                    raise Exception("Could not set up Chrome WebDriver. Please ensure Chrome browser is installed on Linux.")
                
    except Exception as e:
        print(f"Failed to set up WebDriver: {e}")
        raise

# Initialize database
create_tables()

# Global driver variable (will be initialized in main function)
driver = None

# Base URL template
BASE_URL = "https://eur-lex.europa.eu/search.html?scope=EURLEX&lang=en&type=quick&qid=1754451888110&page={}"

# Function to crawl data
def crawl_page(session, parent_id=None):
    """
    Crawl the current page and save document URLs to database
    """
    try:
        # Get current page URL
        current_url = driver.current_url
        print(f"Crawling page: {current_url}")
        
        # Check if current page URL already exists in database
        existing_page = get_case_by_url(session, current_url)
        if existing_page and not IS_CHECK:
            print(f"Page URL already exists in database, skipping: {current_url}")
            return existing_page.id
        
        # Save the current page URL to database
        page_id = insert_or_update_case(
            session=session,
            url=current_url,
            parent_id=parent_id,
            path_url=current_url,
            title="EUR-Lex Search Results Page",
            status_code=200,
            is_check=IS_CHECK
        )
        
        # Extract all document links and titles
        documents = driver.find_elements(By.XPATH, '//*[@id="EurlexContent"]/div')
        document_count = 0
        
        for doc in documents:
            try:
                # Try to find the document title and link
                title_element = doc.find_element(By.TAG_NAME, "a")
                title = title_element.text.strip()
                
                                # Look for a link within the title element
                doc_url = title_element.get_attribute("href")
 
                # Open document URL in new tab to get final URL (handle redirects)
                original_window = driver.current_window_handle
                driver.execute_script("window.open(arguments[0], '_blank');", doc_url)
                
                # Switch to the new tab
                new_window = [window for window in driver.window_handles if window != original_window][0]
                driver.switch_to.window(new_window)
                
                # Wait for page to load and get the final URL
                time.sleep(2)
                doc_url = driver.current_url
                
                # Close the new tab and switch back to original
                driver.close()
                driver.switch_to.window(original_window)
                
                if doc_url and title:
                    # Check if document URL already exists in database
                    existing_doc = get_case_by_url(session, doc_url)
                    if existing_doc and not IS_CHECK:
                        print(f"Document URL already exists, skipping: {title[:50]}...")
                        continue
                    
                    # Save document URL to database
                    doc_id = insert_or_update_case(
                        session=session,
                        url=doc_url,
                        parent_id=page_id,
                        path_url=doc_url,
                        title=title,
                        status_code=200,
                        is_check=IS_CHECK
                    )
                    
                    document_count += 1
                    if existing_doc and IS_CHECK:
                        print(f"Updated document {document_count}: {title[:100]}...")
                    else:
                        print(f"Saved new document {document_count}: {title[:100]}...")
                    
            except Exception as e:
                print(f"Error processing document: {e}")
                continue
        
        print(f"Processed {document_count} documents on this page")
        return page_id
        
    except Exception as e:
        print(f"Error crawling page: {e}")
        return None

def parse_arguments():
    """
    Parse command line arguments for start and end page numbers
    """
    parser = argparse.ArgumentParser(description='EUR-Lex Crawler with page range support')
    parser.add_argument('--start', type=int, default=1, help='Starting page number (default: 1)')
    parser.add_argument('--end', type=int, default=10, help='Ending page number (default: 10)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode (default: True)')
    parser.add_argument('--visible', action='store_true', help='Run with visible browser window')
    
    args = parser.parse_args()
    
    # If --visible is specified, override headless mode
    if args.visible:
        args.headless = False
    
    return args

# Main execution with proper session management
def main():
    """
    Main function to execute the crawler with proper database session management
    """
    global driver
    session = None
    
    # Parse command line arguments
    args = parse_arguments()
    start_page = args.start
    end_page = args.end
    headless_mode = args.headless
    
    print(f"Starting EUR-Lex crawler from page {start_page} to page {end_page}")
    print(f"Headless mode: {headless_mode}")
    
    try:
        # Set up the WebDriver first
        print("Setting up Chrome WebDriver...")
        driver = setup_webdriver(headless=headless_mode)
        
        # Navigate to the start URL
        start_url = BASE_URL.format(start_page)
        print(f"Navigating to: {start_url}")
        driver.get(start_url)
        
        # Create database session
        session = get_session()
        print("Database session created successfully")
        
        # Crawl pages in the specified range
        page_count = 0
        current_page = start_page
        
        while current_page <= end_page:
            try:
                # Navigate to the specific page if not on the first page
                if current_page > start_page:
                    page_url = BASE_URL.format(current_page)
                    print(f"Navigating to page {current_page}: {page_url}")
                    driver.get(page_url)
                    time.sleep(2)  # Wait for page to load
                
                # Crawl the current page
                page_id = crawl_page(session, parent_id=None)
                if not page_id:
                    print(f"Failed to crawl page {current_page}")
                    break
                
                page_count += 1
                print(f"Successfully crawled page {current_page}")
                
                # Move to next page
                current_page += 1
                
            except Exception as e:
                print(f"Error crawling page {current_page}: {e}")
                break
                
        print(f"Crawling completed. Total pages processed: {page_count}")
        
    except Exception as e:
        print(f"Error during crawling: {e}")
    finally:
        # Clean up resources
        if session:
            session.close()
            print("Database session closed")
        
        # Close the browser
        if driver:
            driver.quit()
            print("Browser closed")

# Run the crawler
if __name__ == "__main__":
    main()