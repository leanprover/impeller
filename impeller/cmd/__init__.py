from dataclasses import dataclass
from pathlib import Path

from impeller.sandbox import Sandbox


@dataclass
class CommandContext:
    repo: Path
    url: str | None
    output: Path
    box: Sandbox
