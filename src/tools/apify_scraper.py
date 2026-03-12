from apify import Actor
from apify_client import ApifyClient
import asyncio
import os

async def main():
    async with Actor:
        input_data = await Actor.get_input() or {}
        company = input_data.get("company", "H&M")
        
        Actor.log.info(f"Searching ESG data for: {company}")
        
        search_run = await Actor.call(
            "apify/google-search-scraper",
            run_input={
                "queries": f"{company} ESG sustainability greenwashing 2024 2025",
                "maxPagesPerQuery": 1,
                "resultsPerPage": 10,
            }
        )
        
        token = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
        client = ApifyClient(token)
        dataset_items = client.dataset(search_run.default_dataset_id).list_items().items
        
        results = []
        for item in dataset_items:
            for r in item.get("organicResults", []):
                results.append({
                    "company": company,
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("description", "")[:500],
                    "source_type": "news"
                })
        
        Actor.log.info(f"Found {len(results)} results")
        await Actor.push_data(results)

if __name__ == "__main__":
    asyncio.run(main())
