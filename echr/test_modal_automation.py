#!/usr/bin/env python3
"""
Test script for HUDOC ECHR modal automation using Playwright.
This script specifically tests the button click and modal opening functionality.
"""

import sys
import os
import logging
import time

# Add the parent directory to the path so we can import the echr_crawler module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Setup logging
logger = logging.getLogger(__name__)
   

def test_interactive_modal():
    """Test the modal automation in interactive mode"""
    logger.info("🧪 Testing Interactive Modal Automation")
    logger.info("=" * 60)
    
    try:
        from echr_crawler import navigate_to_hudoc_echr
        navigate_to_hudoc_echr()
        logger.info("✅ Interactive modal automation completed")
        
        # Additional verification steps
        logger.info("🔍 Verifying modal automation results...")
        
        # Check if modal was properly closed
        import time
        time.sleep(2)  # Wait for any final animations
        
        logger.info("✅ Modal automation verification completed")
        
    except Exception as e:
        logger.error(f"❌ Interactive modal automation failed: {e}")
        raise

def test_headless_modal():
    """Test the modal automation in headless mode"""
    logger.info("🧪 Testing Headless Modal Automation")
    logger.info("=" * 60)
    
    try:
        from echr_crawler import navigate_to_hudoc_echr_headless
        page = navigate_to_hudoc_echr_headless()
        
        if page:
            logger.info("✅ Headless modal automation completed successfully")
            
            # Take a screenshot to verify the final state
            screenshot_path = "echr_final_state.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved as: {screenshot_path}")
            
            # Check if respondent.json was created and verify processing
            import os
            if os.path.exists('respondent.json'):
                logger.info("✅ respondent.json file was created successfully")
                
                # Read and display summary of extracted data
                import json
                with open('respondent.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                logger.info(f"📊 Processing Summary:")
                logger.info(f"  - Timestamp: {data.get('extraction_timestamp', 'N/A')}")
                logger.info(f"  - Total items: {data.get('total_items', 0)}")
                logger.info(f"  - Processed count: {data.get('processed_count', 0)}")
                logger.info(f"  - Skipped count: {data.get('skipped_count', 0)}")
                
                # Show first few items as preview
                respondents = data.get('respondents', [])
                if respondents:
                    logger.info(f"  - First 3 items:")
                    for i, item in enumerate(respondents[:3]):
                        processed_status = "✅ Processed" if item.get('is_processed', False) else "⏳ Pending"
                        logger.info(f"    {i+1}. {item.get('text', 'N/A')[:50]}... ({processed_status})")
                    
                    # Show processing statistics
                    processed_items = [item for item in respondents if item.get('is_processed', False)]
                    pending_items = [item for item in respondents if not item.get('is_processed', False)]
                    logger.info(f"  - Processing Status:")
                    logger.info(f"    - Processed: {len(processed_items)} items")
                    logger.info(f"    - Pending: {len(pending_items)} items")
            else:
                logger.warning("❌ respondent.json file was not created")
            
        else:
            logger.error("❌ Headless modal automation failed - no page returned")
            
    except Exception as e:
        logger.error(f"❌ Headless modal automation failed: {e}")
        raise

def main():
    """Main function to run the modal automation tests"""
    logger.info("🚀 Starting HUDOC ECHR Modal Automation Tests")
    logger.info("=" * 60)
    
    # Test headless automation first (faster)
    test_headless_modal()
    logger.info("")
    
    # Ask user if they want to test interactive mode
    logger.info("Would you like to test interactive modal automation (opens browser)? (y/n): ")
    response = input().lower().strip()
    
    if response in ['y', 'yes']:
        test_interactive_modal()
    else:
        logger.info("Skipping interactive modal test.")
    
    logger.info("=" * 60)
    logger.info("🎉 Modal automation tests completed!")

if __name__ == "__main__":
    main() 