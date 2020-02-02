{ pkgs ? import <nixpkgs> {} }:

let
  scripts = [
    (
      pkgs.writeShellScriptBin "mk-pretty" ''
        black .
        nixpkgs-fmt .
      ''
    )
    (pkgs.writeShellScriptBin "mk-venv" "nix-build -o venv -A env pyenv.nix")
  ];
  ganglia = pkgs.callPackage ./deps/ganglia.nix {};
  pyenv = pkgs.callPackage ./pyenv.nix {};
in
pkgs.mkShell {
  buildInputs = [
    ganglia
    scripts
    pkgs.telegraf
    pyenv.env
  ];
}
