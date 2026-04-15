import shlex
import subprocess
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path

type Arg = str | bytes | PathLike[str] | PathLike[bytes]


class Sandbox(ABC):
    def __init__(self, repo: Path) -> None:
        self.repo = repo

    @abstractmethod
    def run(self, *cmd: Arg, silent: bool = False) -> None:
        pass

    @abstractmethod
    def run_stdout(self, *cmd: Arg) -> str:
        pass


class NoSandbox(Sandbox):
    def run(self, *cmd: Arg, silent: bool = False) -> None:
        print("$ " + " ".join(shlex.quote(str(arg)) for arg in cmd))
        subprocess.run(
            cmd,
            check=True,
            cwd=self.repo,
            capture_output=silent,
        )

    def run_stdout(self, *cmd: Arg) -> str:
        print("$ " + " ".join(shlex.quote(str(arg)) for arg in cmd))
        return subprocess.run(
            cmd,
            check=True,
            cwd=self.repo,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout


def _bwrap_bind(path: Path) -> list[Arg]:
    path = path.resolve()
    return ["--bind", path, path]


def _bwrap_ro_bind(path: Path) -> list[Arg]:
    path = path.resolve()
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
            self._add_ro_bind(Path("/lib"))
            self._add_ro_bind(Path("/lib64"))
            self._add_ro_bind(Path("/usr"))

        self._add_ro_bind(Path.home() / ".elan")

    def _add_args(self, *args: Arg) -> None:
        self.args.extend(args)

    def _add_ro_bind(self, path: Path) -> None:
        self.args.extend(_bwrap_ro_bind(path))

    def _args_for_cmd(self, cmd: tuple[Arg, ...]) -> list[Arg]:
        args = list(self.args)
        args.extend(_bwrap_bind(self.repo))
        args.extend(_bwrap_ro_bind(self.repo / ".git"))
        args.extend(("--chdir", self.repo))
        args.append("--")
        args.extend(cmd)
        return args

    def run(self, *cmd: Arg, silent: bool = False) -> None:
        print("$ " + " ".join(shlex.quote(str(arg)) for arg in cmd))
        subprocess.run(
            self._args_for_cmd(cmd=cmd),
            check=True,
            cwd=self.repo,
            capture_output=silent,
        )

    def run_stdout(self, *cmd: Arg) -> str:
        print("$ " + " ".join(shlex.quote(str(arg)) for arg in cmd))
        return subprocess.run(
            self._args_for_cmd(cmd=cmd),
            check=True,
            cwd=self.repo,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout


def get_sandbox(repo: Path, bubblewrap: bool, bubblewrap_nixos: bool) -> Sandbox:
    if bubblewrap:
        return BubblewrapSandbox(repo=repo, nixos=bubblewrap_nixos)
    else:
        return NoSandbox(repo=repo)
