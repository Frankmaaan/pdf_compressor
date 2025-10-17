# Windows User Guide

## WSL environment deployment instructions

Since the command line tools (`pdftoppm`, `tesseract`, `recode_pdf`, `qpdf`) that this PDF compression tool relies on are mainly available in the Linux environment, Windows users need to use WSL (Windows Subsystem for Linux) to use this tool.

## 1. Install WSL

### Method 1: Use the built-in commands of Windows 11/10
```powershell
#Run in Administrator PowerShell
wsl --install

# Or install the specified Ubuntu version
wsl --install -d Ubuntu-24.04
```

### Method 2: Through Microsoft Store
1. Open Microsoft Store
2. Search for "Ubuntu 24.04 LTS"
3. Click Install

## 2. Configure WSL

### Start WSL
```powershell
# Start the default Linux distribution
wsl

# Or start the specified version
wsl -d Ubuntu-24.04
```

### Update system
```bash
sudo apt update && sudo apt upgrade -y
```

## 3. Install project dependencies

### Install Python and pip in WSL
```bash
sudo apt install python3 python3-pip
```

### Copy project to WSL
```bash
# Method 1: Directly access the Windows file system
cd /mnt/c/Users/quying/Projects/pdf_compressor

#Method 2: Copy to WSL file system (recommended)
cp -r /mnt/c/Users/quying/Projects/pdf_compressor ~/pdf_compressor
cd ~/pdf_compressor
```

### Run the installation script
```bash
#Give the script execution permissions
chmod +x install_dependencies.sh

# Run the installation script
./install_dependencies.sh
```

## 4. Verify installation

```bash
# Check dependencies
python3 main.py --check-deps

#Run the test tool
python3 test_tool.py
```

## 5. Usage examples

### Processing PDFs in Windows file systems
```bash
# Process PDF files in C drive
python3 main.py --input /mnt/c/Users/quying/Documents/test.pdf --output-dir ./output --allow-splitting

# Batch process Windows directories
python3 main.py --input /mnt/c/Users/quying/Documents/PDFs --output-dir ./processed --allow-splitting
```

### Use quick script
```bash
#Give quick script execution permissions
chmod +x run.sh

# Use quick script
./run.sh -s /mnt/c/Users/quying/Documents/test.pdf
./run.sh -s -o ./processed /mnt/c/Users/quying/Documents/PDFs
```

## 6. File path description

### Correspondence between Windows and WSL file systems
- Windows `C:\` → WSL `/mnt/c/`
- Windows `D:\` → WSL `/mnt/d/`
- WSL home directory `~` → Windows `\\wsl$\Ubuntu-24.04\home\username`

### Example path conversion
```bash
# Windows path: C:\Users\quying\Projects\pdf_compressor\test.pdf
# WSL path: /mnt/c/Users/quying/Projects/pdf_compressor/test.pdf

# Windows path: D:\Documents\PDFs
# WSL path: /mnt/d/Documents/PDFs
```

## 7. Performance optimization suggestions

### File storage location
```bash
# Recommendation: Copy the project to the WSL file system for better performance
cp -r /mnt/c/Users/quying/Projects/pdf_compressor ~/pdf_compressor

# When processing large files, it is recommended that the output is also in the WSL file system
python3 main.py --input /mnt/c/path/to/large.pdf --output-dir ~/output --allow-splitting
```

### Memory and Storage
- Make sure WSL has enough memory allocated (configured in `.wslconfig`)
- Reserve enough disk space for temporary files

## 8. Troubleshooting

### WSL related issues
```powershell
# Restart WSL
wsl --shutdown
wsl

# Check WSL status
wsl --list --verbose

# Set default version
wsl --set-default Ubuntu-24.04
```

### Permission issues
```bash
# Make sure the file has the correct permissions
chmod +x *.sh
chmod +x *.py
```

### Path problem
```bash
# Use absolute paths to avoid path errors
python3 main.py --input "$(pwd)/test.pdf" --output-dir "$(pwd)/output"
```

## 9. WSL configuration file

### Create `.wslconfig` file
Create `C:\Users\quying\.wslconfig` in the Windows user directory:

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

### Application configuration
```powershell
# Restart WSL to apply the new configuration
wsl --shutdown
wsl
```

## 10. Complete workflow example

```bash
# 1. Enter WSL
wsl

# 2. Switch to the project directory
cd ~/pdf_compressor

# 3. Check dependencies (all should pass)
python3 main.py --check-deps

# 4. Process PDF files in Windows
python3 main.py --input /mnt/c/Users/quying/Documents/application materials.pdf \
                --output-dir ~/output \
                --allow-splitting \
                --verbose

# 5. View results
ls -la ~/output/

# 6. Copy results to Windows
cp ~/output/* /mnt/c/Users/quying/Documents/after compression/
```

## 11. Automation script

Create a Windows batch file to simplify things:

```batch
@echo off
echo starts the PDF compression tool...
wsl -d Ubuntu-24.04 -e bash -c "cd ~/pdf_compressor && python3 main.py %*"
```

Save as `pdf_compress.bat` and then use it in Windows like this:
```cmd
pdf_compress.bat --input C:\path\to\file.pdf --output-dir C:\path\to\output --allow-splitting
```

In this way, you can seamlessly use the PDF compression tool in WSL in a Windows environment!