import shlex
import subprocess
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path

from impeller.util import run

type Arg = str | bytes | PathLike[str] | PathLike[bytes]


class Sandbox(ABC):
    def __init__(self, repo: Path) -> None:
        self.repo = repo

    @abstractmethod
    def run(
        self, *cmd: Arg, check: bool = True, capture: bool = False
    ) -> subprocess.CompletedProcess[str]:
        pass

    def run_stdout(self, *cmd: Arg) -> str:
        return self.run(*cmd, check=True, capture=True).stdout


class NoSandbox(Sandbox):
    def run(
        self, *cmd: Arg, check: bool = True, capture: bool = False
    ) -> subprocess.CompletedProcess[str]:
        return run(*cmd, cwd=self.repo, check=check, capture=capture)


def _bwrap_bind(path: Path) -> list[Arg]:
    return ["--bind", path, path]


def _bwrap_ro_bind(path: Path) -> list[Arg]:
    return ["--ro-bind", path, path]


class BubblewrapSandbox(Sandbox):
    def __init__(self, repo: Path, nixos: bool = False) -> None:
        super().__init__(repo=repo)

        self.args = []
        self._add_args("bwrap")
        self._add_args("--unshare-all")
        self._add_args("--share-net")
        self._add_args("--dev", "/dev")
        self._add_args("--proc", "/proc")
        self._add_args("--tmpfs", "/tmp")

        if nixos:
            self._add_ro_bind(Path("/nix"))
            self._add_ro_bind(Path("/run/current-system/sw"))
        else:
            self._add_ro_bind(Path("/bin"))
            self._add_ro_bind(Path("/etc/ca-certificates"))
            self._add_ro_bind(Path("/etc/resolv.conf"))
            self._add_ro_bind(Path("/etc/ssl"))
            self._add_ro_bind(Path("/lib"))
            self._add_ro_bind(Path("/lib64"))
            self._add_ro_bind(Path("/usr"))

        self._add_ro_bind(Path.home() / ".elan")

    def _add_args(self, *args: Arg) -> None:
        self.args.extend(args)

    def _add_ro_bind(self, path: Path) -> None:
        self.args.extend(_bwrap_ro_bind(path))

    def _args_for_cmd(self, cmd: tuple[Arg, ...]) -> list[Arg]:
        repo = self.repo.resolve()
        args = list(self.args)
        args.extend(_bwrap_bind(repo))
        args.extend(_bwrap_ro_bind(repo / ".git"))
        args.extend(("--chdir", repo))
        args.append("--")
        args.extend(cmd)
        return args

    def run(
        self, *cmd: Arg, check: bool = True, capture: bool = False
    ) -> subprocess.CompletedProcess[str]:
        print("bwrap$ " + " ".join(shlex.quote(str(arg)) for arg in cmd))
        return subprocess.run(
            self._args_for_cmd(cmd=cmd),
            cwd=self.repo,
            check=check,
            capture_output=capture,
            text=True,
        )


def get_sandbox(repo: Path, bubblewrap: bool, bubblewrap_nixos: bool) -> Sandbox:
    if bubblewrap:
        return BubblewrapSandbox(repo=repo, nixos=bubblewrap_nixos)
    else:
        return NoSandbox(repo=repo)
