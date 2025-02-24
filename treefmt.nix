# treefmt.nix
{pkgs, ...}: {
  # Used to find the project root
  projectRootFile = "flake.nix";

  # python
  programs.ruff-format.enable = true;
  # nix
  programs.alejandra.enable = true;
  # toml
  programs.taplo.enable = true;
  # yaml
  programs.yamlfmt.enable = true;
}
