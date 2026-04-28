import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from github import Auth, Github

from impeller.cmd import CommandContext
from impeller.reservoir_config import ReservoirConfig
from impeller.util import run_stdout


@dataclass
class CmdAnalyzeGlobal:
    ctx: CommandContext
    fetch_external_metadata: bool
    github_token_file: Path | None
    github_token_gh: bool

    def get_git_metadata(self) -> dict[str, Any]:
        tags = run_stdout("git", "tag", "--list", "v*", cwd=self.ctx.repo).splitlines()

        return {
            "version_tags": tags,
        }

    def get_lake_metadata(self) -> dict[str, Any] | None:
        try:
            config_json = self.ctx.box.run_stdout("lake", "reservoir-config")
        except subprocess.CalledProcessError:
            return

        config = ReservoirConfig.parse(config_json, self.ctx.repo)

        # Only the global fields, not the version-specific ones
        return {
            "description": config.description,
            "do_index": config.do_index,
            "homepage": config.homepage,
            "keywords": config.keywords,
            "name": config.name,
            "version_tags": config.version_tags,
        }

    def resolve_version_tags(
        self, git: dict[str, Any], lake: dict[str, Any] | None
    ) -> None:
        all_tags = set[str]()
        all_tags.update(git["version_tags"])
        all_tags.update((lake or {}).get("version_tags", []))

        tag_shas: dict[str, str] = {}
        for tag in sorted(all_tags):
            try:
                # https://stackoverflow.com/a/16818141
                stdout = run_stdout(
                    "git", "rev-parse", f"{tag}^{{}}", cwd=self.ctx.repo
                )
                tag_shas[tag] = stdout.strip()
            except subprocess.CalledProcessError:
                pass

        git["tag_shas"] = tag_shas

    def get_github_token(self) -> str | None:
        if self.github_token_gh:
            return run_stdout("gh", "auth", "token").strip()
        if self.github_token_file:
            return self.github_token_file.read_text().strip()

    def get_github_fullname(self) -> str | None:
        if self.ctx.url is None:
            return
        match = re.fullmatch(
            r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
            r"([^/]+/[^/.]+?)(?:\.git)?/?",
            self.ctx.url,
        )
        if not match:
            return
        fullname: str = match.group(1)
        return fullname

    def get_github_metadata(self) -> dict[str, Any] | None:
        if not self.fetch_external_metadata:
            return

        token = self.get_github_token()
        if not token:
            return

        fullname = self.get_github_fullname()
        if not fullname:
            return

        g = Github(auth=Auth.Token(token))
        r = g.get_repo(fullname)

        # A reasonable subset of the fields returned by the GitHub API
        # https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10#get-a-repository
        return {
            "name": r.name,
            "full_name": r.full_name,
            "owner": r.owner.login,
            "description": r.description,
            "fork": r.fork,
            "html_url": r.html_url,
            "clone_url": r.clone_url,
            "homepage": r.homepage,
            "forks_count": r.forks_count,
            "stargazers_count": r.stargazers_count,
            "subscribers_count": r.subscribers_count,
            "default_branch": r.default_branch,
            "topics": r.topics,
            "archived": r.archived,
            "disabled:": r.disabled,
            "pushed_at": r.pushed_at.isoformat(),
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "license_spdx_id": r.license.spdx_id,
        }

    def get_data(self) -> dict[str, Any]:
        git = self.get_git_metadata()
        lake = self.get_lake_metadata()
        github = self.get_github_metadata()

        self.resolve_version_tags(git, lake)

        return {
            "version": "v0",
            "git": git,
            "lake": lake,
            "github": github,
        }
