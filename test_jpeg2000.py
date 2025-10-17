#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_jpeg2000.py
# Test JPEG2000 encoder parameters

import sys
import os

#Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compressor.strategy import STRATEGIES

def test_jpeg2000_params():
    """Test whether all policies include JPEG2000 encoder parameters"""
    print("Test JPEG2000 encoder parameter configuration:")
    print("=" * 50)
    
    for tier, strategy in STRATEGIES.items():
        print(f"\nLevel {tier}: {strategy['name']}")
        print("-" * 30)
        
        for i, params in enumerate(strategy['params_sequence'], 1):
            dpi = params['dpi']
            bg_downsample = params['bg_downsample']
            encoder = params.get('jpeg2000_encoder', 'not set')
            
            print(f"  {i}. DPI={dpi}, BG-Downsample={bg_downsample}, JPEG2000={encoder}")
    
    print(f"\nSummary:")
    print(f"-Total strategy level: {len(STRATEGIES)}")
    
    total_configs = sum(len(strategy['params_sequence']) for strategy in STRATEGIES.values())
    print(f"-Total parameter configuration: {total_configs}")
    
    # Check whether all configurations have JPEG2000 parameters
    missing_encoder = []
    for tier, strategy in STRATEGIES.items():
        for i, params in enumerate(strategy['params_sequence']):
            if 'jpeg2000_encoder' not in params:
                missing_encoder.append(f"Level{tier}-configuration{i+1}")
    
    if missing_encoder:
        print(f"-Missing JPEG2000 parameter configuration: {', '.join(missing_encoder)}")
    else:
        print(f"- ✅ All configurations include JPEG2000 encoder parameters")

def test_command_generation():
    """Test command generation logic"""
    print(f"\n" + "=" * 50)
    print("Test recode_pdf command generation:")
    print("=" * 50)
    
    # Simulation parameters
    test_params = {
        'dpi': 300,
        'bg_downsample': 2,
        'jpeg2000_encoder': 'grok'
    }
    
    # Simulate command build
    image_stack_glob = "/tmp/test/page-*.tif"
    hocr_file = "/tmp/test/combined.hocr"
    output_pdf = "/tmp/test/output.pdf"
    
    command = [
        "recode_pdf",
        "--from-imagestack", image_stack_glob,
        "--hocr-file", hocr_file,
        "--dpi", str(test_params['dpi']),
        "--bg-downsample", str(test_params['bg_downsample']),
        "--mask-compression", "jbig2",
        "-J", test_params.get('jpeg2000_encoder', 'openjpeg'),
        "-o", output_pdf
    ]
    
    print("Generated command:")
    print(" ".join(command))
    
    print(f"\nParameter analysis:")
    print(f"- JPEG2000 encoder: {test_params.get('jpeg2000_encoder', 'openjpeg')}")
    print(f"- DPI: {test_params['dpi']}")
    print(f"- Background sampling: {test_params['bg_downsample']}")

if __name__ == "__main__":
    test_jpeg2000_params()
    test_command_generation()