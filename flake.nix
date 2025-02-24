{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
    treefmt-nix.url = "github:numtide/treefmt-nix";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    systems,
    poetry2nix,
    treefmt-nix,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin"];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});

    # https://github.com/pyproject-nix/uv2nix/blob/master/templates/hello-world/flake.nix
    workspace = uv2nix.lib.workspace.loadWorkspace {workspaceRoot = ./.;};
    overlay = workspace.mkPyprojectOverlay {
      sourcePreference = "wheel"; # or sourcePreference = "sdist";
    };

    python3 = forAllSystems (system: pkgs.${system}.python312);

    pythonSet = forAllSystems (system: let
      python = python3.${system};
      lib = pkgs.${system}.lib;
    in
      (pkgs.${system}.callPackage pyproject-nix.build.packages {
        inherit python;
      })
      .overrideScope
      (
        lib.composeManyExtensions [
          pyproject-build-systems.overlays.default
          overlay
          #   pyprojectOverrides
        ]
      ));

    treefmtEval = forAllSystems (system: treefmt-nix.lib.evalModule nixpkgs.legacyPackages.${system} ./treefmt.nix);
  in {
    packages = forAllSystems (system: {
      default = pythonSet.${system}.mkVirtualEnv "rebuildr" workspace.deps.default;
    });

    formatter = forAllSystems (system: treefmtEval.${system}.config.build.wrapper);

    devShells = forAllSystems (system: let
      inherit (poetry2nix.lib.mkPoetry2Nix {pkgs = pkgs.${system};}) mkPoetryEnv;
    in {
      default = pkgs.${system}.mkShellNoCC {
        packages = with pkgs.${system}; [
          uv
        ];

        env = {
          # Don't create venv using uv
          UV_NO_SYNC = "1";

          # Force uv to use Python interpreter from venv
          UV_PYTHON = "${python3.${system}}/bin/python";

          # Prevent uv from downloading managed Python's
          UV_PYTHON_DOWNLOADS = "never";
        };
      };
    });
  };
}
