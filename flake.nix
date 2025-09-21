{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    pre-commit-hooks.url = "github:cachix/git-hooks.nix";
    pre-commit-hooks.inputs.nixpkgs.follows = "nixpkgs";
    nix-github-actions.url = "github:nix-community/nix-github-actions";
    nix-github-actions.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    systems,
    treefmt-nix,
    pre-commit-hooks,
    nix-github-actions,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin"];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});
    python3 = forAllSystems (system: pkgs.${system}.python310);
    python3Packages = forAllSystems (system: python3.${system}.pkgs);
    treefmtEval = forAllSystems (system: treefmt-nix.lib.evalModule nixpkgs.legacyPackages.${system} ./treefmt.nix);

    rebuildr = forAllSystems (
      system: attrs:
        python3.${system}.pkgs.buildPythonApplication {
          pname = "rebuildr";
          version = "0.2-dev";

          inherit (attrs) doCheck;

          src = ./.;
          format = "pyproject";

          build-system = with python3Packages.${system}; [
            hatchling
          ];

          checkInputs = with python3Packages.${system}; [
            pytest
            pytestCheckHook
          ];

          propagatedBuildInputs = with pkgs.${system}; [
            skopeo
          ];
        }
    );
  in {
    githubActions = nix-github-actions.lib.mkGithubMatrix {inherit (self) checks;};
    packages = forAllSystems (system: {
      default = rebuildr.${system} {
        doCheck = false;
      };

      docker-image = pkgs.${system}.dockerTools.buildImage {
        name = "rebuildr";
        tag = "latest";

        copyToRoot = pkgs.${system}.buildEnv {
          name = "image-root";
          paths = [self.packages.${system}.default];
          pathsToLink = ["/bin"];
        };

        config = {
          Cmd = ["/bin/rebuildr"];
          WorkingDir = "/";
        };
      };
    });

    formatter = forAllSystems (system: treefmtEval.${system}.config.build.wrapper);

    checks = forAllSystems (system: {
      default = rebuildr.${system} {
        doCheck = true;
      };

      pre-commit-check = pre-commit-hooks.lib.${system}.run {
        src = ./.;
        hooks = {
          # nixpkgs-fmt.enable = true;
          treefmt.package = treefmtEval.${system}.config.build.wrapper;
          treefmt.enable = true;
        };
      };
    });

    devShells = forAllSystems (system: let
      _pkgs = pkgs.${system};
    in {
      default = _pkgs.mkShellNoCC {
        inherit (self.checks.${system}.pre-commit-check) shellHook;

        packages = with _pkgs; [
          uv
          git
          bazel_5
          jdk11_headless
        ];

        buildInputs = self.checks.${system}.pre-commit-check.enabledPackages;

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
