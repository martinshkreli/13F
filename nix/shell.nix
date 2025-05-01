# shell.nix
{ pkgs ? import <nixpkgs> {} }:

let
  pkgs = if builtins.getEnv "NIX_PATH" != "" then
    import <nixpkgs> {}
  else
  # lets try and add a let here to get the commit hash
    (import (fetchTarball { 
      url = "https://github.com/NixOS/nixpkgs/archive/da044451c6a70518db5b730fe277b70f494188f1.tar.gz";
      sha256 = "sha256:11z08fa0s7r9hryllhjj7kyn4z6bsixlqz7iwgsmf1k4p3hcl692";
    }) { }).pkgs;
in

(pkgs.buildFHSEnv {
  name = "simpleFHS";
  targetPkgs = pkgs: (with pkgs; [
    cmake
    python312Packages.cmake
  ]);
  multiPkgs = pkgs: (with pkgs; [
    cmake
    python312Packages.cmake
  ]);
  runScript = "nix-shell nix/pyenv.nix";
}).env
