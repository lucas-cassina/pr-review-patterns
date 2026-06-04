#!/usr/bin/env python3
"""
Unified entry point. Fetches PR/MR review comments from GitHub and/or GitLab.

Writes two files:
  output/raw_comments.json   Full data, all fields (reference/debug)
  output/comments.json       Compact version for agent analysis (fewer tokens)

Usage:
    python3 fetch.py
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

import config
import fetch_github
import fetch_gitlab


def main():
    load_dotenv(override=True)

    if not config.GITHUB_REPOS and not config.GITLAB_REPOS:
        print("ERROR: No repos configured. Edit config.py and add entries to GITHUB_REPOS or GITLAB_REPOS.", file=sys.stderr)
        sys.exit(1)

    if config.DAYS_LOOKBACK < 1:
        print(f"ERROR: DAYS_LOOKBACK must be a positive integer, got {config.DAYS_LOOKBACK!r}.", file=sys.stderr)
        sys.exit(1)

    run_start = datetime.now(timezone.utc)
    since = run_start - timedelta(days=config.DAYS_LOOKBACK)
    all_comments = []
    total_prs = 0

    # --- GitHub ---
    if config.GITHUB_REPOS:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("ERROR: GITHUB_REPOS is set but GITHUB_TOKEN is missing from .env", file=sys.stderr)
            sys.exit(1)
        comments, prs = fetch_github.fetch(token, config.GITHUB_REPOS, since)
        all_comments.extend(comments)
        total_prs += prs

    # --- GitLab ---
    if config.GITLAB_REPOS:
        token = os.getenv("GITLAB_TOKEN")
        if not token:
            print("ERROR: GITLAB_REPOS is set but GITLAB_TOKEN is missing from .env", file=sys.stderr)
            sys.exit(1)
        comments, prs = fetch_gitlab.fetch(token, config.GITLAB_BASE_URL, config.GITLAB_REPOS, since)
        all_comments.extend(comments)
        total_prs += prs

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    meta = {
        "fetched_at": run_start.isoformat(),
        "since": since.isoformat(),
        "pr_count": total_prs,
        "comment_count": len(all_comments),
    }

    # Full raw data — keep for debugging and auditing
    raw = {**meta, "comments": all_comments}
    (output_dir / "raw_comments.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False))

    # Compact version for agent analysis — strips fields irrelevant to pattern detection
    # and truncates long bodies to reduce token consumption
    BODY_LIMIT = 300
    compact_comments = [
        {
            "body": c["body"][:BODY_LIMIT] + ("…" if len(c["body"]) > BODY_LIMIT else ""),
            "path": c["path"],
            "type": c["type"],
            "platform": c["platform"],
            "repo": c["repo"],
            "comment_author": c["comment_author"],
            "pr_author": c["pr_author"],
        }
        for c in all_comments
    ]
    compact = {**meta, "comments": compact_comments}
    (output_dir / "comments.json").write_text(json.dumps(compact, ensure_ascii=False))

    print(f"Done: {len(all_comments)} comments from {total_prs} PRs/MRs → output/", file=sys.stderr)


if __name__ == "__main__":
    main()
