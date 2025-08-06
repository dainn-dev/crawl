# Progress Checking Guide

## How `run_fast_crawler.py` Checks `crawl_progress.json`

This guide explains exactly how the crawler determines whether to continue processing or skip URLs based on `crawl_progress.json`.

## Overview

When you run `python run_fast_crawler.py`, the system performs a **multi-layered progress check** to avoid re-crawling already processed URLs:

1. **Load from `crawl_progress.json`** (if exists)
2. **Load from database** (always checked)
3. **Combine both sources** for complete coverage
4. **Skip URLs** that are already in the combined set

## Step-by-Step Process

### **Step 1: Initialize Domain Tracking**

```python
# In start_crawl_hybrid_parallel()
initialize_domain_tracking(resume=True)
```

**What happens:**
- Creates thread-safe `visited_sets` for each domain
- Sets `resume=True` to enable progress loading

### **Step 2: Load Progress from File**

```python
# In initialize_domain_tracking()
if resume:
    # Load existing progress from file
    existing_visited, _ = load_progress(domain)
    visited_sets[domain].update(existing_visited)
```

**What happens:**
- Reads `crawl_progress.json` file
- Loads URLs for each domain
- Adds them to the `visited_sets`

### **Step 3: Load Progress from Database**

```python
# Also load existing URLs from database
from crawler.db import get_existing_urls_for_domain
db_urls = get_existing_urls_for_domain(domain)
visited_sets[domain].update(db_urls)
```

**What happens:**
- Queries database for all URLs for the domain
- Adds database URLs to the `visited_sets`
- **This ensures even if `crawl_progress.json` is empty, database URLs are still skipped**

### **Step 4: Start URL Check**

```python
# In crawl_page_hybrid_parallel()
existing_visited, _ = load_progress(domain)
visited = existing_visited.copy()

# Add start URL to queue if not already visited
if start_url not in visited:
    queue = deque([(start_url, None, 0)])
else:
    queue = deque()
    logger.info(f"Start URL {start_url} already crawled, skipping")
```

**What happens:**
- Checks if the start URL is already in the visited set
- If yes: skips the entire site (no URLs to process)
- If no: adds start URL to the queue for processing

### **Step 5: Per-URL Check During Crawling**

```python
# In crawl_single_url()
with visited_lock:
    if normalized_url in visited:
        return []  # Skip this URL
    visited.add(normalized_url)
    urls_processed += 1
```

**What happens:**
- For each URL discovered during crawling
- Thread-safe check if URL is already visited
- If yes: skip processing
- If no: add to visited set and process

## Progress File Structure

### **`crawl_progress.json` Format:**

```json
{
  "cylaw.org": {
    "visited_urls": [
      "http://cylaw.org",
      "http://cylaw.org/about.html",
      "http://cylaw.org/contact.html"
    ],
    "current_depth": 3,
    "timestamp": 1691172000.0
  },
  "eur-lex.europa.eu": {
    "visited_urls": [
      "https://eur-lex.europa.eu",
      "https://eur-lex.europa.eu/homepage.html"
    ],
    "current_depth": 2,
    "timestamp": 1691172100.0
  }
}
```

## Progress Loading Functions

### **`load_progress(domain)`**

```python
def load_progress(domain):
    """Load crawl progress from file"""
    try:
        if not os.path.exists(PROGRESS_FILE):
            return set(), 0
        
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
        
        if domain in progress:
            visited_urls = set(progress[domain].get('visited_urls', []))
            current_depth = progress[domain].get('current_depth', 0)
            timestamp = progress[domain].get('timestamp', 0)
            
            logger.info(f"Loaded progress for {domain}: {len(visited_urls)} URLs, depth {current_depth}")
            return visited_urls, current_depth
        else:
            return set(), 0
    except Exception as e:
        logger.error(f"Failed to load progress: {e}")
        return set(), 0
```

**What it does:**
- Checks if `crawl_progress.json` exists
- Loads URLs for the specific domain
- Returns visited URLs set and current depth
- Handles errors gracefully

### **`save_progress(domain, visited_urls, current_depth)`**

```python
def save_progress(domain, visited_urls, current_depth=0):
    """Save crawl progress to file"""
    with progress_lock:
        try:
            # Load existing progress
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r') as f:
                    progress = json.load(f)
            else:
                progress = {}
            
            # Update progress for this domain
            progress[domain] = {
                'visited_urls': list(visited_urls),
                'current_depth': current_depth,
                'timestamp': time.time()
            }
            
            # Save to file
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(progress, f, indent=2)
                
            logger.info(f"Progress saved for {domain}: {len(visited_urls)} URLs, depth {current_depth}")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
```

