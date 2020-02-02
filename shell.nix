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
in
pkgs.mkShell {
  buildInputs = [
    scripts
  ];
}
