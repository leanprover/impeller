import shlex
import subprocess
from os import PathLike
from pathlib import Path

type Arg = str | bytes | PathLike[str] | PathLike[bytes]


def run(*args: Arg, cwd: Path | None = None, silent: bool = False) -> None:
    print("$ " + " ".join(shlex.quote(str(arg)) for arg in args))
    subprocess.run(args, check=True, cwd=cwd, capture_output=silent)


def run_stdout(*args: Arg, cwd: Path | None = None) -> str:
    print("$ " + " ".join(shlex.quote(str(arg)) for arg in args))
    res = subprocess.run(args, check=True, stdout=subprocess.PIPE, text=True, cwd=cwd)
    return res.stdout


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
    run("git", "switch", "--detach", "origin/HEAD", cwd=repo)


def install_toolchain(repo: Path) -> None:
    toolchain_file = repo / "lean-toolchain"
    toolchain = toolchain_file.read_text().strip()
    run("elan", "toolchain", "install", toolchain)
