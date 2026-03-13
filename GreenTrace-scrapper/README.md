# GreenTrace-scrapper

GreenTrace-scrapper searches Google for one company, collects link-bearing results, optionally forwards the crawlable URLs into `6sigmag/fast-website-content-crawler`, or fetches page content with `jina.ai`, and stores one combined summary item in the default dataset.

## Inputs

- `company` — company name to search
- `query_suffix` — ESG-related terms appended to the company name
- `results_per_page` — Google results requested per page
- `max_pages_per_query` — maximum Google pages to fetch
- `keyword_terms` — optional keywords used to annotate crawler results
- `enable_fast_crawler` — disabled by default, enable if you want to use `6sigmag/fast-website-content-crawler`
- `enable_jina_ai` — enabled by default, uses `jina.ai` to fetch page content
- `jina_api_key` — optional user-provided Jina API key
- `jina_engine` — Jina engine, `direct` by default, or `browser`
- `jina_timeout_secs` — timeout passed to Jina requests

## Pipeline

1. Run `apify/google-search-scraper` with the company query.
2. Recursively collect link-bearing URLs from the Google output.
3. Normalize and deduplicate those URLs for downstream crawling.
4. If enabled, run `6sigmag/fast-website-content-crawler` with the normalized `startUrls`.
5. If enabled, call `jina.ai` for each forwarded URL, with or without a user-provided API key.
6. Store one summary dataset item containing:

- Google run metadata and raw results
- extracted link candidates
- forwarded crawler URLs
- optional fast crawler output
- optional Jina content output
- keyword-match annotations
- overall status and partial-failure details

## Notes

- Local runs need a valid `APIFY_TOKEN` so this Actor can call Apify Actors.
- The dataset item can become large because it contains output from both stages.
- Local `storage/` data stays local and is not automatically uploaded to Apify Console.
- Fast crawler usage is disabled by default.
- Jina usage is attempted without authentication if no `jina_api_key` is provided.

## Integrating with Python apps or servers

This Actor is easiest to integrate through the official Python client.

### 1. Install the client

```bash
pip install apify-client
```

### 2. Run the Actor from Python

Replace `YOUR_USERNAME/YOUR_ACTOR_NAME` with the deployed Actor name.

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")

actor_input = {
   "company": "H&M",
   "query_suffix": "ESG sustainability greenwashing 2024 2025",
   "results_per_page": 10,
   "max_pages_per_query": 1,
  "enable_fast_crawler": False,
  "enable_jina_ai": True,
  "jina_engine": "direct",
  "jina_timeout_secs": 200,
   "keyword_terms": [
      "esg",
      "sustainability",
      "greenwashing",
      "climate",
      "emissions",
      "governance",
   ],
}

run = client.actor("sama4/greentrace-scrapper").call(run_input=actor_input)

items = client.dataset(run["defaultDatasetId"]).list_items().items

for item in items:
   print(item["company"])
   print(item["overall_status"])
   print(item["forwarded_urls"])
   print(item["crawler_results"])
  print(item["jina_results"])
