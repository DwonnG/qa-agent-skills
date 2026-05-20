import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_URL_RE = re.compile(r'"Repo_Url"\s*:\s*"([^"]+)"')
GITHUB_URL_RE = re.compile(r"(https?://[^\s\"']*github[^\s\"']*/[^/\s\"']+/[^/\s\"']+)")
DEFAULT_GH_HOSTS = ("github.com", "github.com")


def resolve_shared_wrapper(env_var: str, skill_name: str, script_name: str) -> str:
    env_path = os.environ.get(env_var, "").strip()
    if env_path:
        return str(Path(env_path).expanduser())
    candidate = Path.home() / ".agents" / "skills" / skill_name / "scripts" / script_name
    if candidate.exists():
        return str(candidate)
    raise FileNotFoundError(
        f"Could not find the companion {skill_name} wrapper at ~/.agents/skills/{skill_name}/scripts/{script_name}. "
        f"Set {env_var} or install the {skill_name} skill."
    )


def run_json(cmd, env=None):
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "command failed")

    output = proc.stdout
    object_start = output.find("{")
    array_start = output.find("[")
    starts = [i for i in (object_start, array_start) if i != -1]
    start = min(starts) if starts else -1
    if start == -1:
        raise RuntimeError("no JSON payload returned")
    decoder = json.JSONDecoder()
    payload, _ = decoder.raw_decode(output[start:])
    return payload


def parse_repo(repo_url):
    if not repo_url:
        return None, None
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/").split("/")
    if len(path) < 2:
        return parsed.netloc, None
    return parsed.netloc, "/".join(path[:2])


def extract_repo_url(issue_data):
    description = issue_data.get("description") or ""
    match = REPO_URL_RE.search(description)
    if match:
        return match.group(1)

    generic = GITHUB_URL_RE.search(description)
    return generic.group(1) if generic else None


def search_prs(gh, jira_key, host, repo, state):
    cmd = [gh, "search", "prs", jira_key, "--limit", "10",
           "--json", "number,title,url,state,repository"]
    if state == "merged":
        cmd.extend(["--state", "closed", "--merged"])
    elif state == "open":
        cmd.extend(["--state", "open"])
    if repo:
        cmd.extend(["--repo", repo])
    env = None
    if host:
        env = {**os.environ, "GH_HOST": host}
    return run_json(cmd, env=env)


def pr_artifact(gh, host, repo, number):
    cmd = [gh, "pr", "view", str(number), "--repo", repo,
           "--json", "title,url,state,commits,files"]
    env = None
    if host:
        env = {**os.environ, "GH_HOST": host}
    return run_json(cmd, env=env)


def candidate_search_targets(repo_url):
    host, repo = parse_repo(repo_url)
    if repo:
        return [(host, repo)]

    targets = []
    for candidate_host in (host, os.environ.get("GH_HOST"), *DEFAULT_GH_HOSTS):
        if candidate_host and (candidate_host, None) not in targets:
            targets.append((candidate_host, None))
    return targets or [(None, None)]


def summarize_issue(key):
    jira = resolve_shared_wrapper("JIRA_ISSUES_CLI", "jira-issues", "jira-cli")
    gh = resolve_shared_wrapper("GITHUB_MANAGER_GH", "github-manager", "gh")
    issue_payload = run_json([jira, "--format", "json", "view", key])
    issue = issue_payload["data"]
    repo_url = extract_repo_url(issue)

    artifacts = []
    warnings = []
    seen_prs = set()
    for host, repo in candidate_search_targets(repo_url):
        for state in ("merged", "open"):
            try:
                pr_matches = search_prs(gh, key, host, repo, state)
            except RuntimeError as exc:
                warnings.append(f"PR search failed on host={host or 'default'} state={state}: {exc}")
                continue

            for pr in pr_matches:
                pr_key = (pr["repository"]["nameWithOwner"], pr["number"])
                if pr_key in seen_prs:
                    continue
                seen_prs.add(pr_key)
                try:
                    pr_data = pr_artifact(gh, host, pr["repository"]["nameWithOwner"], pr["number"])
                except RuntimeError as exc:
                    warnings.append(
                        f"PR detail lookup failed for {pr['repository']['nameWithOwner']}#{pr['number']}: {exc}"
                    )
                    continue

                artifacts.append({
                    "repository": pr["repository"]["nameWithOwner"],
                    "pull_request": {
                        "number": pr["number"],
                        "title": pr_data["title"],
                        "url": pr_data["url"],
                        "state": pr_data["state"],
                    },
                    "commits": [
                        {
                            "oid": c["oid"],
                            "headline": c["messageHeadline"],
                        }
                        for c in pr_data.get("commits", [])
                    ],
                    "files": [
                        {
                            "path": f["path"],
                            "change_type": f["changeType"],
                        }
                        for f in pr_data.get("files", [])
                    ],
                })

    result = {
        "jira_key": key,
        "summary": issue.get("summary"),
        "repo_url": repo_url,
        "artifacts": artifacts,
    }
    if warnings:
        result["warnings"] = warnings
    return result


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Recover GitHub pull request, commit, and changed-file artifacts from Jira keys."
    )
    parser.add_argument("jira_keys", nargs="+", help="One or more Jira issue keys, for example PROJ-51684")
    return parser.parse_args(argv)


def main():
    args = parse_args(sys.argv[1:])

    results = []
    for key in args.jira_keys:
        results.append(summarize_issue(key))
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
