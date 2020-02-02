{ pkgs ? import <nixpkgs> {} }:

rec {
  py3 = pkgs.python3.override {
    packageOverrides = self: super: {};
  };
  pyPkgs = pythonPackages: with pythonPackages; [
    black
    flake8
    pytest
  ];
  env = py3.withPackages (
    pyPkgs
  );
}
