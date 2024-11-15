{
  description = "A basic flake with a shell";

  # --- Flake Local Nix Configuration ----------------------------
  nixConfig = {
    # This sets the flake to use the IOG nix cache.
    # Nix should ask for permission before using it,
    # but remove it here if you do not want it to.
    experimental-features = [ "nix-command" "flakes" ];
  };

  inputs = {
    # nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs.url = "github:qbisi/nixpkgs/ngsolve";
    # nixpkgs.url = "git+file:/home/qbisi/nixpkgs?branch=netgen";
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      perSystem =
        {
          config,
          pkgs,
          system,
          self',
          ...
        }:
        {
          _module.args = {
            pkgs = import inputs.nixpkgs {
              inherit system;
              overlays = [
                (final: prev: {
                  # stdenv = prev.stdenv.overrideAttrs { avxSupport = true; };
                  netgen = prev.netgen.override { avxSupport = true; };
                })
              ];
              config = { };
            };
          };
          devShells = rec {
            default = pkgs.mkShell {
              packages = [ self'.packages.ngsolve-env ];
              shellHook = ''
                # export PYTHONPATH=$PWD/.pip:$PYTHONPATH
                rm -rf .python-env
                ln -s ${self'.packages.ngsolve-env} .python-env
              '';
            };
          };

          packages = {
            inherit (pkgs) netgen ngsolve;

            webgui-jupyter-widget = pkgs.python312Packages.callPackage ./webgui-jupyter-widget.nix { };

            ngsolve-env = pkgs.jupyter.withPackages (
              ps: with ps; [
                ngsolve
                # matplotlib
                notebook
                ipykernel
                pytest
                pip
                self'.packages.webgui-jupyter-widget
              ]
            );
          };

          formatter = pkgs.nixfmt-rfc-style;
        };
    };
}
