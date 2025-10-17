#Quick Start Guide

## 1. System requirements

- Ubuntu 20.04+ or WSL2 (Ubuntu 24.04 recommended)
- Python 3.7+
- At least 2GB of free disk space (for temporary files)
- 4GB+ RAM (recommended when working with large files)

## 2. Quick installation

### Method 1: Use the installation script (recommended)

```bash
# Clone or download the project to local
cd pdf_compressor

# Run the installation script
chmod +x install_dependencies.sh
./install_dependencies.sh

# Or use the quick start script
chmod +x run.sh
./run.sh --install
```

### Method 2: Manual installation

```bash
# Update system package
sudo apt update

# Install necessary tools
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-chi-sim qpdf pipx

#Install Python package (pipx is recommended)
pipx install archive-pdf-tools

# Make sure PATH is configured correctly
pipx ensurepath
source ~/.bashrc
```

## 3. Verify installation

```bash
# Use Python script to check
python3 main.py --check-deps

# Or use quick start script
./run.sh --check

# Or use a test tool
python3 test_tool.py
```

## 4. Basic usage

### Compress a single file

```bash
# Basic compression
python3 main.py --input document.pdf --output-dir ./output

# Allow splitting (recommended)
python3 main.py --input document.pdf --output-dir ./output --allow-splitting

# Use quick script
./run.sh -s document.pdf
```

### Batch processing directory

```bash
# Process all PDFs in the directory
python3 main.py --input ./pdf_folder --output-dir ./processed --allow-splitting

# Use quick script
./run.sh -s -o ./processed ./pdf_folder
```

### Custom parameters

```bash
# Target 8MB, split into up to 6 parts
python3 main.py --input large.pdf --output-dir ./output \
    --target-size 8.0 --max-splits 6 --allow-splitting

# Verbose mode
python3 main.py --input document.pdf --output-dir ./output \
    --verbose --allow-splitting

# Use quick script
./run.sh -v -s --target-size 8 --max-splits 6 large.pdf
```

## 5. Common usage scenarios

### Scenario 1: Processing of professional title application documents

```bash
# Compress all application materials to less than 2MB
./run.sh -s -o ./Application materials_compressed version ./Original files of application materials/
```

### Scenario 2: Document archiving

```bash
# Compress the archive file, allowing it to be slightly larger
./run.sh -s --target-size 5.0 -o ./archive ./original document/
```

### Scenario 3: Single large file processing

```bash
# Handle very large files, allowing splitting
./run.sh -v -s --max-splits 8 huge document.pdf
```

## 6. Output file description

### Successfully compressed files
- `Original file name_compressed.pdf` - compressed single file

### Split files
- `Original file name_part1.pdf` - Part 1
- `Original file name_part2.pdf` - Part 2
- ...

### Report file
- `processing_report.txt` - Batch processing summary report
- `logs/process.log` - detailed processing log

## 7. Performance optimization suggestions

### Process large batches of files
```bash
# Allocate more time to large batch tasks
# You can process several files first to test the effect
./run.sh -v -s ./test_files/
```

### Handle very large files
```bash
# For files over 100MB, it is recommended:
# 1. Use verbose mode to monitor progress
# 2. Allow a larger number of splits
# 3. Ensure sufficient disk space
./run.sh -v -s --max-splits 10 Very large document.pdf
```

## 8. Troubleshooting

### Tool not found
```bash
# Recheck dependencies
./run.sh --check

# Reinstall
./run.sh --install
```

### Processing failed
```bash
# View detailed logs
cat logs/process.log

# Try again using verbose mode
./run.sh -v -s problem file.pdf
```

### Insufficient memory
```bash
# Process files individually to avoid batching
./run.sh -s single file.pdf

# Or lower the initial quality setting (need to modify the code)
```

## 9. Advanced techniques

### Custom configuration
```bash
#Copy configuration file template
cp config.example.py config.py

# Edit configuration file
nano config.py

# Rerunning the program will use the new configuration
```

### View tool version
```bash
python3 test_tool.py --versions
```

### Create a test environment
```bash
python3 test_tool.py --create-test
```

## 10. Technical Support

- See `README.md` for detailed documentation
- Check `logs/process.log` for processing details
- Run `python3 main.py --help` to view all parameters
- Use `./run.sh --help` to see quick script options