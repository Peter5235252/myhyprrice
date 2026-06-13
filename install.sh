#!/usr/bin/env bash
# ============================================================
# myhyprrice installer
# https://github.com/Peter5235252/myhyprrice
# ============================================================

set -e

REPO_URL="https://github.com/Peter5235252/myhyprrice"
REPO_DIR="$(mktemp -d)/myhyprrice"
CONFIG_DIR="$HOME/.config"

DEPS=(
  hyprland
  waybar
  kitty
  rofi
  mako
  hyprpaper
  dolphin
  brightnessctl
  wireplumber
)

AUR_DEPS=(
  grimblast-git
  pacseek
)

# ============================================================
# COLORS
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ============================================================
# HELPERS
# ============================================================

info()    { echo -e "${CYAN}${BOLD}=>${RESET} $*"; }
success() { echo -e "${GREEN}${BOLD}✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}${BOLD}!${RESET} $*"; }
error()   { echo -e "${RED}${BOLD}✗${RESET} $*"; exit 1; }

ask() {
  # ask <prompt> <var_name>
  local prompt="$1"
  local __var="$2"
  echo -en "${BOLD}${prompt}${RESET} "
  read -r "$__var"
}

confirm() {
  # confirm <prompt> -- returns 0 for yes, 1 for no
  local prompt="$1"
  echo -en "${BOLD}${prompt} [y/N]${RESET} "
  read -r ans
  [[ "$ans" =~ ^[Yy]$ ]]
}

# ============================================================
# DETECT AUR HELPER
# ============================================================

detect_aur_helper() {
  if command -v yay &>/dev/null; then
    echo "yay"
  elif command -v paru &>/dev/null; then
    echo "paru"
  else
    echo ""
  fi
}

# ============================================================
# DEPENDENCY CHECK & INSTALL
# ============================================================

check_deps() {
  local missing_pacman=()
  local missing_aur=()

  for pkg in "${DEPS[@]}"; do
    if ! pacman -Qq "$pkg" &>/dev/null; then
      missing_pacman+=("$pkg")
    fi
  done

  local aur_helper
  aur_helper="$(detect_aur_helper)"

  for pkg in "${AUR_DEPS[@]}"; do
    if ! pacman -Qq "$pkg" &>/dev/null 2>&1; then
      missing_aur+=("$pkg")
    fi
  done

  if [[ ${#missing_pacman[@]} -eq 0 && ${#missing_aur[@]} -eq 0 ]]; then
    success "All dependencies are already installed."
    return
  fi

  if [[ ${#missing_pacman[@]} -gt 0 ]]; then
    warn "Missing pacman packages: ${missing_pacman[*]}"
  fi
  if [[ ${#missing_aur[@]} -gt 0 ]]; then
    warn "Missing AUR packages: ${missing_aur[*]}"
  fi

  if confirm "Install missing dependencies now?"; then
    if [[ ${#missing_pacman[@]} -gt 0 ]]; then
      info "Installing pacman packages..."
      sudo pacman -S --needed "${missing_pacman[@]}"
    fi

    if [[ ${#missing_aur[@]} -gt 0 ]]; then
      if [[ -z "$aur_helper" ]]; then
        warn "No AUR helper (yay/paru) found. Skipping AUR packages: ${missing_aur[*]}"
        warn "Install yay or paru and re-run this script to get them."
      else
        info "Installing AUR packages with $aur_helper..."
        "$aur_helper" -S --needed "${missing_aur[@]}"
      fi
    fi

    success "Dependencies installed."
  else
    warn "Skipping dependency installation. Some things may not work."
  fi
}

# ============================================================
# CONFIG CONFLICT HANDLER
# ============================================================

handle_existing() {
  local target="$1"

  if [[ ! -e "$target" ]]; then
    return 0  # nothing there, proceed
  fi

  echo ""
  warn "Already exists: ${BOLD}$target${RESET}"
  echo "  What do you want to do?"
  echo "  [1] Overwrite"
  echo "  [2] Back up then overwrite  (saves to ${target}.bak)"
  echo "  [3] Skip"
  echo -n "  Choice [1/2/3]: "
  read -r choice

  case "$choice" in
    1)
      rm -rf "$target"
      ;;
    2)
      info "Backing up to ${target}.bak"
      mv "$target" "${target}.bak"
      ;;
    3)
      info "Skipping $target"
      return 1
      ;;
    *)
      warn "Invalid choice, skipping $target"
      return 1
      ;;
  esac
}

# ============================================================
# INSTALL CONFIGS
# ============================================================

install_configs() {
  declare -A CONFIG_MAP=(
    ["hypr"]="$CONFIG_DIR/hypr"
    ["waybar"]="$CONFIG_DIR/waybar"
    ["mako"]="$CONFIG_DIR/mako"
    ["kitty"]="$CONFIG_DIR/kitty"
    ["rofi"]="$CONFIG_DIR/rofi"
  )

  for src_dir in "${!CONFIG_MAP[@]}"; do
    local src="$REPO_DIR/$src_dir"
    local dest="${CONFIG_MAP[$src_dir]}"

    if [[ ! -d "$src" ]]; then
      warn "Source directory not found in repo: $src_dir -- skipping"
      continue
    fi

    if handle_existing "$dest"; then
      info "Installing $src_dir -> $dest"
      mkdir -p "$(dirname "$dest")"
      cp -r "$src" "$dest"
      success "Installed $src_dir"
    fi
  done

  # Install the hypr root-level Lua files (they live at repo root, not in a hypr/ subdir)
  local hypr_dest="$CONFIG_DIR/hypr"
  mkdir -p "$hypr_dest"
  for f in "$REPO_DIR"/*.lua "$REPO_DIR"/*.conf; do
    [[ -e "$f" ]] || continue
    local fname
    fname="$(basename "$f")"
    # skip .bak files
    [[ "$fname" == *.bak ]] && continue
    local fdest="$hypr_dest/$fname"
    if [[ -e "$fdest" ]]; then
      echo ""
      warn "Already exists: ${BOLD}$fdest${RESET}"
      echo "  [1] Overwrite  [2] Back up  [3] Skip"
      echo -n "  Choice [1/2/3]: "
      read -r choice
      case "$choice" in
        1) cp "$f" "$fdest" ;;
        2) mv "$fdest" "${fdest}.bak"; cp "$f" "$fdest" ;;
        *) info "Skipping $fname"; continue ;;
      esac
    else
      cp "$f" "$fdest"
    fi
  done
}

# ============================================================
# MAIN
# ============================================================

echo ""
echo -e "${BOLD}${CYAN}myhyprrice installer${RESET}"
echo -e "  ${CYAN}${REPO_URL}${RESET}"
echo ""

# Sanity checks
command -v git &>/dev/null || error "git is not installed."
command -v pacman &>/dev/null || error "This installer only supports Arch-based distros."

# Dependency check
check_deps

# Clone the repo
info "Cloning repo..."
git clone --depth=1 "$REPO_URL" "$REPO_DIR" &>/dev/null
success "Repo cloned."

# Install configs
echo ""
info "Installing config files..."
install_configs

# Done
echo ""
success "Done! Log out and start Hyprland to apply."
echo -e "  ${CYAN}Tip:${RESET} Edit ${BOLD}~/.config/hypr/hyprland.lua${RESET} to set your monitor name and keyboard layout."
echo ""
