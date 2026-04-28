from dataclasses import dataclass
from typing import Any

from impeller.cmd import CommandContext
from impeller.util import (
    check_for_command,
    get_current_sha,
    get_toolchain,
    now,
    switch_to_ref,
    test_command,
)


@dataclass
class CmdBuildVersion:
    ctx: CommandContext
    rev: str | None
    build: bool | None
    test: bool | None
    lint: bool | None

    def get_data(self) -> dict[str, Any]:
        if self.rev is not None:
            switch_to_ref(self.ctx.repo, self.rev)

        sha = get_current_sha(self.ctx.repo)
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
            "sha": sha,
            "check_build": check_build,
            "check_test": check_test,
            "check_lint": check_lint,
            "build": build,
            "test": test,
            "lint": lint,
        }
