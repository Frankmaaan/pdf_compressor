#!/usr/bin/env python3
# test_tool.py
# Simple script to test tool functionality

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from compressor import utils
import logging

def test_dependencies():
    """Test whether the dependent tools are installed correctly"""
    print("=" * 50)
    print("PDF compression tool - dependency check")
    print("=" * 50)
    
    utils.setup_logging()
    
    if utils.check_dependencies():
        print("\n✅ All dependency tool checks passed!")
        print("The tool is ready to start processing PDF files.")
        return True
    else:
        print("\n❌ Dependency check failed!")
        print("Please run the install_dependencies.sh script to install the missing tools.")
        return False

def show_tool_versions():
    """Show version information of each tool"""
    import subprocess
    
    tools = {
        'pdftoppm': ['pdftoppm', '-v'],
        'tesseract': ['tesseract', '--version'],
        'qpdf': ['qpdf', '--version'],
        'pdfinfo': ['pdfinfo', '-v']
    }
    
    print("\nTool version information:")
    print("-" * 30)
    
    for tool_name, command in tools.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            # Get the first line of version information
            version_info = result.stderr.split('\n')[0] if result.stderr else result.stdout.split('\n')[0]
            print(f"{tool_name:12}: {version_info}")
        except Exception as e:
            print(f"{tool_name:12}: Unable to obtain version information")

def create_test_structure():
    """Create test directory structure"""
    from pathlib import Path
    
    test_dirs = [
        "test_input",
        "test_output", 
        "examples"
    ]
    
    base_path = Path(__file__).parent
    
    for dir_name in test_dirs:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"Create directory: {dir_path}")
    
    #Create sample documentation
    readme_path = base_path / "test_input" / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""Test input directory
================

Place the PDF files to be tested into this directory.

Testing suggestions:
1. Prepare PDF files of different sizes:
   - Small files (< 2MB) - Test skip functionality
   - Medium file size (2-10MB) - Tests high quality compression
   - Large files (10-50MB) - Test balanced compression
   - Very large files (> 50MB) - Test extreme compression and splitting

2. Test command example:
   python main.py --input test_input --output-dir test_output --allow-splitting --verbose
""")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--create-test':
        create_test_structure()
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == '--versions':
        show_tool_versions()
        return
    
    # Run dependency check by default
    if test_dependencies():
        show_tool_versions()
        
        print(f"\nUse 'python {sys.argv[0]} --create-test' to create a test directory")
        print(f"Use 'python {sys.argv[0]} --versions' to view tool versions")

if __name__ == "__main__":
    main()