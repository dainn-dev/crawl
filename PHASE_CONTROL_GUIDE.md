# Hybrid Crawler Phase Control Guide

## Overview

The hybrid crawler now supports **explicit phase control** with clear logging of when each phase starts and ends. This gives you better visibility and control over the crawling process.

## Phase Control Options

### 1. **Automatic Phase Transition** (Default)
The crawler automatically transitions from Phase 1 (BFS) to Phase 2 (DFS) based on depth.

**How it works:**
- **Phase 1 (BFS)**: Crawls up to `bfs_depth` (default: 2) using BFS strategy
- **Phase 2 (DFS)**: Automatically starts when depth exceeds `bfs_depth`
- **Transition**: Seamless and automatic

**Usage:**
```bash
python run_fast_crawler.py
```

**Example Output:**
```
=== Starting Phase 1 (BFS) for eur-lex.europa.eu ===
Phase 1 will crawl up to depth 2 using BFS strategy
Crawling [eur-lex.europa.eu] (Phase BFS depth 0): https://eur-lex.europa.eu/homepage.html
Crawling [eur-lex.europa.eu] (Phase BFS depth 1): https://eur-lex.europa.eu/about.html
=== Phase 1 (BFS) completed for eur-lex.europa.eu ===
Phase 1 processed 50 URLs up to depth 2
=== Starting Phase 2 (DFS) for eur-lex.europa.eu ===
Phase 2 will explore deeper levels (depth 3 to 5) using DFS strategy
Crawling [eur-lex.europa.eu] (Phase DFS depth 3): https://eur-lex.europa.eu/deep/page.html
```

### 2. **Manual Phase Control** (Advanced)
Allows you to manually trigger Phase 2 after reviewing Phase 1 results.

**How it works:**
- **Phase 1 (BFS)**: Runs automatically and stops at `bfs_depth`
- **Phase 2 (DFS)**: Requires manual trigger using `trigger_phase2_dfs()`
- **Control**: You decide when to start Phase 2

**Usage:**
```bash
python manual_phase_crawler.py
```

**Example Workflow:**
```python
from crawler.main import run_manual_phase_crawl
from crawler.crawler import trigger_phase2_dfs

# Run Phase 1 only
phase1_result = run_manual_phase_crawl(max_depth=5, bfs_depth=2)

# Review Phase 1 results
print(f"Phase 1 discovered {phase1_result['phase1_urls']} URLs")

# Manually trigger Phase 2
phase2_result = trigger_phase2_dfs(phase1_result)
```

## Configuration Options

### Phase Depth Control
```python
# In crawler.py
def crawl_page_hybrid_parallel(
    start_url, 
    domain, 
    max_depth=5,           # Total crawl depth
    bfs_depth=2,           # Phase 1 depth (BFS)
    exclude_extensions=None,
    max_workers=10,
    save_interval=50
):
```

**Examples:**
- `bfs_depth=1, max_depth=3`: Phase 1 crawls depth 0-1, Phase 2 crawls depth 2-3
- `bfs_depth=2, max_depth=5`: Phase 1 crawls depth 0-2, Phase 2 crawls depth 3-5
- `bfs_depth=3, max_depth=3`: Only Phase 1 (no Phase 2)

### Phase-Specific Settings
```python
# Phase 1 (BFS) settings
bfs_depth = 2              # How deep to crawl in Phase 1
max_workers_phase1 = 10    # Parallel workers for Phase 1

# Phase 2 (DFS) settings  
max_depth = 5              # Total depth including Phase 2
max_workers_phase2 = 5     # Parallel workers for Phase 2
```

## Phase Logging

### Automatic Phase Logging
The crawler now provides clear phase indicators:

```
=== Starting Phase 1 (BFS) for domain.com ===
Phase 1 will crawl up to depth 2 using BFS strategy
Crawling [domain.com] (Phase BFS depth 0): https://domain.com
Crawling [domain.com] (Phase BFS depth 1): https://domain.com/page1
=== Phase 1 (BFS) completed for domain.com ===
Phase 1 processed 25 URLs up to depth 2
=== Starting Phase 2 (DFS) for domain.com ===
Phase 2 will explore deeper levels (depth 3 to 5) using DFS strategy
Crawling [domain.com] (Phase DFS depth 3): https://domain.com/deep/page
```

