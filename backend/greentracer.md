# GreenTrace-scrapper (`sama4/greentrace-scrapper`) Actor

- **URL**: https://apify.com/sama4/greentrace-scrapper.md
- **Developed by:** [And Sama](https://apify.com/sama4) (community)
- **Categories:** Automation
- **Stats:** 2 total users, 1 monthly users, 100.0% runs succeeded, NaN bookmarks
- **User rating**: No ratings yet

## Pricing

Pay per usage

This Actor is paid per platform usage. The Actor is free to use, and you only pay for the Apify platform usage, which gets cheaper the higher subscription plan you have.

Learn more: https://docs.apify.com/platform/actors/running/actors-in-store#pay-per-usage

## What's an Apify Actor?

Actors are a software tools running on the Apify platform, for all kinds of web data extraction and automation use cases.
In Batch mode, an Actor accepts a well-defined JSON input, performs an action which can take anything from a few seconds to a few hours,
and optionally produces a well-defined JSON output, datasets with results, or files in key-value store.
In Standby mode, an Actor provides a web server which can be used as a website, API, or an MCP server.
Actors are written with capital "A".

## How to integrate an Actor?

If asked about integration, you help developers integrate Actors into their projects.
You adapt to their stack and deliver integrations that are safe, well-documented, and production-ready.
The best way to integrate Actors is as follows.

In JavaScript/TypeScript projects, use official [JavaScript/TypeScript client](https://docs.apify.com/api/client/js.md):

```bash
npm install apify-client
```

In Python projects, use official [Python client library](https://docs.apify.com/api/client/python.md):

```bash
pip install apify-client
```

In shell scripts, use [Apify CLI](https://docs.apify.com/cli/docs.md):

````bash
# MacOS / Linux
curl -fsSL https://apify.com/install-cli.sh | bash
# Windows
irm https://apify.com/install-cli.ps1 | iex
```bash

In AI frameworks, you might use the [Apify MCP server](https://docs.apify.com/platform/integrations/mcp.md).

If your project is in a different language, use the [REST API](https://docs.apify.com/api/v2.md).

For usage examples, see the [API](#api) section below.

For more details, see Apify documentation as [Markdown index](https://docs.apify.com/llms.txt) and [Markdown full-text](https://docs.apify.com/llms-full.txt).


# README

## GreenTrace-scrapper

GreenTrace-scrapper searches Google for one company, collects link-bearing results, optionally forwards the crawlable URLs into `6sigmag/fast-website-content-crawler`, or fetches page content with `jina.ai`, and stores one combined summary item in the default dataset.

### Inputs

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

### Pipeline

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

### Notes

- Local runs need a valid `APIFY_TOKEN` so this Actor can call Apify Actors.
- The dataset item can become large because it contains output from both stages.
- Local `storage/` data stays local and is not automatically uploaded to Apify Console.
- Fast crawler usage is disabled by default.
- Jina usage is attempted without authentication if no `jina_api_key` is provided.

### Integrating with Python apps or servers

This Actor is easiest to integrate through the official Python client.

#### 1. Install the client

```bash
pip install apify-client
````

#### 2. Run the Actor from Python

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

#### 3. What the result contains

This is the most important part of the integration.

Each run currently writes **one summary dataset item per company**. That means when you call GreenTrace-scrapper for `H&M`, the dataset usually contains a single top-level object describing the full pipeline for that company.

The returned item is designed to be used as a **combined response object** for apps, APIs, dashboards, or downstream analysis jobs.

##### Top-level fields

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

##### Google stage fields

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

##### Crawler stage fields

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

##### Jina stage fields

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

##### Recommended usage patterns

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

##### Important storage note

GreenTrace-scrapper currently stores the crawler output **nested inside the final summary object**.

So the current model is:

- **one dataset row per company**, not one dataset row per crawled page

That is why your integration code usually does:

- fetch the first dataset item
- then read `crawler_results` or `matching_crawler_results` from inside it

If you need a flatter format later, the Actor can be extended to push:

- one summary item per company
- plus one additional dataset item per crawled page

#### 4. Helper function for reuse inside apps

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

#### 5. Example FastAPI integration

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

#### 6. Recommended production usage

- Store `APIFY_TOKEN` in environment variables, not in source code.
- Store `jina_api_key` in environment variables too, if you use one.
- Deploy this Actor first, then call the deployed Actor from your app or API server.
- Add request timeouts and error handling around `client.actor(...).call(...)`.
- Cache completed results if you expect repeated lookups for the same company.
- If you need page-by-page persistence instead of one nested summary object, extend the Actor before integrating.
- If you do not want the downstream crawler, leave `enable_fast_crawler` set to `false`.

### Development

- Main implementation: `my_actor/main.py`
- Actor config: `.actor/actor.json`
- Input schema: `.actor/input_schema.json`
- Dataset view: `.actor/dataset_schema.json`

# Actor input Schema

## `company` (type: `string`):

Single company name to search for.

## `query_suffix` (type: `string`):

Keywords appended after the company name in the Google query.

## `results_per_page` (type: `integer`):

How many Google results to request per search page.

## `max_pages_per_query` (type: `integer`):

Maximum number of Google result pages to fetch for the company query.

## `keyword_terms` (type: `array`):

Optional ESG-related keywords used to annotate the crawler output.

## `enable_fast_crawler` (type: `boolean`):

Run 6sigmag/fast-website-content-crawler after Google search. Disabled by default.

## `enable_jina_ai` (type: `boolean`):

Fetch page content from jina.ai for each forwarded URL.

## `jina_api_key` (type: `string`):

Optional jina.ai API key. If omitted, requests are attempted without authentication.

## `jina_engine` (type: `string`):

Choose which jina.ai engine to use.

## `jina_timeout_secs` (type: `integer`):

Timeout header passed to jina.ai in seconds.

## Actor input object example

```json
{
  "company": "H&M",
  "query_suffix": "ESG sustainability greenwashing 2024 2025",
  "results_per_page": 10,
  "max_pages_per_query": 1,
  "keyword_terms": [
    "esg",
    "sustainability",
    "greenwashing",
    "climate",
    "emissions",
    "governance"
  ],
  "enable_fast_crawler": false,
  "enable_jina_ai": true,
  "jina_engine": "direct",
  "jina_timeout_secs": 200
}
```

# Actor output Schema

## `results` (type: `string`):

No description

# API

You can run this Actor programmatically using our API. Below are code examples in JavaScript, Python, and CLI, as well as the OpenAPI specification and MCP server setup.

## JavaScript example

```javascript
import { ApifyClient } from 'apify-client';

// Initialize the ApifyClient with your Apify API token
// Replace the '<YOUR_API_TOKEN>' with your token
const client = new ApifyClient({
    token: '<YOUR_API_TOKEN>',
});

// Prepare Actor input
const input = {};

// Run the Actor and wait for it to finish
const run = await client.actor("sama4/greentrace-scrapper").call(input);

// Fetch and print Actor results from the run's dataset (if any)
console.log('Results from dataset');
console.log(`💾 Check your data here: https://console.apify.com/storage/datasets/${run.defaultDatasetId}`);
const { items } = await client.dataset(run.defaultDatasetId).listItems();
items.forEach((item) => {
    console.dir(item);
});

// 📚 Want to learn more 📖? Go to → https://docs.apify.com/api/client/js/docs

```

## Python example

```python
from apify_client import ApifyClient

# Initialize the ApifyClient with your Apify API token
# Replace '<YOUR_API_TOKEN>' with your token.
client = ApifyClient("<YOUR_API_TOKEN>")

# Prepare the Actor input
run_input = {}

# Run the Actor and wait for it to finish
run = client.actor("sama4/greentrace-scrapper").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
print("💾 Check your data here: https://console.apify.com/storage/datasets/" + run["defaultDatasetId"])
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)

# 📚 Want to learn more 📖? Go to → https://docs.apify.com/api/client/python/docs/quick-start

```

## CLI example

```bash
echo '{}' |
apify call sama4/greentrace-scrapper --silent --output-dataset

```

## MCP server setup

```json
{
    "mcpServers": {
        "apify": {
            "command": "npx",
            "args": [
                "mcp-remote",
                "https://mcp.apify.com/?tools=sama4/greentrace-scrapper",
                "--header",
                "Authorization: Bearer <YOUR_API_TOKEN>"
            ]
        }
    }
}

```

## OpenAPI specification

```json
{
    "openapi": "3.0.1",
    "info": {
        "title": "GreenTrace-scrapper",
        "description": null,
        "version": "0.0",
        "x-build-id": "3G6w6P0M7jgl1dI3b"
    },
    "servers": [
        {
            "url": "https://api.apify.com/v2"
        }
    ],
    "paths": {
        "/acts/sama4~greentrace-scrapper/run-sync-get-dataset-items": {
            "post": {
                "operationId": "run-sync-get-dataset-items-sama4-greentrace-scrapper",
                "x-openai-isConsequential": false,
                "summary": "Executes an Actor, waits for its completion, and returns Actor's dataset items in response.",
                "tags": [
                    "Run Actor"
                ],
                "requestBody": {
                    "required": true,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/inputSchema"
                            }
                        }
                    }
                },
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string"
                        },
                        "description": "Enter your Apify token here"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                }
            }
        },
        "/acts/sama4~greentrace-scrapper/runs": {
            "post": {
                "operationId": "runs-sync-sama4-greentrace-scrapper",
                "x-openai-isConsequential": false,
                "summary": "Executes an Actor and returns information about the initiated run in response.",
                "tags": [
                    "Run Actor"
                ],
                "requestBody": {
                    "required": true,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/inputSchema"
                            }
                        }
                    }
                },
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string"
                        },
                        "description": "Enter your Apify token here"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/runsResponseSchema"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/acts/sama4~greentrace-scrapper/run-sync": {
            "post": {
                "operationId": "run-sync-sama4-greentrace-scrapper",
                "x-openai-isConsequential": false,
                "summary": "Executes an Actor, waits for completion, and returns the OUTPUT from Key-value store in response.",
                "tags": [
                    "Run Actor"
                ],
                "requestBody": {
                    "required": true,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/inputSchema"
                            }
                        }
                    }
                },
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string"
                        },
                        "description": "Enter your Apify token here"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "inputSchema": {
                "type": "object",
                "required": [
                    "company"
                ],
                "properties": {
                    "company": {
                        "title": "Company",
                        "type": "string",
                        "description": "Single company name to search for.",
                        "default": "H&M"
                    },
                    "query_suffix": {
                        "title": "Query suffix",
                        "type": "string",
                        "description": "Keywords appended after the company name in the Google query.",
                        "default": "ESG sustainability greenwashing 2024 2025"
                    },
                    "results_per_page": {
                        "title": "Results per page",
                        "minimum": 1,
                        "type": "integer",
                        "description": "How many Google results to request per search page.",
                        "default": 10
                    },
                    "max_pages_per_query": {
                        "title": "Max pages per query",
                        "minimum": 1,
                        "type": "integer",
                        "description": "Maximum number of Google result pages to fetch for the company query.",
                        "default": 1
                    },
                    "keyword_terms": {
                        "title": "Keyword terms",
                        "type": "array",
                        "description": "Optional ESG-related keywords used to annotate the crawler output.",
                        "items": {
                            "type": "string"
                        },
                        "default": [
                            "esg",
                            "sustainability",
                            "greenwashing",
                            "climate",
                            "emissions",
                            "governance"
                        ]
                    },
                    "enable_fast_crawler": {
                        "title": "Enable fast crawler",
                        "type": "boolean",
                        "description": "Run 6sigmag/fast-website-content-crawler after Google search. Disabled by default.",
                        "default": false
                    },
                    "enable_jina_ai": {
                        "title": "Enable Jina AI",
                        "type": "boolean",
                        "description": "Fetch page content from jina.ai for each forwarded URL.",
                        "default": true
                    },
                    "jina_api_key": {
                        "title": "Jina API key",
                        "type": "string",
                        "description": "Optional jina.ai API key. If omitted, requests are attempted without authentication."
                    },
                    "jina_engine": {
                        "title": "Jina engine",
                        "enum": [
                            "direct",
                            "browser"
                        ],
                        "type": "string",
                        "description": "Choose which jina.ai engine to use.",
                        "default": "direct"
                    },
                    "jina_timeout_secs": {
                        "title": "Jina timeout",
                        "minimum": 1,
                        "type": "integer",
                        "description": "Timeout header passed to jina.ai in seconds.",
                        "default": 200
                    }
                }
            },
            "runsResponseSchema": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string"
                            },
                            "actId": {
                                "type": "string"
                            },
                            "userId": {
                                "type": "string"
                            },
                            "startedAt": {
                                "type": "string",
                                "format": "date-time",
                                "example": "2025-01-08T00:00:00.000Z"
                            },
                            "finishedAt": {
                                "type": "string",
                                "format": "date-time",
                                "example": "2025-01-08T00:00:00.000Z"
                            },
                            "status": {
                                "type": "string",
                                "example": "READY"
                            },
                            "meta": {
                                "type": "object",
                                "properties": {
                                    "origin": {
                                        "type": "string",
                                        "example": "API"
                                    },
                                    "userAgent": {
                                        "type": "string"
                                    }
                                }
                            },
                            "stats": {
                                "type": "object",
                                "properties": {
                                    "inputBodyLen": {
                                        "type": "integer",
                                        "example": 2000
                                    },
                                    "rebootCount": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "restartCount": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "resurrectCount": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "computeUnits": {
                                        "type": "integer",
                                        "example": 0
                                    }
                                }
                            },
                            "options": {
                                "type": "object",
                                "properties": {
                                    "build": {
                                        "type": "string",
                                        "example": "latest"
                                    },
                                    "timeoutSecs": {
                                        "type": "integer",
                                        "example": 300
                                    },
                                    "memoryMbytes": {
                                        "type": "integer",
                                        "example": 1024
                                    },
                                    "diskMbytes": {
                                        "type": "integer",
                                        "example": 2048
                                    }
                                }
                            },
                            "buildId": {
                                "type": "string"
                            },
                            "defaultKeyValueStoreId": {
                                "type": "string"
                            },
                            "defaultDatasetId": {
                                "type": "string"
                            },
                            "defaultRequestQueueId": {
                                "type": "string"
                            },
                            "buildNumber": {
                                "type": "string",
                                "example": "1.0.0"
                            },
                            "containerUrl": {
                                "type": "string"
                            },
                            "usage": {
                                "type": "object",
                                "properties": {
                                    "ACTOR_COMPUTE_UNITS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATASET_READS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATASET_WRITES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "KEY_VALUE_STORE_READS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "KEY_VALUE_STORE_WRITES": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "KEY_VALUE_STORE_LISTS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "REQUEST_QUEUE_READS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "REQUEST_QUEUE_WRITES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATA_TRANSFER_INTERNAL_GBYTES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATA_TRANSFER_EXTERNAL_GBYTES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "PROXY_RESIDENTIAL_TRANSFER_GBYTES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "PROXY_SERPS": {
                                        "type": "integer",
                                        "example": 0
                                    }
                                }
                            },
                            "usageTotalUsd": {
                                "type": "number",
                                "example": 0.00005
                            },
                            "usageUsd": {
                                "type": "object",
                                "properties": {
                                    "ACTOR_COMPUTE_UNITS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATASET_READS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATASET_WRITES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "KEY_VALUE_STORE_READS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "KEY_VALUE_STORE_WRITES": {
                                        "type": "number",
                                        "example": 0.00005
                                    },
                                    "KEY_VALUE_STORE_LISTS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "REQUEST_QUEUE_READS": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "REQUEST_QUEUE_WRITES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATA_TRANSFER_INTERNAL_GBYTES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "DATA_TRANSFER_EXTERNAL_GBYTES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "PROXY_RESIDENTIAL_TRANSFER_GBYTES": {
                                        "type": "integer",
                                        "example": 0
                                    },
                                    "PROXY_SERPS": {
                                        "type": "integer",
                                        "example": 0
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```
