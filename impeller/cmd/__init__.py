import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from impeller.output import Toolchain
from impeller.sandbox import Sandbox
from impeller.util import run, run_stdout


@dataclass
class CommandContext:
    repo: Path
    url: str | None
    output: Path
    box: Sandbox


def get_toolchain(repo: Path) -> str | None:
    toolchain_file = repo / "lean-toolchain"
    try:
        return toolchain_file.read_text().strip()
    except FileNotFoundError:
        return


def get_active_toolchain(repo: Path) -> str | None:
    text = run_stdout("elan", "show", cwd=repo)
    match = re.search(r"active toolchain\n----------------\n\n(\S+)", text)
    if not match:
        raise Exception("Failed to determine active toolchain from elan show")  # noqa: TRY002
    toolchain = match.group(1).strip()
    if toolchain == "no":  # From "no active toolchain"
        return
    return toolchain


def get_lean_githash(box: Sandbox) -> str | None:
    try:
        return box.run_stdout("lean", "--githash").strip()
    except subprocess.CalledProcessError:
        return


def get_toolchain_metadata(ctx: CommandContext) -> Toolchain:
    return Toolchain(
        declared=get_toolchain(ctx.repo),
        active=get_active_toolchain(ctx.repo),
        githash=get_lean_githash(ctx.box),
    )


def install_toolchain(toolchain: str) -> None:
    installed = run_stdout("elan", "toolchain", "list").splitlines()
    if toolchain in installed:
        return

    try:
        run("elan", "toolchain", "install", toolchain)
    except subprocess.CalledProcessError:
        # TODO Check if error message mentions that toolchain is already installed, error otherwise?
        return  # Probably already installed


def get_current_sha(repo: Path) -> str:
    return run_stdout("git", "rev-parse", "HEAD", cwd=repo).strip()
