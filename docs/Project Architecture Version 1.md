Of course, in compliance with your request, we will immediately start iterative development of the project.

This is the first implementation of the project, which builds the complete core architecture and logic, and includes detailed logging functions to facilitate subsequent debugging and feature iterations. The architecture clearly divides functions into different modules and fully follows the design blueprint proposed in the research report.

### **Project Structure**

The following is the project file structure built for you:

pdf\_compressor/  
├── main.py \# Application main entry and command line interface
├── orchestrator.py \# Core business process scheduler
├── compressor/  
│   ├── \_\_init\_\_.py  
│ ├── pipeline.py \# Encapsulates the three-stage process of DAR (deconstruction-analysis-reconstruction)
│ ├── strategy.py \# Implement layered compression strategy and iterative optimization algorithm
│ ├── splitter.py \# Implement PDF splitting logic based on qpdf
│ └── utils.py \# Provides general auxiliary functions (logging, command execution, file operations)
└── logs/  
    └── process.log \# Log file output directory (automatically created)

---

### **Code File**

Below is the detailed code implementation of each file. You can save them to corresponding files and run them directly.

#### **compressor/utils.py**

This module provides the low-level helper functionality needed for the entire project.

Python

\# compressor/utils.py

import logging  
import os  
import subprocess  
import sys  
from pathlib import Path

LOG\_DIR \= "logs"

def setup\_logging():  
    """Configure the logger to output to both the console and a file."""
    log\_dir \= Path(LOG\_DIR)  
    log\_dir.mkdir(exist\_ok=True)  
    log\_file \= log\_dir / "process.log"

    \# Prevent repeated addition of processors
    if logging.getLogger().hasHandlers():  
        logging.getLogger().handlers.clear()

    logging.basicConfig(  
        level=logging.INFO,  
        format\="%(asctime)s \- %(levelname)s \- \[%(module)s:%(lineno)d\] \- %(message)s",  
        handlers=  
    )

def get\_file\_size\_mb(file\_path):  
    """Get the file size in MB."""
    try:  
        return os.path.getsize(file\_path) / (1024 \* 1024)  
    except FileNotFoundError:  
        logging.error(f"File not found: {file\_path}")
        return 0

def run\_command(command, cwd=None):  
    """  
    Execute an external command line command.

    Args:  
        command (list): A list of commands and their parameters.  
        cwd (str, optional): Working directory for command execution.

    Returns:  
        bool: Whether the command was executed successfully.
    """  
    command\_str \= ' '.join(command)  
    logging.info(f"Execute command: {command\_str}")
    try:  
        result \= subprocess.run(  
            command,  
            check=True,  
            capture\_output=True,  
            text=True,  
            encoding='utf-8',  
            errors='ignore',  
            cwd=cwd  
        )  
        if result.stdout:  
            logging.debug(f"Command output:\\n{result.stdout}")
        if result.stderr:  
            logging.warning(f"Command standard error output:\\n{result.stderr}")
        return True  
    except subprocess.CalledProcessError as e:  
        logging.error(f"Command execution failed: {command\_str}")
        logging.error(f"Return code: {e.returncode}")
        logging.error(f"standard output:\\n{e.stdout}")
        logging.error(f"Standard Error:\\n{e.stderr}")
        return False  
    except FileNotFoundError:  
        logging.error(f"Command not found: {command}. Please make sure the tool is installed and in the system PATH.")
        return False

#### **compressor/pipeline.py**

This module encapsulates the "deconstruct-analyze-reconstruct" process that interacts with external tools.

Python

\# compressor/pipeline.py

import logging  
import glob  
from pathlib import Path  
from. import utils

def deconstruct\_pdf\_to\_images(pdf\_path, temp\_dir, dpi):  
    """  
    Convert PDF to TIFF image sequence using pdftoppm.  
    Returns a list of generated image file paths.
    """  
    logging.info(f"Phase 1 \[Deconstruction\]: Start converting {pdf\_path.name} to image (DPI: {dpi})...")
    output\_prefix \= temp\_dir / "page"  
    command \= \[  
        "pdftoppm",  
        "-tiff",  
        "-r", str(dpi),  
        str(pdf\_path),  
        str(output\_prefix)  
    \]  
    if not utils.run\_command(command):  
        logging.error("PDF deconstruction failed.")
        return None  
      
    image\_files \= sorted(glob.glob(f"{output\_prefix}\-\*.tif"))  
    if not image\_files:  
        logging.error("No image file was generated.")
        return None  
          
    logging.info(f"Successfully generated {len(image\_files)} page image.")
    return \[Path(f) for f in image\_files\]

