# Impeller

A command-line tool for analyzing and building individual lake packages.
Impeller can extract metadata from lake packages or build and test them. The
results are output as JSON data.

Impeller has three main commands for extracting information from a lake package:

- `analyze-global`: Retrieve global metadata from a lake package.
- `analyze-version`: Retrieve version-specific metadata from a lake package.
- `build-version`: Attempt to build, test, and lint a specific version of a lake
  package.

For more information, see `impeller --help` and `impeller <command> --help`.

## Versioning

Impeller has two kinds of version number, the _application version_ and the
_output version_.

The **application version** describes impeller itself. It is specified in
[`pyproject.toml`](pyproject.toml) and consists of a _major_, _minor_, and
_patch_ part that function according to normal semver. Examples for _major_
increments are CLI flags being removed or output fields being renamed. Examples
for _minor_ increments are CLI flags or output fields being added. Examples for
_patch_ increments are bug fixes.

The **output version** describes the JSON output of impeller's commands. Each
command has its own output version. It consists of a _major_ and a _minor_ part.
The _major_ part is incremented whenever the output format changes in a
backwards-incompatible way, e.g. a field is renamed or removed. The _minor_ part
is incremented whenever the output changes in a backwards-compatible way, e.g. a
field is added. Impeller expects consumers of its output to ignore any fields
they do not understand.

As a corollary, if a release increments any _output version's_ major part, it
must also increment the _application version's_ major part. The same is true for
minor parts.
