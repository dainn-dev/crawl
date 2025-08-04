# Web Crawler Resume Guide

## Overview

The web crawler now includes a **resume mechanism** that allows you to stop and restart crawling from where you left off. This is especially useful for long-running crawls that might be interrupted.

## How Resume Works

### 1. **Automatic Progress Saving**
- Progress is automatically saved every 50 URLs processed
- Progress is saved to `crawl_progress.json` in the project root
- Each domain's progress is tracked separately

### 2. **Resume Capability**
- When you restart the crawler, it automatically loads saved progress
- Already crawled URLs are skipped
- Crawling continues from where it left off

## Usage

### Check Current Progress
```bash
python resume_crawler.py status
```

**Example Output:**
```
=== Crawl Progress Status ===

Domain: eur-lex.europa.eu
  URLs Crawled: 50
  Current Depth: 1
  Last Updated: 2025-08-04 12:02:05

Total URLs crawled across all domains: 50
```

### Resume Crawling
```bash
python resume_crawler.py resume
```

**What happens:**
1. Loads saved progress for all domains
2. Skips already crawled URLs
3. Continues crawling from where it left off
4. Shows progress summary before starting

### Clear Progress
```bash
# Clear all progress
python resume_crawler.py clear

# Clear progress for specific domain
python resume_crawler.py clear eur-lex.europa.eu
```

### Start Fresh Crawl
```bash
# Clear all progress first
python resume_crawler.py clear

# Then run normal crawl
python run_fast_crawler.py
```

## Resume Features

### ✅ **Automatic Progress Tracking**
- Saves progress every 50 URLs
- Tracks URLs crawled per domain
- Records current crawl depth
- Timestamps for each save

### ✅ **Smart Resume Logic**
- Loads existing progress on startup
- Skips already visited URLs
- Continues from exact point of interruption
- Maintains crawl depth and strategy

### ✅ **Thread-Safe Operations**
- Progress saving is thread-safe
- Multiple domains can be crawled simultaneously
- No race conditions or data corruption

### ✅ **Easy Management**
- Simple command-line interface
- Clear status reporting
- Easy progress clearing
- Domain-specific operations

## Example Workflow

### 1. Start a Long Crawl
```bash
python run_fast_crawler.py
```

### 2. Interrupt the Crawl (Ctrl+C)
The crawler saves progress automatically before stopping.

### 3. Check Progress
```bash
python resume_crawler.py status
```

### 4. Resume Crawling
```bash
python resume_crawler.py resume
```

The crawler will:
- Load saved progress
- Skip already crawled URLs
- Continue from where it left off
- Show progress summary

## Performance Benefits

### 🚀 **Time Savings**
- No need to restart from beginning
- Skip already processed URLs
- Continue exactly where you left off

### 🚀 **Resource Efficiency**
- Avoid re-crawling same URLs
- Maintain crawl state
- Preserve discovered links

### 🚀 **Reliability**
- Handle interruptions gracefully
- Automatic progress saving
- No data loss on restart

## Configuration

### Progress Save Interval
You can adjust how often progress is saved by modifying the `save_interval` parameter:

```python
# In crawler.py, line 554
def crawl_page_hybrid_parallel(start_url, domain, max_depth=5, bfs_depth=2, exclude_extensions=None, max_workers=10, save_interval=50):
```

- **Default**: 50 URLs
- **Lower value**: More frequent saves, slower performance
- **Higher value**: Less frequent saves, faster performance

### Progress File Location
Progress is saved to `crawl_progress.json` in the project root. You can change this by modifying:

```python
# In crawler.py, line 30
PROGRESS_FILE = "crawl_progress.json"
```

## Troubleshooting

### Progress File Corrupted
If the progress file becomes corrupted:
```bash
python resume_crawler.py clear
```

### Domain-Specific Issues
To clear progress for a specific domain:
```bash
python resume_crawler.py clear eur-lex.europa.eu
```

### Start Fresh
To completely restart without any saved progress:
```bash
python resume_crawler.py clear
python run_fast_crawler.py
```

## Advanced Usage

### Resume with Different Parameters
You can resume with different crawl parameters:

```python
from crawler.main import run_resume_crawl

# Resume with different depth
run_resume_crawl(max_depth=5, sites=TARGET_SITES[:1])
```

### Manual Progress Management
```python
from crawler.crawler import get_progress_summary, clear_progress, load_progress

# Get progress summary
summary = get_progress_summary()

# Load progress for specific domain
visited_urls, depth = load_progress("eur-lex.europa.eu")

# Clear specific domain
clear_progress("eur-lex.europa.eu")
```

## Best Practices

1. **Regular Status Checks**: Use `python resume_crawler.py status` to monitor progress
2. **Backup Progress**: The `crawl_progress.json` file contains your crawl state
3. **Domain Isolation**: Each domain's progress is tracked separately
4. **Graceful Interruption**: Use Ctrl+C to stop crawling safely
5. **Resume Verification**: Always check status before resuming

## Summary

The resume functionality provides:
- ✅ **Automatic progress saving** every 50 URLs
- ✅ **Smart resume logic** that skips already crawled URLs
- ✅ **Thread-safe operations** for parallel crawling
- ✅ **Easy management** with simple commands
- ✅ **Performance benefits** by avoiding re-crawling
- ✅ **Reliability** with graceful interruption handling

This makes the crawler much more practical for long-running operations and ensures no work is lost when interruptions occur. 