def analyze\_images\_to\_hocr(image\_files, temp\_dir):  
    """  
    Use tesseract to OCR images, generate and merge hOCR files.  
    Returns the merged hOCR file path.
    """  
    logging.info(f"Phase 2 \[Analysis\]: Start OCR on {len(image\_files)} images...")
    hocr\_files \=  
    for i, img\_path in enumerate(image\_files):  
        output\_prefix \= temp\_dir / img\_path.stem  
        command \= \[  
            "tesseract",  
            str(img\_path),  
            str(output\_prefix),  
            "-l", "chi\_sim", \# Assume Simplified Chinese
            "hocr"  
        \]  
        if not utils.run\_command(command):  
            logging.error(f"OCR of image {img\_path.name} failed.")
            return None  
        hocr\_files.append(Path(f"{output\_prefix}.hocr"))  
        logging.info(f"Complete OCR: {i+1}/{len(image\_files)}")

    \# Merge all hocr files
    combined\_hocr\_path \= temp\_dir / "combined.hocr"  
    logging.info(f"Merge hOCR files into {combined\_hocr\_path}...")
    try:  
        with open(combined\_hocr\_path, 'wb') as outfile:  
            for hocr\_file in hocr\_files:  
                with open(hocr\_file, 'rb') as infile:  
                    outfile.write(infile.read())  
    except IOError as e:  
        logging.error(f"Error merging hOCR files: {e}")
        return None

    logging.info("hOCR files merged successfully.")
    return combined\_hocr\_path

def reconstruct\_pdf(image\_files, hocr\_file, temp\_dir, params, output\_pdf\_path):  
    """  
    Use recode\_pdf to reconstruct the PDF.
    """  
    logging.info(f"Phase 3 \[Rebuild\]: Use parameters {params} to rebuild PDF...")
      
    \# recode\_pdf requires a glob pattern
    image\_stack\_glob \= str(temp\_dir / "page-\*.tif")

    command \= \[  
        "recode\_pdf",  
        "--from-imagestack", image\_stack\_glob,  
        "--hocr-file", str(hocr\_file),  
        "--dpi", str(params\['dpi'\]),  
        "--bg-downsample", str(params\['bg\_downsample'\]),  
        "--mask-compression", "jbig2",  
        "-o", str(output\_pdf\_path)  
    \]  
      
    if not utils.run\_command(command):  
        logging.error("PDF reconstruction failed.")
        return False  
          
    logging.info(f"PDF reconstruction successful, output to {output\_pdf\_path}")
    return True

#### **compressor/strategy.py**

This module defines the core compression strategy and iteration logic.

Python

\# compressor/strategy.py

import logging  
import tempfile  
from pathlib import Path  
from. import utils, pipeline

\# Define compression strategies at different levels
STRATEGIES \= {  
    1: {  \# 2MB \<= S \< 10MB  
        "name": "High Quality Compression",
        "params\_sequence": \[  
            {'dpi': 300, 'bg\_downsample': 1},  
            {'dpi': 300, 'bg\_downsample': 2},  
            {'dpi': 300, 'bg\_downsample': 3},  
            {'dpi': 250, 'bg\_downsample': 2},  
            {'dpi': 200, 'bg\_downsample': 1},  
        \]  
    },  
    2: {  \# 10MB \<= S \< 50MB  
        "name": "Balanced Compression",
        "params\_sequence": \[  
            {'dpi': 300, 'bg\_downsample': 2},  
            {'dpi': 300, 'bg\_downsample': 3},  
            {'dpi': 300, 'bg\_downsample': 4},  
            {'dpi': 250, 'bg\_downsample': 3},  
            {'dpi': 200, 'bg\_downsample': 2},  
            {'dpi': 150, 'bg\_downsample': 1},  
        \]  
    },  
    3: {  \# S \>= 50MB  
        "name": "Extreme compression",
        "params\_sequence": \[  
            {'dpi': 200, 'bg\_downsample': 3},  
            {'dpi': 200, 'bg\_downsample': 4},  
            {'dpi': 200, 'bg\_downsample': 5},  
            {'dpi': 150, 'bg\_downsample': 2},  
            {'dpi': 150, 'bg\_downsample': 3},  
        \]  
    }  
}

