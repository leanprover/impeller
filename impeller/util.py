import datetime
import os
import re
import shlex
import subprocess
from os import PathLike
from pathlib import Path

from impeller.sandbox import Sandbox

type Arg = str | bytes | PathLike[str] | PathLike[bytes]

ENV = os.environ.copy()
ENV["GIT_TERMINAL_PROMPT"] = "0"


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run(
    *args: Arg, cwd: Path | None = None, check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(shlex.quote(str(arg)) for arg in args))
    return subprocess.run(
        args,
        env=ENV,
        cwd=cwd,
        check=check,
        capture_output=capture,
        text=True,
    )


def run_stdout(*args: Arg, cwd: Path | None = None) -> str:
    return run(*args, cwd=cwd, check=True, capture=True).stdout


def clone_and_prepare_repo(repo: Path, url: str) -> None:
    if not repo.exists():
        repo.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", url, repo)

    # Ensure remotes are set up as expected
    remotes = set(run_stdout("git", "remote", cwd=repo).splitlines())
    for remote in remotes | {"origin"}:
        if remote != "origin":
            run("git", "remote", "remove", remote, cwd=repo)
        elif "origin" in remotes:
            run("git", "remote", "set-url", "origin", url, cwd=repo)
        else:
            run("git", "remote", "add", "origin", url, cwd=repo)

    # Sync remote data
    run(
        *("git", "fetch", "--all", "--tags"),
        *("--prune", "--prune-tags", "--force"),
        cwd=repo,
    )

    # Prepare working directory
    run("git", "clean", "-dffx", cwd=repo)
    switch_to_ref(repo, "origin/HEAD")


def switch_to_ref(repo: Path, ref: str) -> None:
    run("git", "switch", "--detach", ref, cwd=repo)
    run("git", "clean", "-dffx", cwd=repo)


def get_toolchain(repo: Path) -> str | None:
    toolchain_file = repo / "lean-toolchain"
    try:
        return toolchain_file.read_text().strip()
    except FileNotFoundError:
        return


def get_active_toolchain(repo: Path) -> str:
    text = run_stdout("elan", "show")
    match = re.search(r"active toolchain\n----------------\n\n(\S+)", text)
    if not match:
        raise Exception("Failed to determine active toolchain from elan show")
    return match.group(1)


def install_toolchain(toolchain: str) -> None:
    installed = run_stdout("elan", "toolchain", "list").splitlines()
    if toolchain in installed:
        return

    try:
        run("elan", "toolchain", "install", toolchain)
    except subprocess.CalledProcessError:
        # TODO Check if error message mentions that toolchain is already installed, error otherwise?
        return  # Probably already installed


def check_for_command(box: Sandbox, name: str) -> bool | None:
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
