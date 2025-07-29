# Multi-Site Legal Web Crawler

A multi-threaded web crawler for legal websites that stores crawled data in a PostgreSQL database. The crawler supports multiple legal information websites including EUR-Lex, CyLaw, HUDOC, Curia, and BAILII, with both Depth-First Search (DFS) and Breadth-First Search (BFS) traversal methods.

## Target Websites

The crawler targets the following legal information websites:

- **[EUR-Lex](https://eur-lex.europa.eu)** - Access to European Union law
- **[CyLaw](https://cylaw.org)** - Cyprus Legal Information Institute
- **[HUDOC](https://hudoc.echr.coe.int)** - European Court of Human Rights
- **[Curia](https://curia.europa.eu)** - Court of Justice of the European Union
- **[BAILII](https://www.bailii.org)** - British and Irish Legal Information Institute

## Features

- **Dual Traversal Methods**: Support for both DFS and BFS crawling strategies
- **Multi-threading**: Parallel crawling of multiple sites
- **Domain Isolation**: Each site crawled independently
- **Thread-safe**: Prevents race conditions with proper locking
- **Respectful Crawling**: Configurable delays between requests
- **Database Storage**: PostgreSQL with relationship tracking
- **Robust Error Handling**: Graceful handling of network and parsing errors
- **Encoding Detection**: Automatic content encoding detection and fallback

## Setup

### 1. Environment Setup

```bash
# Navigate to the crawl directory
cd crawl

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Configuration

The crawler comes with pre-configured database settings. If you need to customize them, create a `.env` file in the crawl directory:

```env
DB_HOST=your_host
DB_PORT=your_port
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
CRAWL_DELAY=0.01
IS_CHECK=true
MAX_THREADS=5
```

**Default Configuration:**
- Host: `150.5.161.34`
- Port: `15432`
- Database: `mindlex_crawl_v2`
- User: `mindlex_dev_usr`

## Usage Guide

### Basic Commands

#### Run All Sites (Default DFS)
```bash
python -m crawler.main
```

#### Run Specific Site
```bash
# Run only CyLaw
python -m crawler.main --site CyLaw

# Run only EUR-Lex
python -m crawler.main --site EUR-Lex
```

### Traversal Methods

#### Depth-First Search (DFS) - Default
DFS goes deep into the site structure before backtracking. Good for hierarchical content discovery.

```bash
# Default DFS behavior
python -m crawler.main --site CyLaw

# Explicit DFS
python -m crawler.main --site CyLaw
```

#### Breadth-First Search (BFS) - New Feature
BFS processes all pages at the same depth before moving to the next level. Better for finding content at similar depths.

```bash
# Use BFS traversal
python -m crawler.main --site CyLaw --use-bfs

# BFS with custom parameters
python -m crawler.main --site CyLaw --use-bfs --max-depth 3
```

### Command Line Options

| Option                                        | Description                       | Default         |
|-----------------------------------------------|-----------------------------------|-----------------|
| `--site {EUR-Lex,CyLaw,HUDOC,Curia,Bailii}`   | Target specific site              | All sites       |
| `--use-bfs`                                   | Use Breadth-First Search          | DFS             |
| `--max-depth N`                               | Maximum crawl depth               | 5               |
| `--threads N`                                 | Number of threads                 | 5               |
| `--delay N`                                   | Delay between requests (seconds)  | 0.01            |
| `--no-check`                                  | Skip checking existing URLs       | Check enabled   |

### Advanced Usage Examples

#### Quick Testing
```bash
# Quick test with shallow depth
python -m crawler.main --site CyLaw --max-depth 2 --threads 2

# Quick test with BFS
python -m crawler.main --site CyLaw --use-bfs --max-depth 2
```

#### Production Crawling
```bash
# Full crawl with respectful delays
python -m crawler.main --site CyLaw --max-depth 5 --threads 3 --delay 0.5

# Full crawl with BFS
python -m crawler.main --site CyLaw --use-bfs --max-depth 5 --threads 3 --delay 0.5
```

#### Performance Optimization
```bash
# Skip URL checking for faster crawling (may create duplicates)
python -m crawler.main --site CyLaw --no-check --max-depth 3

# High-performance crawl
python -m crawler.main --site CyLaw --no-check --max-depth 3 --threads 8 --delay 0.01
```

#### Multi-Site Crawling
```bash
# Crawl all sites with DFS
python -m crawler.main --max-depth 3 --threads 5

# Crawl all sites with BFS
python -m crawler.main --use-bfs --max-depth 3 --threads 5
```

## Traversal Method Comparison

| Aspect                | DFS (Default)               | BFS (--use-bfs)             |
|-----------------------|-----------------------------|-----------------------------|
| **Traversal Pattern** | Deep first, then backtrack  | Level by level              |
| **Memory Usage**      | Lower (call stack)          | Higher (queue)              |
| **Best For**          | Hierarchical content        | Content at same depth       |
| **Speed**             | Faster for deep content     | Faster for broad content    |
| **Use Case**          | Legal document hierarchies  | Finding similar legal cases |

## How It Works

### Architecture
- **Multi-threading**: Each target website is crawled in its own thread
- **Domain isolation**: Each site is crawled independently
- **Thread-safe**: Uses locks to prevent race conditions
- **Respectful crawling**: Configurable delays between requests
- **Database storage**: PostgreSQL with proper relationship tracking

### Crawling Process
1. **URL Validation**: Checks if URL belongs to target domain
2. **Duplicate Prevention**: Tracks visited URLs to avoid re-crawling
3. **Content Fetching**: Downloads page with proper encoding handling
4. **Content Parsing**: Uses BeautifulSoup for HTML/XML parsing
5. **Data Extraction**: Extracts title, links, and breadcrumbs
6. **Database Storage**: Stores data with parent-child relationships
7. **Link Discovery**: Finds new URLs to crawl
8. **Recursive Crawling**: Continues until max depth reached

### Error Handling
- **Network Errors**: Graceful handling of connection timeouts
- **Encoding Issues**: Multiple fallback encodings
- **Parsing Errors**: Robust HTML/XML parsing with fallbacks
- **Database Errors**: Transaction rollback on failures

## Database Schema

The crawler stores data in a `courtcases` table with the following structure:

| Field           | Type      | Description                          |
|-----------------|-----------|--------------------------------------|
| `id`            | UUID      | Primary key                          |
| `url`           | TEXT      | Full URL of the page                 |
| `parent_id`     | UUID      | Parent page ID (for relationships)   |
| `path_url`      | TEXT      | Breadcrumb navigation path           |
| `title`         | TEXT      | Page title                           |
| `crawled_at`    | TIMESTAMP | When page was crawled                |
| `updated_at`    | TIMESTAMP | When data was last updated           |
| `status_code`   | INTEGER   | HTTP status code                     |

## Monitoring and Logging

The crawler provides detailed logging:
- **Progress Tracking**: Shows current depth and URL being processed
- **Performance Metrics**: Crawl speed and completion status
- **Error Reporting**: Detailed error messages for debugging
- **Database Operations**: Logs of data insertion/updates

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check your `.env` file configuration
   - Verify database server is running
   - Ensure network connectivity

2. **Memory Issues with BFS**
   - Reduce `--max-depth` for large sites
   - Use DFS instead of BFS for deep sites
   - Increase system memory if needed

3. **Slow Crawling**
   - Increase `--threads` for more parallelism
   - Reduce `--delay` for faster requests
   - Use `--no-check` to skip URL checking

4. **Network Timeouts**
   - Increase delay between requests
   - Check network connectivity
   - Verify target sites are accessible

### Performance Tips

- **For Deep Sites**: Use DFS with moderate depth
- **For Broad Sites**: Use BFS with shallow depth
- **For Speed**: Use `--no-check` and higher thread count
- **For Stability**: Use longer delays and lower thread count

## Contributing

To add new features or fix issues:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. 