**What it does:**
- Thread-safe progress saving
- Updates progress for specific domain
- Saves timestamp and current depth
- Preserves progress for other domains

## Database Integration

### **`get_existing_urls_for_domain(domain)`**

```python
def get_existing_urls_for_domain(domain):
    """Get all existing URLs for a domain from database"""
    session = get_session()
    try:
        # Query for all URLs for this domain
        results = session.query(CourtCase.url).filter(
            CourtCase.url.like(f'%{domain}%')
        ).all()
        
        # Normalize URLs and return set
        urls = set()
        for (url,) in results:
            normalized = normalize_url(url)
            if normalized:
                urls.add(normalized)
        
        return urls
    except Exception as e:
        logger.error(f"Error getting existing URLs for {domain}: {e}")
        return set()
    finally:
        session.close()
```

**What it does:**
- Queries database for all URLs containing the domain
- Normalizes URLs for consistency
- Returns set of existing URLs

## Complete Flow Example

### **Scenario: Resuming a Crawl**

1. **Start `run_fast_crawler.py`:**
   ```bash
   python run_fast_crawler.py
   ```

2. **Initialize tracking:**
   ```python
   initialize_domain_tracking(resume=True)
   ```

3. **Load progress for `cylaw.org`:**
   ```python
   # From crawl_progress.json
   existing_visited = {"http://cylaw.org", "http://cylaw.org/about.html"}
   
   # From database
   db_urls = {"http://cylaw.org", "http://cylaw.org/about.html", "http://cylaw.org/contact.html"}
   
   # Combined visited set
   visited_sets["cylaw.org"] = {"http://cylaw.org", "http://cylaw.org/about.html", "http://cylaw.org/contact.html"}
   ```

4. **Check start URL:**
   ```python
   start_url = "https://cylaw.org"
   if start_url not in visited:
       # Add to queue for processing
   else:
       # Skip - already crawled
       logger.info(f"Start URL {start_url} already crawled, skipping")
   ```

5. **During crawling:**
   ```python
   for each discovered URL:
       if url in visited:
           skip_url()
       else:
           process_url()
           visited.add(url)
           save_progress()  # Every 50 URLs
   ```

## Log Messages You'll See

### **When Progress is Loaded:**
```
2025-08-04 17:39:11,599 [INFO] Loaded progress for cylaw.org: 4092 URLs, depth 20
2025-08-04 17:39:11,599 [INFO] Resuming crawl for cylaw.org: 4092 URLs already crawled
```

### **When Start URL is Skipped:**
```
2025-08-04 17:39:11,663 [INFO] Start URL https://cylaw.org already crawled, skipping
```

### **When Progress is Saved:**
```
2025-08-04 17:39:11,664 [INFO] Progress saved for cylaw.org: 4092 URLs, depth 20
```

### **When URLs are Skipped During Crawling:**
```
2025-08-04 17:39:11,665 [INFO] Skipping already crawled URL: http://cylaw.org/about.html
```

## Key Features

### **1. Dual Source Loading**
- ✅ Loads from `crawl_progress.json` (if exists)
- ✅ Loads from database (always checked)
- ✅ Combines both sources for complete coverage

### **2. Thread Safety**
- ✅ Uses `threading.Lock()` for visited sets
- ✅ Thread-safe progress saving
- ✅ Safe concurrent URL checking

### **3. Automatic Progress Saving**
- ✅ Saves progress every 50 URLs (configurable)
- ✅ Saves progress at crawl completion
- ✅ Preserves progress across interruptions

### **4. Smart URL Normalization**
- ✅ Normalizes URLs for consistent comparison
- ✅ Removes `www.` prefixes
- ✅ Handles different URL formats

### **5. Error Handling**
- ✅ Graceful handling of missing progress file
- ✅ Database connection error handling
- ✅ Continues crawling even if progress loading fails

## Verification Commands

### **Check Current Progress:**
```bash
python crawl_coverage_analyzer.py analyze cylaw.org
```

### **View Progress File:**
```bash
cat crawl_progress.json
```

### **Check Database URLs:**
```bash
python db_sync_util.py check cylaw.org
```

### **Monitor During Crawling:**
```bash
python speed_monitor_util.py watch
```

This comprehensive progress checking ensures that your crawler never re-processes URLs and can efficiently resume from any interruption point! 