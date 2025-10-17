# compressor/splitter.py

import logging
import math
import tempfile
from pathlib import Path
from . import utils, strategy, pipeline

def split_pdf(pdf_path, output_path, start_page, end_page):
    """
    Use qpdf to split PDF files.
    """
    logging.info(f"Splitting {pdf_path.name}: page number {start_page}-{end_page} -> {output_path.name}")
    command = [
        "qpdf",
        str(pdf_path),
        "--pages",
        ".", # represents the input file
        f"{start_page}-{end_page}",
        "--",
        str(output_path)
    ]
    return utils.run_command(command)

def calculate_split_strategy(total_size_mb, max_splits):
    """
    Calculate the optimal split strategy based on file size.
    Returns the recommended initial number of splits.
    """
    #Heuristic algorithm: Assume that a 25MB block is more likely to be compressed to 2MB
    estimated_chunk_size = 25
    initial_k = min(max_splits, math.ceil(total_size_mb / estimated_chunk_size))
    
    # The minimum number of splits is 2
    if initial_k < 2:
        initial_k = 2
    
    logging.info(f"File size {total_size_mb:.2f}MB, recommended initial number of splits: {initial_k}")
    return initial_k

def run_splitting_protocol(pdf_path, output_dir, args):
    """
    Execute split agreement.
    """
    logging.info(f"Start emergency splitting protocol for {pdf_path.name}...")
    
    # Get the number of PDF pages
    total_pages = pipeline.get_pdf_page_count(pdf_path)
    if total_pages == 0:
        logging.error("Unable to obtain page number, split aborted.")
        return False

    logging.info(f"Total number of PDF pages: {total_pages}")
    
    # Calculate initial split strategy
    original_size_mb = utils.get_file_size_mb(pdf_path)
    initial_k = calculate_split_strategy(original_size_mb, args.max_splits)

    # Try different number of splits
    for k in range(initial_k, args.max_splits + 1):
        logging.info(f"=== try to split into {k} parts ===")
        
        if not try_split_and_compress(pdf_path, output_dir, args, k, total_pages):
            logging.warning(f"Failed to split into {k} parts, try increasing the number of splits...")
            continue
        else:
            logging.info(f"{pdf_path.name} was successfully split into {k} parts and all compressed successfully!")
            return True

    logging.error(f"Split protocol failed: Compression could not be completed even when split into {args.max_splits} parts.")
    return False

def try_split_and_compress(pdf_path, output_dir, args, k, total_pages):
    """
    Try splitting the PDF into k parts and compressing each part.
    """
    pages_per_split = math.ceil(total_pages / k)
    split_files = []
    temp_split_files = []
    
    #Create a temporary directory to store split files
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    
    try:
        # Phase 1: Split PDF
        for i in range(k):
            start_page = i * pages_per_split + 1
            end_page = min((i + 1) * pages_per_split, total_pages)
            
            if start_page > total_pages:
                break

            part_path = temp_dir / f"{pdf_path.stem}_temp_part{i+1}.pdf"
            
            # Split PDF
            if not split_pdf(pdf_path, part_path, start_page, end_page):
                logging.error(f"Splitting part {i+1} failed.")
                return False
            
            temp_split_files.append(part_path)
            logging.info(f"Part {i+1} was successfully split (page {start_page}-{end_page})")

        # Second stage: compress each split file
        for i, part_path in enumerate(temp_split_files):
            logging.info(f"Start compressing part {i+1}: {part_path.name}")
            
            # Use aggressive compression strategy for split files (pass keep_temp_on_failure)
            keep_temp = getattr(args, 'keep_temp_on_failure', False)
            success, compressed_path = strategy.run_aggressive_compression(
                part_path, output_dir, args.target_size, keep_temp_on_failure=keep_temp
            )

            if success:
                # Rename to final file name
                final_part_name = f"{pdf_path.stem}_part{i+1}.pdf"
                final_part_path = output_dir / final_part_name
                
                if compressed_path != final_part_path:
                    utils.copy_file(compressed_path, final_part_path)
                    # Delete temporary compressed files
                    if compressed_path.exists():
                        compressed_path.unlink()
                
                split_files.append(final_part_path)
                logging.info(f"Part {i+1} was compressed successfully: {final_part_path}")
            else:
                logging.error(f"The compression of part {i+1} failed.")
                # Clean up successful files
                for success_file in split_files:
                    if success_file.exists():
                        success_file.unlink()
                return False

        # All parts successful
        logging.info(f"All {len(split_files)} parts have been compressed successfully")
        return True
        
    except Exception as e:
        logging.error(f"An error occurred during splitting and compression: {e}")
        # Clean up created files
        for success_file in split_files:
            if success_file.exists():
                success_file.unlink()
        return False
    finally:
        # Clean up the temporary directory (skip cleanup if user asks to keep it on failure)
        keep_temp = getattr(args, 'keep_temp_on_failure', False)
        # If retention is required and a failure occurs, retain the temporary directory
        if keep_temp:
            logging.info(f"Keep split temporary directory for debugging: {temp_dir_str}")
        else:
            utils.cleanup_directory(temp_dir_str)

def estimate_compression_feasibility(pdf_path, target_size_mb):
    """
    Estimate whether the file is likely to be compressed to the target size.
    This is a heuristic function used to optimize the splitting strategy.
    """
    current_size_mb = utils.get_file_size_mb(pdf_path)
    compression_ratio = target_size_mb / current_size_mb
    
    # Feasibility judgment based on experience
    if compression_ratio > 0.5: # Compression ratio exceeds 50%
        return "likely to succeed"
    elif compression_ratio > 0.2: # Compression ratio exceeds 20%
        return "possibly successful"
    elif compression_ratio > 0.05: # Compression ratio exceeds 5%
        return "difficult but possible"
    else:
        return "almost impossible"

def validate_split_results(split_files, target_size_mb):
    """
    Verify whether the split result meets the requirements.
    """
    all_valid = True
    total_size = 0
    
    for file_path in split_files:
        if not file_path.exists():
            logging.error(f"Split file does not exist: {file_path}")
            all_valid = False
            continue
            
        size_mb = utils.get_file_size_mb(file_path)
        total_size += size_mb
        
        if size_mb > target_size_mb:
            logging.error(f"Split file {file_path.name} size {size_mb:.2f}MB exceeds target {target_size_mb}MB")
            all_valid = False
        else:
            logging.info(f"Split file {file_path.name} size {size_mb:.2f}MB meets the requirements")
    
    logging.info(f"Total size of split files: {total_size:.2f}MB")
    return all_valid