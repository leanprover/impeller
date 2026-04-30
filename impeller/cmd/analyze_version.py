import json
import subprocess
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

from impeller.cmd import CommandContext
from impeller.cmd.build_version import check_for_command
from impeller.reservoir_config import ReservoirConfig
from impeller.util import (
    get_active_toolchain,
    get_current_sha,
    get_toolchain,
    switch_to_ref,
)


@dataclass
class CmdAnalyzeVersion:
    ctx: CommandContext
    rev: str | None

    def get_manifest(self) -> Any | None:
        manifest_file = self.ctx.repo / "lake-manifest.json"
        try:
            return json.loads(manifest_file.read_text())
        except FileNotFoundError, JSONDecodeError:
            return

    def get_lake_metadata(self) -> dict[str, Any] | None:
        try:
            config_json = self.ctx.box.run_stdout("lake", "reservoir-config")
        except subprocess.CalledProcessError:
            return

        config = ReservoirConfig.parse(config_json, self.ctx.repo)

        # Only the version-specific fields, not the global ones
        return {
            "license": config.license,
            "license_files": config.license_files,
            "platform_independent": config.platform_independent,
            "readme_file": config.readme_file,
            "version": config.version,
        }

    def get_data(self) -> dict[str, Any]:
        if self.rev is not None:
            switch_to_ref(self.ctx.repo, self.rev)

        sha = get_current_sha(self.ctx.repo)
        toolchain = get_toolchain(self.ctx.repo)
        active_toolchain = get_active_toolchain(self.ctx.repo)
        manifest = self.get_manifest()
        lake = self.get_lake_metadata()
        check_build = check_for_command(self.ctx.box, "build")
        check_test = check_for_command(self.ctx.box, "test")
        check_lint = check_for_command(self.ctx.box, "lint")

        return {
            "version": "v0",
            "sha": sha,
            "toolchain": toolchain,
            "active_toolchain": active_toolchain,
            "manifest": manifest,
            "lake": lake,
            "check_build": check_build,
            "check_test": check_test,
            "check_lint": check_lint,
        }
