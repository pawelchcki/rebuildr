# Contributing to Rebuildr

First off, thank you for considering contributing to Rebuildr! It's people like you that will make rebuildr the future of building docker images.

## How to Contribute

## Setting Up the Development Environment

We use [Nix](https://nixos.org/) to provide a consistent development environment.

1.  **Install Nix**: Follow the instructions on the [official Nix website](https://nixos.org/download.html) to install Nix on your system.
2.  **Enable Flakes**: Make sure you have Nix Flakes enabled. You can do this by adding `experimental-features = nix-command flakes` to your Nix configuration file.
3.  **Enter the Development Shell**: Run `nix develop` in the project root. This will drop you into a shell with all the necessary dependencies.
4.  **[OPTIONAL] Install Python dependencies**: If nix is not your thinkg - We use `uv` to manage python dependencies. 

Now you should be all set to start developing!
