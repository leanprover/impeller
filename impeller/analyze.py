from argparse import ArgumentParser
from pathlib import Path

from impeller.reservoir_config import ReservoirConfig
from impeller.sandbox import get_sandbox
from impeller.util import clone_and_prepare_repo, install_toolchain


class Args:
    repo: Path
    url: str | None
    infer_metadata: bool
    bubblewrap: bool
    bubblewrap_nixos: bool


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
        "-m",
        "--infer-metadata",
        action="store_true",
        help="infer missing metadata from external sources like GitHub",
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

    if args.url:
        clone_and_prepare_repo(repo=args.repo, url=args.url)
    install_toolchain(repo=args.repo)

    config_json = box.run_stdout("lake", "reservoir-config")
    config = ReservoirConfig.parse(config_json)

    # TODO Fetch metadata from GitHub

    print(config.dump())


if __name__ == "__main__":
    main()
