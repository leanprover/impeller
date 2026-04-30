from dataclasses import dataclass
from typing import Any

from impeller.cmd import CommandContext
from impeller.sandbox import Sandbox
from impeller.util import (
    get_active_toolchain,
    get_current_sha,
    get_toolchain,
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
    except Exception as e:
        print(f"Error checking for {name}:", e)
        return None


def test_command(box: Sandbox, name: str) -> bool:
    try:
        box.run("lake", name)
        return True
    except Exception as e:
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

    def get_data(self) -> dict[str, Any]:
        if self.rev is not None:
            switch_to_ref(self.ctx.repo, self.rev)

        if self.override_toolchain is not None:
            toolchain_file = self.ctx.repo / "lean-toolchain"
            toolchain_file.write_text(self.override_toolchain + "\n")

        sha = get_current_sha(self.ctx.repo)
        toolchain = get_toolchain(self.ctx.repo)
        active_toolchain = get_active_toolchain(self.ctx.repo)
        check_build = check_for_command(self.ctx.box, "build")
        check_test = check_for_command(self.ctx.box, "test")
        check_lint = check_for_command(self.ctx.box, "lint")

        build = None
        if self.build is True or (self.build is None and check_build is not False):
            started = now()
            success = test_command(self.ctx.box, "build")
            finished = now()
            build = {"success": success, "started": started, "finished": finished}

        test = None
        if self.test is True or (self.test is None and check_test is not False):
            started = now()
            success = test_command(self.ctx.box, "test")
            finished = now()
            test = {"success": success, "started": started, "finished": finished}

        lint = None
        if self.lint is True or (self.lint is None and check_lint is not False):
            started = now()
            success = test_command(self.ctx.box, "lint")
            finished = now()
            lint = {"success": success, "started": started, "finished": finished}

        return {
            "version": "v0",
            "sha": sha,
            "toolchain": toolchain,
            "active_toolchain": active_toolchain,
            "check_build": check_build,
            "check_test": check_test,
            "check_lint": check_lint,
            "build": build,
            "test": test,
            "lint": lint,
        }
