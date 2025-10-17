# main.py

import argparse
import logging
import sys
from pathlib import Path
from compressor import utils
import orchestrator

def create_argument_parser():
    """Create a command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Automated PDF compression and splitting tool based on archive-pdf-tools",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Usage example:
  # Process a single file, allowing splitting
  python main.py --input document.pdf --output-dir ./output --allow-splitting

  # Process the entire directory, using default settings
  python main.py --input ./pdf_folder --output-dir ./processed

  # Custom target size is 8MB, splitting is not allowed
  python main.py --input large.pdf --output-dir ./output --target-size 8.0

Things to note:
  - Make sure you have installed the necessary tools: pdftoppm, tesseract, recode_pdf, qpdf
  - Processing of large files may take a long time
  - All processing logs are saved in the logs/process.log file
        """
    )
    
    parser.add_argument(
        "--input",
        help="The input source path can be a PDF file or a directory containing PDF files."
    )
    
    parser.add_argument(
        "--output-dir",
        help="The directory where the processed files are stored."
    )
    
    parser.add_argument(
        "--target-size",
        type=float,
        default=2.0,
        help="Target file size in MB. Default value is 2.0."
    )
    
    parser.add_argument(
        "--allow-splitting",
        action="store_true",
        help="If this argument is provided, allows splitting to be enabled when compression fails."
    )
    
    parser.add_argument(
        "--max-splits",
        type=int,
        default=4,
        choices=[2, 3, 4, 5, 6, 7, 8, 9, 10],
        help="Maximum number of splits allowed. Default is 4."
    )
    
    parser.add_argument(
        "--copy-small-files",
        action="store_true",
        help="Whether to copy files that already meet the size requirement to the output directory."
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Only checks whether dependent tools are installed, no processing is performed."
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed debugging information."
    )

    parser.add_argument(
        "-k", "--keep-temp-on-failure",
        action="store_true",
        help="If compression fails, keep temporary directory for debugging (default will be deleted on failure)."
    )
    parser.add_argument(
        "-?", "--examples",
        action="store_true",
        help="Output common parameter examples and exit."
    )
    parser.add_argument(
        "-m", "--manual",
        action="store_true",
        help="Enter interactive full manual compression mode, allowing input of DPI/bg-downsample/JPEG2000 and other parameters."
    )
    
    return parser

def print_banner():
    """Print the program startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║ PDF compression and splitting tool                           ║
║                                                              ║
║ Automated processing tool for professional title declaration ║
║ PDF files based on archive-pdf-tools                         ║
║ Implement the "Deconstruction-Analysis-Reconstruction" (DAR) ║
║ three-stage compression strategy                             ║
║                                                              ║
║ Version: 1.0.0                                               ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main function: parse parameters and distribute tasks."""
    print_banner()
    
    parser = create_argument_parser()
    args = parser.parse_args()

    # If the user requests to show example usage, print a few common commands and exit
    if getattr(args, 'examples', False):
        examples = [
            "# Compress single.pdf to target 5MB and output to out/ (in the current directory)",
            "python -m main --input single.pdf --output-dir out --target-size 5",
            "",
            "# Runs on bulk directories, allowing splitting and retaining temporary directories for debugging failures",
            "python -m main --input-dir ./pdfs --output-dir ./out --target-size 3 --allow-splitting --max-splits 4 -k",
            "",
            "# Only check dependencies, do not perform compression (for diagnostics)",
            "python -m main --check-deps",
        ]
        print("Example usage:")
        for line in examples:
            print(line)
        return
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    #Initialize the log system
    utils.setup_logging()
    
    logging.info("Program Start")
    logging.info(f"Python version: {sys.version}")
    
    # Check dependencies only
    if args.check_deps:
        print("\nChecking dependent tools...")
        if utils.check_dependencies():
            print("✓ All necessary tools have been installed")
            sys.exit(0)
        else:
            print("✗ Necessary tools are missing, please install them and try again")
            sys.exit(1)
    
    # Interactive full manual mode (standalone module) - placed before required parameter checks for standalone runs
    if getattr(args, 'manual', False):
        # Delay import to avoid affecting the normal process
        try:
            import manual_mode
        except Exception as e:
            logging.error(f"Unable to load manual mode module: {e}")
            sys.exit(1)

        manual_mode.run_manual_interactive()
        return

    # Check required parameters
    if not args.input:
        logging.error("Error: --input parameter must be specified")
        parser.print_help()
        sys.exit(1)
    
    if not args.output_dir:
        logging.error("Error: --output-dir parameter must be specified")
        parser.print_help()
        sys.exit(1)
    
    # Verify parameters
    if not orchestrator.validate_arguments(args):
        logging.error("Parameter verification failed")
        sys.exit(1)
    
    # Check dependency tools
    logging.info("Check necessary tools...")
    if not utils.check_dependencies():
        logging.error("Dependency check failed, program exited")
        sys.exit(1)
    
    input_path = Path(args.input)
    output_path = Path(args.output_dir)
    
    logging.info("=== Task starts ===")
    logging.info(f"Input path: {input_path}")
    logging.info(f"Output directory: {output_path}")
    logging.info(f"Target size: < {args.target_size} MB")
    logging.info(f"Allow splitting: {'yes' if args.allow_splitting else 'no'}")
    if args.allow_splitting:
        logging.info(f"Maximum split: {args.max_splits} part")
    logging.info(f"Copy small files: {'yes' if args.copy_small_files else 'no'}")

    try:
        if input_path.is_dir():
            # Process directory
            logging.info("Input is directory, start batch processing...")
            results = orchestrator.process_directory(input_path, args)
            
            # Generate summary report
            if results:
                orchestrator.generate_summary_report(results, output_path)
                
        elif input_path.is_file() and input_path.suffix.lower() == '.pdf':
            # Process a single file
            logging.info("Input is a single PDF file, start processing...")
            success = orchestrator.process_file(input_path, args)
            
            if success:
                logging.info("✓ File processing successful")
            else:
                logging.error("✗ File processing failed")
                sys.exit(1)
        else:
            logging.error("The input path is neither a valid directory nor a PDF file.")
            sys.exit(1)

    except KeyboardInterrupt:
        logging.warning("The user interrupted program execution")
        sys.exit(130)
    except Exception as e:
        logging.critical(f"An unexpected error occurred during program execution: {e}", exc_info=True)
        sys.exit(1)
    
    logging.info("=== All tasks completed ===")
    print("\nProcessing completed! Please check the logs/process.log file for detailed logs.")

if __name__ == "__main__":
    main()
