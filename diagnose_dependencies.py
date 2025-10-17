#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# diagnose_dependencies.py
# WSL/Ubuntu environment dependency diagnostic tool

import subprocess
import os
import sys
from pathlib import Path

def check_tool_detailed(tool_name, install_method=None):
    """Check the installation status of individual tools in detail"""
    print(f"\n{'='*50}")
    print(f"Check tool: {tool_name}")
    print(f"{'='*50}")
    
    # Check which command
    try:
        result = subprocess.run(['which', tool_name], 
                              capture_output=True, 
                              check=True,
                              timeout=5)
        tool_path = result.stdout.decode('utf-8').strip()
        print(f"✓ tool path: {tool_path}")
        
        # Try to get version information
        version_commands = [['--version'], ['--help'], ['-v'], ['-h']]
        version_found = False
        
        for cmd in version_commands:
            try:
                ver_result = subprocess.run([tool_name] + cmd,
                                          capture_output=True,
                                          timeout=10)
                if ver_result.returncode in [0, 1]: # Success or help information
                    output = ver_result.stdout.decode('utf-8', errors='ignore')
                    if not output:
                        output = ver_result.stderr.decode('utf-8', errors='ignore')
                    
                    if output:
                        # Show only the first few lines
                        lines = output.split('\n')[:3]
                        clean_output = ' '.join(lines).strip()
                        if clean_output:
                            print(f"✓ Version information: {clean_output}")
                            version_found = True
                            break
            except:
                continue
        
        if not version_found:
            print("⚠ Unable to obtain version information, but the tool exists")
        
        return True
        
    except subprocess.CalledProcessError:
        print(f"✗ tool not found")
        if install_method:
            print(f"Installation method: {install_method}")
        return False
    except Exception as e:
        print(f"✗ Error while checking: {e}")
        return False

def check_path_configuration():
    """Check PATH configuration"""
    print(f"\n{'='*50}")
    print("PATH configuration check")
    print(f"{'='*50}")
    
    current_path = os.environ.get('PATH', '')
    path_dirs = current_path.split(':')
    
    print(f"The current PATH contains {len(path_dirs)} directories:")
    for i, dir_path in enumerate(path_dirs[:10], 1): # Only display the first 10
        exists = "✓" if os.path.exists(dir_path) else "✗"
        print(f"  {i:2d}. {exists} {dir_path}")
    
    if len(path_dirs) > 10:
        print(f" ... there are {len(path_dirs) - 10} directories")
    
    # Check important directories
    important_dirs = [
        '/usr/bin',
        '/usr/local/bin', 
        os.path.expanduser('~/.local/bin')
    ]
    
    print("\nImportant directory check:")
    for dir_path in important_dirs:
        in_path = dir_path in path_dirs
        exists = os.path.exists(dir_path)
        status = "✓" if in_path and exists else "✗"
        print(f" {status} {dir_path} (in PATH: {in_path}, exists: {exists})")

def check_python_environment():
    """Check the Python environment"""
    print(f"\n{'='*50}")
    print("Python environment check")
    print(f"{'='*50}")
    
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    
    # Check pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                              capture_output=True, check=True, timeout=10)
        print(f"pip version: {result.stdout.decode('utf-8').strip()}")
    except:
        print("✗ pip is not available")
    
    # Check pipx
    try:
        result = subprocess.run(['pipx', '--version'],
                              capture_output=True, check=True, timeout=10)
        print(f"pipx version: {result.stdout.decode('utf-8').strip()}")
    except:
        print("✗ pipx is not available")
    
    # Check archive-pdf-tools
    try:
        result = subprocess.run([sys.executable, '-c', 
                               'import pkg_resources; print(pkg_resources.get_distribution("archive-pdf-tools").version)'],
                              capture_output=True, check=True, timeout=10)
        print(f"archive-pdf-tools version: {result.stdout.decode('utf-8').strip()}")
    except:
        print("✗ archive-pdf-tools is not installed via pip")

def main():
    print("PDF compression tool - detailed dependency diagnosis")
    print("="*60)
    
    # Tool list and installation method
    tools_info = {
        'pdftoppm': 'sudo apt install poppler-utils',
        'pdfinfo': 'sudo apt install poppler-utils', 
        'tesseract': 'sudo apt install tesseract-ocr tesseract-ocr-eng',
        'qpdf': 'sudo apt install qpdf',
        'recode_pdf': 'pipx install archive-pdf-tools'
    }
    
    # Check each tool
    results = {}
    for tool, install_cmd in tools_info.items():
        results[tool] = check_tool_detailed(tool, install_cmd)
    
    # Check PATH and Python environment
    check_path_configuration()
    check_python_environment()
    
    # Summarize
    print(f"\n{'='*60}")
    print("Diagnosis Summary")
    print(f"{'='*60}")
    
    missing_tools = [tool for tool, found in results.items() if not found]
    
    if missing_tools:
        print(f"Missing tools ({len(missing_tools)}):")
        for tool in missing_tools:
            print(f"  ✗ {tool}")
            print(f"Installation: {tools_info[tool]}")
        
        print(f"\nRecommended action:")
        apt_tools = [tool for tool in missing_tools if tool != 'recode_pdf']
        if apt_tools:
            # Build apt installation command
            packages = []
            if 'pdftoppm' in apt_tools or 'pdfinfo' in apt_tools:
                packages.append('poppler-utils')
            if 'tesseract' in apt_tools:
                packages.append('tesseract-ocr tesseract-ocr-eng')
            if 'qpdf' in apt_tools:
                packages.append('qpdf')
            
            if packages:
                print(f"  1. sudo apt update && sudo apt install {' '.join(packages)}")
        
        if 'recode_pdf' in missing_tools:
            print(f"  2. pipx install archive-pdf-tools")
            print(f" if there is no pipx: sudo apt install pipx")
    else:
        print("✓ All necessary tools have been installed!")
    
    print(f"\nRun the main program to check:")
    print(f"  python3 main.py --check-deps")

if __name__ == "__main__":
    main()
