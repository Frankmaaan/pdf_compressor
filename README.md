# PDF compression and splitting tool

An automatic compression and splitting tool for professional title declaration PDF files based on archive-pdf-tools, which implements the "Deconstruction-Analysis-Reconstruction" (DAR) three-stage processing process.

## Features

- **Intelligent Layered Compression**: Automatically select the optimal compression strategy based on file size
- **Iterative Optimization Algorithm**: Find the best balance between quality and file size
- **Emergency Split Mechanism**: Automatically split files when compression fails to ensure compliance with size requirements
- **Batch Processing**: Supports batch processing of single files and directories
- **Detailed Log**: Complete processing records and error tracking
- **Chinese Support**: Optimized Chinese OCR recognition

## Technical architecture

### DAR three-stage process

1. **Deconstruct**: Use `pdftoppm` to convert PDF to high-quality images
2. **Analyze**: Use `tesseract` to perform OCR and generate hOCR files
3. **Reconstruct**: Use `recode_pdf` to reconstruct and optimize PDF based on MRC technology

### Layered compression strategy

- **Level 1** (2-10MB): High-quality compression, quality first
- **Level 2** (10-50MB): Balanced compression, prioritizing splitting
- **Level 3** (≥50MB): Extreme compression, aggressive parameter settings

## Installation requirements

### System environment

**Only supports Ubuntu/WSL environment:**
- Ubuntu 24.04+ or WSL2 (recommended)
- Python 3.7+
- At least 2GB of free disk space (for temporary files)

**Note**: This project is designed and tested for Ubuntu/WSL environment and does not support other operating systems.

### Important note: pipx installation method

This tool uses `pipx` to install `archive-pdf-tools` to avoid contaminating the system Python environment. The installation script automatically handles Ubuntu version compatibility issues.

If you have installed archive-pdf-tools using pip before, it is recommended to uninstall it first:
```bash
pip3 uninstall archive-pdf-tools
```

### System tool dependencies

Install necessary tools in Ubuntu/WSL environment:

```bash
# Update package manager
sudo apt update

#Install core tools
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-eng qpdf pipx

#Install archive-pdf-tools (pipx is recommended)
pipx install archive-pdf-tools

# Make sure PATH is configured correctly
pipx ensurepath
source ~/.bashrc
```

### Python environment

- Python 3.7+
- Standard library modules (no additional installation required)

## How to use

### Quick Start for Windows users

```batch
# Use Windows batch script (automatically handles WSL configuration)
pdf_compress.bat C:\Documents\test.pdf

# Allow split batch processing
pdf_compress.bat C:\Documents\PDFs --allow-splitting --target-size 8.0
```

### Linux/WSL users

#### Basic usage

```bash
# Process a single file (split allowed)
python main.py --input document.pdf --output-dir ./output --allow-splitting

# Process the entire directory
python main.py --input ./pdf_folder --output-dir ./processed

# Custom target size
python main.py --input large.pdf --output-dir ./output --target-size 8.0
```

### Command line parameters

| Parameters | Type | Default value | Description |
|------|------|--------|------|
| `--input` | Required | - | Input PDF file or directory path |
| `--output-dir` | Required | - | Output directory path |
| `--target-size` | Optional | 2.0 | Target file size (MB) |
| `--allow-splitting` | Optional | False | Allow splitting of files |
| `--max-splits` | Optional | 4 | Maximum number of splits (2-10) |
| `--copy-small-files` | Optional | False | Copy small files to the output directory |
| `--check-deps` | Optional | False | Only check dependencies |
| `--verbose` | Optional | False | Show detailed debugging information |

### Usage examples

```bash
# Check tool dependencies
python -m main --check-deps

# Process a single file (compress single.pdf to target 5MB and output to out/)
python -m main --input single.pdf --output-dir out --target-size 5

# Run on bulk directories, allowing splitting and retaining temporary directories for debugging failures
python -m main --input-dir ./pdfs --output-dir ./out --target-size 3 --allow-splitting --max-splits 4 -k

# Only check dependencies, do not perform compression (for diagnostics)
python -m main --check-deps

# Quickly output common command examples (from the command line)
python -m main -? # or --examples
```

