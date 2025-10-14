{
  description = "Dev env for Automaton on NixOS";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    #python = pkgs.python313;

    #pythonEnv = python.withPackages (ps: with ps; [
      #pip
      #numpy
      # pyside6
      # pyyaml
      # pytest
      # requests
      # urllib3
      # stdlib-list
      # pyinstaller
    #]);
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [
        #pythonEnv
        # pkgs.qt6.full
        pkgs.gcc
        pkgs.glibc
        pkgs.fontconfig
        pkgs.freetype
        pkgs.python3

        pkgs.xorg.libX11
        pkgs.xorg.libXext
        pkgs.xorg.libXrender
        pkgs.xorg.libXrandr
        pkgs.xorg.libxcb

        pkgs.glib
        pkgs.gobject-introspection
        pkgs.gtk3  # includes common supporting libs like pango, cairo

        pkgs.libxkbcommon

        pkgs.zstd

        pkgs.dbus
        pkgs.libuuid

        # X11 + xcb deps
        pkgs.xorg.libXfixes
        pkgs.xorg.libXi
        pkgs.xorg.libSM
        pkgs.xorg.libICE

        # Qt xcb plugin deps
        pkgs.xorg.xcbutil
        pkgs.xorg.xcbutilimage
        pkgs.xorg.xcbutilkeysyms
        pkgs.xorg.xcbutilrenderutil
        pkgs.xorg.xcbutilwm
        pkgs.xorg.xcbutilcursor
      ];

      shellHook = ''
        export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins"
        # export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.fontconfig}/lib:$LD_LIBRARY_PATH"
        # Automatically collect all library paths
        export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
          # pkgs.qt6.full
          pkgs.fontconfig
          pkgs.freetype
          pkgs.gcc
          pkgs.stdenv.cc.cc.lib
          pkgs.glibc

          pkgs.xorg.libX11
          pkgs.xorg.libXext
          pkgs.xorg.libXrender
          pkgs.xorg.libXrandr
          pkgs.xorg.libxcb

          pkgs.glib
          pkgs.gobject-introspection
          pkgs.gtk3  # includes common supporting libs like pango, cairo

          pkgs.libxkbcommon

          pkgs.zstd

          pkgs.dbus
          pkgs.libuuid

          pkgs.xorg.libXfixes
          pkgs.xorg.libXi
          pkgs.xorg.libSM
          pkgs.xorg.libICE
          pkgs.xorg.xcbutil
          pkgs.xorg.xcbutilimage
          pkgs.xorg.xcbutilkeysyms
          pkgs.xorg.xcbutilrenderutil
          pkgs.xorg.xcbutilwm
          pkgs.xorg.xcbutilcursor
        ]}:$LD_LIBRARY_PATH"
        export PYTHONNOUSERSITE="true"
        # echo "Dev shell ready."
      '';
    };
  };
}