def determine\_tier(size\_mb):  
    """Determine the processing level based on file size."""
    if 2 \<= size\_mb \< 10:  
        return 1  
    if 10 \<= size\_mb \< 50:  
        return 2  
    if size\_mb \>= 50:  
        return 3  
    return 0 \# Less than 2MB or invalid value

def run\_iterative\_compression(pdf\_path, output\_dir, target\_size\_mb):  
    """  
    Execute an iterative compression process.  
    Return (bool, Path): (whether successful, output file path)
    """  
    original\_size\_mb \= utils.get\_file\_size\_mb(pdf\_path)  
    tier \= determine\_tier(original\_size\_mb)  
      
    if tier \== 0:  
        logging.warning(f"The size of file {pdf\_path.name} does not meet the compression range, skip.")
        return False, None

    strategy \= STRATEGIES\[tier\]  
    logging.info(f"File {pdf\_path.name} (Size: {original\_size\_mb:.2f}MB) Application Strategy: Level {tier} ({strategy\['name'\]})")

    for i, params in enumerate(strategy\['params\_sequence'\]):  
        logging.info(f"--- {i+1}/{len(strategy\['params\_sequence'\])} attempt: DPI={params\['dpi'\]}, BG-Downsample={params\['bg\_downsample'\]} \---")
          
        with tempfile.TemporaryDirectory() as temp\_dir\_str:  
            temp\_dir \= Path(temp\_dir\_str)  
            output\_pdf\_path \= temp\_dir / f"output\_{pdf\_path.stem}.pdf"

            \# 1\. Deconstruction
            image\_files \= pipeline.deconstruct\_pdf\_to\_images(pdf\_path, temp\_dir, params\['dpi'\])  
            if not image\_files: continue

            \# 2\. Analysis
            hocr\_file \= pipeline.analyze\_images\_to\_hocr(image\_files, temp\_dir)  
            if not hocr\_file: continue

            \# 3\. Rebuild
            if not pipeline.reconstruct\_pdf(image\_files, hocr\_file, temp\_dir, params, output\_pdf\_path):  
                continue

            \# 4\. Check size
            result\_size\_mb \= utils.get\_file\_size\_mb(output\_pdf\_path)  
            logging.info(f"Compressed result size: {result\_size\_mb:.2f}MB (target: \< {target\_size\_mb}MB)")

            if result\_size\_mb \<= target\_size\_mb:  
                final\_path \= output\_dir / f"{pdf\_path.stem}\_compressed.pdf"  
                output\_pdf\_path.rename(final\_path)  
                logging.info(f"Success! The file has been compressed and saved to: {final\_path}")
                return True, final\_path

    logging.warning(f"All compression attempts failed, unable to compress {pdf\_path.name} to target size.")
    return False, None

#### **compressor/splitter.py**

This module is responsible for performing PDF splitting when compression fails.

Python

\# compressor/splitter.py

import logging  
import math  
from pathlib import Path  
from. import utils, strategy

def get\_pdf\_page\_count(pdf\_path):  
    """Use \`pdfinfo\` to get the total number of pages in the PDF."""
    command \= \["pdfinfo", str(pdf\_path)\]  
    \# We need to run this command ourselves to capture the output
    try:  
        result \= subprocess.run(command, check=True, capture\_output=True, text=True, encoding='utf-8')  
        for line in result.stdout.splitlines():  
            if line.startswith("Pages:"):  
                return int(line.split(":").\[1\]strip())  
    except (subprocess.CalledProcessError, FileNotFoundError) as e:  
        logging.error(f"Failed to obtain the page number of {pdf\_path.name}: {e}")
    return 0

def split\_pdf(pdf\_path, output\_path, start\_page, end\_page):  
    """  
    Use qpdf to split PDF files.
    """  
    logging.info(f"Splitting {pdf\_path.name}: page number {start\_page}\-{end\_page} \-\> {output\_path.name}")
    command \= \[  
        "qpdf",  
        str(pdf\_path),  
        "--pages",  
        ".", \# represents the input file
        f"{start\_page}\-{end\_page}",  
        "--",  
        str(output\_path)  
    \]  
    return utils.run\_command(command)

