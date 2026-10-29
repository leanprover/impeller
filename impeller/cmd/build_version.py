from dataclasses import dataclass

from impeller.cmd import CommandContext
from impeller.output import BuildStep, BuildVersionOutput
from impeller.sandbox import Sandbox
from impeller.util import (
    get_current_sha,
    get_toolchain,
    get_toolchain_metadata,
    install_toolchain,
    now,
    switch_to_ref,
)


def check_for_command(box: Sandbox, name: str) -> bool | None:
    try:
        result = box.run("lake", f"check-{name}", check=False, capture=True)
        if result.returncode == 0:
            return True
        if "unknown command" in result.stderr:
            return None
        return False
    except Exception as e:  # noqa: BLE001
        print(f"Error checking for {name}:", e)
        return None


def test_command(box: Sandbox, name: str) -> bool:
    try:
        box.run("lake", name)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"Error running {name}:", e)
        return False


@dataclass
class CmdBuildVersion:
    ctx: CommandContext
    rev: str | None
    override_toolchain: str | None
    build: bool | None
    test: bool | None
    lint: bool | None

    def get_output(self) -> BuildVersionOutput:
        if self.rev is not None:
            switch_to_ref(self.ctx.repo, self.rev)
        if self.override_toolchain is not None:
            toolchain_file = self.ctx.repo / "lean-toolchain"
            toolchain_file.write_text(self.override_toolchain + "\n")
        if toolchain := get_toolchain(self.ctx.repo):
            install_toolchain(toolchain)

        sha = get_current_sha(self.ctx.repo)
        toolchain = get_toolchain_metadata(self.ctx.repo)
        check_build = check_for_command(self.ctx.box, "build")
        check_test = check_for_command(self.ctx.box, "test")
        check_lint = check_for_command(self.ctx.box, "lint")

        build = None
        if self.build is True or (self.build is None and check_build is not False):
            started = now()
            self.ctx.box.run("lake", "exe", "cache", "get", check=False)
            success = test_command(self.ctx.box, "build")
            finished = now()
            build = BuildStep(success=success, started=started, finished=finished)

        test = None
        if self.test is True or (self.test is None and check_test is not False):
            started = now()
            success = test_command(self.ctx.box, "test")
            finished = now()
            test = BuildStep(success=success, started=started, finished=finished)

        lint = None
        if self.lint is True or (self.lint is None and check_lint is not False):
            started = now()
            success = test_command(self.ctx.box, "lint")
            finished = now()
            lint = BuildStep(success=success, started=started, finished=finished)

        return BuildVersionOutput(
            sha=sha,
            toolchain=toolchain,
            check_build=check_build,
            check_test=check_test,
            check_lint=check_lint,
            build=build,
            test=test,
            lint=lint,
        )
