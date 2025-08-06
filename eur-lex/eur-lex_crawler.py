from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import sys
import os
import argparse
import logging

# Add the parent directory to the path to import crawler modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.db import create_tables, get_session, insert_or_update_case, get_case_by_url
from crawler.config import IS_CHECK
from crawler.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def setup_webdriver(headless=True):
    """
    Set up Chrome WebDriver with proper options and error handling for Ubuntu server
    
    Args:
        headless (bool): If True, runs browser in headless mode (no visible window)
    """
    try:
        # Configure Chrome options optimized for Ubuntu server
        chrome_options = Options()

        # Essential options for Ubuntu server environments
        chrome_options.add_argument("--no-sandbox")  # Required for running as root
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
        chrome_options.add_argument("--disable-extensions")  # Disable extensions
        chrome_options.add_argument("--disable-plugins")  # Disable plugins
        chrome_options.add_argument("--disable-images")  # Disable images for faster loading
        chrome_options.add_argument("--disable-javascript")  # Disable JavaScript if not needed
        chrome_options.add_argument("--disable-web-security")  # Disable web security
        chrome_options.add_argument("--allow-running-insecure-content")  # Allow insecure content
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Enable headless mode if requested
        if headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            logger.info("Running in headless mode (no browser window will be visible)")
        else:
            logger.info("Running with visible browser window")

        # Try multiple setup strategies for Ubuntu server
        driver = None

        # Strategy 1: Try ChromeDriverManager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("ChromeDriver set up successfully with ChromeDriverManager")
            return driver
        except Exception as e:
            logger.warning(f"ChromeDriverManager failed: {e}")

        # Strategy 2: Try system Chrome driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Using system ChromeDriver")
            return driver
        except Exception as e:
            logger.warning(f"System ChromeDriver failed: {e}")

        # Strategy 3: Try with specific Chrome binary path (common Ubuntu locations)
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
            "/opt/google/chrome/chrome"
        ]

        for chrome_path in chrome_paths:
            try:
                chrome_options.binary_location = chrome_path
                driver = webdriver.Chrome(options=chrome_options)
                logger.info(f"ChromeDriver set up successfully with binary at: {chrome_path}")
                return driver
            except Exception as e:
                logger.debug(f"Failed with binary path {chrome_path}: {e}")
                continue

        # Strategy 4: Try with specific ChromeDriver path
        chromedriver_paths = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "/snap/bin/chromedriver"
        ]

        for chromedriver_path in chromedriver_paths:
            try:
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info(f"ChromeDriver set up successfully with driver at: {chromedriver_path}")
                return driver
            except Exception as e:
                logger.debug(f"Failed with driver path {chromedriver_path}: {e}")
                continue

        # If all strategies fail, provide helpful error message
        error_msg = (
            "Could not set up Chrome WebDriver. Please ensure:\n"
            "1. Chrome browser is installed: sudo apt-get install google-chrome-stable\n"
            "2. ChromeDriver is installed: sudo apt-get install chromium-chromedriver\n"
            "3. Or install via snap: sudo snap install chromium\n"
            "4. Check if running as root (use --no-sandbox option)\n"
            "5. Ensure DISPLAY is set for non-headless mode"
        )
        logger.error(error_msg)
        raise Exception(error_msg)

    except Exception as e:
        logger.error(f"Failed to set up WebDriver: {e}")
        raise


# Initialize database
create_tables()

# Global driver variable (will be initialized in main function)
driver = None

# Base URL template
BASE_URL = "https://eur-lex.europa.eu/search.html?lang=en&qid=1754472457836&type=quick&DD_YEAR={}&page={}"
DOMAIN = "https://eur-lex.europa.eu/search.html?lang=en&qid=1754472457836&type=quick"


# TODO - write function to get years value from xpath //*[@id="genericFacetStateDD_YEAR_list"]/li and //*[@id="DD_YEAR"]/option

def get_years_from_page(driver):
    """
    Extract years from the EUR-Lex search page using the specified XPath selectors.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        list: List of available years as strings
    """
    years = []

    try:
        # Try the first XPath selector for year list items
        year_elements = driver.find_elements(By.XPATH, '//*[@id="genericFacetStateDD_YEAR_list"]/li')

        if year_elements:
            logger.info(f"Found {len(year_elements)} year elements using genericFacetStateDD_YEAR_list selector")
            for element in year_elements:
                try:
                    year_text = element.text.split(' ')[0].strip()
                    if year_text and year_text.isdigit():
                        years.append(year_text)
                except Exception as e:
                    logger.debug(f"Error extracting year from element: {e}")
                    continue

            # If no years found with first selector, try the second XPath selector
            year_elements = driver.find_elements(By.XPATH, '//*[@id="DD_YEAR"]/option')

            if year_elements:
                logger.info(f"Found {len(year_elements)} year elements using DD_YEAR selector")
                for element in year_elements:
                    try:
                        year_text = element.text.split(' ')[0].strip()
                        if year_text and year_text.isdigit():
                            years.append(year_text)
                    except Exception as e:
                        logger.debug(f"Error extracting year from element: {e}")
                        continue

        # Remove duplicates and sort
        years = sorted(list(set(years)), key=int)

        if years:
            logger.info(f"Successfully extracted {len(years)} unique years: {years}")
        else:
            logger.warning("No years found with either XPath selector")

    except Exception as e:
        logger.error(f"Error extracting years from page: {e}")

    return years


