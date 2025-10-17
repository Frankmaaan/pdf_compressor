# compressor/strategy.py

import logging
import tempfile
from pathlib import Path
from . import utils, pipeline

# Define compression strategies at different levels
STRATEGIES = {
    1: {  # 2MB <= S < 10MB
        "name": "High Quality Compression",
        "params_sequence": [
            {'dpi': 300, 'bg_downsample': 1, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 300, 'bg_downsample': 2, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 300, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
            {'dpi': 250, 'bg_downsample': 3, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
        ]
    },
    2: {  # 10MB <= S < 50MB
        "name": "Balanced Compression",
        "params_sequence": [
            {'dpi': 300, 'bg_downsample': 2, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 300, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
            {'dpi': 300, 'bg_downsample': 4, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 250, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
            {'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 150, 'bg_downsample': 5, 'jpeg2000_encoder': 'grok'},
        ]
    },
    3: {  # S >= 50MB
        "name": "Extreme compression",
        "params_sequence": [
            {'dpi': 200, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
            {'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
            {'dpi': 200, 'bg_downsample': 5, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 150, 'bg_downsample': 5, 'jpeg2000_encoder': 'grok'},
            {'dpi': 110, 'bg_downsample': 6, 'jpeg2000_encoder': 'grok'},
        ]
    }
}

def determine_tier(size_mb):
    """Determine the processing level based on file size."""
    if 2 <= size_mb < 10:
        return 1
    elif 10 <= size_mb < 50:
        return 2
    elif size_mb >= 50:
        return 3
    return 0 # Less than 2MB or invalid value

def run_iterative_compression(pdf_path, output_dir, target_size_mb, keep_temp_on_failure=False):
    """
    Execute an iterative compression process.
    Return (bool, Path): (whether successful, output file path)
    """
    original_size_mb = utils.get_file_size_mb(pdf_path)
    tier = determine_tier(original_size_mb)
    
    if tier == 0:
        logging.warning(f"The size of file {pdf_path.name} does not meet the compression range, skip.")
        return False, None

    strategy = STRATEGIES[tier]
    logging.info(f"File {pdf_path.name} (Size: {original_size_mb:.2f}MB) Application Strategy: Tier {tier} ({strategy['name']})")

    # To avoid generating hOCR repeatedly for each attempt, we first choose the highest dpi for OCR and generate hOCR only once
    max_dpi = max(p['dpi'] for p in strategy['params_sequence'])
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    try:
        logging.info(f"Generate one-time images and hOCR (using DPI={max_dpi}) for reuse across all attempts")
        # Generate image (using highest dpi) and run OCR once
        image_files = pipeline.deconstruct_pdf_to_images(pdf_path, temp_dir, max_dpi)
        if not image_files:
            logging.error("Failed while generating image for hOCR, terminating compression process.")
            return False, None

        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("Failed to generate hOCR file, terminate the compression process.")
            return False, None

        logging.info(f"The hOCR file will be reused: {hocr_file}")

        # First perform the 1st attempt
        first_params = strategy['params_sequence'][0]
        encoder = first_params.get('jpeg2000_encoder', 'openjpeg')
        logging.info(f"--- First try (conservative): DPI={first_params['dpi']}, BG-Downsample={first_params['bg_downsample']}, JPEG2000={encoder} ---")
        output_pdf_path = temp_dir / f"output_{pdf_path.stem}_first.pdf"
        if pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, first_params, output_pdf_path):
            result_size_mb = utils.get_file_size_mb(output_pdf_path)
            logging.info(f"First attempt result size: {result_size_mb:.2f}MB (target: < {target_size_mb}MB)")
            if result_size_mb <= target_size_mb:
                final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                final_path.parent.mkdir(parents=True, exist_ok=True)
                utils.copy_file(output_pdf_path, final_path)
                logging.info(f"Success! The file has been compressed and saved to: {final_path}")
                return True, final_path

            # If it is far from the target (threshold: 1.5x), directly try the most aggressive parameters
            threshold_factor = 1.5
            if result_size_mb > target_size_mb * threshold_factor:
                logging.info("The first result is far from the target, try the most aggressive strategy directly")
                last_index = len(strategy['params_sequence']) - 1
                last_params = strategy['params_sequence'][last_index]
                logging.info(f"--- Directly try the most aggressive parameters: DPI={last_params['dpi']}, BG-Downsample={last_params['bg_downsample']} ---")
                last_output = temp_dir / f"output_{pdf_path.stem}_last.pdf"
                if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, last_params, last_output):
                    logging.error("The most aggressive parameter attempt failed, and the overall compression failed.")
                    return False, None

                last_size = utils.get_file_size_mb(last_output)
                logging.info(f"Most aggressive attempt result size: {last_size:.2f}MB (target: < {target_size_mb}MB)")
                if last_size > target_size_mb:
                    logging.error("The most aggressive attempt still failed to reach the goal and declared failure.")
                    return False, None

                # The most aggressive success, backtracking upward to improve quality
                logging.info("The most aggressive attempt was successful, starting to backtrack upwards to try higher quality parameters")
                # Backtrack from last_index-1 to 0 until the first one that does not meet the goal is found
                chosen_path = last_output
                for idx in range(last_index - 1, -1, -1):
                    params = strategy['params_sequence'][idx]
                    logging.info(f"--- Backtrace attempt idx={idx}: DPI={params['dpi']}, BG-Downsample={params['bg_downsample']} ---")
                    test_output = temp_dir / f"output_{pdf_path.stem}_back_{idx}.pdf"
                    if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, test_output):
                        logging.warning(f"Backtracking attempt idx={idx} failed to rebuild, retaining the previous successful result")
                        break
                    test_size = utils.get_file_size_mb(test_output)
                    logging.info(f"Backtracking attempt result size: {test_size:.2f}MB")
                    if test_size <= target_size_mb:
                        chosen_path = test_output
                    else:
                        # If the current quality exceeds the target, stop backtracking and use the last successful result.
                        logging.info("The current backtracking attempt exceeds the target, stop backtracking, and use the last successful result")
                        break

                final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                final_path.parent.mkdir(parents=True, exist_ok=True)
                utils.copy_file(chosen_path, final_path)
                logging.info(f"Success! The final file has been saved to: {final_path}")
                return True, final_path

            # Otherwise continue the subsequent configuration in order (try sequentially starting from 2)
        else:
            logging.warning("The first attempt to rebuild failed, continue to try subsequent parameters in sequence")

        # Try the remaining configurations in order (starting with the second item)
        for i in range(1, len(strategy['params_sequence'])):
            params = strategy['params_sequence'][i]
            encoder = params.get('jpeg2000_encoder', 'openjpeg')
            logging.info(f"--- Sequential attempts {i+1}/{len(strategy['params_sequence'])}: DPI={params['dpi']}, BG-Downsample={params['bg_downsample']}, JPEG2000={encoder} ---")
            output_pdf_path = temp_dir / f"output_{pdf_path.stem}_{i}.pdf"
            try:
                if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, output_pdf_path):
                    continue
                result_size_mb = utils.get_file_size_mb(output_pdf_path)
                logging.info(f"Try result size: {result_size_mb:.2f}MB (target: < {target_size_mb}MB)")
                if result_size_mb <= target_size_mb:
                    final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    utils.copy_file(output_pdf_path, final_path)
                    logging.info(f"Success! The file has been compressed and saved to: {final_path}")
                    return True, final_path
            except Exception as e:
                logging.error(f"An error occurred while trying {i+1} in sequence: {e}")
                continue

        logging.warning(f"All compression attempts failed, unable to compress {pdf_path.name} to target size.")
        return False, None

    finally:
        #Determine whether to delete the temporary directory based on the keep_temp_on_failure flag
        if keep_temp_on_failure:
            logging.info(f"Keep temporary directory for debugging: {temp_dir_str}")
        else:
            utils.cleanup_directory(temp_dir_str)

def run_aggressive_compression(pdf_path, output_dir, target_size_mb, keep_temp_on_failure=False):
    """
    Runs the most aggressive compression strategy for split file fragments.
    """
    logging.info(f"Run aggressive compression strategy on split file fragment {pdf_path.name}...")
    
    # Use the most aggressive parameter combination
    aggressive_params = [
        {'dpi': 150, 'bg_downsample': 4},
        {'dpi': 150, 'bg_downsample': 5},
        {'dpi': 120, 'bg_downsample': 3},
        {'dpi': 100, 'bg_downsample': 2},
    ]
    
    # For aggressive compression, also generate hOCR once (using highest dpi) and reuse in multiple aggressive parameters
    max_dpi = max(p['dpi'] for p in aggressive_params)
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    try:
        logging.info(f"Aggressive compression: generate image and hOCR (DPI={max_dpi}) once for multiple subsequent attempts")
        image_files = pipeline.deconstruct_pdf_to_images(pdf_path, temp_dir, max_dpi)
        if not image_files:
            logging.error("Failed to generate image for aggressive compression.")
            return False, None

        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("Failed to generate hOCR file (aggressive compression).")
            return False, None

        for i, params in enumerate(aggressive_params):
            logging.info(f"--- Aggressive compression attempt {i+1}/{len(aggressive_params)}: DPI={params['dpi']}, BG-Downsample={params['bg_downsample']} ---")
            output_pdf_path = temp_dir / f"compressed_{pdf_path.stem}_{i}.pdf"
            try:
                if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, output_pdf_path):
                    continue

                result_size_mb = utils.get_file_size_mb(output_pdf_path)
                logging.info(f"Aggressive compression result size: {result_size_mb:.2f}MB (target: < {target_size_mb}MB)")

                if result_size_mb <= target_size_mb:
                    final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    utils.copy_file(output_pdf_path, final_path)
                    logging.info(f"Aggressive compression successful! File saved to: {final_path}")
                    return True, final_path
            except Exception as e:
                logging.error(f"Error occurred during aggressive compression attempt {i+1}: {e}")
                continue

        logging.error(f"Aggressive compression failed, unable to compress {pdf_path.name} to target size.")
        return False, None
    finally:
        if keep_temp_on_failure:
            logging.info(f"Keep aggressively compressed temporary directory for debugging: {temp_dir_str}")
        else:
            utils.cleanup_directory(temp_dir_str)