import json
import re
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from github import Auth, Github

from impeller.reservoir_config import ReservoirConfig
from impeller.sandbox import Sandbox, get_sandbox
from impeller.util import (
    clone_and_prepare_repo,
    get_toolchain,
    install_toolchain,
    now,
    run_stdout,
)


class Args:
    repo: Path
    url: str | None
    output: Path | None
    fetch_external_metadata: bool
    github_token_file: Path | None
    github_token_gh: bool
    bubblewrap: bool
    bubblewrap_nixos: bool


def fetch_git_metadata(args: Args) -> dict[str, Any]:
    tags = run_stdout("git", "tag", "--list", "v*", cwd=args.repo).splitlines()

    return {
        "version_tags": tags,
    }


def fetch_lake_metadata(args: Args, box: Sandbox) -> dict[str, Any] | None:
    try:
        config_json = box.run_stdout("lake", "reservoir-config")
    except subprocess.CalledProcessError:
        return

    config = ReservoirConfig.parse(config_json, args.repo)

    # Only the global fields, not the version-specific ones
    return {
        "description": config.description,
        "do_index": config.do_index,
        "homepage": config.homepage,
        "keywords": config.keywords,
        "name": config.name,
        "version_tags": config.version_tags,
    }


def get_github_token(args: Args) -> str | None:
    if args.github_token_gh:
        return run_stdout("gh", "auth", "token").strip()
    if args.github_token_file:
        return args.github_token_file.read_text().strip()


def get_github_fullname(args: Args) -> str | None:
    if args.url is None:
        return
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
        r"([^/]+/[^/.]+?)(?:\.git)?/?",
        args.url,
    )
    if not match:
        return
    fullname: str = match.group(1)
    return fullname


def fetch_github_metadata(args: Args) -> dict[str, Any] | None:
    if not args.fetch_external_metadata:
        return

    token = get_github_token(args)
    if not token:
        return

    fullname = get_github_fullname(args)
    if not fullname:
        return

    g = Github(auth=Auth.Token(token))
    r = g.get_repo(fullname)

    # A reasonable subset of the fields returned by the GitHub API
    # https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10#get-a-repository
    return {
        "name": r.name,
        "full_name": r.full_name,
        "owner": r.owner.login,
        "description": r.description,
        "fork": r.fork,
        "html_url": r.html_url,
        "clone_url": r.clone_url,
        "homepage": r.homepage,
        "forks_count": r.forks_count,
        "stargazers_count": r.stargazers_count,
        "subscribers_count": r.subscribers_count,
        "default_branch": r.default_branch,
        "topics": r.topics,
        "archived": r.archived,
        "disabled:": r.disabled,
        "pushed_at": r.pushed_at.isoformat(),
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
        "license_spdx_id": r.license.spdx_id,
    }


def get_data(args: Args, box: Sandbox) -> dict[str, Any]:
    data: dict[str, Any] = {}

    try:
        data["metadata_git"] = fetch_git_metadata(args)
    except Exception as e:
        print("Error fetching git metadata:", e)

    try:
        data["metadata_github"] = fetch_github_metadata(args)
    except Exception as e:
        print("Error fetching github metadata:", e)

    try:
        if args.url:
            clone_and_prepare_repo(repo=args.repo, url=args.url)

        toolchain = get_toolchain(args.repo)
        if toolchain is None:
            return data

        install_toolchain(toolchain)
    except Exception as e:
        print("Error setting up repo:", e)
        return data

    try:
        data["metadata_lake"] = fetch_lake_metadata(args, box)
    except Exception as e:
        print("Error fetching lake metadata:", e)

    return data


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "repo",
        type=Path,
        help="path to the (non-bare) git repository",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        help="clone or update the repo from this URL",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output file for the metadata",
    )
    parser.add_argument(
        "-m",
        "--fetch-external-metadata",
        action="store_true",
        help="fetch additional metadata from external sources like GitHub",
    )
    parser.add_argument(
        "-g",
        "--github-token-file",
        type=Path,
        help="path to a file containing a GitHub token for fetching metadata",
    )
    parser.add_argument(
        "-G",
        "--github-token-gh",
        action="store_true",
        help="obtain GitHub token from gh",
    )
    parser.add_argument(
        "-b",
        "--bubblewrap",
        action="store_true",
        help="use bubblewrap to sandbox interactions with the repository",
    )
    parser.add_argument(
        "-n",
        "--bubblewrap-nixos",
        action="store_true",
        help="configure bubblewrap for use on NixOS",
    )
    args = parser.parse_args(namespace=Args())

    box = get_sandbox(
        repo=args.repo,
        bubblewrap=args.bubblewrap,
        bubblewrap_nixos=args.bubblewrap_nixos,
    )

    start = now()
    data = get_data(args, box)
    end = now()
    data["start"] = start
    data["end"] = end

    output = args.output or args.repo.with_name(args.repo.name + ".json")
    output.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
