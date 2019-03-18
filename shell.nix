let
  pkgs = import <nixpkgs> {};
  venv = import ./env.nix;
  ganglia = pkgs.callPackage ./deps/ganglia.nix {};
in
  pkgs.mkShell {
    name = "gmondflux";
    buildInputs = [
      pkgs.influxdb
      ganglia
      venv
    ];

    # Keep project-specific shell commands local
    HISTFILE = "${toString ./.}.bash_history";

    shellHook = ''
      function ci_check() (
        black --check .
      )

      echo "gmondflux" | ${pkgs.figlet}/bin/figlet | ${pkgs.lolcat}/bin/lolcat
    '';
  }


