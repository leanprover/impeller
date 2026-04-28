{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    inputs:
    let
      lib = inputs.nixpkgs.lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = inputs.nixpkgs.legacyPackages.${system};
          pypkgs = pkgs.python314Packages;
          pyproject = lib.importTOML ./pyproject.toml;
        in
        {
          default = pypkgs.buildPythonApplication {
            pname = pyproject.project.name;
            version = pyproject.project.version;
            src = ./.;
            pyproject = true;
            build-system = [ pypkgs.setuptools ];
            dependencies = [ pypkgs.pygithub ];
          };
        }
      );
    };
}
