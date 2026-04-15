from argparse import ArgumentParser
from pathlib import Path



class Args:
    repo: Path
    url: str | None
    rev: str | None
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
        "-r",
        "--rev",
        type=str,
        help="checkout this revision before building",
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
    print(args)


if __name__ == "__main__":
    main()
