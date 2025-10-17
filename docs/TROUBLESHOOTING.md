# Troubleshooting Guide

## Installation related issues

### 1. pipx related issues

#### Problem: recode_pdf command not found
```bash
bash: recode_pdf: command not found
```

**Solution:**
```bash
#Method 1: Make sure the pipx path is in PATH
pipx ensurepath
source ~/.bashrc

#Method 2: Manually add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

#Method 3: Reinstall
pipx uninstall archive-pdf-tools
pipx install archive-pdf-tools
```

#### Problem: pipx is not installed
```bash
bash: pipx: command not found
```

**Solution:**
```bash
# Ubuntu 22.04+
sudo apt install pipx

# Ubuntu 20.04 or earlier
sudo apt install python3-pip
pip3 install --user pipx
export PATH="$HOME/.local/bin:$PATH"
```

#### Problem: pipx installation failed
```bash
pipx install archive-pdf-tools
#Permission or dependency error occurs
```

**Alternatives:**
```bash
# Install using pip user
pip3 install --user archive-pdf-tools

# Use virtual environment
python3 -m venv ~/pdf_env
source ~/pdf_env/bin/activate
pip install archive-pdf-tools
```

### 2. System tool issues

#### Problem: tesseract language package problem
```bash
Error: Tesseract couldn't load any languages!
```

**Solution:**
```bash
# Reinstall language pack
sudo apt install --reinstall tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# Check language pack
tesseract --list-langs

# If you still have problems, install all language packs
sudo apt install tesseract-ocr-all
```

#### Problem: poppler-utils version problem
```bash
pdftoppm: error while loading shared libraries
```

**Solution:**
```bash
#Update system and reinstall
sudo apt update && sudo apt upgrade
sudo apt install --reinstall poppler-utils

# Check version
pdftoppm -v
```

### 3. Permission issues

#### Problem: Unable to write to output directory
```bash
Permission denied: '/path/to/output'
```

**Solution:**
```bash
# Check directory permissions
ls -la /path/to/output

# Modify permissions
chmod 755 /path/to/output

# Or use the user home directory
python3 main.py --input test.pdf --output-dir ~/output --allow-splitting
```

#### Problem: Temporary file permissions issue
```bash
PermissionError: [Errno 13] Permission denied: '/tmp/...'
```

**Solution:**
```bash
# Clean up temporary files
sudo rm -rf /tmp/pdf_compressor_*

# Check /tmp permissions
ls -la /tmp | grep pdf_compressor

# Set environment variables to use other temporary directories
export TMPDIR=~/tmp
mkdir -p ~/tmp
```

## Runtime issues

### 1. Insufficient memory

#### symptom:
- The process is killed
- System slows down
- "Killed" message

**Solution:**
```bash
# Check memory usage
free -h
htop

# Process small files or reduce concurrency
python3 main.py --input small_file.pdf --output-dir ./output

# Increase swap space (if possible)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 2. Insufficient disk space

#### symptom:
- "No space left on device"
- handle interrupts

**Solution:**
```bash
# Check disk space
df -h

# Clean up old logs and temporary files
rm -rf logs/*.log.old
rm -rf /tmp/pdf_compressor_*

# Use another disk location
python3 main.py --input test.pdf --output-dir /mnt/d/output
```

### 3. Processing timeout

#### symptom:
- No response for a long time
- Process hangs

**Solution:**
```bash
# Use verbose mode to monitor progress
python3 main.py --input test.pdf --output-dir ./output --verbose

# Reduce file or pre-split
# Check if the file is damaged
pdfinfo test.pdf
```

## WSL specific issues

### 1. File path problem

#### Problem: Windows file not found
```bash
No such file or directory: '/mnt/c/...'
```

**Solution:**
```bash
# Check WSL mounting
ls /mnt/c/

# Make sure WSL2 is configured correctly
wsl --list --verbose

# Use correct path format
python3 main.py --input "/mnt/c/Users/username/Documents/file.pdf"
```

### 2. Performance issues

#### Problem: Cross-file system access is slow

**Solution:**
```bash
# Copy files to WSL file system
cp /mnt/c/path/to/file.pdf ~/input/
python3 main.py --input ~/input/file.pdf --output-dir ~/output

#Copy back to Windows after processing is complete
cp ~/output/* /mnt/c/Users/username/Documents/
```

### 3. Encoding issues

#### Problem: Chinese file name is garbled

**Solution:**
```bash
# Set the correct locale
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# Permanent settings
echo 'export LANG=zh_CN.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=zh_CN.UTF-8' >> ~/.bashrc
```

## Debugging Tips

### 1. Enable detailed logging
```bash
python3 main.py --input test.pdf --output-dir ./output --verbose
```

### 2. Check intermediate files
```bash
# Modify KEEP_INTERMEDIATE_FILES in the code to True
# Set in config.py:
KEEP_INTERMEDIATE_FILES = True
```

### 3. Step by step debugging
```bash
# Test a single component first
pdftoppm -tiff -r 300 test.pdf page
tesseract page-01.tif output -l chi_sim hocr
```

### 4. Use testing tools
```bash
# Run full tool check
python3 test_tool.py

# Check version information
python3 test_tool.py --versions

#Create test environment
python3 test_tool.py --create-test
```

## Get help

### 1. View logs
```bash
# View the latest log
tail -f logs/process.log

#Search for error messages
grep ERROR logs/process.log
```

### 2. Collect system information
```bash
# System version
lsb_release -a

# tool version
python3 test_tool.py --versions

#Environment variables
echo $PATH
echo $TMPDIR
```

### 3. Reset environment
```bash
# Complete reinstall
pipx uninstall archive-pdf-tools
sudo apt remove --purge tesseract-ocr poppler-utils qpdf
sudo apt autoremove

# Rerun the installation script
./install_dependencies.sh
```