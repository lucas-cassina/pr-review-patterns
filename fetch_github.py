#!/usr/bin/env python3
"""
Fetch GitHub PR review comments from the past N days.
Returns a list of normalized comment dicts (same shape as fetch_gitlab.py).
"""

import sys
from datetime import datetime

import requests

BASE = "https://api.github.com"

_BOT_SUFFIXES = ("-bot", "[bot]")


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_all(url, headers, params=None):
    results = []
    while url:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            break  # unexpected response shape (e.g. error dict with 200 status)
        results.extend(data)
        url = r.links.get("next", {}).get("url")
        params = None
    return results


def _user_login(obj):
    """Safely extract login from a user/author object that may be null."""
    user = obj.get("user") or obj.get("author") or {}
    return user.get("login", "ghost") if user else "ghost"


def _is_bot(login):
    return "[bot]" in login or login.endswith("-bot")


def fetch(token, repos, since, stderr=sys.stderr):
    headers = _headers(token)
    all_comments = []
    pr_count = 0

    for repo in repos:
        print(f"GitHub: fetching PRs from {repo}...", file=stderr)
        try:
            prs = _get_all(
                f"{BASE}/repos/{repo}/pulls",
                headers,
                params={"state": "closed", "per_page": 100, "sort": "updated", "direction": "desc"},
            )
        except requests.RequestException as e:
            print(f"  WARNING: could not fetch PRs from {repo}: {e}", file=stderr)
            continue

        for pr in prs:
            updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            if updated < since:
                break  # sorted by updated desc — safe to stop early
            if not pr.get("merged_at"):
                continue  # closed without merging — skip

            pr_count += 1
            pr_number = pr["number"]
            pr_title = pr["title"]
            pr_author = (pr.get("user") or {}).get("login", "ghost")

            # Inline diff comments
            try:
                for c in _get_all(
                    f"{BASE}/repos/{repo}/pulls/{pr_number}/comments",
                    headers,
                    params={"per_page": 100, "since": since.isoformat()},
                ):
                    created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                    if created < since:
                        continue
                    author = (c.get("user") or {}).get("login", "ghost")
                    if _is_bot(author):
                        continue
                    all_comments.append({
                        "platform": "github",
                        "repo": repo,
                        "pr_number": pr_number,
                        "pr_title": pr_title,
                        "pr_author": pr_author,
                        "comment_author": author,
                        "body": c["body"],
                        "path": c.get("path", ""),
                        "created_at": c["created_at"],
                        "type": "inline",
                        "url": c["html_url"],
                    })
            except requests.RequestException as e:
                print(f"  WARNING: review comments for PR #{pr_number}: {e}", file=stderr)

            # Top-level issue comments
            try:
                for c in _get_all(
                    f"{BASE}/repos/{repo}/issues/{pr_number}/comments",
                    headers,
                    params={"per_page": 100, "since": since.isoformat()},
                ):
                    created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                    if created < since:
                        continue
                    author = (c.get("user") or {}).get("login", "ghost")
                    if author == pr_author or _is_bot(author):
                        continue
                    all_comments.append({
                        "platform": "github",
                        "repo": repo,
                        "pr_number": pr_number,
                        "pr_title": pr_title,
                        "pr_author": pr_author,
                        "comment_author": author,
                        "body": c["body"],
                        "path": "",
                        "created_at": c["created_at"],
                        "type": "top-level",
                        "url": c["html_url"],
                    })
            except requests.RequestException as e:
                print(f"  WARNING: issue comments for PR #{pr_number}: {e}", file=stderr)

    return all_comments, pr_count
