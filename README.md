# URL to Training Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A modular Python pipeline for converting **any web content** into structured training datasets for LLM fine-tuning. Orchestrates **scraping → cleaning → chunking → LLM generation** to produce high-quality JSONL dialogue data.

**Perfect for**: Documentation, tutorials, guides, wikis, knowledge bases, or any content-rich websites you want to transform into conversational training data.

> **Example Use Case**: Currently optimized for Black Desert Online (BDO) game guides, but easily adaptable to any domain by adding custom cleaning and chunking strategies.

## 🎯 **Features**

- **🌐 Multi-Source Scraping**: Pluggable scrapers with fallback strategies (supports custom APIs and generic web scraping)
- **🧹 Intelligent Cleaning**: Domain-specific content cleaning to remove boilerplate, navigation, and clutter
- **✂️ Smart Chunking**: Heading-aware text splitting with token-level precision
- **📊 Table/List Splitting**: Context-preserving segmentation for long structured data
- **🤖 LLM Generation**: Google Gemini API integration for dialogue creation (easily swappable)
- **📁 JSONL Output**: Training-ready conversational format compatible with major LLM frameworks
- **🐳 Docker Support**: Containerized deployment with docker-compose
- **⚙️ Fully Configurable**: Environment-based configuration system
- **🔌 Extensible Architecture**: Easy to add new domains, cleaning strategies, or chunking methods

## 💡 **Use Cases**

- **Game Guides & Wikis**: Convert gaming documentation into interactive Q&A datasets
- **Technical Documentation**: Transform API docs, tutorials, or manuals into conversational training data
- **Knowledge Bases**: Extract structured information from FAQs, help centers, or support sites
- **Educational Content**: Convert courses, lessons, or learning materials into dialogue format
- **Product Documentation**: Turn product guides into customer support training data

**Current Implementation**: Optimized for Black Desert Online guides (3 domains: Black Desert Foundry, Garmoth.com, Official Wiki)

## 📁 **Project Structure**

```
├── config.py                  # Configuration & environment variables
├── data_extraction.py         # Main pipeline orchestration
├── scraper.py                 # Web scraping (multi-API strategy)
├── cleaner.py                 # Domain-specific content cleaning
├── chunker.py                 # Token-aware text chunking
├── table_list_splitter.py     # Long table/list splitting
├── generator.py               # LLM interaction & JSONL output
├── requirements.txt           # Python dependencies
├── requirements-minimal.txt   # Minimal Python dependencies for Docker
├── Dockerfile                 # Container image definition
├── docker-compose.yml         # Docker orchestration
├── .env.example               # Environment variable template
├── ARCHITECTURE.md            # System architecture & data flow
├── CONTRIBUTING.md            # Contribution guidelines
├── LICENSE                    # MIT License
├── data/                      # Input data directory (volume-mounted in Docker)
│   ├── LINKS.md               # Markdown file with URLs to process (batch mode)
│   └── processed_links.txt    # Tracks processed URLs to avoid reprocessing
├── output/                    # Generated JSONL files (volume-mounted in Docker)
│   └── *.jsonl                # Training data output files
└── logs/                      # Application logs (volume-mounted in Docker)
    ├── *_errors.log           # Failed generation attempts with details
    └── short_chunks.log       # Chunks below quality thresholds
```

### 📂 **Directory Purposes**

- **`data/`**: Input files and processing state
  - Place your markdown files with URLs here
  - `processed_links.txt` automatically tracks completed URLs
  - Prevents reprocessing on pipeline restarts

- **`output/`**: Generated training data
  - JSONL files named according to `PATHS_OUTPUT_FILENAME` in `.env`
  - Each line is a complete conversation with metadata
  - Ready for immediate use in LLM fine-tuning

- **`logs/`**: Debugging and quality monitoring
  - Error logs capture failed LLM generations with full context
  - Short chunks log helps tune quality thresholds
  - Useful for troubleshooting and pipeline optimization

## 🚀 **Quick Start**

### Prerequisites

