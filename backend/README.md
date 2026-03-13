# GreenTrace Backend

FastAPI service for running the GreenTrace Apify actor to analyze company ESG data.

## Setup

**Requirements**: Python 3.12+, uv

1. Create and activate virtual environment:
```bash
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
```

2. Install dependencies:
```bash
uv pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Apify API token:
```
APIFY_TOKEN=your_apify_token_here
```

## Running the Server

Start the FastAPI server:
```bash
uvicorn app.main:app --reload --port 8000
```

The server will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Using the Script

The `call_company_esg.py` script queries the API for company ESG data:

```bash
python scripts/call_company_esg.py "Company Name"
```

### Examples

Basic usage:
```bash
python scripts/call_company_esg.py "H&M"
```

With optional parameters:
```bash
python scripts/call_company_esg.py "Zara" \
  --base-url http://localhost:8000 \
  --jina-api-key your_jina_key \
  --results-per-page 10 \
  --max-pages-per-query 3
```

Results are saved to `outputs/{company}-{timestamp}.json`

### Script Options

- `--base-url`: API server URL (default: http://localhost:8000)
- `--jina-api-key`: Optional Jina API key for enhanced scraping
- `--query-suffix`: Custom ESG query suffix
- `--results-per-page`: Google results per page
- `--max-pages-per-query`: Maximum Google pages to scrape