```

### 3. What the result contains

This is the most important part of the integration.

Each run currently writes **one summary dataset item per company**. That means when you call GreenTrace-scrapper for `H&M`, the dataset usually contains a single top-level object describing the full pipeline for that company.

The returned item is designed to be used as a **combined response object** for apps, APIs, dashboards, or downstream analysis jobs.

#### Top-level fields

- `company`
  - The company name you passed in the input.
  - Example: `"H&M"`

- `query`
  - The final Google query that was actually sent.
  - Usually built from `company + query_suffix`.
  - Example: `"H&M ESG sustainability greenwashing 2024 2025"`

- `query_suffix`
  - The ESG-related suffix used when building the query.
  - Useful for debugging and reproducibility.

- `keyword_terms`
  - The keywords used to annotate and score the crawler output.
  - These terms are matched against crawler content to help identify ESG-relevant pages.

- `results_per_page`
  - The requested Google result page size used during the search stage.

- `max_pages_per_query`
  - The maximum number of Google result pages requested.

- `enable_fast_crawler`
  - Whether `6sigmag/fast-website-content-crawler` was enabled for this run.
  - Default is `false`.

- `enable_jina_ai`
  - Whether `jina.ai` enrichment was enabled for this run.
  - Default is `true`.

- `jina_engine`
  - Which Jina engine was selected for the run.
  - Supported values are currently `direct` and `browser`.

- `overall_status`
  - High-level result for the entire pipeline.
  - Expected values:
    - `succeeded` — Google search worked and crawler either worked or was intentionally skipped
    - `partial` — one stage worked and another failed
    - `failed` — the pipeline did not produce a usable result

#### Google stage fields

- `google_stage`
  - Summary metadata about the Google scraper run.
  - Contains:
    - `status` — `pending`, `succeeded`, or `failed`
    - `actor_id` — usually `apify/google-search-scraper`
    - `run_id` — the Apify run ID of the Google stage
    - `run_status` — the actual Apify platform status such as `SUCCEEDED`
    - `status_message` — any run message returned by the stage
    - `result_count` — number of dataset items returned by the Google actor
    - `link_candidate_count` — number of link candidates extracted from the Google output
    - `error` — error text if the Google stage failed

- `google_results`
  - Raw dataset items returned by `apify/google-search-scraper`.
  - This is the full upstream evidence collected before filtering.
  - Use this if you want:
    - the original search output
    - search debugging
    - auditing what links were discovered
    - building your own filtering logic later

- `google_link_candidates`
  - Flattened link candidates extracted from the raw Google output.
  - Each entry is typically shaped like:
    - `path` — where in the Google result object the link was found
    - `url` — the extracted URL string
  - This is useful when you want to inspect exactly which URLs were discovered before normalization.

- `forwarded_urls`
  - Final deduplicated URLs that were actually passed into `6sigmag/fast-website-content-crawler`.
  - This is the most important bridge field between the two actors.
  - If you want to know **what the crawler was asked to fetch**, use this field.

#### Crawler stage fields

- `crawler_stage`
  - Summary metadata about the fast crawler run.
  - Contains:
    - `status` — `pending`, `succeeded`, `failed`, or `skipped`
    - `actor_id` — usually `6sigmag/fast-website-content-crawler`
    - `run_id` — the Apify run ID of the crawler stage
    - `run_status` — actual Apify platform status such as `SUCCEEDED`
    - `status_message` — any crawler-stage run message
    - `result_count` — number of crawler dataset items collected
    - `matching_result_count` — how many crawler results matched at least one ESG keyword
    - `error` — error text if the crawler stage failed

- `crawler_results`
  - Raw content results returned by the fast crawler, with extra annotations added by GreenTrace-scrapper.
  - This is the field you should use if you want the actual crawled website content.
  - Each item comes from the downstream crawler and is then enriched with:
    - `analysis_matched_keywords`
    - `analysis_keyword_match_count`
    - `analysis_keyword_relevance`
  - In practice, this is where your application will usually read page-level content, extracted text, or other crawler metadata.

- `matching_crawler_results`
  - Filtered subset of `crawler_results`.
  - Only includes crawler items where at least one ESG keyword matched.
  - This is often the best field for:
    - ESG review pipelines
    - RAG ingestion
    - scoring workflows
    - analyst-facing dashboards

#### Jina stage fields

- `jina_stage`
  - Summary metadata about the `jina.ai` enrichment stage.
  - Contains:
    - `status` — `pending`, `succeeded`, `partial`, `failed`, `skipped`, or `disabled`
    - `provider` — `jina.ai`
    - `engine` — selected engine, for example `direct` or `browser`
    - `attempted_count` — number of URLs sent to Jina
    - `success_count` — number of successful Jina fetches
    - `failure_count` — number of failed Jina fetches
    - `used_api_key` — whether a user-provided API key was used
    - `error` — stage-level error if all requests failed

- `jina_results`
  - Page content returned by `jina.ai` for the forwarded URLs.
  - This is the main field to use if you want extracted article or page text from Jina.
  - Each item usually contains:
    - `url`
    - `engine`
    - `status_code`
    - `content`
    - `used_api_key`
    - `error` when that specific fetch failed

#### Recommended usage patterns

Depending on your app, you will usually read the result like this:

- For the overall run outcome:
  - use `overall_status`

- For debugging the Google phase:
  - use `google_stage`, `google_results`, and `google_link_candidates`

- For seeing exactly what was sent to the crawler:
  - use `forwarded_urls`

- For all crawled content:
  - use `crawler_results`

- For only ESG-relevant content:
  - use `matching_crawler_results`

- For Jina-fetched page text:
  - use `jina_results`

#### Important storage note

GreenTrace-scrapper currently stores the crawler output **nested inside the final summary object**.

So the current model is:

- **one dataset row per company**, not one dataset row per crawled page

That is why your integration code usually does:

- fetch the first dataset item
- then read `crawler_results` or `matching_crawler_results` from inside it

If you need a flatter format later, the Actor can be extended to push:

- one summary item per company
- plus one additional dataset item per crawled page

### 4. Helper function for reuse inside apps

```python
from apify_client import ApifyClient


def fetch_company_esg(company: str, token: str, actor_id: str) -> dict:
   client = ApifyClient(token)

   run = client.actor(actor_id).call(
      run_input={
         "company": company,
         "query_suffix": "ESG sustainability greenwashing 2024 2025",
         "results_per_page": 10,
         "max_pages_per_query": 1,
      "enable_fast_crawler": False,
      "enable_jina_ai": True,
      "jina_engine": "direct",
      }
   )

   items = client.dataset(run["defaultDatasetId"]).list_items().items
   return items[0] if items else {}
```

### 5. Example FastAPI integration

```python
import os

from apify_client import ApifyClient
from fastapi import FastAPI

app = FastAPI()
client = ApifyClient(os.environ["APIFY_TOKEN"])
ACTOR_ID = "YOUR_USERNAME/YOUR_ACTOR_NAME"


@app.get("/company-esg/{company}")
def get_company_esg(company: str):
   run = client.actor(ACTOR_ID).call(
      run_input={
         "company": company,
         "query_suffix": "ESG sustainability greenwashing 2024 2025",
         "results_per_page": 10,
         "max_pages_per_query": 1,
      "enable_fast_crawler": False,
      "enable_jina_ai": True,
      "jina_engine": "direct",
      }
   )

   items = client.dataset(run["defaultDatasetId"]).list_items().items
   return items[0] if items else {"company": company, "overall_status": "empty"}
```

### 6. Recommended production usage

- Store `APIFY_TOKEN` in environment variables, not in source code.
- Store `jina_api_key` in environment variables too, if you use one.
- Deploy this Actor first, then call the deployed Actor from your app or API server.
- Add request timeouts and error handling around `client.actor(...).call(...)`.
- Cache completed results if you expect repeated lookups for the same company.
- If you need page-by-page persistence instead of one nested summary object, extend the Actor before integrating.
- If you do not want the downstream crawler, leave `enable_fast_crawler` set to `false`.

## Development

- Main implementation: `my_actor/main.py`
- Actor config: `.actor/actor.json`
- Input schema: `.actor/input_schema.json`
- Dataset view: `.actor/dataset_schema.json`
