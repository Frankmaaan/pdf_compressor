#!/bin/bash

# ==============================================================================
# archive-pdf-tools final installation script (install.sh) - qpdf version
# ------------------------------------------------------------------------------
# Target environment: Ubuntu 24.04 LTS (WSL)
# Function:
# 1. APT installs all tools (including qpdf, Grok, OpenJPEG, etc.).
# 2. Compile and install jbig2enc from source.
# 3. Use pipx to safely install archive-pdf-tools.
# ==============================================================================

# --- Configuration ---
set -e 

# --- Helper function (for color output) ---
print_info() { echo -e "\n\e[34m==> $1\e[0m"; }
print_success() { echo -e "  \e[32m✔ $1\e[0m"; }
print_error() { echo -e "  \e[31m✖ $1\e[0m"; }

# --- Check running user ---
if [ "$(id -u)" -eq 0 ]; then
  print_error "Error: Please do not run this script as root."
  echo "This script is designed to be run by a normal user and will request administrator privileges via 'sudo' when needed." >&2
  exit 1
fi

# --- Script starts ---
echo "======================================================================================="
echo "Start installing archive-pdf-tools and its dependencies (APT optimized qpdf version)..."
echo "======================================================================================="

# --- Step 1: Update the system and install all APT dependency packages ---
print_info "Step 1/3: Update system package list and install all dependencies (requires sudo permissions)..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    git \
    python3-pip \
    python3-dev \
    pipx \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    autoconf \
    automake \
    libtool \
    pkg-config \
    autoconf-archive \
    libleptonica-dev \
    libjbig2dec0-dev \
    libtiff-dev \
    libpng-dev \
    libjpeg-turbo8-dev \
    imagemagick \
    ghostscript \
    enscript \
    qpdf \
    grokj2k-tools \
    libopenjp2-7 \
    libopenjp2-tools

print_success "APT dependency installation completed."

# --- Step 2: Compile and install jbig2enc from source ---
print_info "Step 2/3: Compiling and installing jbig2enc from source..."
JBG2_DIR="/tmp/jbig2enc"
if [ -d "$JBG2_DIR" ]; then rm -rf "$JBG2_DIR"; fi
git clone https://github.com/agl/jbig2enc.git "$JBG2_DIR"
cd "$JBG2_DIR"
./autogen.sh
./configure
make -j$(nproc)
sudo make install
print_success "jbig2enc installation completed."

# --- Step 3: Safely install archive-pdf-tools using pipx ---
print_info "Step 3/3: Installing archive-pdf-tools in an isolated environment using pipx..."
export PATH="$PATH:$HOME/.local/bin" 
pipx install archive-pdf-tools || pipx upgrade archive-pdf-tools
print_success "archive-pdf-tools installation completed."

# --- Final summary ---
echo
echo "============================================================"
echo -e "\e[32m🎉 All dependencies and tools are installed successfully!\e[0m"
echo "Next step: run the 'verify.sh' script to verify functionality."
echo "============================================================"
