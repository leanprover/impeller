import json
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from impeller.reservoir_config import ReservoirConfig
from impeller.sandbox import Sandbox, get_sandbox
from impeller.util import (
    clone_and_prepare_repo,
    install_toolchain,
    run_stdout,
    switch_to_ref,
)


class Args:
    repo: Path
    url: str | None
    output: Path | None
    ref: str | None
    bubblewrap: bool
    bubblewrap_nixos: bool


def fetch_git_metadata(args: Args) -> dict[str, Any]:
    data = {}

    if args.ref:
        data["ref"] = args.ref

    try:
        data["sha"] = run_stdout("git", "rev-parse", "HEAD", cwd=args.repo).strip()
    except Exception as e:
        print("Error fetching sha:", e)

    return data


def fetch_lake_metadata(args: Args, box: Sandbox) -> dict[str, Any] | None:
    try:
        config_json = box.run_stdout("lake", "reservoir-config")
    except subprocess.CalledProcessError:
        return

    config = ReservoirConfig.parse(config_json, args.repo)

    # Only the version-specific fields, not the global ones
    return {
        "license": config.license,
        "license_files": config.license_files,
        "readme_file": config.readme_file,
        "version": config.version,
    }


def fetch_manifest(args: Args) -> Any:
    manifest_file = args.repo / "lake-manifest.json"
    return json.loads(manifest_file.read_text())


def check(box: Sandbox, name: str) -> bool | None:
    try:
        result = box.run("lake", f"check-{name}", check=False, capture=True)
        if result.returncode == 0:
            return True
        if "unknown command" in result.stderr:
            return None
        return False
    except Exception as e:
        print(f"Error checking for {name}:", e)
        return None


def do(box: Sandbox, name: str) -> bool:
    try:
        box.run("lake", name)
        return True
    except Exception as e:
        print(f"Error running {name}:", e)
        return False


def get_data(args: Args, box: Sandbox) -> dict[str, Any]:
    data: dict[str, Any] = {}

    try:
        data["metadata_git"] = fetch_git_metadata(args)
    except Exception as e:
        print("Error fetching git metadata:", e)

    try:
        if args.url:
            clone_and_prepare_repo(repo=args.repo, url=args.url)
        if args.ref:
            switch_to_ref(args.repo, args.ref)
        install_toolchain(repo=args.repo)
    except Exception as e:
        print("Error setting up repo:", e)
        return data

    try:
        data["metadata_lake"] = fetch_lake_metadata(args, box)
    except Exception as e:
        print("Error fetching lake metadata:", e)

    try:
        data["manifest"] = fetch_manifest(args)
    except Exception as e:
        print("Error fetching manifest:", e)

    check_build = check(box, "build")
    build = None
    if check_build != False:  # noqa: E712
        build = do(box, "build")
    data["check_build"] = check_build
    data["build"] = build

    check_test = check(box, "test")
    test = None
    if check_test != False and build:  # noqa: E712
        test = do(box, "test")
    data["check_test"] = check_test
    data["test"] = test

    check_lint = check(box, "lint")
    lint = None
    if check_lint != False and build:  # noqa: E712
        lint = do(box, "lint")
    data["check_lint"] = check_lint
    data["lint"] = lint

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
        "-r",
        "--ref",
        type=str,
        help="switch to this reference before building",
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

    data = get_data(args, box)

    output = args.output or args.repo.with_name(args.repo.name + ".json")
    output.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
