"""
This module documents and implements the output formats of the different commands.
Each command has its own output class that can be serialized into JSON.
See the README for how the versions work.
"""

import importlib.metadata
import json
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

############
## Common ##
############


@dataclass(kw_only=True)
class Output:
    """Fields shared by the output of all commands."""

    VERSION: ClassVar[str]

    version: str = field(init=False)
    """Output version of the command, in the form `<major>.<minor>`."""

    app_version: str = field(init=False)
    """Application version of impeller, in the form `<major>.<minor>.<patch>`."""

    started: str = ""
    """When the command was started, as an RFC 3339 timestamp."""

    finished: str = ""
    """When the command finished, as an RFC 3339 timestamp."""

    def __post_init__(self) -> None:
        self.version = self.VERSION
        self.app_version = importlib.metadata.version("impeller")

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class Toolchain:
    declared: str | None
    """Toolchain specified in the `lean-toolchain` file, if any."""

    active: str | None
    """Toolchain reported as active by `elan show`, if any."""

    githash: str | None
    """Output of `lean --githash`, if the command succeeded."""


####################
## analyze-global ##
####################


@dataclass
class GlobalGit:
    default_branch: str
    """Name of the remote's default branch."""

    default_branch_sha: str
    """Current commit hash of the remote's default branch."""

    version_tags: list[str]
    """All git tags starting with `v`."""

    tag_shas: dict[str, str]
    """
    Commit hashes of all git and lake version tags.
    Tags that could not be resolved are omitted.
    """


@dataclass
class GlobalLake:
    """The global fields of `lake reservoir-config`."""

    description: str
    do_index: bool
    homepage: str
    keywords: list[str]
    name: str
    version_tags: list[str]


@dataclass
class GlobalGitHub:
    """A subset of the repository information returned by the GitHub API."""

    name: str
    full_name: str
    owner: str
    description: str | None
    fork: bool
    html_url: str
    clone_url: str
    homepage: str | None
    forks_count: int
    stargazers_count: int
    subscribers_count: int
    default_branch: str
    topics: list[str]
    archived: bool
    disabled: bool
    pushed_at: str
    created_at: str
    updated_at: str
    license_spdx_id: str | None


@dataclass(kw_only=True)
class AnalyzeGlobalOutput(Output):
    """Output of `impeller analyze-global`."""

    VERSION = "0.0"

    toolchain: Toolchain
    git: GlobalGit

    lake: GlobalLake | None
    """Null if `lake reservoir-config` failed."""

    github: GlobalGitHub | None
    """Null if external metadata was not requested or could not be fetched."""


#####################
## analyze-version ##
#####################


@dataclass
class VersionLake:
    """The version-specific fields of `lake reservoir-config`."""

    license: str | None
    license_files: list[str]
    platform_independent: bool | None
    readme_file: str | None
    version: str


@dataclass(kw_only=True)
class AnalyzeVersionOutput(Output):
    """Output of `impeller analyze-version`."""

    VERSION = "0.0"

    sha: str
    """Commit that was analyzed."""

    toolchain: Toolchain

    manifest: Any | None
    """Contents of `lake-manifest.json` verbatim, null if missing or invalid."""

    lake: VersionLake | None
    """Null if `lake reservoir-config` failed."""

    check_build: bool | None
    """
    Result of `lake check-build`.
    True if `lake build` is available, false if not.
    Null if this version of lake does not support the `check_build` command.
    """

    check_test: bool | None
    """
    Result of `lake check-test`.
    True if `lake test` is available, false if not.
    Null if this version of lake does not support the `check_test` command.
    """

    check_lint: bool | None
    """
    Result of `lake check-lint`.
    True if `lake lint` is available, false if not.
    Null if this version of lake does not support the `check_lint` command.
    """


###################
## build-version ##
###################


@dataclass
class BuildStep:
    success: bool
    """True if the build step was executed successfully, false otherwise."""

    started: str
    """When the step was started, as an RFC 3339 timestamp."""

    finished: str
    """When the step finished, as an RFC 3339 timestamp."""


@dataclass(kw_only=True)
class BuildVersionOutput(Output):
    """Output of `impeller build-version`."""

    VERSION = "0.0"

    sha: str
    """Commit that was built."""

    toolchain: Toolchain

    check_build: bool | None
    """
    Result of `lake check-build`.
    True if `lake build` is available, false if not.
    Null if this version of lake does not support the `check_build` command.
    """

    check_test: bool | None
    """
    Result of `lake check-test`.
    True if `lake test` is available, false if not.
    Null if this version of lake does not support the `check_test` command.
    """

    check_lint: bool | None
    """
    Result of `lake check-lint`.
    True if `lake lint` is available, false if not.
    Null if this version of lake does not support the `check_lint` command.
    """

    build: BuildStep | None
    """Result of `lake build`, null if it was skipped."""

    test: BuildStep | None
    """Result of `lake test`, null if it was skipped."""

    lint: BuildStep | None
    """Result of `lake lint`, null if it was skipped."""
