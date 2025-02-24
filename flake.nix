{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = {
    self,
    nixpkgs,
    systems,
    poetry2nix,
    treefmt-nix,
    flake-parts,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin"];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});

    eachSystem = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

    treefmtEval = forAllSystems (system: treefmt-nix.lib.evalModule nixpkgs.legacyPackages.${system} ./treefmt.nix);
  in {
    packages = forAllSystems (system: let
      inherit (poetry2nix.lib.mkPoetry2Nix {pkgs = pkgs.${system};}) mkPoetryApplication;
    in {
      default = pkgs.${system}.bashInteractive;
    });
    formatter = forAllSystems (system: treefmtEval.${system}.config.build.wrapper);

    devShells = forAllSystems (system: let
      inherit (poetry2nix.lib.mkPoetry2Nix {pkgs = pkgs.${system};}) mkPoetryEnv;
    in {
      default = pkgs.${system}.mkShellNoCC {
        packages = with pkgs.${system}; [
          (mkPoetryEnv {projectDir = self;})
          poetry
        ];
      };
    });
  };
}
