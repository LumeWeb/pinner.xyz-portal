#!/usr/bin/env python3
"""Update portal-plugins.yaml with latest git hashes from GitHub.

Usage:
  ./update-hashes.py              # Update all entries
  ./update-hashes.py --dry-run    # Show what would change without writing
  ./update-hashes.py --branch main # Use a different branch (default: develop)

Resolves Go module paths to GitHub repos via the go-import meta tag,
then fetches the latest commit SHA from GitHub API.

Set GITHUB_TOKEN env var for authenticated API (5,000 req/hr vs 60).
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from ruamel.yaml import YAML

YAML_FILE = Path(__file__).parent / "portal-plugins.yaml"
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, multiplied by attempt number

PORTAL_MODULE = "go.lumeweb.com/portal"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


class GitHubAPI:
    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.session.headers["Accept"] = "application/vnd.github+json"
        self._default_branch_cache: dict[str, str | None] = {}

    def _request(self, path: str) -> dict | None:
        url = f"https://api.github.com{path}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, timeout=10)
            except requests.RequestException as exc:
                print(f"  retry {attempt}/{MAX_RETRIES}: {exc}", file=sys.stderr)
                if attempt == MAX_RETRIES:
                    return None
                time.sleep(RETRY_BACKOFF * attempt)
                continue

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                print(f"  rate limited, retry {attempt}/{MAX_RETRIES}", file=sys.stderr)
                time.sleep(RETRY_BACKOFF * attempt)
                continue

            return None

        return None

    def resolve_github_repo(self, module: str) -> str | None:
        """Resolve a Go module path to its GitHub repo URL via go-import meta tag."""
        try:
            resp = self.session.get(f"https://{module}", timeout=10)
        except requests.RequestException:
            return None
        m = re.search(r'content=\"[^\"]*git\s+([^\"]+)\"', resp.text)
        return m.group(1) if m else None

    def _default_branch(self, api_path: str) -> str | None:
        if api_path not in self._default_branch_cache:
            repo = self._request(f"/repos/{api_path}")
            branch: str | None = repo.get("default_branch") if repo else None
            self._default_branch_cache[api_path] = branch
        return self._default_branch_cache[api_path]

    def fetch_commit(self, api_path: str, branch: str) -> tuple[str, str] | None:
        """Fetch latest commit SHA for a repo+branch. Returns (sha, resolved_branch)."""
        data = self._request(f"/repos/{api_path}/commits/{branch}")
        if data and "sha" in data:
            return data["sha"], branch

        # Branch not found — fall back to repo's default branch
        default = self._default_branch(api_path)
        if not default or default == branch:
            return None

        data = self._request(f"/repos/{api_path}/commits/{default}")
        if data and "sha" in data:
            return data["sha"], default

        return None

    def fetch_latest_sha(self, module: str, branch: str) -> str | None:
        """Resolve module path and fetch latest commit SHA."""
        repo = self.resolve_github_repo(module)
        if not repo:
            return None
        api_path = repo.removeprefix("https://github.com/")
        result = self.fetch_commit(api_path, branch)
        return result[0] if result else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Update portal-plugins.yaml with latest git hashes")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--branch", default="develop", help="Target branch (default: develop)")
    args = parser.parse_args()

    if not YAML_FILE.exists():
        die(f"{YAML_FILE} not found")

    ryaml = YAML()
    ryaml.preserve_quotes = True
    ryaml.indent(mapping=2, sequence=4, offset=2)
    with open(YAML_FILE) as f:
        manifest = ryaml.load(f)

    api = GitHubAPI(token=os.environ.get("GITHUB_TOKEN"))
    changed = 0
    total = 0

    print(f"=== Updating portal-plugins.yaml (branch: {args.branch}) ===\n")

    # --- portalVersion ---
    current = manifest.get("portalVersion", "")
    if current:
        total += 1
        print("--- portal (core) ---")
        sha = api.fetch_latest_sha(PORTAL_MODULE, args.branch)
        if sha:
            if sha != current:
                print(f"  portalVersion: {current} → {sha}")
                manifest["portalVersion"] = sha
                changed += 1
        else:
            print("  portalVersion: FAILED to fetch SHA", file=sys.stderr)

    # --- plugins ---
    plugins = manifest.get("plugins", [])
    if plugins:
        print("\n--- plugins ---")

    for plugin in plugins:
        module = plugin["module"]
        current = plugin["version"]
        label = module.rsplit("/", 1)[-1]
        total += 1

        sha = api.fetch_latest_sha(module, args.branch)
        if sha:
            if sha != current:
                print(f"  {label}: {current} → {sha}")
                plugin["version"] = sha
                changed += 1
        else:
            print(f"  {label}: FAILED", file=sys.stderr)

    print(f"\n=== Done: {changed}/{total} entries updated ===")

    if not args.dry_run and changed > 0:
        with open(YAML_FILE, "w") as f:
            ryaml.dump(manifest, f)
        subprocess.run(["git", "diff", "--stat", str(YAML_FILE)], check=False)


if __name__ == "__main__":
    main()
