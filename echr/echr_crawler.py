import requests
import os
import sys
import logging
from playwright.sync_api import sync_playwright
import time
import re
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.db import get_session, insert_or_update_case
from crawler.logging_config import setup_logging
from urllib.parse import quote_plus

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://hudoc.echr.coe.int"
QUERY_STRING = "contentsitename:ECHR AND (NOT (doctype:PR OR doctype:HFCOMOLD OR doctype:HECOMOLD))"
FIELDS = [
    "sharepointid", "rank", "echrranking", "languagenumber", "itemid", "docname", "doctype",
    "application", "appno", "conclusion", "importance", "originatingbody", "typedescription",
    "kpdate", "kpdateastext", "documentcollectionid", "documentcollectionid2", "languageisocode",
    "extractedappno", "isplaceholder", "doctypebranch", "respondent", "advopidentifier",
    "advopstatus", "ecli", "appnoparts", "sclappnos", "ECHRConcepts"
]
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
    'Authorization': 'Bearer',
    'Referer': 'https://hudoc.echr.coe.int/Javascript/Shared/webWorker.js',
    'Cookie': '__cf_bm=c0Xjoitf5Hc0LIPAN.OK5nZGZG7ZkMM2.ue7b.HrfUc-1754548868-1.0.1.1-MaYJqk7Rz0FIPuvfiptaaYOXhmNPZlEehrDRLVbXSbChzWTT8OaJqFmZ6ORJWh0HgkE9gVmoLn37kS2WYVGF6S3nygfkQBkmO.zb9q34hu0'
}

def fetch_echr_data(start=0, length=1000):
    encoded_query = quote_plus(QUERY_STRING)
    select_fields = ",".join(FIELDS)
    url = f"{BASE_URL}/app/query/results?query={encoded_query}&select={select_fields}&sort=&start={start}&length={length}&rankingModelId=11111111-0000-0000-0000-000000000000"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return None

def process_echr_results(results, session):
    """Process a batch of ECHR results and save them to the database"""
    saved_count = 0
    error_count = 0
    
    for item in results:
        itemid = item.get("columns").get("itemid")
        docname = item.get("columns").get("docname")

        if not itemid or not docname:
            continue  # skip incomplete records

        # Construct document URL
        url = BASE_URL + f"/?i={itemid}"
        title = docname
        path_url = "home"
        status_code = 200  # Since response was OK

        try:
            insert_or_update_case(session, url=url, parent_id=None, path_url=path_url, title=title, status_code=status_code)
            saved_count += 1
        except Exception as e:
            logger.error(f"Error saving case {itemid}: {e}")
            error_count += 1
    
    return saved_count, error_count

def _is_modal_open(page):
    """Check if the refinement modal is currently open."""
    try:
        # Check if modal is visible
        modal_elements = page.query_selector_all('.modal.fade.in')
        return len(modal_elements) > 0 and any(element.is_visible() for element in modal_elements)
    except Exception as e:
        logger.debug(f"Error checking modal state: {e}")
        return False

def _open_refinement_modal(page):
    """Open the refinement filter modal."""
    try:
        logger.info("Opening refinement filter modal...")
        
        # Wait for the button to be visible and clickable
        button_xpath = '//*[@id="refinement-filters-row2-left"]/div/div/div[3]/button'
        page.wait_for_selector(button_xpath, timeout=10000)
        
        # Click the button
        page.click(button_xpath)
        logger.info("✅ Successfully clicked the refinement filter button")
        
        # Wait for the modal to appear
        modal_selector = '.modal.fade.in'
        page.wait_for_selector(modal_selector, timeout=10000)
        logger.info("✅ Modal opened successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to open refinement modal: {e}")
        return False

