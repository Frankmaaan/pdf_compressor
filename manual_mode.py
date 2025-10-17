"""manual_mode.py

Interactive manual compression module.
This module is as independent as possible from the main scheduler (orchestrator) and directly uses low-level functions in the pipeline to complete one-time manual reconstruction.
Supports batch manual processing of individual files or directories; optionally enables splitting (splitting calls the existing splitter protocol).
"""

import logging
from pathlib import Path
from types import SimpleNamespace
from compressor import pipeline, utils, splitter


def prompt(prompt_text, default=None, cast=str):
    """Auxiliary function: input prompt with default value and type conversion."""
    if default is not None:
        prompt_full = f"{prompt_text} [{default}]: "
    else:
        prompt_full = f"{prompt_text}: "

    val = input(prompt_full).strip()
    if val == "":
        return default
    try:
        return cast(val)
    except Exception:
        print(f"Invalid input, expected type {cast.__name__}, please try again.")
        return prompt(prompt_text, default, cast)


def run_single_manual(pdf_path: Path, dest_path: Path, dpi: int, bg_downsample: int, jpeg2000: str, keep_temp_on_failure: bool = False):
    """Run the manual DAR process on a single PDF and write the results to dest_path(Path)."""
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    success = False
    try:
        logging.info(f"Manual mode: Convert {pdf_path} to image (DPI={dpi})")
        image_files = pipeline.deconstruct_pdf_to_images(pdf_path, temp_dir, dpi)
        if not image_files:
            logging.error("Failed to generate image, manual process aborted.")
            return False

        logging.info("Run OCR to generate hOCR...")
        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("Failed to generate hOCR, manual process aborted.")
            return False

        params = {
            'dpi': dpi,
            'bg_downsample': bg_downsample,
            'jpeg2000_encoder': jpeg2000
        }

        logging.info(f"Start rebuilding PDF, parameters: {params}")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        success = pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, dest_path)
        if success:
            logging.info(f"Manual reconstruction successful: {dest_path}")
            return True
        else:
            logging.error("Manual rebuild failed.")
            # Skip cleanup if user requires temporary directory to be preserved on failure
            if keep_temp_on_failure:
                logging.info(f"Keep temporary directory for debugging: {temp_dir_str}")
                print(f"Temporary directory reserved: {temp_dir_str}")
                return False
            return False
    finally:
        # Clean only if retention is not requested or if successful
        if not (keep_temp_on_failure and not success):
            utils.cleanup_directory(temp_dir_str)


def run_manual_interactive():
    """Main interaction entrance: prompts the user to enter parameters and perform single or batch manual compression.

    Input items (as prompted):
    - Source path (single PDF or directory)
    - Destination path (if the source is a file, fill in the final output file; if it is a directory, fill in the output directory)
    - DPI (int)
    - bg-downsample (int)
    - JPEG2000 tools (openjpeg/grok)
    - Whether to enable splitting (y/n)
    - If splitting is enabled: maximum number of splits (int) and target size (MB)
    """
    print("Enter interactive full manual compression mode (Manual Mode)")

    src = prompt("Please enter the source path (PDF file or directory containing PDF)", None, str)
    if not src:
        print("Source path must be provided, exit.")
        return
    src_path = Path(src).expanduser()
    if not src_path.exists():
        print(f"Source path does not exist: {src_path}")
        return

    dest = prompt("Please enter the destination path (file or directory, depending on the source)", None, str)
    if not dest:
        print("Destination path must be provided, exit.")
        return
    dest_path = Path(dest).expanduser()

    # DPI check
    while True:
        dpi = prompt("Please enter DPI", 300, int)
        if dpi is None:
            print("DPI cannot be empty")
            continue
        if 72 <= dpi <= 1200:
            break
        print("DPI should be between 72 and 1200, please try again.")

    # bg-downsample verification
    while True:
        bg_downsample = prompt("Please enter bg-downsample", 2, int)
        if bg_downsample is None:
            print("bg-downsample cannot be empty")
            continue
        if 1 <= bg_downsample <= 10:
            break
        print("bg-downsample should be between 1 and 10, please try again.")

    # JPEG2000 checksum
    while True:
        jpeg2000 = prompt("Please select JPEG2000 tool (openjpeg/grok)", "openjpeg", str)
        if jpeg2000 is None:
            jpeg2000 = 'openjpeg'
        jpeg2000 = jpeg2000.lower()
        if jpeg2000 in ("openjpeg", "grok"):
            break
        print("Invalid option, please enter openjpeg or grok.")

    # Whether to keep the temporary directory
    keep_choice = prompt("Do you want to keep the temporary directory for debugging on failure? (y/n)", "n", str)
    keep_temp_on_failure = str(keep_choice).lower().startswith('y')

    split_choice = prompt("Enable split protocol? (y/n)", "n", str)
    do_split = str(split_choice).lower().startswith('y')

    if do_split:
        while True:
            max_splits = prompt("Maximum number of splits (2-10)", 4, int)
            if 2 <= max_splits <= 10:
                break
            print("The maximum number of splits should be between 2 and 10, please try again.")

        while True:
            target_size = prompt("Target size of each part after splitting (MB)", 2.0, float)
            if target_size is not None and target_size > 0:
                break
            print("Target size must be greater than 0, please try again.")

    # Process files or directories
    if src_path.is_file() and src_path.suffix.lower() == '.pdf':
        # If the target is a directory, construct the file name
        if dest_path.is_dir():
            out_file = dest_path / f"{src_path.stem}_manual.pdf"
        else:
            out_file = dest_path

        if do_split:
            # Use the splitting protocol: you need to construct a small object with attributes and pass it to the splitter
            args = SimpleNamespace(target_size=target_size, max_splits=max_splits, allow_splitting=True, keep_temp_on_failure=keep_temp_on_failure)
            print("Start split protocol (interactive manual)...")
            return splitter.run_splitting_protocol(src_path, dest_path, args)
        else:
            return run_single_manual(src_path, out_file, dpi, bg_downsample, jpeg2000, keep_temp_on_failure=keep_temp_on_failure)

    elif src_path.is_dir():
        # Batch directory: Make sure the destination is a directory
        out_dir = dest_path
        out_dir.mkdir(parents=True, exist_ok=True)
        pdfs = sorted([p for p in src_path.glob('*.pdf')])
        if not pdfs:
            print("PDF file not found in source directory.")
            return

        success_count = 0
        for pdf in pdfs:
            print(f"Processing: {pdf.name}")
            if do_split:
                args = SimpleNamespace(target_size=target_size, max_splits=max_splits, allow_splitting=True, keep_temp_on_failure=keep_temp_on_failure)
                ok = splitter.run_splitting_protocol(pdf, out_dir, args)
            else:
                out_file = out_dir / f"{pdf.stem}_manual.pdf"
                ok = run_single_manual(pdf, out_file, dpi, bg_downsample, jpeg2000, keep_temp_on_failure=keep_temp_on_failure)

            if ok:
                success_count += 1

        print(f"Batch processing completed: Success {success_count}/{len(pdfs)}")
        return
    else:
        print("The source path is neither a PDF file nor a directory, exit.")
        return
