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
