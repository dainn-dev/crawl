import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', '150.5.161.34')
DB_PORT = int(os.getenv('DB_PORT', 15432))
DB_NAME = os.getenv('DB_NAME', 'mindlex_crawl_v2')
DB_USER = os.getenv('DB_USER', 'mindlex_dev_usr')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'SF-05a_15aJe6LOu')

CRAWL_DELAY = float(os.getenv('CRAWL_DELAY', 0.01))  # seconds
IS_CHECK = os.getenv('IS_CHECK', 'true').lower() == 'true'  # Check and update existing URLs
MAX_THREADS = int(os.getenv('MAX_THREADS', 5))  # Number of threads for crawling

# Target websites configuration
TARGET_SITES = [
    {
        'domain': 'eur-lex.europa.eu',
        'start_url': 'https://eur-lex.europa.eu',
        'name': 'EUR-Lex'
    },
    {
        'domain': 'cylaw.org',
        'start_url': 'https://cylaw.org',
        'name': 'CyLaw'
    },
    {
        'domain': 'hudoc.echr.coe.int',
        'start_url': 'https://hudoc.echr.coe.int',
        'name': 'HUDOC'
    },
    {
        'domain': 'curia.europa.eu',
        'start_url': 'https://curia.europa.eu',
        'name': 'Curia'
    },
    {
        'domain': 'www.bailii.org',
        'start_url': 'https://www.bailii.org',
        'name': 'Bailii'
    }
] 