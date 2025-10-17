# orchestrator.py

import logging
from pathlib import Path
from compressor import utils, strategy, splitter

def process_file(file_path, args):
    """
    General entry point for processing single PDF files.
    """
    logging.info(f"================== Start processing files: {file_path.name} ==================")
    
    try:
        original_size_mb = utils.get_file_size_mb(file_path)
        logging.info(f"Original file size: {original_size_mb:.2f}MB")
        
        if original_size_mb < args.target_size:
            logging.info(f"The file size ({original_size_mb:.2f}MB) has met the requirement (< {args.target_size}MB), skipping processing.")
            # Optional: copy the files to the output directory
            if args.copy_small_files:
                output_path = Path(args.output_dir) / file_path.name
                utils.copy_file(file_path, output_path)
                logging.info(f"The original file has been copied to the output directory: {output_path}")
            return True

        # Run iterative compression
        logging.info(f"Start the iterative compression process...")
        success, result_path = strategy.run_iterative_compression(
            file_path,
            Path(args.output_dir),
            args.target_size,
            keep_temp_on_failure=getattr(args, 'keep_temp_on_failure', False)
        )

        if success:
            logging.info(f"✓ Compression successful: {file_path.name} -> {result_path.name}")
            return True
        elif args.allow_splitting:
            logging.info(f"Compression failed, but splitting is enabled. Start splitting protocol...")
            split_success = splitter.run_splitting_protocol(
                file_path, 
                Path(args.output_dir), 
                args
            )
            if split_success:
                logging.info(f"✓ Split and compress successfully: {file_path.name}")
                return True
            else:
                logging.error(f"✗ Split compression failed: {file_path.name}")
                return False
        else:
            logging.warning(f"✗ Compression failed and splitting is not enabled: {file_path.name}")
            return False

    except Exception as e:
        logging.critical(f"An unexpected error occurred while processing file {file_path.name}: {e}", exc_info=True)
        return False
    finally:
        logging.info(f"================== End of file processing: {file_path.name} ==================\n")

def process_directory(input_dir, args):
    """
    Process all PDF files in the directory.
    """
    input_path = Path(input_dir)
    logging.info(f"Start scanning directory: {input_path}")
    
    # Find all PDF files (supports case insensitivity)
    pdf_files = []
    for pattern in ["*.pdf", "*.PDF", "*.Pdf", "*.pDf", "*.pdF", "*.PdF", "*.PDf", "*.pDF"]:
        pdf_files.extend(sorted(input_path.glob(pattern)))
    
    # Deduplication (prevent file name case changes from causing duplication)
    unique_files = list(set(pdf_files))
    unique_files.sort()
    
    if not unique_files:
        logging.warning("The PDF file was not found in the specified directory.")
        return []
    
    logging.info(f"Found {len(unique_files)} PDF files, ready to process...")
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for i, pdf_file in enumerate(unique_files, 1):
        logging.info(f"\n>>> Processing progress: {i}/{len(unique_files)} <<<")
        success = process_file(pdf_file, args)
        results.append({
            'file': pdf_file,
            'success': success
        })
        
        if success:
            successful_count += 1
        else:
            failed_count += 1
    
    # Generate processing report
    logging.info(f"\n" + "="*60)
    logging.info(f"Batch processing completed")
    logging.info(f"Total number of files: {len(unique_files)}")
    logging.info(f"Processing successfully: {successful_count}")
    logging.info(f"Processing failed: {failed_count}")
    logging.info(f"Success rate: {(successful_count/len(unique_files)*100):.1f}%")
    
    if failed_count > 0:
        logging.info(f"\nFailed file list:")
        for result in results:
            if not result['success']:
                logging.info(f"  - {result['file'].name}")
    
    logging.info("="*60)
    
    return results

def generate_summary_report(results, output_dir):
    """
    Generate a summary report of processing results.
    """
    report_path = Path(output_dir) / "processing_report.txt"
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("PDF compression processing report\n")
            f.write("=" * 50 + "\n\n")
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            f.write(f"Processing time: {utils.get_current_timestamp()}\n")
            f.write(f"Total number of files: {len(results)}\n")
            f.write(f"Successful processing: {len(successful)}\n")
            f.write(f"Processing failed: {len(failed)}\n")
            f.write(f"Success rate: {(len(successful)/len(results)*100):.1f}%\n\n")
            
            if successful:
                f.write("File processed successfully:\n")
                f.write("-" * 30 + "\n")
                for result in successful:
                    f.write(f"✓ {result['file'].name}\n")
                f.write("\n")
            
            if failed:
                f.write("File processing failed:\n")
                f.write("-" * 30 + "\n")
                for result in failed:
                    f.write(f"✗ {result['file'].name}\n")
                f.write("\n")
            
            f.write("For detailed logs, please view the logs/process.log file\n")
        
        logging.info(f"Processing report has been generated: {report_path}")
        
    except Exception as e:
        logging.error(f"Error generating report: {e}")

def validate_arguments(args):
    """
    Verify the validity of command line parameters.
    """
    input_path = Path(args.input)
    output_path = Path(args.output_dir)
    
    # Check input path
    if not input_path.exists():
        logging.error(f"The input path does not exist: {input_path}")
        return False
    
    # Check target size
    if args.target_size <= 0:
        logging.error(f"Target size must be greater than 0: {args.target_size}")
        return False
    
    # Check the maximum number of splits
    if args.max_splits < 2 or args.max_splits > 10:
        logging.error(f"The maximum number of splits should be between 2-10: {args.max_splits}")
        return False
    
    #Create output directory
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Unable to create output directory {output_path}: {e}")
        return False
    
    return True