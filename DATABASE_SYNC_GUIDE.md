# Database Sync Guide

## Problem Scenario

You have **100k records in the database** but **no data in `crawl_progress.json`**. This means:
- ✅ URLs are stored in the database
- ❌ Crawl progress tracking is empty
- 🔄 Need to sync database URLs to progress to avoid re-crawling

## Solution Overview

The system now automatically checks the database for existing URLs and skips them during crawling, even when `crawl_progress.json` is empty.

## How It Works

### 1. **Automatic Database Check**
When you start crawling with `resume=True`, the system:
- ✅ Loads existing URLs from `crawl_progress.json` (if any)
- ✅ **NEW**: Also loads existing URLs from the database
- ✅ Combines both sources to create a complete "visited" set
- ✅ Skips all already crawled URLs

### 2. **Database Sync Utility**
Use `db_sync_util.py` to manage the sync process:

## Step-by-Step Solution

### **Step 1: Check Existing URLs**
```bash
# Check what URLs exist in database for a domain
python db_sync_util.py check cylaw.org
```

**Example Output:**
```
=== Checking existing URLs for cylaw.org ===
Found 4,092 existing URLs for cylaw.org

Sample URLs:
  1. http://cylaw.org
  2. http://cylaw.org/about.html
  3. http://cylaw.org/additions.html
  ... and 4082 more URLs

Domain Statistics:
  Total URLs: 4,092
  Successful: 4,092 (100.0%)
  Failed: 0
```

### **Step 2: Sync Database to Progress**
```bash
# Sync database URLs to crawl progress
python db_sync_util.py sync cylaw.org
```

**Example Output:**
```
=== Syncing database URLs to progress for cylaw.org ===
Current progress URLs: 50
✅ Progress synced! 4,092 URLs now in progress file
Added 4,042 new URLs from database to progress
```

### **Step 3: Verify Sync**
```bash
# Check statistics and overlap
python db_sync_util.py stats cylaw.org
```

**Example Output:**
```
=== Domain Statistics for cylaw.org ===
📊 DATABASE STATISTICS:
   Total URLs: 4,092
   Successful: 4,092 (100.0%)
   Failed: 0

📈 PROGRESS STATISTICS:
   URLs in progress: 4,092
   Current depth: 3

🔄 OVERLAP ANALYSIS:
   Database URLs: 4,092
   Progress URLs: 4,092
   Overlapping URLs: 4,092
   URLs only in DB: 0
   URLs only in progress: 0
```

### **Step 4: Start Crawling**
```bash
# Start crawling - it will automatically skip existing URLs
python run_fast_crawler.py
```

**Expected Behavior:**
```
2025-08-04 17:39:11,599 [INFO] Resuming crawl for cylaw.org: 4092 URLs already crawled
2025-08-04 17:39:11,663 [INFO] Start URL https://cylaw.org already crawled, skipping
2025-08-04 17:39:11,664 [INFO] === Phase 1 (BFS) completed for cylaw.org ===
2025-08-04 17:39:11,664 [INFO] Phase 1 processed 0 URLs up to depth 2
```

## Automatic Database Integration

### **Enhanced Resume Functionality**
The crawler now automatically:
1. **Loads from progress file** (if exists)
2. **Loads from database** (always checked)
3. **Combines both sources** for complete coverage
4. **Skips all existing URLs** during crawling

### **No Manual Sync Required**
You can start crawling immediately:
```bash
python run_fast_crawler.py
```

The system will automatically detect and skip existing URLs from the database, even if `crawl_progress.json` is empty.

## Database Sync Commands

### **Check Existing URLs**
```bash
python db_sync_util.py check <domain>
```
- Shows existing URLs in database
- Displays domain statistics
- Lists sample URLs

### **Sync Database to Progress**
```bash
python db_sync_util.py sync <domain>
```
- Copies database URLs to progress file
- Merges with existing progress
- Shows what was added

### **View Statistics**
```bash
python db_sync_util.py stats <domain>
```
- Shows database vs progress comparison
- Displays overlap analysis
- Lists status code breakdown

### **Clear Progress**
```bash
python db_sync_util.py clear_progress
```
- Clears all progress files
- Keeps database intact
- Use with caution

## Performance Benefits

### **Before (Re-crawling everything)**
- ❌ Crawls 100k URLs again
- ❌ Wastes time and resources
- ❌ Duplicate database entries

### **After (Smart skipping)**
- ✅ Skips 100k existing URLs
- ✅ Only crawls new URLs
- ✅ Saves significant time
- ✅ No duplicate processing

## Example Workflow

### **Scenario: 100k URLs in DB, empty progress**

1. **Check what exists:**
   ```bash
   python db_sync_util.py check cylaw.org
   # Shows 100,000 URLs exist
   ```

2. **Start crawling (automatic skip):**
   ```bash
   python run_fast_crawler.py
   # Automatically skips 100k URLs
   # Only processes new URLs
   ```

3. **Monitor progress:**
   ```bash
   python speed_monitor_util.py watch
   # Shows only new URLs being processed
   ```

## Troubleshooting

### **No URLs Found in Database**
```bash
python db_sync_util.py check cylaw.org
# Output: "No existing URLs found for cylaw.org"
```
**Solution:** Start fresh crawling - no existing data to skip.

### **Sync Shows 0 New URLs**
```bash
python db_sync_util.py sync cylaw.org
# Output: "No new URLs added (all were already in progress)"
```
**Solution:** Progress already contains all database URLs.

### **Crawler Still Processes Known URLs**
**Check:**
1. Database connection is working
2. Domain name matches exactly
3. URL normalization is consistent

**Debug:**
```bash
python db_sync_util.py stats cylaw.org
# Check overlap analysis
```

## Advanced Usage

### **Multiple Domains**
```bash
# Sync all domains at once
for domain in cylaw.org eur-lex.europa.eu; do
    python db_sync_util.py sync $domain
done
```

### **Selective Sync**
```bash
# Only sync specific domains
python db_sync_util.py sync cylaw.org
python db_sync_util.py sync eur-lex.europa.eu
```

### **Progress Backup**
```bash
# Backup progress before sync
cp crawl_progress.json crawl_progress_backup.json
python db_sync_util.py sync cylaw.org
```

## Integration with Other Tools

### **Database Cleanup + Sync**
```bash
# Clean database first, then sync
python db_cleanup.py cleanup
python db_sync_util.py sync cylaw.org
```

### **Speed Monitoring + Sync**
```bash
# Sync then monitor speed
python db_sync_util.py sync cylaw.org
python run_fast_crawler.py &
python speed_monitor_util.py watch
```

This comprehensive solution ensures that your 100k database records are properly recognized and skipped during crawling, saving significant time and resources! 