### Interactive manual mode (Manual)

```bash
# Start interactive full manual mode (enter parameters as prompted in the terminal)
python -m main --manual
# or short option (-m is safe to use in some shells):
python -m main -m

# PowerShell Note: The short option `-?` may be interpreted as a help symbol, it is recommended to use the long option `--examples`.
```

## Project structure

```
pdf_compressor/
├── main.py # Main program entry
├── orchestrator.py # Business process scheduler
├── compressor/
│   ├── __init__.py
│ ├── pipeline.py # DAR three-stage process implementation
│ ├── strategy.py # Layered compression strategy
│ ├── splitter.py # PDF splitting logic
│ └── utils.py # Utility function
├── logs/
│ └── process.log # Processing log (automatically generated)
├── docs/ # Project documentation
├── requirements.txt # Python dependencies
└── README.md # Project description
```

## Algorithm description

### Iterative compression algorithm

The program uses a heuristic search algorithm that starts with high-quality parameters and gradually reduces the quality until the size requirements are met:

1. **Priority to adjust background downsampling** (`bg-downsample`): minimal impact on text clarity
2. **Secondly lower the resolution** (`dpi`): affects the overall quality but can significantly reduce the file size

### Split strategy

Start the split protocol when compression fails:

1. **Smart Sharding**: Estimate the optimal number of splits based on file size
2. **Progressive Try**: Start with the estimated value and gradually increase the number of splits until success
3. **Quality Assurance**: Use aggressive compression strategy for each shard

## Logging and Monitoring

### Log file

- **Location**: `logs/process.log`
- **Content**: Detailed processing process, parameter selection, error message
- **Format**: timestamp + log level + module information + message

### Process report

`processing_report.txt` is automatically generated after batch processing, including:
- Process statistics
- List of successful/failed files
- Processing time recording

## Performance considerations

### Processing time

- **Single page document**: usually 30 seconds-2 minutes
- **Multi-page documents**: linear growth by the number of pages
- **Large Files**: May take 10-30 minutes

### Influencing factors

- PDF page count and complexity
- Image resolution settings
- System hardware performance
- OCR processing complexity

### Optimization suggestions

-Allow sufficient time for high-volume tasks
- Run on a machine with better performance
- Consider using an SSD to store temporary files

## troubleshooting

### FAQ

1. **Tool not found error**
   ```bash
   # Check tool installation
   python main.py --check-deps
   
   # Reinstall missing tools
   sudo apt install poppler-utils tesseract-ocr qpdf pipx
   pipx install archive-pdf-tools
   ```

2. **recode_pdf command not found**
   ```bash
   # Make sure the pipx path is in PATH
   pipx ensurepath
   source ~/.bashrc
   ```

3. **Insufficient memory**
   - Reduce the number of concurrently processed files
   - Lower initial DPI settings
   - Make sure there is enough disk space to store temporary files

4. **OCR recognition error**
   - Check tesseract language pack installation
   - Try increasing the image resolution
   - Confirm PDF content clarity

5. **Permission issues**
   ```bash
   # Make sure the output directory has write permissions
   chmod 755 output_directory
   ```

### Detailed Exclusion Guide

View the complete troubleshooting guide: `docs/TROUBLESHOOTING.md`

### Debugging Tips

- Use the `--verbose` parameter to view detailed information
- Check the `logs/process.log` file
- Process problem files one by one to locate the problem

## Technical support

### Log analysis

Important log information:
- `Phase 1 [Deconstruction]`: PDF to image process
- `Phase 2 [Analysis]`: OCR processing
- `Phase 3 [Reconstruction]`: PDF reconstruction process
- `Compression result size`: the result of each attempt

### contact information

In case of technical issues, please provide:
1. Complete error message
2. `logs/process.log` file
3. Basic information of the problem file (size, number of pages, etc.)
4. Commands and parameters used

## License

This project is open source under the MIT license.

## Update log

### v1.0.0 (2024-10-09)
- Initial version release
- Implement a complete DAR processing process
- Support layered compression strategy
- Integrated PDF splitting function
- Add detailed logging
