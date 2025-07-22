#!/usr/bin/env bash
set -euo pipefail

confirm_and_rm() {
  target="$1"

  if [ -e "$target" ]; then
    printf "Remove '%s'? [y/N] " "$target"
    read answer
    case "$answer" in
      [Yy]*) rm -rf "$target"; echo "Removed $target" ;;
      *) echo "Skipped $target" ;;
    esac
  fi
}

# Detect the flake root (directory containing flake.nix)
flake_root="$(pwd)"
echo "$flake_root"
while [ ! -f "$flake_root/flake.nix" ] && [ "$flake_root" != "/" ]; do
  flake_root="$(dirname "$flake_root")"
done

if [ ! -f "$flake_root/flake.nix" ]; then
  echo "Error: flake.nix not found in current or parent directories"
  exit 1
fi

target_dir="src/default-config/core/extra-libs"
project_root="$(dirname "$(pwd)")"

confirm_and_rm "$project_root/.nixpy"
mkdir -p "$project_root/.nixpy/bin"

cat > "$project_root/.nixpy/bin/python" <<EOF
#!/bin/sh
exec nix --extra-experimental-features 'nix-command flakes' develop "$flake_root" --command python "\$@"
EOF
chmod +x "$project_root/.nixpy/bin/python"
echo "Successfully created nixpy interpreter from flake.nix"

# Install extra requirements
if [ -d .venv ]; then
  confirm_and_rm .venv
fi
python -m venv .venv
echo "Created .venv"
echo "Installing extra requirements"  # We create a venv so we can upgrade pip
. .venv/bin/activate  # As . is more universal than source
python -m pip install --upgrade pip  # We upgrade pip so we are sure to have the target flag
echo "$project_root/requirements.txt"
if [ -f "$project_root/requirements.txt" ]; then
  echo "Filtering requirements..."
  true > nix-extra-reqs.txt  # Clear or create the filtered output file
  prefixes_to_skip="numpy pyside6 pyyaml pytest requests urllib3 stdlib_list pyinstaller"  # Everything installed by flake

  while IFS= read -r line; do
    skip_line=false

    for prefix in $prefixes_to_skip; do
      case "$line" in
        "$prefix"* )
          skip_line=true
          break
          ;;
      esac
    done

    if [ "$skip_line" = false ]; then
      echo "$line" >> nix-extra-reqs.txt
    fi
  done < "$project_root/requirements.txt"

  python -m pip install --upgrade -r nix-extra-reqs.txt  #  --target "$project_root/$target_dir"
  echo "Installed all extra requirements"
else
  echo "No requirements.txt found"
fi

confirm_and_rm nix-extra-reqs.txt

echo "Collecting Nix-flake provided packages..."
nix_pkgs=$(nix --extra-experimental-features 'nix-command flakes' develop "$flake_root" --command python -m pip list --format=freeze | cut -d= -f1 | tr '[:upper:]' '[:lower:]')

echo "Cleaning up duplicates from $target_dir..."
cd "$project_root/$target_dir"

for nix_pkg in $nix_pkgs; do
  if [ "$nix_pkg" != "pip" ]; then
    python -m pip uninstall -y "$nix_pkg"  # --target "$project_root/$target_dir"
  fi
done

# Copy everything from .venv/lib/python3.13/site-packages to "$project_root/$target_dir"
if [ -d "$project_root/$target_dir" ]; then
  confirm_and_rm "$project_root/$target_dir"
fi
mkdir -p "$project_root/$target_dir"
cd "$flake_root"
venv_site=$(find .venv/lib -type d -path "*/site-packages" | head -n 1)

if [ -d "$venv_site" ]; then
  echo "Copying packages from $venv_site to $project_root/$target_dir..."
  cp -r "$venv_site/"* "$project_root/$target_dir"
  echo "Copy complete."
else
  echo "Could not find site-packages inside .venv"
  exit 1
fi

confirm_and_rm .venv

echo "Done."
