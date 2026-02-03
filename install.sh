#!/usr/bin/env bash
set -euo pipefail

# Colors
GREEN="\033[0;32m"
CYAN="\033[0;36m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
RESET="\033[0m"

info() { echo -e "${CYAN}[*] $1${RESET}"; }
success() { echo -e "${GREEN}[+] $1${RESET}"; }
warn() { echo -e "${YELLOW}[!] $1${RESET}"; }
error() { echo -e "${RED}[!] $1${RESET}"; }

spinner() {
  local pid=$1
  local message=$2
  local delay=0.1
  local spinstr='|/-\'
  printf ">>> %s " "$message"
  while kill -0 "$pid" 2>/dev/null; do
    for i in $(seq 0 3); do
      printf "\b%c" "${spinstr:i:1}"
      sleep $delay
    done
  done
  printf "\b Done\n"
}

info "WIP: Installation script is under development."

#sudo pacman -S libportaudio2 libsndfile1
#uv pip install pedalboard sounddevice opencv-python numpy