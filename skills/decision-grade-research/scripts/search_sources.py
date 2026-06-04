#!/usr/bin/env python3
"""Search for source candidates using an optional Tavily or Brave adapter.

The script normalizes search results into a provider-independent JSON contract. It is
designed for Decision-Grade Research, where raw search results are only candidates:
claims still need to be read, judged, tagged, and entered into the evidence ledger.

Provider modes:
  none   Load an existing JSON file and normalize it without network calls.
  tavily Use Tavily Search. Reads TAVILY_API_KEY from the environment.
  brave  Use Brave Search. Reads BRAVE_API_KEY from the environment.

Examples:
    python3 search_sources.py --provider none --input source_candidates.json
    python3 search_sources.py --provider tavily --query "market size"
    python3 search_sources.py --provider brave --query "official data"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

TAVILY_ENDPOINT = "https://api.tavily.com/search"
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


def normalize_result(title="", url="", snippet="", published_date=None, score=None):
    return {
        "title": title or "",
        "url": url or "",
        "snippet": snippet or "",
        "published_date": published_date or "",
        "score": score,
    }


def normalize_existing(payload, provider):
    if isinstance(payload, list):
        results = payload
        query = ""
    else:
        results = payload.get("results", [])
        query = payload.get("query", "")
        provider = payload.get("provider", provider)
    return {
        "query": query,
        "provider": provider,
        "retrieved_at": date.today().isoformat(),
        "results": [
            normalize_result(
                title=r.get("title"),
                url=r.get("url") or r.get("href"),
                snippet=r.get("snippet") or r.get("content") or r.get("description"),
                published_date=r.get("published_date") or r.get("date"),
                score=r.get("score"),
            )
            for r in results
        ],
    }


def request_json(url, *, method="GET", headers=None, body=None, timeout=30):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def tavily_search(query, max_results):
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is required for provider=tavily")
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
    }
    data = request_json(
        TAVILY_ENDPOINT,
        method="POST",
        headers={"Content-Type": "application/json"},
        body=payload,
    )
    return {
        "query": query,
        "provider": "tavily",
        "retrieved_at": date.today().isoformat(),
        "results": [
            normalize_result(
                title=r.get("title"),
                url=r.get("url"),
                snippet=r.get("content"),
                score=r.get("score"),
            )
            for r in data.get("results", [])
        ],
    }


def brave_search(query, max_results):
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        raise RuntimeError("BRAVE_API_KEY is required for provider=brave")
    qs = urllib.parse.urlencode({"q": query, "count": max_results})
    data = request_json(
        f"{BRAVE_ENDPOINT}?{qs}",
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        },
    )
    web = data.get("web", {}).get("results", [])
    return {
        "query": query,
        "provider": "brave",
        "retrieved_at": date.today().isoformat(),
        "results": [
            normalize_result(
                title=r.get("title"),
                url=r.get("url"),
                snippet=r.get("description"),
                published_date=r.get("age"),
            )
            for r in web
        ],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--provider", choices=["none", "tavily", "brave"], default=os.environ.get("SEARCH_PROVIDER", "none"))
    parser.add_argument("--query", help="Search query for live providers.")
    parser.add_argument("--input", metavar="FILE", help="Existing source-candidate JSON for provider=none.")
    parser.add_argument("--output", metavar="FILE", help="Write normalized JSON here instead of stdout.")
    parser.add_argument("--output-dir", metavar="DIR", help="Write RUN-ID-source-candidates.json into this directory.")
    parser.add_argument("--run-id", metavar="ID", help="Filename prefix for output-dir mode (default: today's date).")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum live results to request.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.provider == "none":
            if not args.input:
                print("error: --input is required when --provider none", file=sys.stderr)
                return 2
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
            output = normalize_existing(payload, "none")
        else:
            if not args.query:
                print("error: --query is required for live search providers", file=sys.stderr)
                return 2
            output = tavily_search(args.query, args.max_results) if args.provider == "tavily" else brave_search(args.query, args.max_results)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    text = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        run_id = args.run_id or date.today().isoformat()
        path = out_dir / f"{run_id}-source-candidates.json"
        path.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {path}")
    elif args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
