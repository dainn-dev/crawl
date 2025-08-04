import logging
import os
from datetime import datetime

def setup_logging():
    """Setup logging configuration for the crawler"""
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Generate filename with current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"logs/crawler_{current_date}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_filename, mode='a', encoding='utf-8')  # File output
        ]
    )

# Initialize logging when module is imported
setup_logging() 