def run\_splitting\_protocol(pdf\_path, output\_dir, args):  
    """  
    Execute split agreement.
    """  
    logging.info(f"Start emergency splitting protocol for {pdf\_path.name}...")
    total\_pages \= get\_pdf\_page\_count(pdf\_path)  
    if total\_pages \== 0:  
        logging.error("Unable to obtain page number, split aborted.")
        return

    \# Heuristic algorithm to determine the initial number of splits
    original\_size\_mb \= utils.get\_file\_size\_mb(pdf\_path)  
    \# Assume that a 25MB block can hopefully be compressed to 2MB
    initial\_k \= min(args.max\_splits, math.ceil(original\_size\_mb / 25))  
    if initial\_k \< 2: initial\_k \= 2

    for k in range(initial\_k, args.max\_splits \+ 1):  
        logging.info(f"Try splitting into {k} parts...")
        pages\_per\_split \= math.ceil(total\_pages / k)  
          
        all\_parts\_successful \= True  
        split\_files \=

        for i in range(k):  
            start\_page \= i \* pages\_per\_split \+ 1  
            end\_page \= min((i \+ 1) \* pages\_per\_split, total\_pages)  
              
            if start\_page \> total\_pages:  
                break

            part\_path \= output\_dir / f"{pdf\_path.stem}\_part{i+1}.pdf"  
              
            \# 1\. Split
            if not split\_pdf(pdf\_path, part\_path, start\_page, end\_page):  
                logging.error(f"Splitting part {i+1} failed.")
                all\_parts\_successful \= False  
                break  
              
            \# 2\. Compress the split part
            logging.info(f"Compress the split file {part\_path.name}...")
            \# For the split files, we directly use the most aggressive strategy
            \# Note: For simplicity, iterative compression is directly called here, but a more aggressive strategy can actually be passed in.
            success, compressed\_path \= strategy.run\_iterative\_compression(  
                part\_path, output\_dir, args.target\_size  
            )

            if success:  
                split\_files.append(compressed\_path)  
                part\_path.unlink() \# Delete uncompressed split files
            else:  
                logging.error(f"Compression of part {i+1} failed. Increase the number of splits...")
                all\_parts\_successful \= False  
                \# Clean up the generated files for this round
                part\_path.unlink(missing\_ok=True)  
                for f in split\_files:  
                    f.unlink(missing\_ok=True)  
                break  
          
        if all\_parts\_successful:  
            logging.info(f"Successfully split {pdf\_path.name} into {k} parts and compressed them all successfully!")
            return

    logging.error(f"Split protocol failed: Compression could not be completed even when split into {args.max\_splits} parts.")

#### **orchestrator.py**

This module is the core of the business process and determines what operations should be performed on a file.

Python

\# orchestrator.py

import logging  
from pathlib import Path  
from compressor import utils, strategy, splitter

def process\_file(file\_path, args):  
    """  
    General entry point for processing single PDF files.
    """  
    logging.info(f"================== Start processing file: {file\_path.name} \==================")
      
    try:  
        original\_size\_mb \= utils.get\_file\_size\_mb(file\_path)  
        if original\_size\_mb \< args.target\_size:  
            logging.info(f"File size ({original\_size\_mb:.2f}MB) has met the requirements, skip.")
            \# Optional: files can be copied to the output directory if desired
            \# import shutil  
            \# shutil.copy(file\_path, args.output\_dir)  
            return

        \# Run iterative compression
        success, \_ \= strategy.run\_iterative\_compression(  
            file\_path,  
            Path(args.output\_dir),  
            args.target\_size  
        )

        if not success and args.allow\_splitting:  
            logging.info(f"Compression failed and splitting function is enabled. Start splitting protocol...")
            splitter.run\_splitting\_protocol(file\_path, Path(args.output\_dir), args)  
        elif not success:  
            logging.warning(f"Compression failed and splitting is not enabled.")

    except Exception as e:  
        logging.critical(f"An unexpected error occurred while processing file {file\_path.name}: {e}", exc\_info=True)
    finally:  
        logging.info(f"================== End of file processing: {file\_path.name} \==================\\n")

