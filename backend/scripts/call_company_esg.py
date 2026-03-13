from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call the local GreenTrace API and save the result to a file."
    )
    parser.add_argument("company", help="Company name to search, for example Zara")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the local FastAPI server",
    )
    parser.add_argument(
        "--jira-api-key",
        dest="jina_api_key",
        default=None,
        help="Optional Jina API key alias",
    )
    parser.add_argument(
        "--jina-api-key",
        dest="jina_api_key",
        default=None,
        help="Optional Jina API key sent to the API",
    )
    parser.add_argument(
        "--query-suffix",
        default=None,
        help="Optional ESG query suffix override",
    )
    parser.add_argument(
        "--results-per-page",
        type=int,
        default=None,
        help="Optional Google results per page",
    )
    parser.add_argument(
        "--max-pages-per-query",
        type=int,
        default=None,
        help="Optional maximum Google pages",
    )
    parser.add_argument(
        "--enable-fast-crawler",
        action="store_true",
        help="Enable the downstream fast crawler",
    )
    parser.add_argument(
        "--disable-jina-ai",
        action="store_true",
        help="Disable Jina enrichment",
    )
    parser.add_argument(
        "--jina-engine",
        choices=["direct", "browser"],
        default=None,
        help="Optional Jina engine override",
    )
    parser.add_argument(
        "--jina-timeout-secs",
        type=int,
        default=None,
        help="Optional Jina timeout in seconds",
    )
    parser.add_argument(
        "--keyword-term",
        dest="keyword_terms",
        action="append",
        default=None,
        help="Optional keyword term; repeat the flag for multiple values",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file path. Defaults to outputs/<company>-<timestamp>.json",
    )
    return parser.parse_args()


def build_url(args: argparse.Namespace) -> str:
    params: list[tuple[str, str]] = []
    if args.jina_api_key:
        params.append(("jina_api_key", args.jina_api_key))
    if args.query_suffix:
        params.append(("query_suffix", args.query_suffix))
    if args.results_per_page is not None:
        params.append(("results_per_page", str(args.results_per_page)))
    if args.max_pages_per_query is not None:
        params.append(("max_pages_per_query", str(args.max_pages_per_query)))
    if args.enable_fast_crawler:
        params.append(("enable_fast_crawler", "true"))
    if args.disable_jina_ai:
        params.append(("enable_jina_ai", "false"))
    if args.jina_engine:
        params.append(("jina_engine", args.jina_engine))
    if args.jina_timeout_secs is not None:
        params.append(("jina_timeout_secs", str(args.jina_timeout_secs)))
    for keyword in args.keyword_terms or []:
        params.append(("keyword_terms", keyword))

    query = urlencode(params, doseq=True)
    company = quote(args.company, safe="")
    base = args.base_url.rstrip("/")
    return f"{base}/company-esg/{company}" + (f"?{query}" if query else "")


def build_output_path(args: argparse.Namespace) -> Path:
    if args.output:
        return Path(args.output)
    slug = "-".join(args.company.lower().split()) or "company"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("outputs") / f"{slug}-{stamp}.json"


def main() -> int:
    args = parse_args()
    url = build_url(args)
    output_path = build_output_path(args)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urlopen(url) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Request failed with HTTP {exc.code}: {detail}")
        return 1
    except URLError as exc:
        print(f"Could not reach server: {exc.reason}")
        return 1

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("Server returned a non-JSON response")
        return 1

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(data.get('articles', []))} articles to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