### Manual Phase Control Logging
```
=== Starting Phase 1 (BFS) for domain.com ===
Phase 1 will crawl up to depth 1 using BFS strategy
Phase 1 will run automatically. Phase 2 will require manual trigger.
=== Phase 1 (BFS) completed for domain.com ===
Phase 1 processed 15 URLs up to depth 1
Phase 1 discovered 15 URLs
Phase 2 ready to start. Use trigger_phase2_dfs() to continue.
```

## Use Cases

### 1. **Quick Discovery** (Automatic)
Use automatic phase transition for fast, comprehensive crawling:
```bash
python run_fast_crawler.py
```

**Best for:**
- Quick site exploration
- Automated crawling
- When you want both phases to run

### 2. **Controlled Exploration** (Manual)
Use manual phase control when you want to review results:
```bash
python manual_phase_crawler.py
```

**Best for:**
- Reviewing Phase 1 results before Phase 2
- Selective deep crawling
- Resource management
- Quality control

### 3. **Phase 1 Only**
Run only the discovery phase:
```python
# Set bfs_depth = max_depth
crawl_page_hybrid_parallel(
    start_url="https://example.com",
    domain="example.com", 
    max_depth=2,
    bfs_depth=2  # Same as max_depth = Phase 1 only
)
```

**Best for:**
- Quick site mapping
- URL discovery only
- When you don't need deep crawling

## Performance Comparison

### Automatic vs Manual Control

| Aspect | Automatic | Manual |
|--------|-----------|--------|
| **Speed** | Faster (no pauses) | Slower (manual review) |
| **Control** | Limited | Full control |
| **Resource Usage** | Continuous | Phased |
| **Quality Control** | None | Full review |
| **Use Case** | Production | Development/Testing |

### Phase Performance

| Phase | Strategy | Speed | Discovery | Depth |
|-------|----------|-------|-----------|-------|
| **Phase 1 (BFS)** | Breadth-First | Fast | Wide | Shallow |
| **Phase 2 (DFS)** | Depth-First | Slower | Deep | Deep |

## Advanced Configuration

### Custom Phase Transitions
```python
# Custom phase transition logic
def custom_phase_transition(phase1_result):
    if phase1_result['urls_processed'] > 100:
        # Only start Phase 2 if Phase 1 found many URLs
        return trigger_phase2_dfs(phase1_result)
    else:
        print("Phase 1 found too few URLs, skipping Phase 2")
        return None
```

### Phase-Specific Settings
```python
# Different settings per phase
phase1_settings = {
    'max_workers': 10,
    'save_interval': 25,
    'exclude_extensions': ['.pdf', '.jpg']
}

phase2_settings = {
    'max_workers': 5,
    'save_interval': 50,
    'exclude_extensions': []  # Include all in Phase 2
}
```

## Troubleshooting

### Phase 1 Too Fast
- Increase `bfs_depth` for more discovery
- Reduce `max_workers` for slower processing
- Add more `exclude_extensions` to skip unwanted files

### Phase 2 Too Slow
- Reduce `max_depth` for less deep crawling
- Increase `max_workers` for parallel processing
- Use manual control to review Phase 1 results

### No Phase 2 Trigger
- Check if `bfs_depth < max_depth`
- Verify Phase 1 completed successfully
- Use manual control for explicit Phase 2 trigger

## Summary

The hybrid crawler now provides:

✅ **Clear Phase Logging**: See exactly when each phase starts/ends
✅ **Automatic Transition**: Seamless Phase 1 → Phase 2
✅ **Manual Control**: Trigger Phase 2 when ready
✅ **Flexible Configuration**: Customize depth and settings per phase
✅ **Performance Options**: Choose speed vs control

**Choose based on your needs:**
- **Automatic**: For production crawling
- **Manual**: For development and testing
- **Phase 1 Only**: For quick discovery 