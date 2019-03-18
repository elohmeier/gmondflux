with import <nixpkgs> {};

let
  python3 = pkgs.python3;
  altgraph = python3.pkgs.callPackage ./deps/altgraph.nix { };
  macholib = python3.pkgs.callPackage ./deps/macholib.nix { altgraph = altgraph; };
  pefile = python3.pkgs.callPackage ./deps/pefile.nix { };
  pyinstaller = python3.pkgs.callPackage ./deps/pyinstaller.nix { 
    altgraph = altgraph;
    macholib = macholib;
    pefile = pefile; 
  };
in
python3.withPackages (pythonPackages: with pythonPackages; [
  black
  flake8
  gevent
  influxdb
  jupyterlab
  pytest
  pyinstaller
])

