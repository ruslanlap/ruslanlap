
#!/usr/bin/env python3

from datetime import datetime, timedelta
"""
sum_github_downloads.py
---------------------------------
Sums GitHub release asset downloads across repositories for a user or org.

Usage examples:
  python sum_github_downloads.py --user ruslanlap
  python sum_github_downloads.py --user ruslanlap --filter "^PowerToysRun-|^Community\.PowerToys\.Run" --include-prereleases
  python sum_github_downloads.py --org my-org --out-json stats/total_downloads.json --out-shield stats/total_downloads_shield.json

Notes:
- Counts only attached release assets (ZIPs, installers, etc). GitHub does NOT count source code .zip/.tarball downloads via API.
- Requires a GitHub token (fine-grained or classic) with public_repo scope for public repos.
  Set env var: GITHUB_TOKEN=xxxxx
"""

import argparse
import json
import os
import re
import sys
import time
from urllib import request, parse, error

API_BASE = "https://api.github.com"

def gh_request(url, token, accept="application/vnd.github+json"):
    headers = {
        "Accept": accept,
        "User-Agent": "sum-github-downloads-script",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            # Handle rate limit headers
            remaining = resp.headers.get("X-RateLimit-Remaining")
            reset = resp.headers.get("X-RateLimit-Reset")
            return json.loads(data), remaining, reset, resp.headers
    except error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTPError {e.code} for {url}:\n{msg}") from None
    except error.URLError as e:
        raise RuntimeError(f"URLError for {url}: {e}") from None

def paginate(url, token):
    """Yield items across paginated GitHub endpoints (Link header based)."""
    while url:
        data, remaining, reset, headers = gh_request(url, token)
        if isinstance(data, list):
            for item in data:
                yield item
        else:
            # For endpoints that return dict with 'items'
            items = data.get("items", [])
            for item in items:
                yield item

        # Parse Link header for next
        link = headers.get("Link", "")
        next_url = None
        if link:
            parts = [p.strip() for p in link.split(",")]
            for p in parts:
                if 'rel="next"' in p:
                    start = p.find("<") + 1
                    end = p.find(">")
                    next_url = p[start:end]
                    break
        url = next_url

def list_repos(user=None, org=None, token=None, include_forks=False):
    if user and org:
        raise ValueError("Provide either --user or --org, not both.")
    if not user and not org:
        raise ValueError("Must provide --user or --org.")

    if user:
        url = f"{API_BASE}/users/{parse.quote(user)}/repos?per_page=100&type=owner&sort=full_name&direction=asc"
    else:
        url = f"{API_BASE}/orgs/{parse.quote(org)}/repos?per_page=100&type=all&sort=full_name&direction=asc"

    for repo in paginate(url, token):
        if not include_forks and repo.get("fork"):
            continue
        yield repo

def list_releases(owner, repo, token):
    url = f"{API_BASE}/repos/{parse.quote(owner)}/{parse.quote(repo)}/releases?per_page=100"
    for rel in paginate(url, token):
        yield rel

def sum_repo_downloads(owner, repo, token, include_prereleases=False, exclude_drafts=True):
    total = 0
    per_release = []
    for rel in list_releases(owner, repo, token):
        if exclude_drafts and rel.get("draft"):
            continue
        if (not include_prereleases) and rel.get("prerelease"):
            continue
        assets = rel.get("assets", []) or []
        count = sum(int(a.get("download_count", 0) or 0) for a in assets)
        total += count
        per_release.append({
            "tag": rel.get("tag_name"),
            "name": rel.get("name"),
            "draft": rel.get("draft"),
            "prerelease": rel.get("prerelease"),
            "published_at": rel.get("published_at"),
            "assets": [
                {
                    "name": a.get("name"),
                    "download_count": int(a.get("download_count", 0) or 0),
                    "browser_download_url": a.get("browser_download_url"),
                } for a in assets
            ],
            "release_total": count,
        })
    return total, per_release

def human_int(n):
    return f"{n:,}".replace(",", " ")

def load_history(history_path):
    """Load download history from JSON file."""
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history, history_path):
    """Save download history to JSON file."""
    os.makedirs(os.path.dirname(history_path) or ".", exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def compute_growth_metrics(history, current_total):
    """Compute growth metrics from history."""
    if len(history) < 2:
        return {"monthly_growth": "N/A", "weekly_avg": "N/A", "growth_pct": 0}

    # Get last entry
    last_total = history[-1]["grand_total"]
    growth_pct = ((current_total - last_total) / last_total * 100) if last_total > 0 else 0

    # Weekly average: sum last 7 days / 7, but since weekly runs, approximate as recent deltas
    recent_deltas = []
    for i in range(1, min(8, len(history))):
        delta = history[-i]["grand_total"] - history[-i-1]["grand_total"] if i < len(history) else 0
        recent_deltas.append(delta)
    weekly_avg = sum(recent_deltas[-7:]) / 7 if recent_deltas else 0

    return {
        "monthly_growth": f"+{growth_pct:.1f}%" if growth_pct > 0 else f"{growth_pct:.1f}%",
        "weekly_avg": human_int(int(weekly_avg)),
        "growth_pct": growth_pct
    }

def main():
    ap = argparse.ArgumentParser(description="Sum GitHub release downloads across repos.")
    who = ap.add_mutually_exclusive_group(required=True)
    who.add_argument("--user", help="GitHub username (e.g., ruslanlap)")
    who.add_argument("--org", help="GitHub org")
    ap.add_argument("--filter", help="Regex to include only repos matching (e.g., '^PowerToysRun-|^Community\\.PowerToys\\.Run')")
    ap.add_argument("--include-forks", action="store_true", help="Include forked repos (default: false)")
    ap.add_argument("--include-prereleases", action="store_true", help="Include prerelease downloads (default: false)")
    ap.add_argument("--timeout", type=int, default=0, help="Sleep seconds between repos to avoid abuse detection (default: 0)")
    ap.add_argument("--out-json", default="total_downloads.json", help="Path to write detailed JSON output")
    ap.add_argument("--out-shield", default="total_downloads_shield.json", help="Path to write a Shields.io endpoint JSON")
    ap.add_argument("--print", action="store_true", help="Print human summary to stdout")
    args = ap.parse_args()

    token = os.getenv("GH_TOKEN", "").strip()
    if not token:
        print("Warning: GH_TOKEN is not set; you may hit rate limits on GitHub API.", file=sys.stderr)

    filt = re.compile(args.filter) if args.filter else None

    owner = args.user or args.org
    results = []
    grand_total = 0

    for repo in list_repos(user=args.user, org=args.org, token=token, include_forks=args.include_forks):
        name = repo.get("name")
        if filt and not filt.search(name or ""):
            continue
        # Only count if the repo has releases at all; skip if no releases endpoint items
        try:
            subtotal, per_release = sum_repo_downloads(owner, name, token, include_prereleases=args.include_prereleases)
        except RuntimeError as e:
            print(f"Error on {owner}/{name}: {e}", file=sys.stderr)
            continue

        results.append({
            "repo": name,
            "html_url": repo.get("html_url"),
            "downloads": subtotal,
            "releases": per_release,
        })
        grand_total += subtotal
        if args.timeout:
            time.sleep(args.timeout)

    results_sorted = sorted(results, key=lambda r: r["downloads"], reverse=True)
    # Handle historical data
    history_path = "stats/download_history.json"
    history = load_history(history_path)
    
    today = datetime.now().strftime("%Y-%m-%d")
    new_entry = {
        "date": today,
        "grand_total": grand_total,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Avoid duplicates for same day
    if not history or history[-1]["date"] != today:
        history.append(new_entry)
        save_history(history, history_path)
    
    # Compute growth metrics
    growth_metrics = compute_growth_metrics(history, grand_total)

    data = {
        "owner": owner,
        "filter": args.filter or None,
        "include_prereleases": args.include_prereleases,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "grand_total": grand_total,
        "grand_total_human": human_int(grand_total),
        "growth": growth_metrics,
        "repos": results_sorted,
    }

    # Write detailed JSON
    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Write shields endpoint JSON
    shield = {
        "schemaVersion": 1,
        "label": "total downloads",
        "message": human_int(grand_total),
        "color": "blue" if grand_total > 0 else "lightgrey",
    }
    os.makedirs(os.path.dirname(args.out_shield) or ".", exist_ok=True)
    with open(args.out_shield, "w", encoding="utf-8") as f:
        json.dump(shield, f, ensure_ascii=False)
    
    # Write growth shield JSON
    growth_shield_path = args.out_shield.replace("total_downloads_shield.json", "growth_shield.json")
    growth_pct = growth_metrics["growth_pct"]
    growth_shield = {
        "schemaVersion": 1,
        "label": "monthly growth",
        "message": growth_metrics["monthly_growth"],
        "color": "brightgreen" if growth_pct > 10 else "yellow" if growth_pct > 0 else "red"
    }
    os.makedirs(os.path.dirname(growth_shield_path) or ".", exist_ok=True)
    with open(growth_shield_path, "w", encoding="utf-8") as f:
        json.dump(growth_shield, f, ensure_ascii=False)

    if args.print:
        print(f"Мої плагіни сумарно скачали {human_int(grand_total)} разів")
        print(f"Monthly growth: {growth_metrics['monthly_growth']}")
        print(f"Weekly avg: {growth_metrics['weekly_avg']}")

if __name__ == "__main__":
    main()
