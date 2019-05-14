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

      alias cd..="cd .."
      alias l="ls -laF"
      alias ll="ls -l"
      alias la="ls -la"
      alias gs="git status"
      alias gc="git commit"
      alias ga="git add"
      alias ga.="git add ."
      alias gco="git checkout"
      alias gp="git pull"
      alias gpp"git push"

      echo "gmondflux" | ${pkgs.figlet}/bin/figlet | ${pkgs.lolcat}/bin/lolcat
    '';
  }


