import logging

def setup_logging():
    """Setup logging configuration for the crawler"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

# Initialize logging when module is imported
setup_logging() 