import datetime
import importlib.metadata
import os
import shlex
import subprocess
from os import PathLike
from pathlib import Path

type Arg = str | bytes | PathLike[str] | PathLike[bytes]

ENV = os.environ.copy()
ENV["GIT_TERMINAL_PROMPT"] = "0"


def get_app_version() -> str:
    return importlib.metadata.version("impeller")


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def run(
    *args: Arg, cwd: Path | None = None, check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(shlex.quote(str(arg)) for arg in args))
    result = subprocess.run(
        args,
        env=ENV,
        cwd=cwd,
        capture_output=capture,
        text=True,
        check=False,
    )
    if capture and result.returncode != 0:
        print(f"returncode: {result.returncode}")
        print(f"stdout:\n{result.stdout}")
        print(f"stderr:\n{result.stderr}")
    if check:
        result.check_returncode()
    return result


def run_stdout(*args: Arg, cwd: Path | None = None) -> str:
    return run(*args, cwd=cwd, check=True, capture=True).stdout


def reset_workdir(repo: Path) -> None:
    run("git", "clean", "-dffx", cwd=repo)
    run("git", "checkout", "--", ".", cwd=repo)


def switch_to_ref(repo: Path, ref: str) -> None:
    reset_workdir(repo)
    run("git", "switch", "--detach", ref, cwd=repo)
    reset_workdir(repo)


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
    switch_to_ref(repo, "origin/HEAD")