def navigate_to_hudoc_echr_headless():
    """
    Navigate to HUDOC ECHR website using Playwright in headless mode.
    This version is suitable for automated scripts.
    """
    target_url = "https://hudoc.echr.coe.int/#{%22languageisocode%22:[%22ENG%22],%22pl%22:{%22kt%22:%22AND%22}}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            logger.info(f"Navigating to: {target_url}")
            
            # Navigate to the target URL
            page.goto(target_url, wait_until="networkidle")
            
            # Wait for the page to load completely
            page.wait_for_load_state("networkidle")
            
            logger.info("✅ Successfully navigated to HUDOC ECHR website")
            logger.info(f"Page title: {page.title()}")
            logger.info(f"Current URL: {page.url}")
            
            # Step 1: Click the button to open the modal
            try:
                logger.info("Attempting to click the refinement filter button...")

                open_modal_by_xpath(page, '//*[@id="refinement-filters-row2-left"]/div/div/div[3]/button')

                # Step 2: Extract refinement items from modal and save to respondent.json
                try:
                    logger.info("Extracting refinement items from modal...")

                    refinement_items = get_refinement_items(page)

                    json, output_file, respondents_data = save_refinement_data(refinement_items, 'respondents.json')

                    # Step 2.1: Loop through respondents_data and process unprocessed items
                    try:
                        logger.info("Step 2.1: Processing unprocessed respondents...")
                        
                        # Load existing processed data if available
                        processed_items = set()
                        if os.path.exists('respondent.json'):
                            try:
                                with open('respondent.json', 'r', encoding='utf-8') as f:
                                    existing_data = json.load(f)
                                    for item in existing_data.get('respondents', []):
                                        if item.get('is_processed', False):
                                            processed_items.add(item.get('element_id', ''))
                            except Exception as e:
                                logger.warning(f"Could not load existing processed data: {e}")
                        
                        logger.info(f"Found {len(processed_items)} already processed items")
                        
                        # Process each respondent item
                        processed_count = 0
                        skipped_count = 0
                        
                        for i, item in enumerate(respondents_data):
                            element_id = item.get('element_id', '')
                            text = item.get('text', '')
                            match = re.search(r'\((.*?)\)', text)
                            size =0
                            if match:
                                size = int(match.group(1))

                            
                            # Check if item is already processed
                            if element_id in processed_items or item.get('is_processed', False):
                                logger.info(f"Skipping already processed item {i+1}: {text[:30]}...")
                                skipped_count += 1
                                continue
                            
                            try:
                                logger.info(f"Processing item {i+1}: {text[:50]}...")
                                
                                # Check if the modal is not open then open it
                                if not _is_modal_open(page):
                                    logger.info("Modal is not open, opening it...")
                                    if not _open_refinement_modal(page):
                                        logger.error(f"Failed to open modal for item {i+1}")
                                        continue
                                
                                # Find and click the checkbox for this specific item
                                # Use a more specific selector to target the checkbox for this item
                                item_checkbox_selector = f'.modal.fade.in .refinement-line:nth-child({i+1}) input[type="checkbox"]'
                                
                                # Alternative approach: find checkbox by item text
                                try:
                                    # Wait for the checkbox to be available
                                    page.wait_for_selector(item_checkbox_selector, timeout=5000)
                                    page.click(item_checkbox_selector)
                                    logger.info(f"✅ Successfully clicked checkbox for item {i+1}")
                                    
                                    # Click the AND radio button
                                    and_radio_xpath = '//*[@id="radio_choices_AND"]'
                                    page.wait_for_selector(and_radio_xpath, timeout=10000)
                                    page.click(and_radio_xpath)
                                    logger.info("✅ Successfully clicked AND radio button")

                                    # Click the OK button
                                    ok_button_xpath = '//*[@id="okbutton"]'
                                    page.wait_for_selector(ok_button_xpath, timeout=10000)
                                    page.click(ok_button_xpath)
                                    logger.info("✅ Successfully clicked OK button")
                                    
                                    # Wait for modal to close
                                    page.wait_for_selector('.modal.fade.in', state='hidden', timeout=10000)
                                    logger.info("✅ Modal closed successfully")
                                    
                                    if size > 10000:
                                        # Click the importance button
                                        importance_button_xpath = '//*[@id="refinement-filters-row1-right"]/div/div/div[3]/button'
                                        if open_modal_by_xpath(page, importance_button_xpath):
                                            logger.info("✅ Successfully clicked the importance button")
                                        else:
                                            logger.warning("Failed to click importance button")
                                    else:
                                        logger.info("✅ Successfully processed item (no importance button needed)")

                                except Exception as e:
                                    logger.warning(f"Could not find specific checkbox for item {i+1}, trying alternative method")
                                    
                                    # Alternative: click the first available checkbox
                                    first_checkbox_selector = '.modal.fade.in input[type="checkbox"]'
                                    checkboxes = page.query_selector_all(first_checkbox_selector)
                                    
                                    if i < len(checkboxes):
                                        checkboxes[i].click()
                                        logger.info(f"✅ Successfully clicked checkbox {i+1} using alternative method")
                                    else:
                                        logger.warning(f"No checkbox found for item {i+1}")
                                        continue
                                
                                # Mark item as processed
                                item['is_processed'] = True
                                processed_count += 1
                                
                                # Small delay between clicks to avoid overwhelming the UI
                                time.sleep(0.5)
                                
                            except Exception as e:
                                logger.error(f"Error processing item {i+1}: {e}")
                                continue
                        
                        logger.info(f"Processing summary: {processed_count} processed, {skipped_count} skipped")
                        

                        
                        # Update the JSON file with processed status
                        try:
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump({
                                    'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'total_items': len(respondents_data),
                                    'processed_count': processed_count,
                                    'skipped_count': skipped_count,
                                    'respondents': respondents_data
                                }, f, indent=2, ensure_ascii=False)
                            logger.info(f"✅ Updated {output_file} with processing status")
                        except Exception as e:
                            logger.error(f"Error updating JSON file: {e}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing respondents: {e}")
                        # Continue execution even if this step fails
                    
                except Exception as e:
                    logger.error(f"❌ Error extracting refinement items: {e}")
                    # Continue execution even if extraction fails 
                
            except Exception as e:
                logger.error(f"❌ Error clicking button or opening modal: {e}")
                # Continue execution even if this step fails
                
            # For example, extract data, click buttons, etc.
            
            return page
            
        except Exception as e:
            logger.error(f"❌ Error navigating to HUDOC ECHR: {e}")
            raise
        finally:
            browser.close()