#### **main.py**

This is the entry point of the program and is responsible for parsing command line arguments and starting processing.

Python

\# main.py

import argparse  
import logging  
from pathlib import Path  
from compressor import utils  
import orchestrator

def main():  
    """Main function: parse parameters and distribute tasks."""
    utils.setup\_logging()  
      
    parser \= argparse.ArgumentParser(  
        description="Automated PDF compression and splitting tool based on archive-pdf-tools.",
        formatter\_class=argparse.RawTextHelpFormatter  
    )  
    parser.add\_argument(  
        "--input",  
        required=True,  
        help\="The input source path can be a PDF file or a directory containing PDF files."
    )  
    parser.add\_argument(  
        "--output-dir",  
        required=True,  
        help\="The directory where the processed files are stored."
    )  
    parser.add\_argument(  
        "--target-size",  
        type\=float,  
        default=2.0,  
        help\="Target file size in MB. Default is 2.0."
    )  
    parser.add\_argument(  
        "--allow-splitting",  
        action="store\_true",  
        help\="If this parameter is provided, allows splitting to be enabled when compression fails."
    )  
    parser.add\_argument(  
        "--max-splits",  
        type\=int,  
        default=4,  
        choices=\[2, 3, 4\],  
        help\="Maximum number of splits allowed. Default is 4."
    )  
      
    args \= parser.parse\_args()  
      
    input\_path \= Path(args.input)  
    output\_path \= Path(args.output\_dir)  
      
    \# Make sure the output directory exists
    output\_path.mkdir(parents=True, exist\_ok=True)  
      
    logging.info(f"---task started \---")
    logging.info(f"Input path: {input\_path}")
    logging.info(f"Output directory: {output\_path}")
    logging.info(f"Target size: \< {args.target\_size} MB")
    logging.info(f"Allow splitting: {'yes' if args.allow\_splitting else 'no'}")
    if args.allow\_splitting:  
        logging.info(f"Maximum split: {args.max\_splits} part")

    if not input\_path.exists():  
        logging.error(f"The input path does not exist: {input\_path}")
        return

    if input\_path.is\_dir():  
        logging.info("Input as directory, start scanning PDF files...")
        pdf\_files \= sorted(list(input\_path.glob("\*.pdf")) \+ list(input\_path.glob("\*.PDF")))  
        if not pdf\_files:  
            logging.warning("The PDF file was not found in the specified directory.")
            return  
          
        logging.info(f"Found {len(pdf\_files)} PDF files, ready to process...")
        for pdf\_file in pdf\_files:  
            orchestrator.process\_file(pdf\_file, args)  
              
    elif input\_path.is\_file() and input\_path.suffix.lower() \== '.pdf':  
        logging.info("The input is a single PDF file, ready for processing...")
        orchestrator.process\_file(input\_path, args)  
    else:  
        logging.error("The input path is neither a valid directory nor a PDF file.")

    logging.info("--- All tasks completed \---")

if \_\_name\_\_ \== "\_\_main\_\_":  
    main()

### **How ​​to run**

1. **Save file**: Save the above code blocks to the corresponding files in the pdf\_compressor/ directory and its subdirectory compressor/.  
2. **Installation dependencies**: Make sure you have installed poppler-utils, tesseract-ocr, tesseract-ocr-chi-sim, archive-pdf-tools, and qpdf in the WSL/Ubuntu environment as required in the research report.  
3. **Execute command**: Open the terminal, enter the upper-level directory of pdf\_compressor/, and then run the program.

**Example command:**

* **Handle single large file and allow splitting:**
  Bash  
  python3 pdf\_compressor/main.py \--input /path/to/your/large\_document.pdf \--output-dir /path/to/output \--allow-splitting

* **Process all PDFs within an entire folder, using the default 2MB target size: **
  Bash  
  python3 pdf\_compressor/main.py \--input /path/to/source\_folder \--output-dir /path/to/processed\_files

* **Processing file, target set to 8MB, no splitting allowed:**
  Bash  
  python3 pdf\_compressor/main.py \--input document.pdf \--output-dir./output \--target-size 8.0

All processing details will be displayed on the console in real time and fully recorded in the pdf\_compressor/logs/process.log file, which provides great convenience for debugging and tracing.