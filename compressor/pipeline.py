# compressor/pipeline.py

import logging
import glob
import subprocess
from pathlib import Path
from . import utils

def deconstruct_pdf_to_images(pdf_path, temp_dir, dpi):
    """
    Convert PDF to TIFF image sequence using pdftoppm.
    Returns a list of generated image file paths.
    """
    logging.info(f"Phase 1 [Deconstruction]: Start converting {pdf_path.name} to image (DPI: {dpi})...")
    output_prefix = temp_dir / "page"
    command = [
        "pdftoppm",
        "-tiff",
        "-r", str(dpi),
        str(pdf_path),
        str(output_prefix)
    ]
    if not utils.run_command(command):
        logging.error("PDF deconstruction failed.")
        return None
    
    image_files = sorted(glob.glob(f"{output_prefix}-*.tif"))
    if not image_files:
        logging.error("No image file was generated.")
        return None
        
    logging.info(f"Successfully generated {len(image_files)} page image.")
    return [Path(f) for f in image_files]

def analyze_images_to_hocr(image_files, temp_dir):
    """
    Use tesseract to OCR images, generate and merge hOCR files.
    Returns the merged hOCR file path.
    """
    logging.info(f"Phase 2 [Analysis]: Start OCR on {len(image_files)} images...")
    hocr_files = []
    
    for i, img_path in enumerate(image_files):
        output_prefix = temp_dir / img_path.stem
        command = [
            "tesseract",
            str(img_path),
            str(output_prefix),
            "-l", "eng", # English
            "hocr"
        ]
        if not utils.run_command(command):
            logging.error(f"OCR failed for image {img_path.name}.")
            return None
        hocr_files.append(Path(f"{output_prefix}.hocr"))
        logging.info(f"Complete OCR: {i+1}/{len(image_files)}")

    # Merge all hocr files
    combined_hocr_path = temp_dir / "combined.hocr"
    logging.info(f"Merge hOCR files to {combined_hocr_path}...")
    try:
        with open(combined_hocr_path, 'w', encoding='utf-8') as outfile:
            #Write HTML header
            outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            outfile.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n')
            outfile.write('"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')
            outfile.write('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n')
            outfile.write('<head>\n<title></title>\n')
            outfile.write('<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n')
            outfile.write('<meta name="ocr-system" content="tesseract" />\n')
            outfile.write('</head>\n<body>\n')
            
            # Combine the content of each page
            for hocr_file in hocr_files:
                with open(hocr_file, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    # Extract page content (remove HTML header and trailer)
                    start_marker = '<div class=\'ocr_page\''
                    end_marker = '</div>'
                    
                    start_idx = content.find(start_marker)
                    if start_idx != -1:
                        # Find the corresponding closing tag
                        page_content = content[start_idx:]
                        # Find the complete end of div
                        div_count = 0
                        end_idx = -1
                        for i, char in enumerate(page_content):
                            if page_content[i:i+5] == '<div ':
                                div_count += 1
                            elif page_content[i:i+6] == '</div>':
                                div_count -= 1
                                if div_count == 0:
                                    end_idx = i + 6
                                    break
                        
                        if end_idx != -1:
                            outfile.write(page_content[:end_idx] + '\n')
                        else:
                            # Alternative: Find the first </div>
                            first_end = page_content.find('</div>')
                            if first_end != -1:
                                outfile.write(page_content[:first_end + 6] + '\n')
            
            outfile.write('</body>\n</html>\n')
            
    except IOError as e:
        logging.error(f"Error merging hOCR files: {e}")
        return None

    logging.info("hOCR files merged successfully.")
    return combined_hocr_path

def reconstruct_pdf(image_files, hocr_file, temp_dir, params, output_pdf_path):
    """
    Use recode_pdf to reconstruct the PDF.
    """
    logging.info(f"Phase 3 [Rebuild]: Rebuild PDF using parameters {params}...")
    
    # recode_pdf requires a glob pattern
    image_stack_glob = str(temp_dir / "page-*.tif")

    command = [
        "recode_pdf",
        "--from-imagestack", image_stack_glob,
        "--hocr-file", str(hocr_file),
        "--dpi", str(params['dpi']),
        "--bg-downsample", str(params['bg_downsample']),
        "--mask-compression", "jbig2",
        "-J", params.get('jpeg2000_encoder', 'openjpeg'), # JPEG2000 encoder selection
        "-o", str(output_pdf_path)
    ]
    
    if not utils.run_command(command):
        logging.error("PDF reconstruction failed.")
        return False
        
    logging.info(f"PDF reconstruction successful, output to {output_pdf_path}")
    return True

def get_pdf_page_count(pdf_path):
    """Use pdfinfo to get the total number of pages in a PDF."""
    command = ["pdfinfo", str(pdf_path)]
    try:
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Failed to obtain the page number of {pdf_path.name}: {e}")
    return 0
