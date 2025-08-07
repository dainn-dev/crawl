#!/usr/bin/env python3
"""
Optimized HUDOC ECHR crawler with improved structure and performance.
"""

import requests
import os
import sys
import logging
import json
import time
import re
from playwright.sync_api import sync_playwright
from typing import List, Dict, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.db import get_session, insert_or_update_case
from crawler.logging_config import setup_logging
from urllib.parse import quote_plus

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://hudoc.echr.coe.int"
TARGET_URL = "https://hudoc.echr.coe.int/#{%22languageisocode%22:[%22ENG%22],%22pl%22:{%22kt%22:%22AND%22}}"
SELECTORS = {
    'refinement_button': '//*[@id="refinement-filters-row2-left"]/div/div/div[3]/button',
    'modal': '.modal.fade.in',
    'refinement_items': '.modal.fade.in .refinement-line',
    'checkbox': '.modal.fade.in input[type="checkbox"]',
    'and_radio': '//*[@id="radio_choices_AND"]',
    'ok_button': '//*[@id="okbutton"]',
    'importance_button': '//*[@id="refinement-filters-row1-right"]/div/div/div[3]/button'
}
TIMEOUTS = {
    'short': 5000,
    'medium': 10000,
    'long': 15000
}

class HUDOCProcessor:
    """Optimized HUDOC ECHR processor with better structure and error handling."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.page = None
        self.browser = None
        self.processed_items = set()
        self.respondents_data = []
        
    def __enter__(self):
        """Context manager entry."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
    
    def navigate_to_hudoc(self) -> bool:
        """Navigate to HUDOC ECHR website."""
        try:
            logger.info(f"Navigating to: {TARGET_URL}")
            
            # Navigate with optimized wait strategy
            self.page.goto(TARGET_URL, wait_until="domcontentloaded")
            self.page.wait_for_load_state("networkidle", timeout=TIMEOUTS['medium'])
            
            logger.info("✅ Successfully navigated to HUDOC ECHR website")
            logger.info(f"Page title: {self.page.title()}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False
    
    def open_refinement_modal(self) -> bool:
        """Open the refinement filter modal."""
        try:
            logger.info("Opening refinement filter modal...")
            
            # Wait for button and click
            self.page.wait_for_selector(SELECTORS['refinement_button'], timeout=TIMEOUTS['medium'])
            self.page.click(SELECTORS['refinement_button'])
            
            # Wait for modal to appear
            self.page.wait_for_selector(SELECTORS['modal'], timeout=TIMEOUTS['medium'])
            logger.info("✅ Modal opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to open modal: {e}")
            return False
    
    def extract_refinement_items(self) -> bool:
        """Extract refinement items from modal."""
        try:
            logger.info("Extracting refinement items...")
            
            # Wait for items to load
            self.page.wait_for_selector(SELECTORS['refinement_items'], timeout=TIMEOUTS['medium'])
            refinement_items = self.page.query_selector_all(SELECTORS['refinement_items'])
            
            logger.info(f"Found {len(refinement_items)} refinement items")
            
            # Extract data efficiently
            self.respondents_data = []
            for i, item in enumerate(refinement_items):
                try:
                    item_text = item.text_content().strip()
                    
                    # Extract size from parentheses
                    size = 0
                    match = re.search(r'\((\d+)\)', item_text)
                    if match:
                        size = int(match.group(1))
                    
                    item_data = {
                        'index': i,
                        'text': item_text,
                        'element_id': item.get_attribute('id') or f'item_{i}',
                        'class': item.get_attribute('class') or '',
                        'size': size,
                        'is_processed': False
                    }
                    
                    self.respondents_data.append(item_data)
                    logger.debug(f"Extracted item {i+1}: {item_text[:50]}... (size: {size})")
                    
                except Exception as e:
                    logger.warning(f"Error extracting item {i}: {e}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to extract refinement items: {e}")
            return False
    
    def load_processed_data(self) -> None:
        """Load existing processed data from JSON."""
        try:
            if os.path.exists('respondent.json'):
                with open('respondent.json', 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for item in existing_data.get('respondents', []):
                        if item.get('is_processed', False):
                            self.processed_items.add(item.get('element_id', ''))
                logger.info(f"Loaded {len(self.processed_items)} already processed items")
        except Exception as e:
            logger.warning(f"Could not load existing processed data: {e}")
    
    def process_respondents(self) -> Tuple[int, int]:
        """Process unprocessed respondents efficiently."""
        processed_count = 0
        skipped_count = 0
        
        logger.info("Processing unprocessed respondents...")
        
        for i, item in enumerate(self.respondents_data):
            element_id = item.get('element_id', '')
            text = item.get('text', '')
            size = item.get('size', 0)
            
            # Skip already processed items
            if element_id in self.processed_items or item.get('is_processed', False):
                logger.info(f"Skipping already processed item {i+1}: {text[:30]}...")
                skipped_count += 1
                continue
            
            try:
                logger.info(f"Processing item {i+1}: {text[:50]}... (size: {size})")
                
                # Click checkbox with optimized targeting
                if self._click_checkbox(i):
                    # Mark as processed
                    item['is_processed'] = True
                    self.processed_items.add(element_id)
                    processed_count += 1
                    
                    # Apply filters for this item
                    if self._apply_filters():
                        # Check if importance button should be clicked
                        if size > 10000:
                            if self._click_importance_button():
                                logger.info(f"✅ Processed high-value item {i+1} (size: {size})")
                            else:
                                logger.warning(f"Failed to click importance button for item {i+1}")
                        else:
                            logger.info(f"✅ Processed item {i+1} (size: {size})")
                    else:
                        logger.warning(f"Failed to apply filters for item {i+1}")
                
                # Optimized delay
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing item {i+1}: {e}")
                continue
        
        logger.info(f"Processing summary: {processed_count} processed, {skipped_count} skipped")
        return processed_count, skipped_count
    
    def _click_checkbox(self, index: int) -> bool:
        """Click checkbox for specific item with fallback strategies."""
        try:
            # Primary method: specific selector
            item_checkbox_selector = f'{SELECTORS["refinement_items"]}:nth-child({index+1}) input[type="checkbox"]'
            self.page.wait_for_selector(item_checkbox_selector, timeout=TIMEOUTS['short'])
            self.page.click(item_checkbox_selector)
            logger.debug(f"Clicked checkbox {index+1} using primary method")
            return True
            
        except Exception:
            try:
                # Fallback: index-based selection
                checkboxes = self.page.query_selector_all(SELECTORS['checkbox'])
                if index < len(checkboxes):
                    checkboxes[index].click()
                    logger.debug(f"Clicked checkbox {index+1} using fallback method")
                    return True
                else:
                    logger.warning(f"No checkbox found for item {index+1}")
                    return False
            except Exception as e:
                logger.error(f"Failed to click checkbox {index+1}: {e}")
                return False
    
    def _apply_filters(self) -> bool:
        """Apply AND filter and OK button."""
        try:
            # Click AND radio button
            self.page.wait_for_selector(SELECTORS['and_radio'], timeout=TIMEOUTS['short'])
            self.page.click(SELECTORS['and_radio'])
            
            # Click OK button
            self.page.wait_for_selector(SELECTORS['ok_button'], timeout=TIMEOUTS['short'])
            self.page.click(SELECTORS['ok_button'])
            
            # Wait for modal to close
            self.page.wait_for_selector(SELECTORS['modal'], state='hidden', timeout=TIMEOUTS['short'])
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply filters: {e}")
            return False
    
    def _click_importance_button(self) -> bool:
        """Click importance button for high-value items."""
        try:
            self.page.wait_for_selector(SELECTORS['importance_button'], timeout=TIMEOUTS['short'])
            self.page.click(SELECTORS['importance_button'])
            logger.info("✅ Successfully clicked importance button")
            return True
        except Exception as e:
            logger.error(f"Failed to click importance button: {e}")
            return False
    
    def save_results(self, processed_count: int, skipped_count: int) -> bool:
        """Save results to JSON file."""
        try:
            output_data = {
                'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_items': len(self.respondents_data),
                'processed_count': processed_count,
                'skipped_count': skipped_count,
                'respondents': self.respondents_data
            }
            
            with open('respondent.json', 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved results to respondent.json")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False

def navigate_to_hudoc_echr_optimized(headless: bool = True) -> Optional[Dict]:
    """
    Optimized HUDOC ECHR navigation and processing.
    
    Args:
        headless: Whether to run in headless mode
        
    Returns:
        Dictionary with processing results or None if failed
    """
    try:
        with HUDOCProcessor(headless=headless) as processor:
            # Step 1: Navigate to website
            if not processor.navigate_to_hudoc():
                return None
            
            # Step 2: Open refinement modal
            if not processor.open_refinement_modal():
                return None
            
            # Step 3: Extract refinement items
            if not processor.extract_refinement_items():
                return None
            
            # Step 4: Load existing processed data
            processor.load_processed_data()
            
            # Step 5: Process respondents
            processed_count, skipped_count = processor.process_respondents()
            
            # Step 6: Save results
            if processor.save_results(processed_count, skipped_count):
                return {
                    'success': True,
                    'processed_count': processed_count,
                    'skipped_count': skipped_count,
                    'total_items': len(processor.respondents_data)
                }
            else:
                return None
                
    except Exception as e:
        logger.error(f"❌ HUDOC processing failed: {e}")
        return None

# Legacy function for backward compatibility
def navigate_to_hudoc_echr():
    """Legacy function - use navigate_to_hudoc_echr_optimized instead."""
    logger.warning("Using legacy function. Consider using navigate_to_hudoc_echr_optimized for better performance.")
    return navigate_to_hudoc_echr_optimized(headless=True)

if __name__ == "__main__":
    # Test the optimized function
    result = navigate_to_hudoc_echr_optimized(headless=True)
    if result:
        logger.info(f"✅ Processing completed successfully: {result}")
    else:
        logger.error("❌ Processing failed") 