- **Python 3.13+**
- **Google Generative AI API Key** ([Get one here](https://makersuite.google.com/app/apikey))
- **Hugging Face Token** ([Get one here](https://huggingface.co/settings/tokens))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nidea1/content-to-training-data.git
   cd content-to-training-data
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env  # Windows
   # cp .env.example .env  # macOS/Linux
   ```
   
   Edit `.env` and add your API keys:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   HF_TOKEN=your_huggingface_token_here
   ```

5. **Run the pipeline**
   ```bash
   # Single URL mode
   python data_extraction.py
   
   # Batch mode (processes links from markdown file)
   # Edit .env: APP_BATCH_MODE=true
   python data_extraction.py
   ```

## 🐳 **Docker Deployment**

### Quick Start with Docker Compose

1. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

2. **Create data directories** (if not already present)
   ```bash
   mkdir -p data output logs
   ```

3. **Place input markdown file**
   ```bash
   # Create a markdown file with your target URLs
   # Default location: data/LINKS.md (configurable via PATHS_MARKDOWN_FILENAME)
   
   # Example format:
   cat > data/LINKS.md << 'EOF'
   # My Content Links
   
   ## Category 1
   - [Article Title 1](https://example.com/article1)
   - [Article Title 2](https://example.com/article2)
   
   ## Category 2
   - [Guide Title](https://example.com/guide)
   EOF
   ```

4. **Run with Docker Compose**
   ```bash
   # Build and run in foreground (see logs)
   docker-compose up
   
   # Or run in detached mode (background)
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop and remove containers
   docker-compose down
   
   # Stop and remove volumes (cleans everything)
   docker-compose down -v
   ```

### 🗂️ **Docker Volume Mounting Explained**

The pipeline uses **volume mounting** to persist data between container runs:

```yaml
# docker-compose.yml mounts three directories:
volumes:
  - ./data:/app/data       # Input files & processing state
  - ./output:/app/output   # Generated JSONL training data
  - ./logs:/app/logs       # Error logs & debug info
```

**What this means:**

- **`./data → /app/data`**: 
  - Your local `data/` folder is accessible inside the container
  - Put markdown files with URLs here
  - `processed_links.txt` persists between runs (no reprocessing)
  - **Required for batch mode**: Place your links file here

- **`./output → /app/output`**:
  - Generated JSONL files appear in your local `output/` folder
  - Survives container restarts and rebuilds
  - Easy access to training data without entering container

- **`./logs → /app/logs`**:
  - Error logs and quality reports written to local `logs/` folder
  - Debug failed generations without `docker exec`
  - Monitor pipeline health in real-time

### 📋 **Docker Workflow Examples**

#### Example 1: Process Single URL

```bash
# 1. Configure for single URL mode
cat > .env << 'EOF'
GOOGLE_API_KEY=your_key_here
HF_TOKEN=your_token_here
APP_BATCH_MODE=false
APP_TARGET_URL=https://example.com/article
PATHS_OUTPUT_FILENAME=output/single_article.jsonl
EOF

# 2. Run container
docker-compose up

# 3. Check output
cat output/single_article.jsonl | jq .
```

#### Example 2: Batch Process Multiple URLs

```bash
# 1. Create input file with URLs
mkdir -p data
cat > data/my_guides.md << 'EOF'
# Gaming Guides
- [Guide 1](https://example.com/guide1)
- [Guide 2](https://example.com/guide2)
- [Guide 3](https://example.com/guide3)
EOF

# 2. Configure for batch mode
cat > .env << 'EOF'
GOOGLE_API_KEY=your_key_here
HF_TOKEN=your_token_here
APP_BATCH_MODE=true
PATHS_MARKDOWN_FILENAME=data/my_guides.md
PATHS_PROCESSED_LINKS_FILE=data/processed_links.txt
PATHS_OUTPUT_FILENAME=output/my_guides_dataset.jsonl
EOF

# 3. Run pipeline
docker-compose up

# 4. Check results
ls -lh output/my_guides_dataset.jsonl
wc -l output/my_guides_dataset.jsonl

# 5. View processing state
cat data/processed_links.txt
```

#### Example 3: Resume Failed Pipeline

```bash
# If pipeline failed or was interrupted:

# 1. Check what was already processed
cat data/processed_links.txt

# 2. Check error logs
cat logs/*_errors.log

# 3. Resume (automatically skips processed URLs)
docker-compose up

# Pipeline reads processed_links.txt and continues from where it stopped!
```

#### Example 4: Monitor Pipeline in Real-Time

```bash
# Terminal 1: Run pipeline
docker-compose up

# Terminal 2: Watch output file grow
watch -n 2 'wc -l output/*.jsonl'

# Terminal 3: Monitor errors
tail -f logs/*_errors.log

# Terminal 4: Check short chunks (quality issues)
tail -f logs/short_chunks.log
```

### 🔧 **Docker Configuration Tips**

#### Custom Meta Prompt

Mount a custom prompt file:

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data
  - ./output:/app/output
  - ./logs:/app/logs
  - ./my_custom_prompt.txt:/app/meta_prompt.txt:ro  # Read-only mount
```

## 📖 **Usage**

### Directory Setup

Before running the pipeline, ensure these directories exist:

```bash
# Create required directories
mkdir -p data output logs

# Verify structure
ls -la data/ output/ logs/
```

**Directory Roles:**
- **`data/`**: Input markdown files and processing state tracker
- **`output/`**: Generated JSONL training datasets
- **`logs/`**: Error logs and quality reports

### Single URL Mode

Extract data from a single webpage:

```bash
# Configure in .env
APP_BATCH_MODE=false
APP_TARGET_URL=https://example.com/your-guide-or-article
PATHS_OUTPUT_FILENAME=output/single_article.jsonl

# Run pipeline
python data_extraction.py

# Check output
cat output/single_article.jsonl
```

**Output location**: File specified by `PATHS_OUTPUT_FILENAME` (default: `output/bdo_guides.jsonl`)

### Batch Mode

Process multiple URLs from a markdown file:

```bash
# 1. Create input file with URLs
cat > data/my_links.md << 'EOF'
# My Content Links

## Technical Docs
- [Python Tutorial](https://example.com/python-tutorial)
- [API Guide](https://example.com/api-guide)

## Tutorials
- [Getting Started](https://example.com/getting-started)
EOF

# 2. Configure in .env
APP_BATCH_MODE=true
PATHS_MARKDOWN_FILENAME=data/my_links.md
PATHS_PROCESSED_LINKS_FILE=data/processed_links.txt
PATHS_OUTPUT_FILENAME=output/my_dataset.jsonl

# 3. Run pipeline
python data_extraction.py

# 4. Check results
wc -l output/my_dataset.jsonl
cat data/processed_links.txt
```

**Markdown file format** (standard markdown links):
```markdown
# Your Content Links

## Category 1
- [Article Title 1](https://example.com/article1)
- [Article Title 2](https://example.com/article2)

## Category 2
- [Guide Title](https://example.com/guide)
```

**Processing State:**
- `processed_links.txt` tracks completed URLs
- Re-running skips already processed links
- Delete file to reprocess everything

### Monitoring Progress

```bash
# Watch output file grow
tail -f output/my_dataset.jsonl

# Count generated conversations
wc -l output/my_dataset.jsonl

# Check for errors
cat logs/*_errors.log

# View quality issues (short chunks)
cat logs/short_chunks.log

# See processed URLs
cat data/processed_links.txt
```

### Output File Locations

All output paths are configurable via `.env`:

```bash
# Input
PATHS_MARKDOWN_FILENAME=data/LINKS.md           # Batch mode input
PATHS_PROCESSED_LINKS_FILE=data/processed_links.txt  # Progress tracker

# Output
PATHS_OUTPUT_FILENAME=output/training_data.jsonl     # Generated dataset

# Logs
PATHS_SHORT_CHUNKS_LOG=logs/short_chunks.log    # Quality warnings
# Error logs auto-generated: logs/<output_name>_errors.log
```

### Configuration

All settings can be configured via environment variables. See [`.env.example`](.env.example) for full options:

**Key Settings:**
- `GENERATION_MODEL_NAME`: LLM model (`gemma-3-27b-it`, `gemini-2.0-flash`, etc.)
- `GENERATION_TEMPERATURE`: Creativity (0-2, default 0.6)
- `CHUNKING_MAX_TOKENS`: Max tokens per chunk (default 3500)
- `QUALITY_MIN_PAIRS_PER_CHUNK`: Minimum QA pairs (default 10)

## 📊 **Output Format**

Generated JSONL files contain conversational dialogues ready for LLM fine-tuning:

```json
{
  "conversations": [
    {"role": "system", "content": "You are a helpful assistant with expertise in..."},
    {"role": "user", "content": "What are the key features of X?"},
    {"role": "assistant", "content": "X has several key features including..."}
  ],
  "url": "https://example.com/article",
  "date": "2024-01-15"
}
```

**Compatible with**: OpenAI fine-tuning format, Axolotl, Hugging Face Transformers, and most LLM training frameworks.

## 🏗️ **Architecture**

The pipeline follows a modular design:

```
URL → Scraper → Cleaner → Chunker → TableListSplitter → Generator → JSONL
```

Each component is independently configurable and replaceable. See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams and data flow.

### Component Overview

- **Scraper**: Fetches content using domain-specific APIs or generic fallbacks
- **Cleaner**: Removes navigation, boilerplate, and site-specific clutter
- **Chunker**: Splits text by headings while respecting token limits
- **TableListSplitter**: Segments long tables/lists with context preservation
- **Generator**: Creates Q&A dialogues using LLM prompts
- **Output**: Writes validated JSONL with metadata

## 🔧 **Adapting to Your Domain**

This pipeline is designed to be easily adapted to any content source. Here's how:

### 1. Quick Start (Generic Scraping)
No code changes needed! The pipeline includes fallback scrapers that work with most websites:
```bash
# Just set your target URL
APP_TARGET_URL=https://your-website.com/article
python data_extraction.py
```

### 2. Custom Domain (Recommended for Production)

**For better results**, add domain-specific logic:

#### Step 1: Add Scraper Strategy (optional)
Edit `scraper.py` to add your domain's API or custom scraping:
```python
# In scraper.py, add to scrape_content():
if "yourdomain.com" in url:
    return self._scrape_your_custom_api(url)
```

#### Step 2: Add Content Cleaner
Edit `cleaner.py` to remove your site's boilerplate:
```python
def clean_yourdomain(content: str) -> str:
    """Remove navigation, footers, etc. specific to yourdomain.com"""
    # Your cleaning logic here
    return cleaned_content

# Register in CLEANING_STRATEGIES dict
CLEANING_STRATEGIES = {
    "yourdomain.com": clean_yourdomain,
    # ... existing strategies
}
```

#### Step 3: Customize Chunking (optional)
If your content has unique heading patterns, add to `chunker.py`:
```python
def chunk_by_headings_yourdomain(self, text: str) -> List[str]:
    """Split by your domain's heading structure"""
    # Your chunking logic
    return chunks
```

#### Step 4: Adjust System Prompt
Edit `meta_prompt.txt` or set `META_PROMPT_TEMPLATE` in `config.py` to match your domain expertise.

### 3. Example: Gaming Wiki → Tutorial Site

```python
# From: Black Desert Online game guides (current)
# To: Programming tutorial site

# In cleaner.py:
def clean_programming_tutorials(content: str) -> str:
    # Remove code playground widgets
    content = re.sub(r'<CodeSandbox.*?/>', '', content)
    # Remove "Try it yourself" buttons
    content = re.sub(r'\[Try it\]\(.*?\)', '', content)
    return content

CLEANING_STRATEGIES["programming-tutorials.com"] = clean_programming_tutorials
```


## 🤝 **Contributing**

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code of conduct
- Development setup
- Code style guidelines
- Pull request process

**Priority areas:**
- Unit tests and test coverage
- New domain support (add your website/documentation source!)
- New scraping/cleaning strategies
- Performance improvements
- Documentation enhancements

### Adding a New Domain

1. **Scraper**: Add method in `scraper.py` for domain-specific API/scraping
2. **Cleaner**: Add cleaning function in `cleaner.py` to remove boilerplate
3. **Chunker**: Add heading pattern detection in `chunker.py` (if needed)
4. **Test**: Process a sample URL and verify output quality

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed component descriptions.

## 📝 **Documentation**

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design & data flow
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[.env.example](.env.example)** - Configuration reference

## 🐛 **Troubleshooting**
**Docker permission issues (Linux/macOS)**
```bash
# Fix directory permissions
chmod -R 777 data output logs

# Or set proper ownership
sudo chown -R $(id -u):$(id -g) data output logs

# Verify directories exist
ls -la data/ output/ logs/
```

**Output files not appearing**
- Check `PATHS_OUTPUT_FILENAME` points to `output/` directory
- Verify Docker volume mounts: `docker-compose config`
- Local run: Ensure `output/` directory exists: `mkdir -p output`
- Check for write permissions

**Low quality output (too few QA pairs)**
- Lower quality thresholds in `.env`:
  ```bash
  QUALITY_MIN_PAIRS_PER_CHUNK=5  # Default: 10
  QUALITY_MAX_PAIRS_PER_CHUNK=50 # Default: 30
  ```
- Adjust generation settings:
  ```bash
  GENERATION_TEMPERATURE=0.8  # More creative (default: 0.6)
  GENERATION_MAX_OUTPUT_TOKENS=16000  # More content (default: 10240)
  ```
- Check `logs/short_chunks.log` for rejected chunks

**Docker container not starting**
```bash
# Rebuild without cache
docker-compose down
docker-compose build --no-cache
docker-compose up

# Check for port conflicts
docker-compose ps

# Verify .env file format (no spaces around =)
cat .env
```

**Changes to .env not taking effect**
```bash
# Docker: Restart containers
docker-compose down
docker-compose up

# Local: Ensure .env is in current directory
ls -la .env

# Verify environment variables loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

### Debug Mode

Enable comprehensive logging:

```bash
# In .env
APP_DEBUG_MODE=true

# Run pipeline
python data_extraction.py

# Or with Docker
docker-compose up
```

**Debug output includes:**
- Detailed scraping responses
- Chunk token counts
- LLM prompts and responses
- JSON validation details
- Processing step timing

### Log Files Reference

| File | Contents | When to Check |
|------|----------|---------------|
| `logs/*_errors.log` | Failed LLM generations with full context | Empty/invalid output |
| `logs/short_chunks.log` | Chunks below quality thresholds | Low data yield |
| Console output | Pipeline progress and status | Real-time monitoring |

### Getting Help

If issues persist:

1. Enable debug mode: `APP_DEBUG_MODE=true`
2. Run pipeline and save full output: `python data_extraction.py > debug.log 2>&1`
3. Collect error logs: `cat logs/*_errors.log`
4. Check your configuration: `cat .env`
5. Open an issue with:
   - Debug output
   - Error logs
   - Configuration (remove API keys!)
   - Target URL (if not sensitive)

## 📄 **License**

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

## 🙏 **Acknowledgments**

- **Google Generative AI** for LLM capabilities
- **Jina AI Reader** for web-to-markdown conversion
- **urltomarkdown & tomarkdown APIs** for content extraction
- **HuggingFace** for tokenizer support

## 🔗 **Links**

- **Repository**: [https://github.com/nidea1/content-to-training-data](https://github.com/nidea1/content-to-training-data)
- **Issues**: [https://github.com/nidea1/content-to-training-data/issues](https://github.com/nidea1/content-to-training-data/issues)
- **Discussions**: [https://github.com/nidea1/content-to-training-data/discussions](https://github.com/nidea1/content-to-training-data/discussions)

---

**Made with ❤️ for the open source and LLM community**
