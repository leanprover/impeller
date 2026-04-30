import json
from argparse import ArgumentParser
from pathlib import Path

from impeller.cmd import CommandContext
from impeller.cmd.analyze_global import CmdAnalyzeGlobal
from impeller.cmd.analyze_version import CmdAnalyzeVersion
from impeller.cmd.build_version import CmdBuildVersion
from impeller.sandbox import get_sandbox
from impeller.util import clone_and_prepare_repo, now, reset_workdir, switch_to_ref


def add_common_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
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
        required=True,
        help="output file for the result",
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


def main():
    parser = ArgumentParser(prog="impeller")

    subparsers = parser.add_subparsers(dest="command", required=True)

    #################################
    ## impeller analyze-global ... ##
    #################################

    ag = subparsers.add_parser("analyze-global")
    add_common_arguments(ag)
    ag.add_argument(
        "-m",
        "--fetch-external-metadata",
        action="store_true",
        help="fetch additional metadata from external sources like GitHub",
    )
    ag.add_argument(
        "-g",
        "--github-token-file",
        type=Path,
        help="path to a file containing a GitHub token for fetching metadata",
    )
    ag.add_argument(
        "-G",
        "--github-token-gh",
        action="store_true",
        help="obtain GitHub token from gh",
    )

    ##################################
    ## impeller analyze-version ... ##
    ##################################

    av = subparsers.add_parser("analyze-version")
    add_common_arguments(av)
    av.add_argument(
        "--rev",
        type=str,
        help="switch to this commit before analyzing",
    )

    ################################
    ## impeller build-version ... ##
    ################################

    bv = subparsers.add_parser("build-version")
    add_common_arguments(bv)
    bv.add_argument(
        "--rev",
        type=str,
        help="switch to this commit before building",
    )
    bv.add_argument(
        "--override-toolchain",
        type=str,
        help="override the toolchain specified in the repo",
    )
    bv_build = bv.add_mutually_exclusive_group()
    bv_build.add_argument(
        "--build",
        action="store_const",
        const=True,
        help="always run `lake build`",
    )
    bv_build.add_argument(
        "--no-build",
        action="store_const",
        const=False,
        dest="build",
        help="never run `lake build`",
    )
    bv_test = bv.add_mutually_exclusive_group()
    bv_test.add_argument(
        "--test",
        action="store_const",
        const=True,
        help="always run `lake test`",
    )
    bv_test.add_argument(
        "--no-test",
        action="store_const",
        const=False,
        dest="test",
        help="never run `lake test`",
    )
    bv_lint = bv.add_mutually_exclusive_group()
    bv_lint.add_argument(
        "--lint",
        action="store_const",
        const=True,
        help="always run `lake lint`",
    )
    bv_lint.add_argument(
        "--no-lint",
        action="store_const",
        const=False,
        dest="lint",
        help="never run `lake lint`",
    )

    args = parser.parse_args()

    ctx = CommandContext(
        repo=args.repo,
        url=args.url,
        output=args.output,
        box=get_sandbox(
            repo=args.repo,
            bubblewrap=args.bubblewrap,
            bubblewrap_nixos=args.bubblewrap_nixos,
        ),
    )

    started = now()

    if ctx.url:
        clone_and_prepare_repo(ctx.repo, ctx.url)
    else:
        switch_to_ref(ctx.repo, "HEAD")

    command: str = args.command
    if command == "analyze-global":
        data = CmdAnalyzeGlobal(
            ctx=ctx,
            fetch_external_metadata=args.fetch_external_metadata,
            github_token_file=args.github_token_file,
            github_token_gh=args.github_token_gh,
        ).get_data()
    elif command == "analyze-version":
        data = CmdAnalyzeVersion(
            ctx=ctx,
            rev=args.rev,
        ).get_data()
    elif command == "build-version":
        data = CmdBuildVersion(
            ctx=ctx,
            rev=args.rev,
            override_toolchain=args.override_toolchain,
            build=args.build,
            test=args.test,
            lint=args.lint,
        ).get_data()
    else:
        raise SystemExit(f"Unknown command: {command}")

    reset_workdir(ctx.repo)

    finished = now()

    data["started"] = started
    data["finished"] = finished
    ctx.output.write_text(json.dumps(data, indent=2))
