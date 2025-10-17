#!/bin/bash

# install_dependencies.sh
# PDF compression tool depends on the installation script (Ubuntu/WSL)

echo "======================================"
echo "PDF compression tool depends on installation script"
echo "======================================"

# Check if it is an Ubuntu/Debian system
if ! command -v apt &> /dev/null; then
    echo "Error: This script only works on Ubuntu/Debian systems"
    exit 1
fi

echo "Updating package manager..."
if ! sudo apt update; then
    echo "❌ Package manager update failed, please check the network connection and software source configuration"
    exit 1
fi

echo "Installing system tools..."

# Install poppler-utils (including pdftoppm, pdfinfo)
echo "-install poppler-utils..."
sudo apt install -y poppler-utils

#Install tesseract-ocr
echo "-install tesseract-ocr..."
sudo apt install -y tesseract-ocr

#Install Chinese language pack
echo "-Install Chinese language pack..."
sudo apt install -y tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# Install qpdf
echo "-install qpdf..."
sudo apt install -y qpdf

# Check Python and pipx
if ! command -v python3 &> /dev/null; then
    echo "-Install Python3..."
    sudo apt install -y python3 python3-pip
fi

# Install pipx (recommended Python package management tool)
if ! command -v pipx &> /dev/null; then
    echo "-install pipx..."
    # Try installing via apt (Ubuntu 22.04+)
    if sudo apt install -y pipx 2>/dev/null; then
        echo "Successfully installed pipx via apt"
    else
        echo "apt installation failed, try to install through pip..."
        # Alternatives for Ubuntu 20.04 or earlier
        pip3 install --user pipx
        export PATH="$HOME/.local/bin:$PATH"
    fi
    # Make sure the pipx path is in PATH
    pipx ensurepath 2>/dev/null || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

#Install archive-pdf-tools
echo "Installing Python package..."
echo "-install archive-pdf-tools (using pipx)..."
if pipx install archive-pdf-tools; then
    echo "Successfully installed archive-pdf-tools via pipx"
else
    echo "pipx installation failed, try pip user installation..."
    if pip3 install --user archive-pdf-tools; then
        echo "Successfully installed archive-pdf-tools via pip --user"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    else
        echo " ❌ All Python package installation methods failed"
        echo "Please install manually: pip3 install --user archive-pdf-tools"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Installation completed! Verifying tools..."
echo "======================================"

# Verify installation
check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "✓ $1 installed"
        return 0
    else
        echo "✗ $1 not found"
        return 1
    fi
}

all_good=true

check_tool "pdftoppm" || all_good=false
check_tool "pdfinfo" || all_good=false
check_tool "tesseract" || all_good=false
check_tool "qpdf" || all_good=false

# Check recode_pdf
if command -v recode_pdf &> /dev/null; then
    echo "✓ recode_pdf installed"
elif python3 -c "import pkg_resources; pkg_resources.get_distribution('archive-pdf-tools')" &> /dev/null 2>&1; then
    echo "✓ archive-pdf-tools installed (via pip)"
else
    echo "✗ archive-pdf-tools is not installed correctly"
    echo "Tip: Make sure ~/.local/bin is in your PATH"
    echo "Run: echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
    all_good=false
fi

# Check tesseract language package
if tesseract --list-langs 2>/dev/null | grep -q "chi_sim"; then
    echo "✓ Chinese language pack has been installed"
else
    echo "✗ Chinese language pack not found"
    all_good=false
fi

echo ""
if [ "$all_good" = true ]; then
    echo "🎉 All dependent tools are installed successfully!"
    echo "The PDF compression tool can now be run."
    echo ""
    echo "Note: If you can't find the recode_pdf command in a new terminal, run:"
    echo "  source ~/.bashrc"
    echo "or reopen the terminal"
    echo ""
    echo "How to use:"
    echo "python3 main.py --check-deps # Check dependencies again"
    echo "  python3 main.py --input test.pdf --output-dir ./output --allow-splitting"
else
    echo "❌ Some tools failed to install, please check the above error message."
    echo ""
    echo "FAQ solutions:"
    echo "1. If recode_pdf is not found, make sure ~/.local/bin is in PATH:"
    echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "   source ~/.bashrc"
    echo "2. If there is a permission problem, you can try:"
    echo "   pip3 install --user archive-pdf-tools"
    exit 1
fi