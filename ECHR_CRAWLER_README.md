# ECHR (European Court of Human Rights) Crawler

This is a Selenium-based web crawler specifically designed for the ECHR HUDOC website. It can navigate to the specified URL, scroll to load dynamic content, extract URLs, and save them to the database.

## Features

- **Selenium-based crawling**: Uses Chrome WebDriver for JavaScript-heavy pages
- **Dynamic content loading**: Scrolls to load more content as needed
- **BFS and DFS traversal**: Supports both Breadth-First and Depth-First Search
- **Database integration**: Saves crawled URLs to PostgreSQL database
- **Configurable parameters**: Adjustable depth, URL limits, scroll behavior
- **Robust error handling**: Handles timeouts, network issues, and page errors
- **Logging**: Comprehensive logging for monitoring and debugging

## Prerequisites

1. **Python 3.7+**
2. **Chrome browser** installed on your system
3. **PostgreSQL database** running with the required tables
4. **Environment variables** configured (see below)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables in a `.env` file:
```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=mindlex_crawl
DB_USER=postgres
DB_PASSWORD=your_password
CRAWL_DELAY=0.01
IS_CHECK=true
MAX_THREADS=5
```

## Usage

### Quick Start

Run the crawler with default settings:
```bash
python run_echr_crawler.py
```

### Command Line Options

```bash
python run_echr_crawler.py [OPTIONS]
```

**Available options:**
- `--url`: Starting URL (default: ECHR HUDOC document page)
- `--headless`: Run browser in headless mode (default: True)
- `--method`: Crawling method - 'bfs' or 'dfs' (default: 'dfs')
- `--max-depth`: Maximum crawl depth (default: 3)
- `--max-urls`: Maximum URLs to crawl for DFS (default: 100)
- `--max-urls-per-depth`: Maximum URLs per depth for BFS (default: 50)
- `--scroll-pause`: Time to wait between scrolls in seconds (default: 2)
- `--max-scrolls`: Maximum scroll attempts per page (default: 10)

### Examples

**Basic DFS crawl:**
```bash
python run_echr_crawler.py --method dfs --max-depth 2 --max-urls 50
```

**BFS crawl with custom parameters:**
```bash
python run_echr_crawler.py --method bfs --max-depth 3 --max-urls-per-depth 30
```

**Visible browser mode:**
```bash
python run_echr_crawler.py --headless false
```

**Custom starting URL:**
```bash
python run_echr_crawler.py --url "https://hudoc.echr.coe.int/eng#{%22itemid%22:[%22001-123456%22]}"
```

## Crawling Methods

### Depth-First Search (DFS)
- Explores one branch completely before moving to the next
- Good for deep exploration of specific areas
- Uses `--max-urls` parameter to limit total URLs

### Breadth-First Search (BFS)
- Explores all URLs at the same depth before going deeper
- Good for broad discovery of URLs
- Uses `--max-urls-per-depth` parameter to limit URLs per depth level

## Configuration

### ECHRCrawler Class Parameters

```python
crawler = ECHRCrawler(
    headless=True,              # Run browser in headless mode
    scroll_pause_time=2,        # Seconds to wait between scrolls
    max_scroll_attempts=10      # Maximum scroll attempts per page
)
```

### Crawling Parameters

**For BFS:**
```python
crawler.crawl_site_bfs(
    start_url="https://hudoc.echr.coe.int/...",
    max_depth=3,                # Maximum crawl depth
    max_urls_per_depth=50       # Max URLs per depth level
)
```

**For DFS:**
```python
crawler.crawl_site_dfs(
    start_url="https://hudoc.echr.coe.int/...",
    max_depth=3,                # Maximum crawl depth
    max_urls=100                # Maximum total URLs to crawl
)
```

## Database Schema

The crawler saves data to the `courtcases` table with the following structure:

- `id`: UUID primary key
- `url`: Normalized URL (unique)
- `parent_id`: Parent case ID (for hierarchical relationships)
- `path_url`: Breadcrumb path
- `title`: Page title
- `crawled_at`: Timestamp when crawled
- `updated_at`: Timestamp when updated
- `status_code`: HTTP status code

## Logging

The crawler provides comprehensive logging:

- **Console output**: Real-time progress and error messages
- **File logging**: Daily log files in `logs/` directory
- **Log levels**: INFO, WARNING, ERROR, DEBUG

Log files are named: `logs/crawler_YYYY-MM-DD.log`

## Error Handling

The crawler handles various error scenarios:

- **Network timeouts**: Retries with exponential backoff
- **Page load failures**: Logs error and continues with next URL
- **Database errors**: Rolls back transactions and logs errors
- **WebDriver issues**: Graceful shutdown and cleanup

## Performance Considerations

### Memory Usage
- Uses thread-safe visited URL tracking
- Implements depth and URL limits to prevent memory overflow
- Cleans up WebDriver resources properly

### Network Usage
- Configurable delays between requests
- Respects robots.txt (if implemented)
- Uses efficient URL normalization

### Database Performance
- Batch processing for database operations
- Connection pooling
- Proper session management

## Troubleshooting

### Common Issues

1. **Chrome WebDriver not found**
   - Solution: The crawler automatically downloads ChromeDriver using webdriver-manager

2. **Database connection errors**
   - Check your `.env` file configuration
   - Ensure PostgreSQL is running
   - Verify database credentials

3. **Page load timeouts**
   - Increase scroll pause time: `--scroll-pause 5`
   - Reduce max scrolls: `--max-scrolls 5`

4. **Memory issues**
   - Reduce max URLs: `--max-urls 50`
   - Reduce max depth: `--max-depth 2`

### Debug Mode

For debugging, run with visible browser:
```bash
python run_echr_crawler.py --headless false --method dfs --max-urls 10
```

## Advanced Usage

### Custom URL Filtering

You can modify the `is_valid_echr_url()` method in `echr_crawler.py` to customize URL filtering:

```python
def is_valid_echr_url(self, url):
    # Add your custom filtering logic here
    if 'specific-pattern' in url:
        return False
    return super().is_valid_echr_url(url)
```

### Custom Page Processing

Extend the `extract_page_info()` method to extract additional data:

```python
def extract_page_info(self):
    info = super().extract_page_info()
    
    # Add custom extraction logic
    try:
        # Extract additional data from the page
        custom_data = self.driver.find_element(By.CLASS_NAME, "custom-class")
        info['custom_field'] = custom_data.text
    except:
        pass
    
    return info
```

## Monitoring and Maintenance

### Progress Tracking
- Check log files for progress updates
- Monitor database for new entries
- Use database queries to track crawl statistics

### Database Maintenance
```sql
-- Check crawl statistics
SELECT COUNT(*) as total_urls, 
       COUNT(DISTINCT parent_id) as unique_parents,
       MIN(crawled_at) as first_crawl,
       MAX(crawled_at) as last_crawl
FROM courtcases 
WHERE url LIKE '%hudoc.echr.coe.int%';
```

## License

This project is part of the larger crawler system. Please refer to the main project license.

## Support

For issues and questions:
1. Check the logs in `logs/` directory
2. Review the troubleshooting section above
3. Check database connectivity and configuration
4. Verify Chrome browser installation 