def open_modal_by_xpath(page, button_xpath):
    # Wait for the button to be visible and clickable
    page.wait_for_selector(button_xpath, timeout=10000)
    # Click the button
    page.click(button_xpath)
    logger.info("✅ Successfully clicked the refinement filter button")
    # Wait for the modal to appear
    modal_selector = '.modal.fade.in'
    page.wait_for_selector(modal_selector, timeout=10000)
    logger.info("✅ Modal opened successfully")


def save_refinement_data(refinement_items, output_file):
    # Extract data from each refinement item
    respondents_data = []
    for i, item in enumerate(refinement_items):
        try:
            # Get the text content of the refinement item
            item_text = item.text_content().strip()

            # Get any additional attributes (like data attributes)
            item_data = {
                'index': i,
                'text': item_text,
                'element_id': item.get_attribute('id') or f'item_{i}',
                'class': item.get_attribute('class') or '',
                'is_processed': False  # Flag to indicate if this item has been processed
            }
            respondents_data.append(item_data)
            logger.info(f"Extracted item {i + 1}: {item_text[:50]}...")

        except Exception as e:
            logger.warning(f"Error extracting item {i}: {e}")
            continue
    # Save to respondent.json file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_items': len(respondents_data),
            'respondents': respondents_data
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Successfully saved {len(respondents_data)} refinement items to {output_file}")
    # Log summary of extracted data
    logger.info(f"Extraction summary:")
    logger.info(f"  - Total items found: {len(respondents_data)}")
    logger.info(f"  - Output file: {output_file}")
    return json, output_file, respondents_data


def get_refinement_items(page):
    # Wait for refinement items to load in the modal
    refinement_items_selector = '.modal.fade.in .refinement-line'
    page.wait_for_selector(refinement_items_selector, timeout=10000)
    # Get all refinement items
    refinement_items = page.query_selector_all(refinement_items_selector)
    logger.info(f"Found {len(refinement_items)} refinement items")
    return refinement_items

def main():
    session = get_session()
    
    # Configuration
    total_count = 204957
    page_size = 1000
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    
    logger.info(f"Starting ECHR crawler - Total records: {total_count}, Pages: {total_pages}")
    
    total_saved = 0
    total_errors = 0
    
    for page in range(total_pages):
        start_offset = page * page_size
        
        logger.info(f"Fetching page {page + 1}/{total_pages} (offset: {start_offset})")
        
        # Fetch data for current page
        data = fetch_echr_data(start=start_offset, length=page_size)
        
        if data is None:
            logger.warning(f"Failed to fetch page {page + 1}, skipping...")
            continue
            
        results = data.get("results", [])
        
        if not results:
            logger.info(f"No results found on page {page + 1}, stopping pagination")
            break
            
        logger.info(f"Fetched {len(results)} ECHR records from page {page + 1}")
        
        # Process and save results
        saved_count, error_count = process_echr_results(results, session)
        total_saved += saved_count
        total_errors += error_count
        
        logger.info(f"Page {page + 1} completed - Saved: {saved_count}, Errors: {error_count}")
        
        # Add a small delay between requests to be respectful to the server
        if page < total_pages - 1:  # Don't delay after the last page
            time.sleep(1)
    
    logger.info(f"✅ ECHR import completed.")
    logger.info(f"Total records saved: {total_saved}")
    logger.info(f"Total errors: {total_errors}")

if __name__ == "__main__":
    main()
