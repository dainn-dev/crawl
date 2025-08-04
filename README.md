# Fast Web Crawler - Hybrid DFS/BFS Implementation

A high-performance web crawler that combines Depth-First Search (DFS) and Breadth-First Search (BFS) strategies for optimal crawling speed and coverage.

## 🚀 Key Features

- **Hybrid Crawling Strategy**: Combines BFS for initial discovery with DFS for deep exploration
- **Multi-threaded**: Parallel processing across multiple sites
- **Thread-safe**: Proper synchronization for concurrent crawling
- **Robust Error Handling**: Graceful handling of network issues and encoding problems
- **Configurable**: Easy to adjust depth, delay, and target sites

## 🏆 Performance Benefits

The hybrid approach provides significant speed improvements:

- **BFS Phase**: Quickly discovers many URLs at the same depth level
- **DFS Phase**: Efficiently explores discovered paths in depth
- **Best of Both Worlds**: Faster than pure DFS or BFS alone

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🎯 Quick Start

### Run the Fast Hybrid Crawler

```bash
python run_fast_crawler.py
```

### Compare Different Strategies

```bash
python run_fast_crawler.py compare
```

### Run Performance Tests

```bash
python -m crawler.performance_test
```

## 🔧 Configuration

Edit `crawler/config.py` to customize:

- **CRAWL_DELAY**: Delay between requests (default: 0.01s)
- **MAX_THREADS**: Number of concurrent threads (default: 5)
- **TARGET_SITES**: List of sites to crawl
- **MAX_DEPTH**: Maximum crawl depth

## 📊 Crawling Strategies

### 1. Hybrid (Recommended - Fastest)
```python
from crawler.main import run_hybrid_crawl
run_hybrid_crawl(max_depth=3, sites=target_sites)
```

**Benefits:**
- Uses BFS for initial levels (depth 0-2) to discover many URLs quickly
- Switches to DFS for deeper levels (depth 3+) for thorough exploration
- Significantly faster than pure DFS or BFS

### 2. BFS (Breadth-First Search)
```python
from crawler.main import run_bfs_crawl
run_bfs_crawl(max_depth=3, sites=target_sites)
```

**Benefits:**
- Good for wide discovery of URLs at the same depth
- Efficient for finding many pages quickly
- Better for shallow crawling

### 3. DFS (Depth-First Search)
```python
from crawler.main import run_dfs_crawl
run_dfs_crawl(max_depth=3, sites=target_sites)
```

**Benefits:**
- Good for deep exploration of specific paths
- Efficient for finding deeply nested content
- Better for thorough crawling of specific sections

## 🏗️ Architecture

```
crawler/
├── crawler.py          # Main crawling logic (DFS, BFS, Hybrid)
├── config.py           # Configuration settings
├── db.py              # Database operations
├── breadcrumb.py       # Breadcrumb extraction
├── utils.py           # URL normalization utilities
├── logging_config.py   # Logging setup
└── main.py            # Entry point and convenience functions
```

## 🔍 How the Hybrid Strategy Works

1. **Phase 1 (BFS)**: 
   - Crawls initial levels (depth 0-2) using breadth-first approach
   - Discovers many URLs quickly at each level
   - Builds a wide foundation of discovered pages

2. **Phase 2 (DFS)**:
   - Takes discovered URLs from BFS phase
   - Explores each path in depth using depth-first approach
   - Thoroughly crawls deeper levels (depth 3+)

3. **Benefits**:
   - Faster discovery of URLs compared to pure DFS
   - More thorough exploration compared to pure BFS
   - Optimal balance of speed and coverage

## 📈 Performance Comparison

| Strategy | Speed | Coverage | Memory Usage | Best For |
|----------|-------|----------|--------------|----------|
| Hybrid   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | General purpose |
| BFS      | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Wide discovery |
| DFS      | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Deep exploration |

## 🛠️ Advanced Usage

### Custom Hybrid Configuration

```python
from crawler.crawler import crawl_page_hybrid

# Customize BFS depth before switching to DFS
crawl_page_hybrid(
    start_url="https://example.com",
    domain="example.com", 
    max_depth=5,
    bfs_depth=2  # Use BFS for first 2 levels, then DFS
)
```

### Multi-site Parallel Crawling

```python
from crawler.crawler import start_crawl_hybrid

# Crawl multiple sites in parallel
start_crawl_hybrid(
    max_depth=3,
    sites=target_sites  # List of site configurations
)
```

## 🔧 Environment Variables

Set these environment variables for customization:

```bash
CRAWL_DELAY=0.01        # Delay between requests (seconds)
MAX_THREADS=5           # Number of concurrent threads
IS_CHECK=true           # Check existing URLs in database
DB_HOST=localhost       # Database host
DB_PORT=5432           # Database port
```

## 📝 Logging

The crawler provides detailed logging:

- **INFO**: Crawling progress and URL discovery
- **WARNING**: Parsing issues and encoding problems
- **ERROR**: Network errors and database issues

## 🚨 Error Handling

The crawler handles various error scenarios:

- **Network timeouts**: Automatic retry with exponential backoff
- **Encoding issues**: Multiple fallback encoding strategies
- **Database errors**: Graceful rollback and continuation
- **Invalid URLs**: Automatic filtering and skipping

## 📊 Monitoring

Track crawling progress through:

- **Console output**: Real-time progress indicators
- **Log files**: Detailed logging for debugging
- **Database**: Stored crawl results and metadata

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **Slow crawling**: Reduce `CRAWL_DELAY` or increase `MAX_THREADS`
2. **Memory issues**: Reduce `MAX_DEPTH` or use BFS strategy
3. **Network errors**: Check internet connection and target site availability
4. **Database errors**: Verify database connection and permissions

### Performance Tips

- Use **Hybrid strategy** for best overall performance
- Adjust `bfs_depth` parameter based on your target sites
- Monitor memory usage with large sites
- Use appropriate `max_depth` for your use case 