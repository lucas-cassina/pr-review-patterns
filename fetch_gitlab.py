#!/usr/bin/env python3
"""
Fetch GitLab MR review comments from the past N days.
Returns a list of normalized comment dicts (same shape as fetch_github.py).
"""

import sys
from datetime import datetime, timezone
from urllib.parse import quote

import requests


def _headers(token):
    return {"PRIVATE-TOKEN": token}


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


def _encode_id(project_id):
    # Numeric IDs pass through; path-style IDs ("group/project") need %2F encoding.
    # Use quote(..., safe='') — not quote_plus, which encodes spaces as '+' (form encoding),
    # which GitLab rejects in URL path segments.
    try:
        int(project_id)
        return project_id
    except (ValueError, TypeError):
        return quote(str(project_id), safe="")


def _is_bot(author_obj, login):
    return (
        author_obj.get("bot")
        or login.endswith("-bot")
        or "[bot]" in login
    )


def fetch(token, base_url, repos, since, stderr=sys.stderr):
    headers = _headers(token)
    all_comments = []
    pr_count = 0

    for repo in repos:
        encoded_id = _encode_id(repo["id"])
        repo_name = repo["name"]
        api = f"{base_url}/api/v4/projects/{encoded_id}"

        print(f"GitLab: fetching MRs from {repo_name}...", file=stderr)
        try:
            mrs = _get_all(
                f"{api}/merge_requests",
                headers,
                params={
                    "state": "all",
                    "updated_after": since.isoformat(),
                    "per_page": 100,
                    "order_by": "updated_at",
                    "sort": "desc",
                },
            )
        except requests.RequestException as e:
            print(f"  WARNING: could not fetch MRs from {repo_name}: {e}", file=stderr)
            continue

        for mr in mrs:
            updated = datetime.fromisoformat(mr["updated_at"].replace("Z", "+00:00"))
            if updated < since:
                break  # sorted by updated_at desc — all subsequent MRs are also stale

            iid = mr["iid"]
            pr_title = mr["title"]
            author_obj = mr.get("author") or {}
            pr_author = author_obj.get("username", "ghost")

            try:
                notes = _get_all(
                    f"{api}/merge_requests/{iid}/notes",
                    headers,
                    # Sort asc by created_at so we can break early once we pass the window
                    params={"per_page": 100, "order_by": "created_at", "sort": "asc"},
                )
            except requests.RequestException as e:
                print(f"  WARNING: could not fetch notes for MR !{iid}: {e}", file=stderr)
                continue

            mr_has_new_notes = False
            for note in notes:
                # Skip system messages (merged, approved, pipeline events, etc.)
                if note.get("system"):
                    continue

                created = datetime.fromisoformat(note["created_at"].replace("Z", "+00:00"))
                if created < since:
                    continue  # notes sorted asc — older ones appear first, keep going
                # Past this point all notes are within the window (asc sort)
                mr_has_new_notes = True

                note_author = note.get("author") or {}
                author = note_author.get("username", "ghost")

                if author == pr_author:
                    continue
                if _is_bot(note_author, author):
                    continue

                position = note.get("position") or {}
                path = position.get("new_path") or position.get("old_path") or ""
                comment_type = "inline" if note.get("type") == "DiffNote" else "top-level"

                all_comments.append({
                    "platform": "gitlab",
                    "repo": repo_name,
                    "pr_number": iid,
                    "pr_title": pr_title,
                    "pr_author": pr_author,
                    "comment_author": author,
                    "body": note["body"],
                    "path": path,
                    "created_at": note["created_at"],
                    "type": comment_type,
                    "url": mr.get("web_url", ""),
                })

            if mr_has_new_notes:
                pr_count += 1

    return all_comments, pr_count
