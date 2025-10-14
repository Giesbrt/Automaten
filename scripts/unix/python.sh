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

project_root="$(dirname "$(pwd)")"  # Because for me this is in ./scripts

venv="$project_root/.venv"
if [ -d "$venv" ]; then
  confirm_and_rm "$venv"
fi

# Install extra requirements
python -m venv "$venv"
echo "Created .venv"
echo "Installing extra requirements"  # We create a venv so we can upgrade pip
. "$venv/bin/activate"  # As . is more universal than source
python -m pip install --upgrade pip  # We upgrade pip so we are sure to have the target flag
echo "$project_root/requirements.txt"
python -m pip install --upgrade -r "$project_root/requirements.txt"

echo "Done."
