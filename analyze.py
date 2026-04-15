from argparse import ArgumentParser
from pathlib import Path

from impeller.sandbox import get_sandbox


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


if __name__ == "__main__":
    main()
