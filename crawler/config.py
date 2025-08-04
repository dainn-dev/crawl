import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'mindlex_crawl')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

CRAWL_DELAY = float(os.getenv('CRAWL_DELAY', 0.01))  # seconds
IS_CHECK = os.getenv('IS_CHECK', 'true').lower() == 'true'  # Check and update existing URLs
MAX_THREADS = int(os.getenv('MAX_THREADS', 5))  # Number of threads for crawling

# Target websites configuration
TARGET_SITES = [
    {
        'domain': 'cylaw.org',
        'start_url': 'https://cylaw.org',
        'name': 'CyLaw',
        'exclude_extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz']
    },
    {
        'domain': 'eur-lex.europa.eu',
        'start_url': 'https://eur-lex.europa.eu/homepage.html?locale=en',
        'name': 'EUR-Lex',
        'exclude_extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz']
    },    
    {
        'domain': 'hudoc.echr.coe.int',
        'start_url': 'https://hudoc.echr.coe.int',
        'name': 'HUDOC',
         'exclude_extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz']
    },
    {
        'domain': 'curia.europa.eu',
        'start_url': 'https://curia.europa.eu/jcms/jcms/j_6/en/',
        'name': 'Curia',
        'exclude_extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz']
    },
    {
        'domain': 'www.bailii.org',
        'start_url': 'https://www.bailii.org',
        'name': 'Bailii',
        'exclude_extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz']
    }
] 