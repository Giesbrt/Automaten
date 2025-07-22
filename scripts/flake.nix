{
  description = "Dev env for Automaton on NixOS";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    python = pkgs.python313;

    pythonEnv = python.withPackages (ps: with ps; [
      pip
      numpy
      pyside6
      pyyaml
      pytest
      requests
      urllib3
      stdlib-list
      pyinstaller
    ]);
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [
        pythonEnv
        pkgs.qt6.full
        pkgs.gcc
        pkgs.glibc
        pkgs.fontconfig
      ];

      shellHook = ''
        export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins"
        export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.fontconfig}/lib:$LD_LIBRARY_PATH"
        export PYTHONNOUSERSITE="true"
        # echo "Dev shell ready."
      '';
    };
  };
}