def crawl_year_with_pagination(session, year, driver):
    """
    Crawl all pages for a specific year using pagination
    
    Args:
        session: Database session
        year: Year to crawl
        driver: Selenium WebDriver instance
        
    Returns:
        int: Number of pages processed for this year
    """
    pages_processed = 0
    current_page = 1

    try:
        # Start with the first page for this year
        year_url = BASE_URL.format(year, current_page)
        logger.info(f"Starting to crawl year {year}, page {current_page}: {year_url}")
        driver.get(year_url)
        time.sleep(2)  # Wait for page to load

        while True:
            try:
                # Crawl the current page
                page_id = crawl_page(session, parent_id=None)
                if not page_id:
                    logger.error(f"Failed to crawl year {year}, page {current_page}")
                    break

                pages_processed += 1
                logger.info(f"Successfully crawled year {year}, page {current_page}")

                # Look for next page button
                next_button = None

                # Try different selectors for next page button
                next_selectors = [
                    "#pagingFormtop > a:nth-child",
                    "//a[contains(@class, 'next')]",
                    "//a[contains(text(), 'Next')]",
                    "//a[contains(text(), '>')]",
                    "//button[contains(@class, 'next')]",
                    "//button[contains(text(), 'Next')]",
                    "//a[@aria-label='Next page']",
                    "//a[contains(@aria-label, 'Next')]",
                    "//li[@class='next']/a",
                    "a[title='Next Page']"
                    # "//a[contains(@href, 'page=')]"
                ]

                for selector in next_selectors:
                    try:
                        next_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if next_button and next_button.is_enabled() and next_button.is_displayed():
                            logger.info(f"Found next button using selector: {selector}")
                            break
                        else:
                            next_button = None
                    except Exception:
                        continue

                if not next_button:
                    logger.info(f"No more pages found for year {year}. Total pages processed: {pages_processed}")
                    break

                # Check if next button is disabled or not clickable
                try:
                    if not next_button.is_enabled() or 'disabled' in next_button.get_attribute('class'):
                        logger.info(
                            f"Next button is disabled for year {year}. Total pages processed: {pages_processed}")
                        break
                except Exception:
                    pass

                # Click next page
                try:
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2)  # Wait for page to load
                    current_page += 1
                    logger.info(f"Navigated to page {current_page} for year {year}")
                except Exception as e:
                    logger.error(f"Failed to click next button for year {year}, page {current_page}: {e}")
                    break

            except Exception as e:
                logger.error(f"Error processing page {current_page} for year {year}: {e}")
                break

        return pages_processed

    except Exception as e:
        logger.error(f"Error crawling year {year}: {e}")
        return pages_processed


# Function to crawl data
def crawl_page(session, parent_id=None):
    """
    Crawl the current page and save document URLs to database
    """
    try:
        # Get current page URL
        current_url = driver.current_url
        logger.info(f"Crawling page: {current_url}")

        # Check if current page URL already exists in database
        existing_page = get_case_by_url(session, current_url)
        if existing_page and not IS_CHECK:
            logger.info(f"Page URL already exists in database, skipping: {current_url}")
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
                        logger.info(f"Document URL already exists, skipping: {title[:50]}...")
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
                        logger.info(f"Updated document {document_count}: {title[:100]}...")
                    else:
                        logger.info(f"Saved new document {document_count}: {title[:100]}...")

            except Exception as e:
                logger.error(f"Error processing document: {e}")
                continue

        logger.info(f"Processed {document_count} documents on this page")
        return page_id

    except Exception as e:
        logger.error(f"Error crawling page: {e}")
        return None


def parse_arguments():
    """
    Parse command line arguments for crawler options
    """
    parser = argparse.ArgumentParser(description='EUR-Lex Crawler')
    parser.add_argument('--year', type=str, help='Specific year to crawl (e.g., "2023")')
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
    headless_mode = args.headless
    specific_year = args.year
    
    if specific_year:
        logger.info(f"Starting EUR-Lex crawler for specific year: {specific_year}")
    else:
        logger.info(f"Starting EUR-Lex crawler for all available years")
    logger.info(f"Headless mode: {headless_mode}")

    try:
        # Set up the WebDriver first
        logger.info("Setting up Chrome WebDriver...")
        driver = setup_webdriver(headless=headless_mode)

                # Get years to process
        if specific_year:
            # Use only the specified year
            years = [specific_year]
            logger.info(f"Using specified year: {specific_year}")
        else:
            # Navigate to the base domain to get all available years
            logger.info(f"Navigating to base domain: {DOMAIN}")
            driver.get(DOMAIN)
            time.sleep(2)  # Wait for page to load
            
            # Get years from page
            years = get_years_from_page(driver)
            logger.info(f"Years found: {years}")

        # Create database session
        session = get_session()
        logger.info("Database session created successfully")

        # Crawl each year's search results with pagination
        total_years_processed = 0
        total_pages_processed = 0

        for year in years:
            try:
                # Crawl all pages for this year using pagination
                pages_for_year = crawl_year_with_pagination(session, year, driver)

                if pages_for_year > 0:
                    total_years_processed += 1
                    total_pages_processed += pages_for_year
                    logger.info(f"Completed year {year} with {pages_for_year} pages")
                else:
                    logger.warning(f"No pages processed for year {year}")

            except Exception as e:
                logger.error(f"Error crawling year {year}: {e}")
                continue

        logger.info(
            f"Crawling completed. Total years processed: {total_years_processed}, Total pages processed: {total_pages_processed}")

    except Exception as e:
        logger.error(f"Error during crawling: {e}")
    finally:
        # Clean up resources
        if session:
            session.close()
            logger.info("Database session closed")

        # Close the browser
        if driver:
            driver.quit()
            logger.info("Browser closed")


# Run the crawler
if __name__ == "__main__":
    main()
