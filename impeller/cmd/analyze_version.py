import json
import subprocess
from dataclasses import dataclass
from typing import Any

from impeller.cmd import CommandContext
from impeller.reservoir_config import ReservoirConfig
from impeller.util import (
    clone_and_prepare_repo,
    get_active_toolchain,
    get_toolchain,
    install_toolchain,
    now,
    run_stdout,
    switch_to_ref,
)


@dataclass
class CmdAnalyzeVersion:
    ctx: CommandContext
    rev: str | None

    def fetch_git_metadata(self) -> dict[str, Any]:
        data = {}

        if self.rev:
            data["sha"] = self.rev
        else:
            try:
                data["sha"] = run_stdout(
                    "git", "rev-parse", "HEAD", cwd=self.ctx.repo
                ).strip()
            except Exception as e:
                print("Error fetching sha:", e)

        return data

    def fetch_lake_metadata(self) -> dict[str, Any] | None:
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

    def fetch_manifest(self) -> Any:
        manifest_file = self.ctx.repo / "lake-manifest.json"
        return json.loads(manifest_file.read_text())

    def check(self, name: str) -> bool | None:
        try:
            result = self.ctx.box.run(
                "lake", f"check-{name}", check=False, capture=True
            )
            if result.returncode == 0:
                return True
            if "unknown command" in result.stderr:
                return None
            return False
        except Exception as e:
            print(f"Error checking for {name}:", e)
            return None

    def do(self, name: str) -> bool:
        try:
            self.ctx.box.run("lake", name)
            return True
        except Exception as e:
            print(f"Error running {name}:", e)
            return False

    def get_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}

        try:
            data["metadata_git"] = self.fetch_git_metadata()
        except Exception as e:
            print("Error fetching git metadata:", e)

        toolchain = get_toolchain(self.ctx.repo)
        data["toolchain"] = toolchain

        try:
            if self.ctx.url:
                clone_and_prepare_repo(repo=self.ctx.repo, url=self.ctx.url)
            if self.rev:
                switch_to_ref(self.ctx.repo, self.rev)
            if toolchain is not None:
                install_toolchain(toolchain)
        except Exception as e:
            print("Error setting up repo:", e)
            return data

        try:
            data["active_toolchain"] = get_active_toolchain(self.ctx.repo)
        except Exception as e:
            print("Error fetching active toolchain:", e)
            return data

        try:
            data["metadata_lake"] = self.fetch_lake_metadata()
        except Exception as e:
            print("Error fetching lake metadata:", e)

        try:
            data["manifest"] = self.fetch_manifest()
        except Exception as e:
            print("Error fetching manifest:", e)

        check_build = self.check("build")
        build = None
        if check_build != False:  # noqa: E712
            data["build_start"] = now()
            build = self.do("build")
            data["build_end"] = now()
        data["check_build"] = check_build
        data["build"] = build

        check_test = self.check("test")
        test = None
        if check_test != False and build:  # noqa: E712
            data["test_start"] = now()
            test = self.do("test")
            data["test_end"] = now()
        data["check_test"] = check_test
        data["test"] = test

        check_lint = self.check("lint")
        lint = None
        if check_lint != False and build:  # noqa: E712
            data["lint_start"] = now()
            lint = self.do("lint")
            data["lint_end"] = now()
        data["check_lint"] = check_lint
        data["lint"] = lint

        return data
