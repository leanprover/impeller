import json
from dataclasses import dataclass
from typing import Any, Callable, Self


def as_str(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(f"expected a string, got {type(value).__name__}")
    return value


def as_bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"expected a boolean, got {type(value).__name__}")
    return value


def as_none_or[T](as_func: Callable[[Any], T], value: Any) -> T | None:
    if value is None:
        return None
    return as_func(value)


def as_list_of[T](as_func: Callable[[Any], T], value: Any) -> list[T]:
    if not isinstance(value, list):
        raise ValueError(f"expected a list, got {type(value).__name__}")
    return [as_func(item) for item in value]


@dataclass
class ReservoirConfig:
    # Global
    description: str
    do_index: bool
    homepage: str
    keywords: list[str]
    name: str
    platform_independent: bool | None
    version_tags: list[str]
    # Version-specific
    license: str
    license_files: list[str]
    readme_file: str
    version: str

    @classmethod
    def parse(cls, json_str: str) -> Self:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")

        schema_version = data.get("schemaVersion")
        if schema_version != "1.0.0":
            raise ValueError(f"unsupported schema version: {schema_version}")

        return cls(
            description=as_str(data.get("description")),
            do_index=as_bool(data.get("doIndex")),
            homepage=as_str(data.get("homepage")),
            keywords=as_list_of(as_str, data.get("keywords")),
            license=as_str(data.get("license")),
            license_files=as_list_of(as_str, data.get("licenseFiles")),
            name=as_str(data.get("name")),
            platform_independent=as_none_or(as_bool, data.get("platformIndependent")),
            readme_file=as_str(data.get("readmeFile")),
            version=as_str(data.get("version")),
            version_tags=as_list_of(as_str, data.get("versionTags")),
        )
